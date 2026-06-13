from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CompanyFitMatch(BaseModel):
    company: str
    company_type: str | None = None
    target_roles: list[str] = Field(default_factory=list)
    score: int
    rationale: str | None = None
    matched_evidence: list[str] = Field(default_factory=list)
    missing_requirements: list[str] = Field(default_factory=list)
    preparation_plan: list[str] = Field(default_factory=list)
    hiring_signal_summary: str | None = None


class CompanyFitRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_profile_id: int
    matches: list[CompanyFitMatch]
    created_at: datetime
