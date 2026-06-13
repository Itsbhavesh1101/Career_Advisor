from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_context, get_db
from app.schemas.employability_score import EmployabilityScoreRead
from app.services.employability_service import EmployabilityService

router = APIRouter(prefix="/employability", tags=["employability"])


@router.post("/{profile_id}", response_model=EmployabilityScoreRead, status_code=status.HTTP_201_CREATED)
def compute_employability_score(
    profile_id: int,
    db: Session = Depends(get_db),
    context=Depends(get_current_user_context),
) -> EmployabilityScoreRead:
    current_user, role = context
    service = EmployabilityService(db)
    try:
        score = service.compute_score(profile_id, current_user.id, allow_admin=role == "admin")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return EmployabilityScoreRead.model_validate(score)


@router.get("/{profile_id}", response_model=EmployabilityScoreRead)
def get_employability_score(
    profile_id: int,
    db: Session = Depends(get_db),
    context=Depends(get_current_user_context),
) -> EmployabilityScoreRead:
    current_user, role = context
    service = EmployabilityService(db)
    score = service.get_latest_score(profile_id, current_user.id, allow_admin=role == "admin")
    if score is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Score not found")
    return EmployabilityScoreRead.model_validate(score)
