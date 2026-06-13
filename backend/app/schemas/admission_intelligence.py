from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AdmissionMetricsRead(BaseModel):
    total_twelfth_profiles: int
    analyzed_profiles: int
    needs_analysis: int
    high_intent: int
    wrong_branch_risk: int
    ready_for_counseling: int


class AdmissionCounselorBriefRead(BaseModel):
    best_fit: str | None = None
    confidence: int | None = None
    talking_points: list[str] = Field(default_factory=list)
    expectation_checks: list[str] = Field(default_factory=list)
    first_year_actions: list[str] = Field(default_factory=list)
    evidence_titles: list[str] = Field(default_factory=list)
    follow_up_questions: list[str] = Field(default_factory=list)


class AdmissionLeadRead(BaseModel):
    profile_id: int
    student_name: str
    current_interest: str
    preferred_stream: str
    recommended_program: str | None = None
    confidence: int | None = None
    status: str
    priority: str
    lost_reason_signals: list[str] = Field(default_factory=list)
    counselor_brief: AdmissionCounselorBriefRead
    created_at: datetime


class AdmissionDashboardRead(BaseModel):
    metrics: AdmissionMetricsRead
    leads: list[AdmissionLeadRead]
