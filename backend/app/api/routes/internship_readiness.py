from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_context, get_db
from app.models.student_profile import StudentProfile
from app.schemas.internship_readiness import (
    InternshipOpportunityCatalogRead,
    InternshipReadinessRead,
)
from app.services.admin_management_service import AdminManagementService
from app.services.internship_readiness_service import InternshipReadinessService

router = APIRouter(prefix="/internship-readiness", tags=["internship-readiness"])


def _get_owned_profile_or_404(
    profile_id: int,
    db: Session,
    context,
) -> StudentProfile:
    current_user, role = context
    profile = db.get(StudentProfile, profile_id)
    if profile is None or (profile.user_id != current_user.id and role != "admin"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return profile


@router.post("/{profile_id}", response_model=InternshipReadinessRead, status_code=status.HTTP_201_CREATED)
def generate_internship_readiness(
    profile_id: int,
    db: Session = Depends(get_db),
    context=Depends(get_current_user_context),
) -> InternshipReadinessRead:
    profile = _get_owned_profile_or_404(profile_id, db, context)

    service = InternshipReadinessService(db)
    return service.generate(profile)


@router.get(
    "/{profile_id}/managed-opportunities",
    response_model=InternshipOpportunityCatalogRead,
)
def list_managed_internship_opportunities(
    profile_id: int,
    db: Session = Depends(get_db),
    context=Depends(get_current_user_context),
) -> InternshipOpportunityCatalogRead:
    _get_owned_profile_or_404(profile_id, db, context)
    catalog = AdminManagementService(db).list_active_internship_opportunities()
    return InternshipOpportunityCatalogRead(items=catalog.items, total=catalog.total)


@router.get("/{profile_id}", response_model=InternshipReadinessRead)
def get_internship_readiness(
    profile_id: int,
    db: Session = Depends(get_db),
    context=Depends(get_current_user_context),
) -> InternshipReadinessRead:
    _get_owned_profile_or_404(profile_id, db, context)

    service = InternshipReadinessService(db)
    result = service.get_latest_by_profile(profile_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Internship readiness not found")
    return result
