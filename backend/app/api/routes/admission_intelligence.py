from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_db
from app.schemas.admission_intelligence import AdmissionDashboardRead
from app.services.admission_intelligence_service import AdmissionIntelligenceService

router = APIRouter(prefix="/admission-intelligence", tags=["admission-intelligence"])


@router.get("/dashboard", response_model=AdmissionDashboardRead)
def get_admission_dashboard(
    limit: int = Query(default=12, ge=1, le=50),
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
) -> AdmissionDashboardRead:
    return AdmissionIntelligenceService(db).get_dashboard(limit=limit)
