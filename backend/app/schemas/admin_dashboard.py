from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class AdminMetricsRead(BaseModel):
    total_profiles: int
    total_students: int
    placement_ready: int
    needs_training: int
    high_risk: int


class AdminStudentRead(BaseModel):
    profile_id: int
    user_id: int
    name: str
    user_type: str | None = None
    degree: str
    specialization: str
    cgpa: float
    created_at: datetime
    employability_score: int | None
    placement_risk: str | None
    has_analysis: bool = False
    has_resume: bool = False
    readiness_band: str = "unknown"


class AdminStudentPageRead(BaseModel):
    items: list[AdminStudentRead]
    total: int
    page: int
    page_size: int
    total_pages: int


class AdminStudentFilters(BaseModel):
    student_type: str | None = None
    specialization: str | None = None
    readiness_band: Literal["ready", "watch", "risk", "unknown"] | None = None
    placement_risk: str | None = None
    missing_analysis: bool | None = None
    missing_resume: bool | None = None
    sort: Literal["created_desc", "created_asc", "readiness_desc", "readiness_asc"] = (
        "created_desc"
    )


class AdminReadinessSummaryRead(BaseModel):
    pending_rag_reviews: int
    stale_rag_sources: int
    failed_embeddings: int
    chunks_without_embeddings: int
    failed_analysis_jobs: int
    missing_analysis: int
    missing_resume: int


class SystemReadinessRead(BaseModel):
    llm_provider: str
    llm_configured: bool
    embedding_provider: str
    embedding_configured: bool
    vector_search_enabled: bool
    celery_task_always_eager: bool
    failed_analysis_jobs: int
    failed_embedding_jobs: int
    pending_rag_reviews: int
    stale_rag_sources: int
    hints: list[str]
