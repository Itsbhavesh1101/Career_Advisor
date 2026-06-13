from __future__ import annotations

import json
import re
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.services.ai_engine import CareerAIEngine
from app.services.llm_client import LLMClient
from app.schemas.llm_outputs import (
    BranchAnalysisLLMOutput,
    CareerAnalysisLLMOutput,
    CompanyFitAdjustments,
    EmployabilityAdjustments,
    ProgramFitLLMOutput,
)
from app.services.llm_cost_control import (
    get_llm_events,
    get_llm_usage,
    record_llm_event,
    record_llm_usage,
)


def test_career_analysis_output_rejects_extra_fields() -> None:
    payload = {
        "career_recommendations": [{"role": "AI Engineer", "score": 82}],
        "skill_gaps": [{"skill": "Machine Learning", "priority": "high"}],
        "learning_roadmap": [{"stage": "Foundations", "topics": ["Python"]}],
        "salary_insights": {
            "currency": "INR",
            "estimate_min": 600000,
            "estimate_max": 1200000,
            "extra": "not-allowed",
        },
        "industry_trends": [{"trend": "AI Agents", "impact": "high"}],
    }

    with pytest.raises(ValidationError):
        CareerAnalysisLLMOutput.model_validate(payload)


def test_salary_range_validation_enforced() -> None:
    payload = {
        "career_recommendations": [{"role": "AI Engineer", "score": 82}],
        "skill_gaps": [{"skill": "Machine Learning", "priority": "high"}],
        "learning_roadmap": [{"stage": "Foundations", "topics": ["Python"]}],
        "salary_insights": {
            "currency": "INR",
            "estimate_min": 900000,
            "estimate_max": 600000,
        },
        "industry_trends": [{"trend": "AI Agents", "impact": "high"}],
    }

    with pytest.raises(ValidationError):
        CareerAnalysisLLMOutput.model_validate(payload)


def test_company_fit_delta_bounds_enforced() -> None:
    with pytest.raises(ValidationError):
        CompanyFitAdjustments.model_validate({"Google": 999})


def test_employability_delta_bounds_enforced() -> None:
    with pytest.raises(ValidationError):
        EmployabilityAdjustments.model_validate({"academic_delta": -99})


def test_branch_schema_restricts_recommended_branch() -> None:
    payload = {
        "aiml_score": 80,
        "cyber_security_score": 70,
        "recommended_branch": "AIML/Cyber",
        "branch_reasoning": [{"reason": "Strong logic"}],
        "aiml_roles": [{"role": "Machine Learning Engineer", "score": 88}],
        "cyber_roles": [{"role": "Security Analyst", "score": 78}],
        "aiml_skills": ["Python"],
        "cyber_skills": ["Linux"],
        "aiml_roadmap": [{"year": 1, "topics": ["Python"]}],
        "cyber_roadmap": [{"year": 1, "topics": ["Networking"]}],
        "industry_insights": [{"branch": "AIML", "insight": "Growing market"}],
    }

    with pytest.raises(ValidationError):
        BranchAnalysisLLMOutput.model_validate(payload)


def test_program_fit_schema_rejects_unknown_fit_level() -> None:
    payload = {
        "program_fit_summary": {
            "recommended_program_id": "sirt-btech-cse-aiml",
            "recommended_program_name": "B.Tech CSE - AIML",
            "confidence": 88,
            "summary": "Strong fit for programming and mathematics.",
        },
        "program_recommendations": [
            {
                "program_id": "sirt-btech-cse-aiml",
                "program_name": "B.Tech CSE - AIML",
                "school": "SIRT Engineering",
                "fit_score": 88,
                "fit_level": "Excellent",
                "reasons": ["Strong mathematics"],
                "career_paths": ["Machine Learning Engineer"],
                "priority_skills": ["Python"],
                "first_year_focus": ["Python foundations"],
            }
        ],
        "expectation_reality_checks": [
            {
                "expectation": "AI means only model training.",
                "reality": "AI starts with programming, mathematics, and data handling.",
                "counselor_note": "Explain first-year foundation path.",
            }
        ],
        "first_year_roadmap": [
            {
                "term": "Semester 1",
                "focus": ["Programming fundamentals"],
                "evidence_to_build": ["Mini project"],
            }
        ],
        "counselor_summary": {
            "best_fit": "B.Tech CSE - AIML",
            "risk_flags": ["May underestimate mathematics"],
            "talking_points": ["Discuss daily coding practice"],
            "follow_up_questions": ["Can you practice coding daily?"],
        },
    }

    with pytest.raises(ValidationError):
        ProgramFitLLMOutput.model_validate(payload)


def test_program_fit_schema_accepts_high_medium_low_levels() -> None:
    payload = {
        "program_fit_summary": {
            "recommended_program_id": "sirt-btech-cse-aiml",
            "recommended_program_name": "B.Tech CSE - AIML",
            "confidence": 88,
            "summary": "Strong fit for programming and mathematics.",
        },
        "program_recommendations": [
            {
                "program_id": "sirt-btech-cse-aiml",
                "program_name": "B.Tech CSE - AIML",
                "school": "SIRT Engineering",
                "fit_score": 88,
                "fit_level": "High",
                "reasons": ["Strong mathematics"],
                "career_paths": ["Machine Learning Engineer"],
                "priority_skills": ["Python"],
                "first_year_focus": ["Python foundations"],
            },
            {
                "program_id": "sirt-btech-cse-cyber",
                "program_name": "B.Tech CSE - Cyber Security",
                "school": "SIRT Engineering",
                "fit_score": 64,
                "fit_level": "Medium",
                "reasons": ["Moderate systems interest"],
                "career_paths": ["Security Analyst"],
                "priority_skills": ["Networking"],
                "first_year_focus": ["Linux basics"],
            },
            {
                "program_id": "sage-bba",
                "program_name": "BBA",
                "school": "SAGE Management",
                "fit_score": 34,
                "fit_level": "Low",
                "reasons": ["Less business-facing interest"],
                "career_paths": ["Operations Associate"],
                "priority_skills": ["Communication"],
                "first_year_focus": ["Business fundamentals"],
            },
        ],
        "expectation_reality_checks": [
            {
                "expectation": "AI means only model training.",
                "reality": "AI starts with programming, mathematics, and data handling.",
                "counselor_note": "Explain first-year foundation path.",
            }
        ],
        "first_year_roadmap": [
            {
                "term": "Semester 1",
                "focus": ["Programming fundamentals"],
                "evidence_to_build": ["Mini project"],
            }
        ],
        "counselor_summary": {
            "best_fit": "B.Tech CSE - AIML",
            "risk_flags": ["May underestimate mathematics"],
            "talking_points": ["Discuss daily coding practice"],
            "follow_up_questions": ["Can you practice coding daily?"],
        },
    }

    parsed = ProgramFitLLMOutput.model_validate(payload)

    assert [item.fit_level for item in parsed.program_recommendations] == [
        "High",
        "Medium",
        "Low",
    ]


def _student_profile() -> SimpleNamespace:
    return SimpleNamespace(
        id=101,
        user_id=202,
        name="Test Student",
        twelfth_percentage=82,
        subjects=["Physics", "Mathematics"],
        math_strength="High",
        logical_reasoning="Medium",
        programming_interest="High",
        interests=["AI"],
        current_skills=["Python"],
        degree="B.Tech",
        specialization="CSE",
    )


def _program_options(count: int = 1) -> list[dict]:
    return [
        {
            "program_id": f"sirt-btech-cse-{index}",
            "program_name": f"B.Tech CSE Option {index}",
            "school": "SIRT Engineering",
            "priority_skills": ["Python"],
            "career_paths": ["Software Developer"],
            "admission_fit_signals": ["Programming interest"],
            "reality_checks": ["Requires steady coding practice"],
            "internal_notes": "must not reach prompt",
            "is_active": index != count,
        }
        for index in range(count)
    ]


def _program_fit_payload(
    *,
    summary_program_id: str = "sirt-btech-cse-0",
    recommendation_program_id: str = "sirt-btech-cse-0",
) -> dict:
    return {
        "program_fit_summary": {
            "recommended_program_id": summary_program_id,
            "recommended_program_name": "B.Tech CSE Option 0",
            "confidence": 88,
            "summary": "Strong fit for programming and mathematics.",
        },
        "program_recommendations": [
            {
                "program_id": recommendation_program_id,
                "program_name": "B.Tech CSE Option 0",
                "school": "SIRT Engineering",
                "fit_score": 88,
                "fit_level": "High",
                "reasons": ["Strong mathematics"],
                "career_paths": ["Software Developer"],
                "priority_skills": ["Python"],
                "first_year_focus": ["Python foundations"],
            }
        ],
        "expectation_reality_checks": [
            {
                "expectation": "AI means only model training.",
                "reality": "AI starts with programming, mathematics, and data handling.",
                "counselor_note": "Explain first-year foundation path.",
            }
        ],
        "first_year_roadmap": [
            {
                "term": "Semester 1",
                "focus": ["Programming fundamentals"],
                "evidence_to_build": ["Mini project"],
            }
        ],
        "counselor_summary": {
            "best_fit": "B.Tech CSE Option 0",
            "risk_flags": ["May underestimate mathematics"],
            "talking_points": ["Discuss daily coding practice"],
            "follow_up_questions": ["Can you practice coding daily?"],
        },
    }


def test_program_fit_rejects_hallucinated_recommendation_program_id() -> None:
    client = object.__new__(LLMClient)
    client._safe_llm_call = lambda **_kwargs: "{}"  # type: ignore[attr-defined]
    client._repair_json_if_needed = lambda **_kwargs: _program_fit_payload(  # type: ignore[attr-defined]
        recommendation_program_id="made-up-program"
    )
    before = get_llm_events("user:202", "program_fit").get("schema_fail", 0)

    with pytest.raises(ValueError, match="unknown configured program"):
        client.generate_program_fit_analysis(
            _student_profile(),
            _program_options(),
            "sage-initial-2026-05",
        )

    after = get_llm_events("user:202", "program_fit").get("schema_fail", 0)
    assert after - before == 1


def test_program_fit_rejects_summary_program_id_missing_from_recommendations() -> None:
    client = object.__new__(LLMClient)
    client._safe_llm_call = lambda **_kwargs: "{}"  # type: ignore[attr-defined]
    client._repair_json_if_needed = lambda **_kwargs: _program_fit_payload(  # type: ignore[attr-defined]
        summary_program_id="sirt-btech-cse-1",
        recommendation_program_id="sirt-btech-cse-0",
    )

    with pytest.raises(ValueError, match="unknown configured program"):
        client.generate_program_fit_analysis(
            _student_profile(),
            _program_options(count=2),
            "sage-initial-2026-05",
        )


def test_program_fit_requires_configured_program_options_before_llm_call() -> None:
    client = object.__new__(LLMClient)

    def fail_if_called(**_kwargs):
        raise AssertionError("LLM should not be called without configured programs")

    client._safe_llm_call = fail_if_called  # type: ignore[attr-defined]

    with pytest.raises(ValueError, match="configured program option"):
        client.generate_program_fit_analysis(
            _student_profile(),
            [],
            "sage-initial-2026-05",
        )


def test_program_fit_prompt_uses_bounded_canonical_program_options() -> None:
    client = object.__new__(LLMClient)
    captured: dict[str, str] = {}

    def capture_prompt(**kwargs):
        captured["user_prompt"] = kwargs["user_prompt"]
        return "{}"

    client._safe_llm_call = capture_prompt  # type: ignore[attr-defined]
    client._repair_json_if_needed = lambda **_kwargs: _program_fit_payload()  # type: ignore[attr-defined]

    client.generate_program_fit_analysis(
        _student_profile(),
        _program_options(count=14),
        "sage-initial-2026-05",
    )

    match = re.search(
        r"Program options JSON: (.*)\nRetrieved institution evidence JSON:",
        captured["user_prompt"],
        re.DOTALL,
    )
    assert match is not None
    prompt_options = json.loads(match.group(1))

    assert len(prompt_options) == 12
    assert set(prompt_options[0]) == {
        "program_id",
        "program_name",
        "school",
        "priority_skills",
        "career_paths",
        "admission_fit_signals",
        "reality_checks",
    }
    assert "internal_notes" not in prompt_options[0]


def test_program_fit_prompt_includes_bounded_rag_context() -> None:
    client = object.__new__(LLMClient)
    captured: dict[str, str] = {}

    def capture_prompt(**kwargs):
        captured["user_prompt"] = kwargs["user_prompt"]
        return json.dumps(_program_fit_payload())

    client._safe_llm_call = capture_prompt  # type: ignore[attr-defined]

    client.generate_program_fit_analysis(
        _student_profile(),
        [
            {
                "program_id": "sirt-btech-cse-0",
                "program_name": "B.Tech CSE - AIML",
                "school": "SIRT Engineering",
            }
        ],
        "test-catalog",
        rag_context=[
            {
                "source_title": "AIML Foundation",
                "source_type": "program",
                "excerpt": "AIML requires Python and mathematics.",
                "internal_note": "must not be sent",
            }
        ],
    )

    assert "AIML Foundation" in captured["user_prompt"]
    assert "AIML requires Python and mathematics." in captured["user_prompt"]
    assert "internal_note" not in captured["user_prompt"]


def test_program_fit_engine_cache_key_includes_program_options_and_source() -> None:
    calls: list[list[dict]] = []

    def generate_program_fit_analysis(
        profile,
        program_options,
        catalog_version,
        rag_context=None,
    ):
        del profile, catalog_version, rag_context
        calls.append(program_options)
        return {
            "program_fit_summary": {
                "recommended_program_id": program_options[0]["program_id"]
            }
        }

    engine = CareerAIEngine(use_llm=False)
    engine.use_llm = True
    engine._llm_client = SimpleNamespace(
        client=object(),
        generate_program_fit_analysis=generate_program_fit_analysis,
    )

    first = engine.generate_program_fit_analysis(
        _student_profile(),
        _program_options(count=1),
        "sage-initial-2026-05",
    )
    second_options = _program_options(count=1)
    second_options[0]["program_id"] = "sirt-btech-cse-new"
    second = engine.generate_program_fit_analysis(
        _student_profile(),
        second_options,
        "sage-initial-2026-05",
    )
    second_options_with_new_internal_note = [dict(second_options[0])]
    second_options_with_new_internal_note[0]["internal_notes"] = "changed raw-only metadata"
    third = engine.generate_program_fit_analysis(
        _student_profile(),
        second_options_with_new_internal_note,
        "sage-initial-2026-05",
    )

    assert len(calls) == 2
    assert first != second
    assert third == second
    assert engine.branch_analysis_source == "not_applicable"
    assert engine.program_fit_analysis_source == "llm"


def test_llm_event_counter_tracks_events() -> None:
    user_key = "user:test-metrics"
    endpoint = "analysis"
    record_llm_event(user_key=user_key, endpoint=endpoint, event="schema_fail")
    record_llm_event(user_key=user_key, endpoint=endpoint, event="schema_fail")
    record_llm_event(user_key=user_key, endpoint=endpoint, event="fallback")

    events = get_llm_events(user_key, endpoint)
    assert events["schema_fail"] >= 2
    assert events["fallback"] >= 1


def test_llm_usage_isolated_by_scope() -> None:
    user_key = "user:test-scope"
    endpoint = "quiz_generation"
    scope_a = "quiz_session:scope-a"
    scope_b = "quiz_session:scope-b"

    before_a = int(get_llm_usage(user_key, endpoint, usage_scope=scope_a).get("tokens", 0))
    before_b = int(get_llm_usage(user_key, endpoint, usage_scope=scope_b).get("tokens", 0))

    record_llm_usage(
        user_key=user_key,
        endpoint=endpoint,
        usage_scope=scope_a,
        prompt_chars=100,
        output_chars=40,
        total_tokens=25,
    )
    record_llm_usage(
        user_key=user_key,
        endpoint=endpoint,
        usage_scope=scope_b,
        prompt_chars=80,
        output_chars=35,
        total_tokens=11,
    )

    usage_a = get_llm_usage(user_key, endpoint, usage_scope=scope_a)
    usage_b = get_llm_usage(user_key, endpoint, usage_scope=scope_b)

    assert int(usage_a["tokens"]) - before_a == 25
    assert int(usage_b["tokens"]) - before_b == 11
