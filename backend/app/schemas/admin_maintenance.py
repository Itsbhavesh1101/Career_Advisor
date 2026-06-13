from __future__ import annotations

from pydantic import BaseModel, Field


class AdminSmokeDataCleanupPreviewRead(BaseModel):
    users: int = 0
    profiles: int = 0
    analysis_jobs: int = 0
    career_analyses: int = 0
    resume_analyses: int = 0
    employability_scores: int = 0
    placement_risks: int = 0
    company_fits: int = 0
    role_gap_analyses: int = 0
    internship_readiness: int = 0
    quiz_sessions: int = 0
    quiz_questions: int = 0
    quiz_answers: int = 0
    quiz_results: int = 0
    rag_sources: int = 0
    rag_chunks: int = 0
    sample_emails: list[str] = Field(default_factory=list)
    sample_rag_titles: list[str] = Field(default_factory=list)


class AdminSmokeDataCleanupRequest(BaseModel):
    confirm: str


class AdminSmokeDataCleanupResultRead(AdminSmokeDataCleanupPreviewRead):
    deleted: bool


class AdminPresentationDemoDataPreviewRead(BaseModel):
    users: int = 0
    profiles: int = 0
    career_analyses: int = 0
    resume_analyses: int = 0
    employability_scores: int = 0
    placement_risks: int = 0
    company_fits: int = 0
    role_gap_analyses: int = 0
    internship_readiness: int = 0
    quiz_sessions: int = 0
    quiz_results: int = 0
    admin_managed_items: int = 0
    placement_companies: int = 0
    placement_opportunities: int = 0
    notifications: int = 0
    sample_emails: list[str] = Field(default_factory=list)
    sample_items: list[str] = Field(default_factory=list)


class AdminPresentationDemoDataSeedRequest(BaseModel):
    confirm: str


class AdminPresentationDemoDataSeedResultRead(AdminPresentationDemoDataPreviewRead):
    seeded: bool
