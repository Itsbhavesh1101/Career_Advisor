from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.llm_outputs import (
    CompanyFitLLMOutput,
    EmployabilityScoreLLMOutput,
    InternshipReadinessLLMOutput,
    PlacementRiskLLMOutput,
    RoleGapAnalysisLLMOutput,
)
from app.services.resume_service import ResumeService


def _sample_profile():
    class _P:
        certifications = 2

    return _P()


def test_resume_score_stays_bounded() -> None:
    profile = _sample_profile()
    service = ResumeService(db=None)  # type: ignore[arg-type]
    score = service._resume_score(  # type: ignore[attr-defined]
        skills=["Python", "SQL", "ML"],
        projects=["Project A", "Project B"],
        experience=["Internship"],
        education=["B.Tech"],
        profile=profile,
    )
    assert 0 <= score <= 100


def test_employability_llm_output_bounds() -> None:
    payload = {
        "overall_score": 76,
        "academic_strength": 80,
        "technical_skills": 74,
        "industry_readiness": 70,
        "resume_quality": 78,
    }
    validated = EmployabilityScoreLLMOutput.model_validate(payload)
    assert validated.overall_score == 76


def test_company_fit_llm_output_requires_unique_companies() -> None:
    payload = {
        "matches": [
            {"company": "Google", "score": 80, "rationale": "Good fit"},
            {"company": "Google", "score": 72, "rationale": "Duplicate"},
        ]
    }
    with pytest.raises(ValidationError):
        CompanyFitLLMOutput.model_validate(payload)


def test_company_fit_llm_output_requires_evidence_and_action_plan() -> None:
    payload = {
        "matches": [
            {
                "company": "Infosys",
                "score": 78,
                "rationale": "Good general fit",
            }
        ]
    }
    with pytest.raises(ValidationError):
        CompanyFitLLMOutput.model_validate(payload)


def test_role_gap_llm_output_requires_non_empty_lists() -> None:
    payload = {
        "role_gaps": [
            {
                "role": "AI Engineer",
                "missing_skills": [],
                "learning_plan": ["Build one project"],
            }
        ]
    }
    with pytest.raises(ValidationError):
        RoleGapAnalysisLLMOutput.model_validate(payload)


def test_role_gap_llm_output_requires_evidence_and_project_proof() -> None:
    payload = {
        "role_gaps": [
            {
                "role": "Backend Developer",
                "missing_skills": ["System design"],
                "learning_plan": ["Build an API project"],
            }
        ]
    }
    with pytest.raises(ValidationError):
        RoleGapAnalysisLLMOutput.model_validate(payload)


def test_placement_risk_llm_output_restricts_levels() -> None:
    payload = {"risk_level": "Critical", "reasons": ["Low CGPA"]}
    with pytest.raises(ValidationError):
        PlacementRiskLLMOutput.model_validate(payload)


def test_internship_readiness_consistency_guard() -> None:
    payload = {
        "readiness_score": 88,
        "readiness_level": "Low",
        "action_plan": ["Practice interviews"],
    }
    with pytest.raises(ValidationError):
        InternshipReadinessLLMOutput.model_validate(payload)
