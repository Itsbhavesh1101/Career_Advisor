from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.industry_demand import IndustryDemandRead
from app.services.industry_demand_service import IndustryDemandService

router = APIRouter(prefix="/industry-demand", tags=["industry-demand"])


@router.get("", response_model=IndustryDemandRead)
def get_industry_demand(
    current_user: User = Depends(get_current_user),
) -> IndustryDemandRead:
    service = IndustryDemandService()
    try:
        return service.get_trends(user_id=current_user.id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"LLM industry-demand generation failed: {exc}",
        ) from exc
