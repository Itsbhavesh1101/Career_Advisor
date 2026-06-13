from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_current_user_context, get_db
from app.schemas.institution import (
    InstitutionBranding,
    InstitutionCatalog,
    InstitutionOverridePayload,
    InstitutionProgramDetail,
)
from app.services.institution_config_service import InstitutionConfigService

router = APIRouter(prefix="/institution", tags=["institution"])


@router.get("/branding", response_model=InstitutionBranding)
def get_branding() -> InstitutionBranding:
    return InstitutionConfigService().get_branding()


@router.get("/programs", response_model=InstitutionCatalog)
def list_programs(
    db: Session = Depends(get_db),
    _context=Depends(get_current_user_context),
) -> InstitutionCatalog:
    return InstitutionConfigService(db).get_catalog()


@router.get("/programs/{program_id}", response_model=InstitutionProgramDetail)
def get_program(
    program_id: str,
    db: Session = Depends(get_db),
    _context=Depends(get_current_user_context),
) -> InstitutionProgramDetail:
    match = InstitutionConfigService(db).find_program(program_id)
    if match is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Program not found",
        )

    school, program = match
    return InstitutionProgramDetail(school=school, program=program)


@router.get("/admin/overrides", response_model=InstitutionOverridePayload)
def get_overrides(
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
) -> InstitutionOverridePayload:
    return InstitutionConfigService(db).get_effective_overrides()


@router.put("/admin/overrides", response_model=InstitutionOverridePayload)
def update_overrides(
    payload: InstitutionOverridePayload,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
) -> InstitutionOverridePayload:
    service = InstitutionConfigService(db)
    service.upsert_default_overrides(payload)
    return service.get_effective_overrides()
