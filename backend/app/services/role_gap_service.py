from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.role_gap_analysis import RoleGapAnalysis
from app.models.student_profile import StudentProfile
from app.services.llm_client import LLMClient


class RoleGapService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.llm = LLMClient()

    def get_latest_by_profile(self, profile_id: int) -> RoleGapAnalysis | None:
        stmt = (
            select(RoleGapAnalysis)
            .where(RoleGapAnalysis.student_profile_id == profile_id)
            .order_by(RoleGapAnalysis.created_at.desc())
        )
        return self.db.scalar(stmt)

    def generate(self, profile: StudentProfile) -> RoleGapAnalysis:
        role_gaps = self.llm.generate_role_gaps(profile)

        analysis = RoleGapAnalysis(student_profile_id=profile.id, role_gaps=role_gaps)
        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)
        return analysis
