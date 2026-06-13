from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_db
from app.schemas.admin_dashboard import (
    AdminMetricsRead,
    AdminReadinessSummaryRead,
    AdminStudentFilters,
    AdminStudentPageRead,
    SystemReadinessRead,
)
from app.schemas.admin_maintenance import (
    AdminPresentationDemoDataPreviewRead,
    AdminPresentationDemoDataSeedRequest,
    AdminPresentationDemoDataSeedResultRead,
    AdminSmokeDataCleanupPreviewRead,
    AdminSmokeDataCleanupRequest,
    AdminSmokeDataCleanupResultRead,
)
from app.services.admin_dashboard_service import AdminDashboardService
from app.services.admin_maintenance_service import AdminMaintenanceService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/metrics", response_model=AdminMetricsRead)
def get_admin_metrics(
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
) -> AdminMetricsRead:
    service = AdminDashboardService(db)
    return service.get_metrics()


@router.get("/readiness-summary", response_model=AdminReadinessSummaryRead)
def get_admin_readiness_summary(
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
) -> AdminReadinessSummaryRead:
    service = AdminDashboardService(db)
    return service.get_readiness_summary()


@router.get("/system-readiness", response_model=SystemReadinessRead)
def get_system_readiness(
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
) -> SystemReadinessRead:
    service = AdminDashboardService(db)
    return service.get_system_readiness()


@router.get("/students", response_model=AdminStudentPageRead)
def list_admin_students(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    student_type: str | None = Query(default=None),
    specialization: str | None = Query(default=None),
    readiness_band: str | None = Query(default=None),
    placement_risk: str | None = Query(default=None),
    missing_analysis: bool | None = Query(default=None),
    missing_resume: bool | None = Query(default=None),
    sort: str = Query(default="created_desc"),
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
) -> AdminStudentPageRead:
    service = AdminDashboardService(db)
    filters = AdminStudentFilters(
        student_type=student_type,
        specialization=specialization,
        readiness_band=readiness_band,
        placement_risk=placement_risk,
        missing_analysis=missing_analysis,
        missing_resume=missing_resume,
        sort=sort,
    )
    items, total, total_pages = service.list_students(
        page=page,
        page_size=page_size,
        filters=filters,
    )
    return AdminStudentPageRead(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/students/export")
def export_admin_students(
    student_type: str | None = Query(default=None),
    specialization: str | None = Query(default=None),
    readiness_band: str | None = Query(default=None),
    placement_risk: str | None = Query(default=None),
    missing_analysis: bool | None = Query(default=None),
    missing_resume: bool | None = Query(default=None),
    sort: str = Query(default="created_desc"),
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
) -> Response:
    filters = AdminStudentFilters(
        student_type=student_type,
        specialization=specialization,
        readiness_band=readiness_band,
        placement_risk=placement_risk,
        missing_analysis=missing_analysis,
        missing_resume=missing_resume,
        sort=sort,
    )
    csv_body = AdminDashboardService(db).export_students_csv(filters=filters)
    return Response(
        content=csv_body,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=sage-students.csv"},
    )


@router.get(
    "/maintenance/smoke-data/preview",
    response_model=AdminSmokeDataCleanupPreviewRead,
)
def preview_smoke_data_cleanup(
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
) -> AdminSmokeDataCleanupPreviewRead:
    return AdminMaintenanceService(db).preview_smoke_data_cleanup()


@router.post(
    "/maintenance/smoke-data/cleanup",
    response_model=AdminSmokeDataCleanupResultRead,
)
def cleanup_smoke_data(
    payload: AdminSmokeDataCleanupRequest,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
) -> AdminSmokeDataCleanupResultRead:
    try:
        return AdminMaintenanceService(db).cleanup_smoke_data(confirm=payload.confirm)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "/maintenance/presentation-demo-data/preview",
    response_model=AdminPresentationDemoDataPreviewRead,
)
def preview_presentation_demo_data(
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
) -> AdminPresentationDemoDataPreviewRead:
    return AdminMaintenanceService(db).preview_presentation_demo_data()


@router.post(
    "/maintenance/presentation-demo-data/seed",
    response_model=AdminPresentationDemoDataSeedResultRead,
)
def seed_presentation_demo_data(
    payload: AdminPresentationDemoDataSeedRequest,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
) -> AdminPresentationDemoDataSeedResultRead:
    try:
        return AdminMaintenanceService(db).seed_presentation_demo_data(
            confirm=payload.confirm,
            created_by_user_id=admin.id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
