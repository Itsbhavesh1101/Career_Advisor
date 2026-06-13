from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.placement_risk import PlacementRisk
from app.models.student_profile import StudentProfile
from app.services.llm_client import LLMClient


class PlacementRiskService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.llm = LLMClient()

    def get_latest_by_profile(self, profile_id: int) -> PlacementRisk | None:
        stmt = (
            select(PlacementRisk)
            .where(PlacementRisk.student_profile_id == profile_id)
            .order_by(PlacementRisk.created_at.desc())
        )
        return self.db.scalar(stmt)

    def generate(self, profile: StudentProfile) -> PlacementRisk:
        risk = self.llm.generate_placement_risk(profile)
        record = PlacementRisk(
            student_profile_id=profile.id,
            risk_level=risk["risk_level"],
            reasons=risk["reasons"],
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record
