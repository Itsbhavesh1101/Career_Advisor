from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.schemas.analysis_orchestrator import AnalysisSnapshotSummary


JobStatusLiteral = Literal["queued", "running", "completed", "failed"]


class JobDispatchRead(BaseModel):
    job_id: str
    status: JobStatusLiteral


class JobStatusRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    student_profile_id: int
    status: JobStatusLiteral
    progress: int
    message: str | None = None
    error: str | None = None
    analysis_id: int | None = None
    snapshot_summary: AnalysisSnapshotSummary | dict | None = None
    created_at: datetime
    updated_at: datetime


class JobStatusEnvelope(BaseModel):
    job: JobStatusRead
