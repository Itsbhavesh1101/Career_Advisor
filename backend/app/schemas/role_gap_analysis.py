from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RoleGapItem(BaseModel):
    role: str
    missing_skills: list[str]
    learning_plan: list[str]
    current_evidence: list[str] = Field(default_factory=list)
    gap_reason: str | None = None
    next_project: str | None = None
    proof_to_build: list[str] = Field(default_factory=list)
    priority: str | None = None


class RoleGapAnalysisRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_profile_id: int
    role_gaps: list[RoleGapItem]
    created_at: datetime
