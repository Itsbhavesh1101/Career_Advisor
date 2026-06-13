from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models.notification import UserNotification
from app.models.student_profile import StudentProfile
from app.models.user import User
from app.schemas.notification import (
    NotificationAnnouncementResult,
    NotificationListRead,
    NotificationMarkAllResult,
    NotificationRead,
    PlacementAnnouncementCreate,
)


def _to_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


class NotificationService:
    def __init__(self, db: Session):
        self.db = db

    def create_for_user(
        self,
        *,
        recipient_user_id: int,
        notification_type: str,
        title: str,
        message: str | None = None,
        action_url: str | None = None,
        profile_id: int | None = None,
        priority: str = "normal",
        created_by_user_id: int | None = None,
        metadata: dict[str, Any] | None = None,
        commit: bool = True,
    ) -> NotificationRead:
        row = UserNotification(
            recipient_user_id=recipient_user_id,
            profile_id=profile_id,
            notification_type=notification_type,
            title=title,
            message=message,
            action_url=action_url,
            priority=priority,
            created_by_user_id=created_by_user_id,
            event_metadata=metadata or {},
        )
        self.db.add(row)
        self.db.flush()
        if commit:
            self.db.commit()
            self.db.refresh(row)
        return self._read(row)

    def create_for_profile(
        self,
        *,
        profile_id: int,
        notification_type: str,
        title: str,
        message: str | None = None,
        action_url: str | None = None,
        priority: str = "normal",
        created_by_user_id: int | None = None,
        metadata: dict[str, Any] | None = None,
        commit: bool = True,
    ) -> NotificationRead | None:
        profile = self.db.get(StudentProfile, profile_id)
        if profile is None:
            return None
        return self.create_for_user(
            recipient_user_id=profile.user_id,
            profile_id=profile.id,
            notification_type=notification_type,
            title=title,
            message=message,
            action_url=action_url,
            priority=priority,
            created_by_user_id=created_by_user_id,
            metadata=metadata,
            commit=commit,
        )

    def list_user_notifications(
        self,
        *,
        user: User,
        unread_only: bool = False,
        limit: int = 20,
    ) -> NotificationListRead:
        stmt: Select[tuple[UserNotification]] = select(UserNotification).where(
            UserNotification.recipient_user_id == user.id
        )
        count_stmt = select(func.count(UserNotification.id)).where(
            UserNotification.recipient_user_id == user.id
        )
        if unread_only:
            stmt = stmt.where(UserNotification.read_at.is_(None))
            count_stmt = count_stmt.where(UserNotification.read_at.is_(None))
        rows = self.db.scalars(
            stmt.order_by(UserNotification.created_at.desc(), UserNotification.id.desc()).limit(
                limit
            )
        ).all()
        unread_count = int(
            self.db.scalar(
                select(func.count(UserNotification.id)).where(
                    UserNotification.recipient_user_id == user.id,
                    UserNotification.read_at.is_(None),
                )
            )
            or 0
        )
        return NotificationListRead(
            items=[self._read(row) for row in rows],
            total=int(self.db.scalar(count_stmt) or 0),
            unread_count=unread_count,
        )

    def mark_read(self, *, notification_id: int, user: User) -> NotificationRead:
        row = self.db.get(UserNotification, notification_id)
        if row is None or row.recipient_user_id != user.id:
            raise ValueError("Notification not found")
        if row.read_at is None:
            row.read_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(row)
        return self._read(row)

    def mark_all_read(self, *, user: User) -> NotificationMarkAllResult:
        rows = self.db.scalars(
            select(UserNotification).where(
                UserNotification.recipient_user_id == user.id,
                UserNotification.read_at.is_(None),
            )
        ).all()
        now = datetime.now(timezone.utc)
        for row in rows:
            row.read_at = now
        self.db.commit()
        return NotificationMarkAllResult(updated_count=len(rows))

    def create_placement_announcement(
        self,
        payload: PlacementAnnouncementCreate,
        *,
        created_by_user_id: int,
    ) -> NotificationAnnouncementResult:
        stmt = select(StudentProfile)
        if payload.audience != "all":
            stmt = stmt.where(StudentProfile.user_type == payload.audience)
        profiles = self.db.scalars(stmt).all()
        seen_user_ids: set[int] = set()
        created = 0
        for profile in profiles:
            if profile.user_id in seen_user_ids:
                continue
            seen_user_ids.add(profile.user_id)
            self.create_for_user(
                recipient_user_id=profile.user_id,
                profile_id=profile.id,
                notification_type="placement_announcement",
                title=payload.title,
                message=payload.message,
                action_url=payload.action_url,
                priority=payload.priority,
                created_by_user_id=created_by_user_id,
                metadata={"audience": payload.audience},
                commit=False,
            )
            created += 1
        self.db.commit()
        return NotificationAnnouncementResult(created_count=created)

    def _read(self, row: UserNotification) -> NotificationRead:
        return NotificationRead(
            id=row.id,
            recipient_user_id=row.recipient_user_id,
            profile_id=row.profile_id,
            notification_type=row.notification_type,
            title=row.title,
            message=row.message,
            action_url=row.action_url,
            priority=row.priority,
            read_at=_to_aware(row.read_at) if row.read_at else None,
            created_by_user_id=row.created_by_user_id,
            metadata=row.event_metadata or {},
            created_at=_to_aware(row.created_at),
        )
