from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.employability_score import EmployabilityScore
from app.models.student_profile import StudentProfile
from app.services.llm_client import LLMClient


class EmployabilityService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.llm = LLMClient()

    def compute_score(
        self, profile_id: int, user_id: int, allow_admin: bool = False
    ) -> EmployabilityScore:
        profile = self.db.get(StudentProfile, profile_id)
        if profile is None or (profile.user_id != user_id and not allow_admin):
            raise ValueError("Profile not found")

        llm_scores = self.llm.generate_employability_score(profile)

        record = EmployabilityScore(
            student_profile_id=profile_id,
            overall_score=llm_scores["overall_score"],
            academic_strength=llm_scores["academic_strength"],
            technical_skills=llm_scores["technical_skills"],
            industry_readiness=llm_scores["industry_readiness"],
            resume_quality=llm_scores["resume_quality"],
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def get_latest_score(
        self, profile_id: int, user_id: int, allow_admin: bool = False
    ) -> EmployabilityScore | None:
        profile = self.db.get(StudentProfile, profile_id)
        if profile is None or (profile.user_id != user_id and not allow_admin):
            return None
        stmt = (
            select(EmployabilityScore)
            .where(EmployabilityScore.student_profile_id == profile_id)
            .order_by(EmployabilityScore.created_at.desc())
        )
        return self.db.scalar(stmt)
