from __future__ import annotations

from app.services.analysis_verifier_service import AnalysisVerifierService


def test_verifier_approves_complete_college_snapshot() -> None:
    summary = {
        "profile_id": 1,
        "user_type": "college_student",
        "career_analysis_id": 101,
        "career_analysis_source": "llm",
        "branch_analysis_source": "not_applicable",
        "placement_risk_id": 201,
        "internship_readiness_id": 202,
        "employability_score_id": 203,
        "company_fit_id": 204,
        "role_gap_id": 205,
        "agent_stages": [
            {
                "stage": "profile_understanding",
                "label": "Profile Understanding Agent",
                "status": "completed",
                "source": "rule_engine",
            },
            {
                "stage": "career_pathway_agent",
                "label": "Career Pathway Agent",
                "status": "completed",
                "source": "llm",
            },
            {
                "stage": "placement_risk_agent",
                "label": "Placement Risk Agent",
                "status": "completed",
                "source": "llm",
            },
            {
                "stage": "internship_readiness_agent",
                "label": "Internship Readiness Agent",
                "status": "completed",
                "source": "llm",
            },
            {
                "stage": "employability_agent",
                "label": "Employability Agent",
                "status": "completed",
                "source": "llm",
            },
            {
                "stage": "company_readiness_agent",
                "label": "Company Readiness Agent",
                "status": "completed",
                "source": "llm",
            },
            {
                "stage": "role_gap_agent",
                "label": "Role Gap Agent",
                "status": "completed",
                "source": "llm",
            },
        ],
        "evidence_count": 2,
    }

    result = AnalysisVerifierService().verify(summary, career_recommendations=[{"role": "AI Engineer"}])

    assert result["status"] == "approved"
    assert result["confidence"] >= 85
    assert result["blockers"] == []
    assert result["next_best_actions"]


def test_verifier_blocks_missing_career_recommendations() -> None:
    summary = {
        "profile_id": 2,
        "user_type": "college_student",
        "agent_stages": [],
        "career_analysis_id": 101,
    }

    result = AnalysisVerifierService().verify(summary, career_recommendations=[])

    assert result["status"] == "blocked"
    assert result["confidence"] < 70
    assert any("career recommendations" in item.lower() for item in result["blockers"])


def test_verifier_warns_when_twelfth_program_fit_has_no_evidence() -> None:
    summary = {
        "profile_id": 3,
        "user_type": "twelfth_student",
        "career_analysis_id": 101,
        "program_fit_summary": {"recommended_program_id": "sirt-btech-cse-aiml"},
        "agent_stages": [
            {
                "stage": "profile_understanding",
                "label": "Profile Understanding Agent",
                "status": "completed",
                "source": "rule_engine",
            },
            {
                "stage": "program_fit_agent",
                "label": "Program Fit Agent",
                "status": "completed",
                "source": "llm",
            },
        ],
        "evidence_count": 0,
    }

    result = AnalysisVerifierService().verify(summary, career_recommendations=[{"role": "AI Engineer"}])

    assert result["status"] == "approved_with_warnings"
    assert any("evidence" in item.lower() for item in result["warnings"])


def test_verifier_warns_for_invalid_evidence_count() -> None:
    summary = {
        "profile_id": 4,
        "user_type": "twelfth_student",
        "career_analysis_id": 101,
        "program_fit_summary": {"recommended_program_id": "sirt-btech-cse-aiml"},
        "agent_stages": [
            {
                "stage": "program_fit_agent",
                "label": "Program Fit Agent",
                "status": "completed",
                "source": "llm",
            }
        ],
        "evidence_count": "not-a-number",
    }

    result = AnalysisVerifierService().verify(summary, career_recommendations=[{"role": "AI Engineer"}])

    assert result["status"] == "approved_with_warnings"
    assert result["evidence_count"] == 0
    assert any("invalid" in item.lower() for item in result["warnings"])
