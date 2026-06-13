from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_db
from app.schemas.placement_intelligence import PlacementDashboardRead
from app.services.placement_intelligence_service import PlacementIntelligenceService

router = APIRouter(prefix="/placement-intelligence", tags=["placement-intelligence"])


@router.get("/dashboard", response_model=PlacementDashboardRead)
def get_placement_dashboard(
    limit: int = Query(default=12, ge=1, le=50),
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
) -> PlacementDashboardRead:
    return PlacementIntelligenceService(db).get_dashboard(limit=limit)
