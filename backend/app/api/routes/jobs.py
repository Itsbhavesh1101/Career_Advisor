from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_context, get_db
from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.schemas.job import JobStatusEnvelope, JobStatusRead
from app.services.analysis_job_service import AnalysisJobService

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}", response_model=JobStatusEnvelope)
@limiter.limit(get_settings().analysis_rate_limit)
def get_job_status(
    request: Request,
    job_id: str,
    db: Session = Depends(get_db),
    context=Depends(get_current_user_context),
) -> JobStatusEnvelope:
    del request
    current_user, role = context
    service = AnalysisJobService(db)
    job = service.get_job(job_id, current_user.id, allow_admin=role == "admin")
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return JobStatusEnvelope(job=JobStatusRead.model_validate(job))
