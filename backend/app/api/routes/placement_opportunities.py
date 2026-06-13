from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_current_user, get_db
from app.models.user import User
from app.schemas.placement_opportunity import (
    PlacementActivityEventListRead,
    PlacementApplicationBulkShortlistCreate,
    PlacementApplicationBulkStatusUpdate,
    PlacementApplicationCreate,
    PlacementApplicationListRead,
    PlacementApplicationRead,
    PlacementApplicationStatus,
    PlacementApplicationStudentUpdate,
    PlacementApplicationUpdate,
    PlacementCompanyCreate,
    PlacementCompanyListRead,
    PlacementCompanyRead,
    PlacementCompanyStatus,
    PlacementCompanyUpdate,
    PlacementEligibleStudentListRead,
    PlacementInterviewRoundRead,
    PlacementInterviewRoundUpdate,
    PlacementInterviewRoundCreate,
    PlacementOfferUpdate,
    PlacementOpportunityCreate,
    PlacementOpportunityListRead,
    PlacementOpportunityRead,
    PlacementOpportunityStatus,
    PlacementOpportunityType,
    PlacementOpportunityUpdate,
    PlacementUpcomingActionListRead,
)
from app.services.placement_opportunity_service import PlacementOpportunityService

router = APIRouter(prefix="/placement-opportunities", tags=["placement-opportunities"])


@router.get("", response_model=PlacementOpportunityListRead)
def list_student_opportunities(
    profile_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlacementOpportunityListRead:
    try:
        return PlacementOpportunityService(db).list_student_opportunities(
            profile_id=profile_id,
            user=current_user,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/applications", response_model=PlacementApplicationListRead)
def list_student_applications(
    profile_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlacementApplicationListRead:
    try:
        return PlacementOpportunityService(db).list_student_applications(
            profile_id=profile_id,
            user=current_user,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/activity", response_model=PlacementActivityEventListRead)
def list_student_activity(
    profile_id: int = Query(...),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlacementActivityEventListRead:
    try:
        return PlacementOpportunityService(db).list_student_activity(
            profile_id=profile_id,
            user=current_user,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/upcoming", response_model=PlacementUpcomingActionListRead)
def list_student_upcoming_actions(
    profile_id: int = Query(...),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlacementUpcomingActionListRead:
    try:
        return PlacementOpportunityService(db).list_student_upcoming_actions(
            profile_id=profile_id,
            user=current_user,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch(
    "/applications/{application_id}",
    response_model=PlacementApplicationRead,
)
def update_student_application(
    application_id: int,
    payload: PlacementApplicationStudentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlacementApplicationRead:
    try:
        return PlacementOpportunityService(db).update_student_application(
            application_id,
            payload,
            user=current_user,
        )
    except ValueError as exc:
        status_code = (
            status.HTTP_404_NOT_FOUND
            if "not found" in str(exc).lower()
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post(
    "/{opportunity_id}/apply",
    response_model=PlacementApplicationRead,
    status_code=status.HTTP_201_CREATED,
)
def apply_to_opportunity(
    opportunity_id: int,
    payload: PlacementApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlacementApplicationRead:
    try:
        return PlacementOpportunityService(db).apply_to_opportunity(
            opportunity_id,
            payload,
            user=current_user,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/admin/opportunities", response_model=PlacementOpportunityListRead)
def list_admin_opportunities(
    status_filter: PlacementOpportunityStatus | None = Query(default=None, alias="status"),
    opportunity_type: PlacementOpportunityType | None = Query(default=None),
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
) -> PlacementOpportunityListRead:
    return PlacementOpportunityService(db).list_admin_opportunities(
        status=status_filter,
        opportunity_type=opportunity_type,
    )


@router.get("/admin/companies", response_model=PlacementCompanyListRead)
def list_admin_companies(
    status_filter: PlacementCompanyStatus | None = Query(default=None, alias="status"),
    q: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
) -> PlacementCompanyListRead:
    return PlacementOpportunityService(db).list_admin_companies(
        status=status_filter,
        q=q,
    )


@router.get("/admin/activity", response_model=PlacementActivityEventListRead)
def list_admin_activity(
    opportunity_id: int | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
) -> PlacementActivityEventListRead:
    return PlacementOpportunityService(db).list_admin_activity(
        opportunity_id=opportunity_id,
        limit=limit,
    )


@router.get("/admin/upcoming", response_model=PlacementUpcomingActionListRead)
def list_admin_upcoming_actions(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
) -> PlacementUpcomingActionListRead:
    return PlacementOpportunityService(db).list_admin_upcoming_actions(limit=limit)


@router.post(
    "/admin/companies",
    response_model=PlacementCompanyRead,
    status_code=status.HTTP_201_CREATED,
)
def create_admin_company(
    payload: PlacementCompanyCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> PlacementCompanyRead:
    try:
        return PlacementOpportunityService(db).create_company(payload, user_id=admin.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.patch("/admin/companies/{company_id}", response_model=PlacementCompanyRead)
def update_admin_company(
    company_id: int,
    payload: PlacementCompanyUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> PlacementCompanyRead:
    try:
        return PlacementOpportunityService(db).update_company(
            company_id,
            payload,
            user_id=admin.id,
        )
    except ValueError as exc:
        status_code = (
            status.HTTP_404_NOT_FOUND
            if "not found" in str(exc).lower()
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.delete("/admin/companies/{company_id}", response_model=PlacementCompanyRead)
def archive_admin_company(
    company_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> PlacementCompanyRead:
    try:
        return PlacementOpportunityService(db).archive_company(
            company_id,
            user_id=admin.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/admin/opportunities",
    response_model=PlacementOpportunityRead,
    status_code=status.HTTP_201_CREATED,
)
def create_admin_opportunity(
    payload: PlacementOpportunityCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> PlacementOpportunityRead:
    return PlacementOpportunityService(db).create_opportunity(payload, user_id=admin.id)


@router.patch("/admin/opportunities/{opportunity_id}", response_model=PlacementOpportunityRead)
def update_admin_opportunity(
    opportunity_id: int,
    payload: PlacementOpportunityUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> PlacementOpportunityRead:
    try:
        return PlacementOpportunityService(db).update_opportunity(
            opportunity_id,
            payload,
            user_id=admin.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get(
    "/admin/opportunities/{opportunity_id}/eligible-students",
    response_model=PlacementEligibleStudentListRead,
)
def list_admin_opportunity_eligible_students(
    opportunity_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
) -> PlacementEligibleStudentListRead:
    try:
        return PlacementOpportunityService(db).list_eligible_students_for_opportunity(
            opportunity_id
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/admin/opportunities/{opportunity_id}/shortlist",
    response_model=PlacementApplicationListRead,
    status_code=status.HTTP_201_CREATED,
)
def bulk_shortlist_admin_opportunity_students(
    opportunity_id: int,
    payload: PlacementApplicationBulkShortlistCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> PlacementApplicationListRead:
    try:
        return PlacementOpportunityService(db).bulk_shortlist_eligible_students(
            opportunity_id,
            payload,
            user_id=admin.id,
        )
    except ValueError as exc:
        status_code = (
            status.HTTP_404_NOT_FOUND
            if "not found" in str(exc).lower()
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.get("/admin/applications", response_model=PlacementApplicationListRead)
def list_admin_applications(
    opportunity_id: int | None = Query(default=None),
    application_status: PlacementApplicationStatus | None = Query(
        default=None, alias="status"
    ),
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
) -> PlacementApplicationListRead:
    return PlacementOpportunityService(db).list_admin_applications(
        opportunity_id=opportunity_id,
        status=application_status,
    )


@router.get("/admin/applications/export.csv")
def export_admin_applications(
    opportunity_id: int | None = Query(default=None),
    application_status: PlacementApplicationStatus | None = Query(
        default=None, alias="status"
    ),
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
) -> Response:
    csv_payload = PlacementOpportunityService(db).export_admin_applications_csv(
        opportunity_id=opportunity_id,
        status=application_status,
    )
    return Response(
        content=csv_payload,
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="placement-applications.csv"'
        },
    )


@router.patch("/admin/applications/bulk", response_model=PlacementApplicationListRead)
def bulk_update_admin_application_status(
    payload: PlacementApplicationBulkStatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> PlacementApplicationListRead:
    try:
        return PlacementOpportunityService(db).bulk_update_applications(
            payload,
            user_id=admin.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/admin/applications/{application_id}/interviews",
    response_model=PlacementApplicationRead,
    status_code=status.HTTP_201_CREATED,
)
def create_admin_application_interview(
    application_id: int,
    payload: PlacementInterviewRoundCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> PlacementApplicationRead:
    try:
        return PlacementOpportunityService(db).create_interview_round(
            application_id,
            payload,
            user_id=admin.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch(
    "/admin/interviews/{interview_id}",
    response_model=PlacementInterviewRoundRead,
)
def update_admin_application_interview(
    interview_id: int,
    payload: PlacementInterviewRoundUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> PlacementInterviewRoundRead:
    try:
        return PlacementOpportunityService(db).update_interview_round(
            interview_id,
            payload,
            user_id=admin.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch(
    "/admin/applications/{application_id}",
    response_model=PlacementApplicationRead,
)
def update_admin_application_status(
    application_id: int,
    payload: PlacementApplicationUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> PlacementApplicationRead:
    try:
        return PlacementOpportunityService(db).update_application_status(
            application_id,
            payload,
            user_id=admin.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch(
    "/admin/applications/{application_id}/offer",
    response_model=PlacementApplicationRead,
)
def update_admin_application_offer(
    application_id: int,
    payload: PlacementOfferUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> PlacementApplicationRead:
    try:
        return PlacementOpportunityService(db).update_application_offer(
            application_id,
            payload,
            user_id=admin.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/admin/export.csv")
def export_admin_opportunities(
    status_filter: PlacementOpportunityStatus | None = Query(default=None, alias="status"),
    opportunity_type: PlacementOpportunityType | None = Query(default=None),
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
) -> Response:
    csv_payload = PlacementOpportunityService(db).export_admin_opportunities_csv(
        status=status_filter,
        opportunity_type=opportunity_type,
    )
    return Response(
        content=csv_payload,
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="placement-opportunities.csv"'
        },
    )
