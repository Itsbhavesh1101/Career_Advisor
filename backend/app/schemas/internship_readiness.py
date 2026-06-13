from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.admin_management import ManagedInternshipOpportunityRead


class InternshipReadinessRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_profile_id: int
    readiness_score: int
    readiness_level: str
    action_plan: list[str]
    created_at: datetime


class InternshipOpportunityCatalogRead(BaseModel):
    items: list[ManagedInternshipOpportunityRead]
    total: int
