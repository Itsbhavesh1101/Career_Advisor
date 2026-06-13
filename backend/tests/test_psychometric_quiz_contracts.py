from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.psychometric_quiz import (
    PsychometricAnswerSubmit,
    PsychometricQuestionLLMOutput,
)
from app.services.psychometric_fallback_bank import (
    fallback_traits_coverage,
    has_full_fallback_coverage,
    select_fallback_question,
)


EXPECTED_TRAITS = {
    "analytical",
    "creativity",
    "execution",
    "collaboration",
    "risk_tolerance",
    "learning_agility",
    "domain_curiosity",
}


def test_fallback_bank_has_full_coverage() -> None:
    assert has_full_fallback_coverage()
    assert EXPECTED_TRAITS.issubset(fallback_traits_coverage("college_student"))
    assert EXPECTED_TRAITS.issubset(fallback_traits_coverage("twelfth_student"))


def test_psychometric_llm_output_rejects_invalid_option() -> None:
    payload = {
        "question": "How do you solve complex tasks?",
        "trait_tag": "analytical",
        "options": [
            {
                "option_id": "a",
                "text": "Break it down",
                "trait_effect": {"analytical": 0.2},
            },
            {
                "option_id": "b",
                "text": "Try random steps",
                "trait_effect": {},
            },
            {
                "option_id": "c",
                "text": "Ask peers",
                "trait_effect": {"collaboration": 0.12},
            },
        ],
    }

    with pytest.raises(ValidationError):
        PsychometricQuestionLLMOutput.model_validate(payload)


def test_answer_payload_caps_stale_response_time() -> None:
    payload = PsychometricAnswerSubmit.model_validate(
        {
            "question_id": "q-1",
            "option_id": "a",
            "response_ms": 515041,
        }
    )

    assert payload.response_ms == 300000


def test_guided_fallback_targets_low_confidence_trait() -> None:
    payload = select_fallback_question(
        user_type="twelfth_student",
        asked_trait_tags={"analytical", "creativity"},
        position=3,
        current_traits={
            "analytical": 0.7,
            "creativity": 0.68,
            "execution": 0.25,
            "collaboration": 0.58,
        },
        recent_answers=[{"trait_tag": "analytical"}, {"trait_tag": "creativity"}],
    )

    assert payload["trait_tag"] == "execution"
    assert payload["ai_status"] == "guided_adaptive"
    assert "execution" in payload["adaptation_reason"].lower()


def test_guided_fallback_rotates_variants_after_trait_coverage() -> None:
    first = select_fallback_question(
        user_type="college_student",
        asked_trait_tags=EXPECTED_TRAITS,
        position=8,
        current_traits={"execution": 0.3, "analytical": 0.7},
        recent_answers=[],
    )
    second = select_fallback_question(
        user_type="college_student",
        asked_trait_tags=EXPECTED_TRAITS,
        position=9,
        current_traits={"execution": 0.3, "analytical": 0.7},
        recent_answers=[],
    )

    assert first["trait_tag"] == "execution"
    assert second["trait_tag"] == "execution"
    assert first["question"] != second["question"]
