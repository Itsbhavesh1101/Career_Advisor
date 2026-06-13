from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_context, get_db
from app.models.student_profile import StudentProfile
from app.schemas.role_gap_analysis import RoleGapAnalysisRead
from app.services.role_gap_service import RoleGapService

router = APIRouter(prefix="/role-gaps", tags=["role-gaps"])


@router.post("/{profile_id}", response_model=RoleGapAnalysisRead, status_code=status.HTTP_201_CREATED)
def generate_role_gaps(
    profile_id: int,
    db: Session = Depends(get_db),
    context=Depends(get_current_user_context),
) -> RoleGapAnalysisRead:
    current_user, role = context
    profile = db.get(StudentProfile, profile_id)
    if profile is None or (profile.user_id != current_user.id and role != "admin"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    service = RoleGapService(db)
    return service.generate(profile)


@router.get("/{profile_id}", response_model=RoleGapAnalysisRead)
def get_role_gaps(
    profile_id: int,
    db: Session = Depends(get_db),
    context=Depends(get_current_user_context),
) -> RoleGapAnalysisRead:
    current_user, role = context
    profile = db.get(StudentProfile, profile_id)
    if profile is None or (profile.user_id != current_user.id and role != "admin"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    service = RoleGapService(db)
    result = service.get_latest_by_profile(profile_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role gaps not found")
    return result
