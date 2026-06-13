from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.internship_readiness import InternshipReadiness
from app.models.student_profile import StudentProfile
from app.services.llm_client import LLMClient


class InternshipReadinessService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.llm = LLMClient()

    def get_latest_by_profile(self, profile_id: int) -> InternshipReadiness | None:
        stmt = (
            select(InternshipReadiness)
            .where(InternshipReadiness.student_profile_id == profile_id)
            .order_by(InternshipReadiness.created_at.desc())
        )
        return self.db.scalar(stmt)

    def generate(self, profile: StudentProfile) -> InternshipReadiness:
        readiness = self.llm.generate_internship_readiness(profile)
        record = InternshipReadiness(
            student_profile_id=profile.id,
            readiness_score=readiness["readiness_score"],
            readiness_level=readiness["readiness_level"],
            action_plan=readiness["action_plan"],
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record
