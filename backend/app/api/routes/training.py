from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.schemas.training_recommendations import TrainingRecommendationsRead
from app.services.training_recommendation_service import TrainingRecommendationService

router = APIRouter(prefix="/training", tags=["training"])


@router.get("/recommendations", response_model=TrainingRecommendationsRead)
def get_training_recommendations(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> TrainingRecommendationsRead:
    service = TrainingRecommendationService(db)
    return service.get_recommendations(user_id=current_user.id)
