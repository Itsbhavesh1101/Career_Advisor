from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_context, get_db
from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.schemas.career_analysis import CareerAnalysisRead
from app.services.career_analysis_service import CareerAnalysisService
from app.models.student_profile import StudentProfile

router = APIRouter(prefix="/branch-analysis", tags=["branch-analysis"])


@router.post(
    "/{profile_id}",
    response_model=CareerAnalysisRead,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(get_settings().analysis_rate_limit)
def create_branch_analysis(
    request: Request,
    profile_id: int,
    db: Session = Depends(get_db),
    context=Depends(get_current_user_context),
) -> CareerAnalysisRead:
    del request
    current_user, role = context

    profile = db.get(StudentProfile, profile_id)
    if profile is None or (profile.user_id != current_user.id and role != "admin"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
        )

    if profile.user_type != "twelfth_student":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Branch analysis is only available for 12th grade students",
        )

    service = CareerAnalysisService(db)
    try:
        analysis = service.generate_analysis(
            profile_id, current_user.id, allow_admin=role == "admin"
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    return CareerAnalysisRead.model_validate(analysis)
