from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PlacementRiskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_profile_id: int
    risk_level: str
    reasons: list[str]
    created_at: datetime
