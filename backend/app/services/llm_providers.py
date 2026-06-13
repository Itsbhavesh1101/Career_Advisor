from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Protocol

from app.core.config import Settings

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore[assignment]

try:
    import boto3
    from botocore.config import Config as BotocoreConfig
except Exception:  # pragma: no cover
    boto3 = None  # type: ignore[assignment]
    BotocoreConfig = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LLMProviderResponse:
    text: str
    total_tokens: int = 0


class LLMProvider(Protocol):
    provider_name: str

    def complete(
        self,
        *,
        model: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_output_tokens: int,
        expect_json: bool,
    ) -> LLMProviderResponse:
        ...


class OpenAIChatProvider:
    provider_name = "openai"

    def __init__(self, client: Any) -> None:
        self.client = client

    def complete(
        self,
        *,
        model: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_output_tokens: int,
        expect_json: bool,
    ) -> LLMProviderResponse:
        request_payload: dict[str, Any] = {
            "model": model,
            "temperature": temperature,
            "max_tokens": max_output_tokens,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        if expect_json:
            request_payload["response_format"] = {"type": "json_object"}

        response = self.client.chat.completions.create(**request_payload)
        output_text = (response.choices[0].message.content or "").strip()
        usage = getattr(response, "usage", None)
        return LLMProviderResponse(
            text=output_text,
            total_tokens=int(getattr(usage, "total_tokens", 0) or 0),
        )


class BedrockConverseProvider:
    provider_name = "bedrock"

    def __init__(self, client: Any) -> None:
        self.client = client

    def complete(
        self,
        *,
        model: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_output_tokens: int,
        expect_json: bool,
    ) -> LLMProviderResponse:
        del expect_json
        response = self.client.converse(
            modelId=model,
            system=[{"text": system_prompt}],
            messages=[
                {
                    "role": "user",
                    "content": [{"text": user_prompt}],
                }
            ],
            inferenceConfig={
                "temperature": temperature,
                "maxTokens": max_output_tokens,
            },
        )
        content = response.get("output", {}).get("message", {}).get("content", [])
        text_parts = [
            item.get("text", "")
            for item in content
            if isinstance(item, dict) and item.get("text")
        ]
        output_text = "\n".join(text_parts).strip()
        if not output_text:
            raise ValueError("LLM returned empty response.")

        usage = response.get("usage", {})
        return LLMProviderResponse(
            text=output_text,
            total_tokens=int(usage.get("totalTokens", 0) or 0),
        )


def _create_openai_provider(settings: Settings) -> OpenAIChatProvider | None:
    if not settings.openai_api_key or OpenAI is None:
        return None

    base_url = settings.openai_base_url
    if not base_url and settings.openai_api_key.startswith("nvapi-"):
        base_url = "https://integrate.api.nvidia.com/v1"

    effective_timeout = float(settings.openai_timeout_seconds)
    is_nvidia_endpoint = settings.openai_api_key.startswith("nvapi-") or (
        isinstance(base_url, str) and "integrate.api.nvidia.com" in base_url
    )
    if is_nvidia_endpoint and effective_timeout < 45.0:
        logger.info(
            "llm_timeout_adjusted provider=nvidia configured=%s effective=%s",
            effective_timeout,
            45.0,
        )
        effective_timeout = 45.0

    client_kwargs: dict[str, Any] = {
        "api_key": settings.openai_api_key,
        "timeout": effective_timeout,
        "max_retries": 0,
    }
    if base_url:
        client_kwargs["base_url"] = base_url

    return OpenAIChatProvider(OpenAI(**client_kwargs))


def _create_bedrock_provider(settings: Settings) -> BedrockConverseProvider | None:
    if boto3 is None or BotocoreConfig is None:
        return None
    if not settings.bedrock_region:
        return None

    client = boto3.client(
        "bedrock-runtime",
        region_name=settings.bedrock_region,
        config=BotocoreConfig(
            connect_timeout=settings.bedrock_timeout_seconds,
            read_timeout=settings.bedrock_timeout_seconds,
            retries={"max_attempts": 0},
        ),
    )
    return BedrockConverseProvider(client)


def create_llm_provider(settings: Settings) -> LLMProvider | None:
    if settings.llm_provider == "bedrock":
        return _create_bedrock_provider(settings)
    return _create_openai_provider(settings)
