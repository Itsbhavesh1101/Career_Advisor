from __future__ import annotations

from pydantic import BaseModel


class IndustryTrend(BaseModel):
    trend: str
    impact: str


class IndustryDemandRead(BaseModel):
    year: int
    trends: list[IndustryTrend]
