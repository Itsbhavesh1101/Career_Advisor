from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.career_analysis import CareerAnalysis
from app.models.psychometric_result import PsychometricResult
from app.models.psychometric_session import PsychometricSession
from app.models.resume_analysis import ResumeAnalysis
from app.models.student_profile import StudentProfile
from app.schemas.student_dashboard import StudentDashboardSummaryRead


class StudentDashboardService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_summary(
        self,
        profile_id: int,
        user_id: int,
        *,
        allow_admin: bool = False,
    ) -> StudentDashboardSummaryRead:
        profile = self.db.get(StudentProfile, profile_id)
        if profile is None or (profile.user_id != user_id and not allow_admin):
            raise ValueError("Profile not found")

        student_type = profile.user_type or "college_student"
        analysis = self._latest_analysis(profile_id)
        quiz_done = self._has_quiz_result(profile_id)
        resume = self._latest_resume(profile_id)

        analysis_status = "ready" if analysis else "missing"
        quiz_status = "complete" if quiz_done else self._quiz_session_status(profile_id)
        resume_status = "not_applicable" if student_type == "twelfth_student" else (
            "ready" if resume else "missing"
        )

        next_actions = self._next_actions(
            student_type=student_type,
            analysis_status=analysis_status,
            quiz_status=quiz_status,
            resume_status=resume_status,
        )
        return StudentDashboardSummaryRead(
            profile_id=profile.id,
            student_type=student_type,
            profile_completeness=self._profile_completeness(profile, student_type),
            analysis_status=analysis_status,
            quiz_status=quiz_status,
            resume_status=resume_status,
            readiness_summary=self._readiness_summary(
                student_type=student_type,
                analysis_status=analysis_status,
                quiz_status=quiz_status,
                resume_status=resume_status,
            ),
            next_actions=next_actions[:3],
        )

    def _latest_analysis(self, profile_id: int) -> CareerAnalysis | None:
        return self.db.scalars(
            select(CareerAnalysis)
            .where(CareerAnalysis.student_profile_id == profile_id)
            .order_by(CareerAnalysis.created_at.desc(), CareerAnalysis.id.desc())
            .limit(1)
        ).first()

    def _latest_resume(self, profile_id: int) -> ResumeAnalysis | None:
        return self.db.scalars(
            select(ResumeAnalysis)
            .where(ResumeAnalysis.student_profile_id == profile_id)
            .order_by(ResumeAnalysis.created_at.desc(), ResumeAnalysis.id.desc())
            .limit(1)
        ).first()

    def _has_quiz_result(self, profile_id: int) -> bool:
        return (
            self.db.scalar(
                select(PsychometricResult.id)
                .where(PsychometricResult.student_profile_id == profile_id)
                .limit(1)
            )
            is not None
        )

    def _quiz_session_status(self, profile_id: int) -> str:
        session = self.db.scalars(
            select(PsychometricSession)
            .where(PsychometricSession.student_profile_id == profile_id)
            .order_by(PsychometricSession.created_at.desc())
            .limit(1)
        ).first()
        if session is None:
            return "not_started"
        if session.status == "completed":
            return "complete"
        if session.status in {"abandoned", "expired"}:
            return "needs_restart"
        return "in_progress"

    def _profile_completeness(self, profile: StudentProfile, student_type: str) -> int:
        if student_type == "twelfth_student":
            fields = [
                profile.name,
                profile.twelfth_percentage,
                profile.interests,
                profile.subjects,
                profile.math_strength,
                profile.logical_reasoning,
                profile.programming_interest,
            ]
        else:
            fields = [
                profile.name,
                profile.cgpa,
                profile.degree,
                profile.specialization,
                profile.current_skills,
                profile.interests,
                profile.target_industry,
                profile.projects,
                profile.internships,
                profile.certifications,
            ]
        completed = sum(1 for value in fields if self._is_present(value))
        return int((completed / len(fields)) * 100)

    def _is_present(self, value: object) -> bool:
        if value is None:
            return False
        if isinstance(value, str):
            return bool(value.strip())
        if isinstance(value, list):
            return bool(value)
        if isinstance(value, (int, float)):
            return value > 0
        return True

    def _next_actions(
        self,
        *,
        student_type: str,
        analysis_status: str,
        quiz_status: str,
        resume_status: str,
    ) -> list[str]:
        actions: list[str] = []
        if quiz_status != "complete":
            actions.append("Complete the adaptive quiz.")
        if analysis_status != "ready":
            actions.append("Run career and placement analysis.")
        elif student_type == "twelfth_student":
            actions.append("Review your program-fit recommendation.")
        else:
            actions.append("Review role gaps and company readiness.")
        if resume_status == "missing":
            actions.append("Add a resume for evidence-backed guidance.")
        if student_type == "twelfth_student":
            actions.append("Use the first-year roadmap for counseling discussion.")
        else:
            actions.append("Start a 30-day skill sprint from the roadmap.")
        return actions

    def _readiness_summary(
        self,
        *,
        student_type: str,
        analysis_status: str,
        quiz_status: str,
        resume_status: str,
    ) -> str:
        if analysis_status == "ready":
            if student_type == "twelfth_student":
                return "Admission counseling guidance is ready for review."
            return "Placement readiness guidance is ready for review."
        if student_type == "twelfth_student":
            return "Complete the admission guidance flow to unlock program-fit counseling."
        if quiz_status != "complete" or resume_status == "missing":
            return "Complete the readiness basics before placement planning."
        return "Run analysis to generate placement guidance."
