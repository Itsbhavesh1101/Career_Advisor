from __future__ import annotations

from app.services.llm_client import LLMClient


def test_repair_json_recovers_after_initial_parse_failure(monkeypatch) -> None:
    client = LLMClient()

    def fake_safe_llm_call(**kwargs):  # type: ignore[no-untyped-def]
        return '{"readiness_score": 22, "readiness_level": "Very Low", "action_plan": ["Build one project"]}'

    monkeypatch.setattr(client, "_safe_llm_call", fake_safe_llm_call)

    repaired = client._repair_json_if_needed(
        endpoint="analysis",
        user_key="user:test",
        raw_text='{"readiness_score": 22, "readiness_level": "Very Low"',
    )

    assert repaired["readiness_score"] == 22
    assert repaired["readiness_level"] == "Very Low"


def test_internship_readiness_normalizes_level_aliases() -> None:
    client = LLMClient()

    normalized = client._normalize_internship_readiness_payload(
        payload={
            "readiness_score": 18,
            "readiness_level": "Very Low",
            "action_plan": ["Build portfolio projects"],
        },
        user_key="user:test",
    )

    assert normalized["readiness_level"] == "Low"


def test_internship_readiness_derives_level_from_score_when_invalid() -> None:
    client = LLMClient()

    normalized = client._normalize_internship_readiness_payload(
        payload={
            "readiness_score": 84,
            "readiness_level": "Not sure",
            "action_plan": ["Practice interviews"],
        },
        user_key="user:test",
    )

    assert normalized["readiness_level"] == "High"
