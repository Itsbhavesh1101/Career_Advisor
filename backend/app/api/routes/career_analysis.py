from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_context, get_db
from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.schemas.career_analysis import CareerAnalysisRead
from app.schemas.job import JobDispatchRead
from app.services.analysis_job_service import AnalysisJobService, dispatch_analysis_job
from app.services.career_analysis_service import CareerAnalysisService

router = APIRouter(prefix="/analysis", tags=["career-analysis"])


@router.post("/{profile_id}", response_model=JobDispatchRead, status_code=status.HTTP_202_ACCEPTED)
@limiter.limit(get_settings().analysis_rate_limit)
def create_analysis(
    request: Request,
    profile_id: int,
    db: Session = Depends(get_db),
    context=Depends(get_current_user_context),
) -> JobDispatchRead:
    del request
    current_user, role = context
    service = AnalysisJobService(db)
    try:
        job = service.create_job(profile_id, current_user.id, allow_admin=role == "admin")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    try:
        dispatch_analysis_job(job.id)
    except Exception as exc:
        service.mark_job_failed(
            job.id,
            error=f"Dispatch failed: {exc}",
            message="Analysis job dispatch failed",
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to queue analysis job at the moment. Please retry shortly.",
        ) from exc

    db.expire_all()
    latest_job = service.get_job(job.id, current_user.id, allow_admin=True)
    status_value = latest_job.status if latest_job is not None else "queued"
    return JobDispatchRead(job_id=job.id, status=status_value)


@router.get("/{profile_id}", response_model=CareerAnalysisRead)
@limiter.limit(get_settings().analysis_rate_limit)
def get_analysis(
    request: Request,
    profile_id: int,
    db: Session = Depends(get_db),
    context=Depends(get_current_user_context),
) -> CareerAnalysisRead:
    del request
    current_user, role = context
    service = CareerAnalysisService(db)
    analysis = service.get_analysis_by_profile_id(
        profile_id, current_user.id, allow_admin=role == "admin"
    )
    if analysis is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    return CareerAnalysisRead.model_validate(analysis)
