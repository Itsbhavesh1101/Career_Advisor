from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.student_profile import StudentProfile
from app.services.career_analysis_service import CareerAnalysisService
from app.services.analysis_verifier_service import AnalysisVerifierService
from app.services.company_fit_service import CompanyFitService
from app.services.employability_service import EmployabilityService
from app.services.internship_readiness_service import InternshipReadinessService
from app.services.placement_risk_service import PlacementRiskService
from app.services.role_gap_service import RoleGapService


class AnalysisSnapshotService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def generate_snapshot(
        self,
        profile_id: int,
        user_id: int,
        *,
        allow_admin: bool = False,
    ) -> dict[str, Any]:
        profile = self.db.get(StudentProfile, profile_id)
        if profile is None or (profile.user_id != user_id and not allow_admin):
            raise ValueError("Profile not found")

        stages: list[dict[str, Any]] = []
        self._stage(
            stages,
            stage="profile_understanding",
            label="Profile Understanding Agent",
            source="rule_engine",
            output_ref=f"profile:{profile_id}",
        )

        analysis_service = CareerAnalysisService(self.db)
        career_analysis = analysis_service.generate_analysis(
            profile_id,
            user_id,
            allow_admin=allow_admin,
        )
        user_type = profile.user_type or "college_student"
        is_twelfth = user_type == "twelfth_student"

        if is_twelfth:
            self._stage(
                stages,
                stage="program_fit_agent",
                label="Program Fit Agent",
                source=getattr(career_analysis, "branch_analysis_source", "unknown"),
                output_ref=f"career_analysis:{career_analysis.id}:program_fit",
            )
        else:
            self._stage(
                stages,
                stage="career_pathway_agent",
                label="Career Pathway Agent",
                source=getattr(career_analysis, "career_analysis_source", "unknown"),
                output_ref=f"career_analysis:{career_analysis.id}",
            )

        summary: dict[str, Any] = {
            "snapshot_version": "agentic-snapshot-v1",
            "profile_id": profile_id,
            "career_analysis_id": career_analysis.id,
            "user_type": user_type,
            "career_analysis_source": getattr(
                career_analysis,
                "career_analysis_source",
                "unknown",
            ),
            "branch_analysis_source": getattr(
                career_analysis,
                "branch_analysis_source",
                "not_applicable",
            ),
            "agent_stages": stages,
            "program_fit_summary": getattr(career_analysis, "program_fit_summary", None),
            "evidence_count": len(getattr(career_analysis, "rag_evidence", None) or []),
        }

        placement = PlacementRiskService(self.db).generate(profile)
        internship = InternshipReadinessService(self.db).generate(profile)
        summary["placement_risk_id"] = placement.id
        summary["placement_risk_source"] = "llm"
        summary["internship_readiness_id"] = internship.id
        summary["internship_readiness_source"] = "llm"
        self._stage(
            stages,
            stage="placement_risk_agent",
            label="Placement Risk Agent",
            source=summary["placement_risk_source"],
            output_ref=f"placement_risk:{placement.id}",
        )
        self._stage(
            stages,
            stage="internship_readiness_agent",
            label="Internship Readiness Agent",
            source=summary["internship_readiness_source"],
            output_ref=f"internship_readiness:{internship.id}",
        )

        if not is_twelfth:
            employability = EmployabilityService(self.db).compute_score(
                profile_id,
                user_id,
                allow_admin=allow_admin,
            )
            company_fit = CompanyFitService(self.db).generate(profile)
            role_gaps = RoleGapService(self.db).generate(profile)
            summary["employability_score_id"] = employability.id
            summary["employability_source"] = "llm"
            summary["company_fit_id"] = company_fit.id
            summary["company_fit_source"] = "llm"
            summary["role_gap_id"] = role_gaps.id
            summary["role_gap_source"] = "llm"
            self._stage(
                stages,
                stage="employability_agent",
                label="Employability Agent",
                source=summary["employability_source"],
                output_ref=f"employability_score:{employability.id}",
            )
            self._stage(
                stages,
                stage="company_readiness_agent",
                label="Company Readiness Agent",
                source=summary["company_fit_source"],
                output_ref=f"company_fit:{company_fit.id}",
            )
            self._stage(
                stages,
                stage="role_gap_agent",
                label="Role Gap Agent",
                source=summary["role_gap_source"],
                output_ref=f"role_gap:{role_gaps.id}",
            )
        else:
            summary["employability_source"] = "not_applicable"
            summary["company_fit_source"] = "not_applicable"
            summary["role_gap_source"] = "not_applicable"
            self._stage(
                stages,
                stage="employability_agent",
                label="Employability Agent",
                source="not_applicable",
                status="skipped",
                notes=[
                    "Twelfth-student counseling flow does not require employability scoring."
                ],
            )
            self._stage(
                stages,
                stage="company_readiness_agent",
                label="Company Readiness Agent",
                source="not_applicable",
                status="skipped",
                notes=["Twelfth-student counseling flow does not require company fit."],
            )
            self._stage(
                stages,
                stage="role_gap_agent",
                label="Role Gap Agent",
                source="not_applicable",
                status="skipped",
                notes=["Twelfth-student counseling flow does not require role-gap analysis."],
            )

        verifier = AnalysisVerifierService().verify(
            summary,
            career_recommendations=getattr(career_analysis, "career_recommendations", None)
            or [],
        )
        summary["verifier"] = verifier
        self._stage(
            stages,
            stage="verifier_agent",
            label="Verifier Agent",
            source="rule_engine",
            status="completed" if verifier["status"] != "blocked" else "failed",
            notes=verifier["warnings"] + verifier["blockers"],
        )
        return summary

    def _stage(
        self,
        stages: list[dict[str, Any]],
        *,
        stage: str,
        label: str,
        source: str,
        status: str = "completed",
        output_ref: str | None = None,
        notes: list[str] | None = None,
    ) -> None:
        stages.append(
            {
                "stage": stage,
                "label": label,
                "status": status,
                "source": source,
                "output_ref": output_ref,
                "notes": notes or [],
            }
        )
