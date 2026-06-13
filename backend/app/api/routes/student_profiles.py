from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.student_dashboard import StudentDashboardSummaryRead
from app.schemas.student_profile import StudentProfileCreate, StudentProfileRead
from app.services.student_dashboard_service import StudentDashboardService
from app.services.student_profile_service import StudentProfileService

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.post("", response_model=StudentProfileRead, status_code=status.HTTP_201_CREATED)
def create_profile(
    payload: StudentProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StudentProfileRead:
    service = StudentProfileService(db)
    profile = service.create_profile(payload, current_user.id)
    return StudentProfileRead.model_validate(profile)


@router.get("/{profile_id}", response_model=StudentProfileRead)
def get_profile(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StudentProfileRead:
    service = StudentProfileService(db)
    profile = service.get_profile_by_id(profile_id, current_user.id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return StudentProfileRead.model_validate(profile)


@router.get("/{profile_id}/dashboard", response_model=StudentDashboardSummaryRead)
def get_profile_dashboard_summary(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StudentDashboardSummaryRead:
    try:
        return StudentDashboardService(db).get_summary(profile_id, current_user.id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        ) from exc


@router.get("", response_model=list[StudentProfileRead])
def list_profiles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[StudentProfileRead]:
    service = StudentProfileService(db)
    profiles = service.list_profiles(current_user.id)
    return [StudentProfileRead.model_validate(profile) for profile in profiles]


@router.put("/{profile_id}", response_model=StudentProfileRead)
def update_profile(
    profile_id: int,
    payload: StudentProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StudentProfileRead:
    service = StudentProfileService(db)
    profile = service.update_profile(profile_id, current_user.id, payload)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return StudentProfileRead.model_validate(profile)
