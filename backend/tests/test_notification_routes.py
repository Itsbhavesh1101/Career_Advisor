from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api import deps
from app.api.routes import notifications as notification_routes
from app.schemas.notification import (
    NotificationAnnouncementResult,
    NotificationListRead,
    NotificationRead,
)
from main import app


class _FakeDB:
    def close(self) -> None:
        pass


def _override_db():
    db = _FakeDB()
    try:
        yield db
    finally:
        db.close()


def _override_user():
    return SimpleNamespace(id=11, email="student@example.com", student_type="college_student")


def _override_admin():
    return SimpleNamespace(id=7, email="admin@example.com")


def _notification_read(**overrides):
    data = {
        "id": 5,
        "recipient_user_id": 11,
        "profile_id": 12,
        "notification_type": "placement",
        "title": "Interview scheduled",
        "message": "Round 1 is scheduled.",
        "action_url": "/internship",
        "priority": "normal",
        "read_at": None,
        "created_by_user_id": 7,
        "metadata": {},
        "created_at": datetime(2026, 5, 26, tzinfo=timezone.utc),
    }
    data.update(overrides)
    return NotificationRead.model_validate(data)


class _FakeNotificationService:
    last_announcement = None
    marked_read_id = None

    def __init__(self, _db):
        pass

    def list_user_notifications(self, *, user, unread_only=False, limit=20):
        return NotificationListRead(
            items=[_notification_read(recipient_user_id=user.id)],
            total=1,
            unread_count=1,
        )

    def mark_read(self, *, notification_id: int, user):
        self.__class__.marked_read_id = notification_id
        return _notification_read(id=notification_id, recipient_user_id=user.id, read_at=datetime.now(timezone.utc))

    def mark_all_read(self, *, user):
        return NotificationAnnouncementResult(created_count=1)

    def create_placement_announcement(self, payload, *, created_by_user_id: int):
        self.__class__.last_announcement = (payload, created_by_user_id)
        return NotificationAnnouncementResult(created_count=3)


def test_user_can_list_and_mark_notifications(monkeypatch) -> None:
    app.dependency_overrides[deps.get_db] = _override_db
    app.dependency_overrides[deps.get_current_user] = _override_user
    monkeypatch.setattr(
        notification_routes,
        "NotificationService",
        _FakeNotificationService,
    )
    try:
        client = TestClient(app)
        listing = client.get("/api/v1/notifications")
        read = client.post("/api/v1/notifications/5/read")

        assert listing.status_code == 200
        assert listing.json()["unread_count"] == 1
        assert listing.json()["items"][0]["title"] == "Interview scheduled"
        assert read.status_code == 200
        assert read.json()["read_at"] is not None
        assert _FakeNotificationService.marked_read_id == 5
    finally:
        app.dependency_overrides.clear()


def test_admin_can_create_placement_announcement(monkeypatch) -> None:
    app.dependency_overrides[deps.get_db] = _override_db
    app.dependency_overrides[deps.get_current_admin] = _override_admin
    monkeypatch.setattr(
        notification_routes,
        "NotificationService",
        _FakeNotificationService,
    )
    try:
        client = TestClient(app)
        response = client.post(
            "/api/v1/notifications/admin/placement-announcements",
            json={
                "title": "Drive briefing",
                "message": "Attend the resume briefing.",
                "audience": "college_student",
                "action_url": "/internship",
                "priority": "high",
            },
        )

        assert response.status_code == 200
        assert response.json()["created_count"] == 3
        payload, created_by_user_id = _FakeNotificationService.last_announcement
        assert payload.audience == "college_student"
        assert created_by_user_id == 7
    finally:
        app.dependency_overrides.clear()
