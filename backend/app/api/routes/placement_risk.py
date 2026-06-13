from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_context, get_db
from app.models.student_profile import StudentProfile
from app.schemas.placement_risk import PlacementRiskRead
from app.services.placement_risk_service import PlacementRiskService

router = APIRouter(prefix="/placement-risk", tags=["placement-risk"])


@router.post("/{profile_id}", response_model=PlacementRiskRead, status_code=status.HTTP_201_CREATED)
def generate_placement_risk(
    profile_id: int,
    db: Session = Depends(get_db),
    context=Depends(get_current_user_context),
) -> PlacementRiskRead:
    current_user, role = context
    profile = db.get(StudentProfile, profile_id)
    if profile is None or (profile.user_id != current_user.id and role != "admin"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    service = PlacementRiskService(db)
    return service.generate(profile)


@router.get("/{profile_id}", response_model=PlacementRiskRead)
def get_placement_risk(
    profile_id: int,
    db: Session = Depends(get_db),
    context=Depends(get_current_user_context),
) -> PlacementRiskRead:
    current_user, role = context
    profile = db.get(StudentProfile, profile_id)
    if profile is None or (profile.user_id != current_user.id and role != "admin"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    service = PlacementRiskService(db)
    result = service.get_latest_by_profile(profile_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Placement risk not found")
    return result
