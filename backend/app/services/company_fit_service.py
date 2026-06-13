from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.company_fit import CompanyFit
from app.models.student_profile import StudentProfile
from app.services.llm_client import LLMClient


class CompanyFitService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.llm = LLMClient()

    def get_latest_by_profile(self, profile_id: int) -> CompanyFit | None:
        stmt = (
            select(CompanyFit)
            .where(CompanyFit.student_profile_id == profile_id)
            .order_by(CompanyFit.created_at.desc())
        )
        return self.db.scalar(stmt)

    def generate(self, profile: StudentProfile) -> CompanyFit:
        matches = self.llm.generate_company_fit_matches(profile)

        fit = CompanyFit(student_profile_id=profile.id, matches=matches)
        self.db.add(fit)
        self.db.commit()
        self.db.refresh(fit)
        return fit
