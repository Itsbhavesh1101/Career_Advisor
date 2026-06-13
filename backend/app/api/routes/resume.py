from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.student_profile import StudentProfile
from app.models.user import User
from app.schemas.resume_analysis import ResumeAnalysisRead, ResumeURLRequest
from app.services.resume_service import ResumeFetchError, ResumeService

router = APIRouter(prefix="/resume", tags=["resume"])


@router.post(
    "/{profile_id}",
    response_model=ResumeAnalysisRead,
    status_code=status.HTTP_201_CREATED,
)
def upload_resume_from_url(
    profile_id: int,
    payload: ResumeURLRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResumeAnalysisRead:
    profile = db.get(StudentProfile, profile_id)
    if profile is None or profile.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    service = ResumeService(db)
    try:
        analysis = service.create_analysis_from_url(profile, str(payload.resume_url))
    except ResumeFetchError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return analysis


@router.get("/{profile_id}", response_model=ResumeAnalysisRead)
def get_latest_resume(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResumeAnalysisRead:
    profile = db.get(StudentProfile, profile_id)
    if profile is None or profile.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    service = ResumeService(db)
    analysis = service.get_latest_by_profile(profile_id)
    if analysis is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume analysis not found")

    return analysis
