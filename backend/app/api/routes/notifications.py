from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_current_user, get_db
from app.models.user import User
from app.schemas.notification import (
    NotificationAnnouncementResult,
    NotificationListRead,
    NotificationMarkAllResult,
    NotificationRead,
    PlacementAnnouncementCreate,
)
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=NotificationListRead)
def list_notifications(
    unread_only: bool = False,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> NotificationListRead:
    return NotificationService(db).list_user_notifications(
        user=user,
        unread_only=unread_only,
        limit=limit,
    )


@router.post("/{notification_id}/read", response_model=NotificationRead)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> NotificationRead:
    try:
        return NotificationService(db).mark_read(notification_id=notification_id, user=user)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post("/read-all", response_model=NotificationMarkAllResult)
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> NotificationMarkAllResult:
    return NotificationService(db).mark_all_read(user=user)


@router.post(
    "/admin/placement-announcements",
    response_model=NotificationAnnouncementResult,
)
def create_placement_announcement(
    payload: PlacementAnnouncementCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> NotificationAnnouncementResult:
    return NotificationService(db).create_placement_announcement(
        payload,
        created_by_user_id=admin.id,
    )
