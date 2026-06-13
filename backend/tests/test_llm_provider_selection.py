from __future__ import annotations

import os

import pytest

import app.core.config as config
import app.services.llm_providers as providers
from app.core.config import Settings
from app.services.llm_client import LLMClient
from app.services.llm_providers import (
    BedrockConverseProvider,
    LLMProviderResponse,
    OpenAIChatProvider,
    create_llm_provider,
)


def _base_settings(**overrides):
    values = {
        "database_url": "postgresql+psycopg://postgres:postgres@localhost:5432/test",
        "jwt_secret": "x" * 32,
    }
    values.update(overrides)
    return Settings(**values)


def test_settings_accepts_openai_and_bedrock_providers() -> None:
    assert _base_settings(llm_provider="openai").llm_provider == "openai"
    assert (
        _base_settings(
            llm_provider="bedrock",
            bedrock_region="ap-south-1",
        ).llm_provider
        == "bedrock"
    )


def test_settings_accepts_institution_modes() -> None:
    assert _base_settings(institution_mode="sage").institution_mode == "sage"
    assert _base_settings(institution_mode="generic").institution_mode == "generic"


def test_invalid_institution_mode_is_rejected() -> None:
    with pytest.raises(Exception):
        _base_settings(institution_mode="other-college")


def test_settings_from_env_reads_institution_mode(monkeypatch) -> None:
    monkeypatch.setattr(config, "load_dotenv", lambda override=False: None)
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/test",
    )
    monkeypatch.setenv("JWT_SECRET", "x" * 32)
    monkeypatch.setenv("INSTITUTION_MODE", "generic")

    settings = Settings.from_env()

    assert settings.institution_mode == "generic"


def test_bedrock_settings_accept_region_model_and_timeout() -> None:
    settings = _base_settings(
        llm_provider="bedrock",
        bedrock_region="ap-south-1",
        bedrock_model_id="amazon.nova-pro-v1:0",
        bedrock_timeout_seconds=60,
    )

    assert settings.bedrock_region == "ap-south-1"
    assert settings.bedrock_model_id == "amazon.nova-pro-v1:0"
    assert settings.bedrock_timeout_seconds == 60


def test_bedrock_settings_use_required_defaults() -> None:
    settings = _base_settings(
        llm_provider="bedrock",
        bedrock_region="ap-south-1",
    )

    assert settings.bedrock_model_id == "apac.amazon.nova-lite-v1:0"
    assert settings.bedrock_timeout_seconds == 45


def test_settings_from_env_reads_bedrock_region_fallback(monkeypatch) -> None:
    monkeypatch.setattr(config, "load_dotenv", lambda override=False: None)
    for key in list(os.environ):
        if key.startswith(("LLM_", "BEDROCK_", "AWS_")):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/test",
    )
    monkeypatch.setenv("JWT_SECRET", "x" * 32)
    monkeypatch.setenv("LLM_PROVIDER", "bedrock")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("BEDROCK_MODEL_ID", "amazon.nova-micro-v1:0")
    monkeypatch.setenv("BEDROCK_TIMEOUT_SECONDS", "30")

    settings = Settings.from_env()

    assert settings.llm_provider == "bedrock"
    assert settings.bedrock_region == "us-east-1"
    assert settings.bedrock_model_id == "amazon.nova-micro-v1:0"
    assert settings.bedrock_timeout_seconds == 30


def test_invalid_llm_provider_is_rejected() -> None:
    with pytest.raises(Exception):
        _base_settings(llm_provider="unsupported")


def test_bedrock_provider_requires_region() -> None:
    with pytest.raises(Exception):
        _base_settings(llm_provider="bedrock")


def test_bedrock_timeout_must_be_positive() -> None:
    with pytest.raises(Exception):
        _base_settings(
            llm_provider="bedrock",
            bedrock_region="ap-south-1",
            bedrock_timeout_seconds=0,
        )


class _FakeBedrockClient:
    def __init__(self) -> None:
        self.calls = []

    def converse(self, **kwargs):
        self.calls.append(kwargs)
        return {
            "output": {
                "message": {
                    "content": [
                        {"text": "{\"ok\": true}"},
                    ]
                }
            },
            "usage": {"totalTokens": 17},
        }


class _FakeEmptyBedrockClient(_FakeBedrockClient):
    def converse(self, **kwargs):
        self.calls.append(kwargs)
        return {
            "output": {
                "message": {
                    "content": [
                        {"text": "   "},
                        {"image": {"format": "png"}},
                    ]
                }
            },
            "usage": {"totalTokens": 5},
        }


class _FakeOpenAICompletions:
    def __init__(self) -> None:
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        message = type("Message", (), {"content": " {\"ok\": true} "})()
        choice = type("Choice", (), {"message": message})()
        usage = type("Usage", (), {"total_tokens": 23})()
        return type("Response", (), {"choices": [choice], "usage": usage})()


class _FakeOpenAIClient:
    def __init__(self) -> None:
        self.chat = type(
            "Chat",
            (),
            {"completions": _FakeOpenAICompletions()},
        )()


class _FakeOpenAIConstructor(_FakeOpenAIClient):
    calls = []

    def __init__(self, **kwargs) -> None:
        super().__init__()
        self.__class__.calls.append(kwargs)


class _FakeBotocoreConfig:
    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs


class _FakeBoto3:
    def __init__(self) -> None:
        self.calls = []
        self.client_instance = _FakeBedrockClient()

    def client(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self.client_instance


class _FakeProvider:
    provider_name = "fake"

    def __init__(self) -> None:
        self.calls = []

    def complete(self, **kwargs):
        self.calls.append(kwargs)
        return LLMProviderResponse(
            text="{\"career_recommendations\": []}",
            total_tokens=3,
        )


def test_bedrock_provider_uses_converse_payload() -> None:
    fake = _FakeBedrockClient()
    provider = BedrockConverseProvider(client=fake)

    response = provider.complete(
        model="apac.amazon.nova-lite-v1:0",
        system_prompt="Return JSON.",
        user_prompt="Hello",
        temperature=0.2,
        max_output_tokens=100,
        expect_json=True,
    )

    assert response == LLMProviderResponse(text="{\"ok\": true}", total_tokens=17)
    call = fake.calls[0]
    assert call["modelId"] == "apac.amazon.nova-lite-v1:0"
    assert call["system"] == [{"text": "Return JSON."}]
    assert call["messages"] == [{"role": "user", "content": [{"text": "Hello"}]}]
    assert call["inferenceConfig"] == {"temperature": 0.2, "maxTokens": 100}


def test_bedrock_provider_rejects_empty_text_content() -> None:
    fake = _FakeEmptyBedrockClient()
    provider = BedrockConverseProvider(client=fake)

    with pytest.raises(ValueError, match="empty response"):
        provider.complete(
            model="apac.amazon.nova-lite-v1:0",
            system_prompt="Return JSON.",
            user_prompt="Hello",
            temperature=0.2,
            max_output_tokens=100,
            expect_json=True,
        )


def test_openai_provider_preserves_chat_completion_payload() -> None:
    fake = _FakeOpenAIClient()
    provider = OpenAIChatProvider(client=fake)

    response = provider.complete(
        model="gpt-4.1-mini",
        system_prompt="Return JSON.",
        user_prompt="Hello",
        temperature=0.3,
        max_output_tokens=50,
        expect_json=True,
    )

    assert response == LLMProviderResponse(text="{\"ok\": true}", total_tokens=23)
    call = fake.chat.completions.calls[0]
    assert call == {
        "model": "gpt-4.1-mini",
        "temperature": 0.3,
        "max_tokens": 50,
        "messages": [
            {"role": "system", "content": "Return JSON."},
            {"role": "user", "content": "Hello"},
        ],
        "response_format": {"type": "json_object"},
    }


def test_openai_provider_omits_response_format_when_json_not_expected() -> None:
    fake = _FakeOpenAIClient()
    provider = OpenAIChatProvider(client=fake)

    provider.complete(
        model="gpt-4.1-mini",
        system_prompt="System",
        user_prompt="Hello",
        temperature=0.3,
        max_output_tokens=50,
        expect_json=False,
    )

    call = fake.chat.completions.calls[0]
    assert "response_format" not in call


def test_provider_factory_returns_none_when_openai_key_missing() -> None:
    settings = _base_settings(llm_provider="openai", openai_api_key=None)

    assert create_llm_provider(settings) is None


def test_provider_factory_returns_openai_provider_when_key_and_import_exist(
    monkeypatch,
) -> None:
    _FakeOpenAIConstructor.calls = []
    monkeypatch.setattr(providers, "OpenAI", _FakeOpenAIConstructor)
    settings = _base_settings(
        llm_provider="openai",
        openai_api_key="test-key",
        openai_base_url="https://example.test/v1",
        openai_timeout_seconds=12,
    )

    provider = create_llm_provider(settings)

    assert isinstance(provider, OpenAIChatProvider)
    assert _FakeOpenAIConstructor.calls == [
        {
            "api_key": "test-key",
            "timeout": 12.0,
            "max_retries": 0,
            "base_url": "https://example.test/v1",
        }
    ]


def test_provider_factory_returns_bedrock_provider_when_region_and_import_exist(
    monkeypatch,
) -> None:
    fake_boto3 = _FakeBoto3()
    monkeypatch.setattr(providers, "boto3", fake_boto3)
    monkeypatch.setattr(providers, "BotocoreConfig", _FakeBotocoreConfig)
    settings = _base_settings(
        llm_provider="bedrock",
        bedrock_region="ap-south-1",
        bedrock_timeout_seconds=35,
    )

    provider = create_llm_provider(settings)

    assert isinstance(provider, BedrockConverseProvider)
    assert provider.client is fake_boto3.client_instance
    assert fake_boto3.calls[0][0] == ("bedrock-runtime",)
    assert fake_boto3.calls[0][1]["region_name"] == "ap-south-1"
    assert fake_boto3.calls[0][1]["config"].kwargs == {
        "connect_timeout": 35,
        "read_timeout": 35,
        "retries": {"max_attempts": 0},
    }


def test_llm_client_safe_call_uses_provider() -> None:
    settings = _base_settings(openai_api_key="test-key", openai_max_retries=1)
    provider = _FakeProvider()
    client = object.__new__(LLMClient)
    client._settings = settings
    client.model = "test-model"
    client.provider = provider
    client.client = provider

    text = client._safe_llm_call(
        endpoint="analysis",
        user_key="user:provider-test",
        system_prompt="System",
        user_prompt="User",
        temperature=0.1,
        max_output_tokens=20,
        expect_json=True,
    )

    assert text == "{\"career_recommendations\": []}"
    assert provider.calls[0]["model"] == "test-model"
    assert provider.calls[0]["system_prompt"] == "System"
    assert provider.calls[0]["user_prompt"] == "User"
    assert provider.calls[0]["temperature"] == 0.1
    assert provider.calls[0]["max_output_tokens"] == 20
    assert provider.calls[0]["expect_json"] is True


def test_generic_program_fit_prompt_has_no_sage_or_sirt_context() -> None:
    settings = _base_settings(institution_mode="generic")
    client = object.__new__(LLMClient)
    client._settings = settings
    captured: dict[str, str] = {}

    def _fake_safe_llm_call(**kwargs):
        captured["system_prompt"] = kwargs["system_prompt"]
        captured["user_prompt"] = kwargs["user_prompt"]
        return """
        {
          "program_fit_summary": {
            "recommended_program_id": "generic-btech-cse-ai",
            "recommended_program_name": "B.Tech CSE - Artificial Intelligence",
            "confidence": 84,
            "summary": "Strong fit for programming and applied AI goals."
          },
          "program_recommendations": [{
            "program_id": "generic-btech-cse-ai",
            "program_name": "B.Tech CSE - Artificial Intelligence",
            "school": "School of Engineering",
            "fit_score": 84,
            "fit_level": "High",
            "reasons": ["Strong mathematics"],
            "career_paths": ["AI Application Developer"],
            "priority_skills": ["Python"],
            "first_year_focus": ["Programming foundations"]
          }],
          "expectation_reality_checks": [{
            "expectation": "AI starts with model building",
            "reality": "First year focuses on programming and mathematics.",
            "counselor_note": "Explain the foundation path."
          }],
          "first_year_roadmap": [{
            "term": "Semester 1",
            "focus": ["Programming fundamentals"],
            "evidence_to_build": ["Mini project"]
          }],
          "counselor_summary": {
            "best_fit": "B.Tech CSE - Artificial Intelligence",
            "risk_flags": ["May underestimate mathematics"],
            "talking_points": ["Discuss daily coding practice"],
            "follow_up_questions": ["Can you practice coding daily?"]
          }
        }
        """

    client._safe_llm_call = _fake_safe_llm_call
    profile = type(
        "Profile",
        (),
        {
            "id": 1,
            "user_id": 10,
            "name": "Student",
            "subjects": ["Maths", "Physics"],
            "twelfth_percentage": 82,
            "math_strength": "high",
            "logical_reasoning": "high",
            "programming_interest": "medium",
            "interests": ["AI"],
            "current_skills": ["Python"],
            "degree": "B.Tech",
            "specialization": "CSE",
        },
    )()

    client.generate_program_fit_analysis(
        profile,
        [
            {
                "program_id": "generic-btech-cse-ai",
                "program_name": "B.Tech CSE - Artificial Intelligence",
                "school": "School of Engineering",
                "priority_skills": ["Python"],
                "career_paths": ["AI Application Developer"],
                "admission_fit_signals": ["Strong mathematics"],
                "reality_checks": ["AI requires coding practice."],
            }
        ],
        "generic-initial-2026-05",
    )

    prompt_text = f"{captured['system_prompt']}\n{captured['user_prompt']}"
    assert "Student Success Navigator" in prompt_text
    assert "Partner Institution" in prompt_text
    assert "SAGE" not in prompt_text
    assert "SIRT" not in prompt_text
