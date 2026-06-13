from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.api import deps
from app.api.routes import admin_management as admin_management_routes
from app.schemas.admin_management import AdminManagedItemRead, AdminManagedItemPageRead
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


def _override_admin():
    return SimpleNamespace(id=7, email="admin@institution.edu")


def _override_user():
    raise admin_management_routes.HTTPException(status_code=403, detail="Admin access required")


def _item_read(**overrides):
    data = {
        "id": 10,
        "item_type": "training_program",
        "slug": "python-placement-bootcamp",
        "title": "Python Placement Bootcamp",
        "summary": "Four-week training plan",
        "status": "active",
        "payload": {"focus_skills": ["Python"]},
        "created_by_user_id": 7,
        "updated_by_user_id": 7,
        "created_at": "2026-05-25T00:00:00Z",
        "updated_at": "2026-05-25T00:00:00Z",
    }
    data.update(overrides)
    return AdminManagedItemRead.model_validate(data)


class _FakeAdminManagementService:
    created_payload = None
    updated_payload = None

    def __init__(self, db) -> None:
        self.db = db

    def list_items(self, **_kwargs):
        return AdminManagedItemPageRead(items=[_item_read()], total=1)

    def create_item(self, payload, user_id: int):
        type(self).created_payload = (payload, user_id)
        return _item_read(
            slug=payload.slug,
            title=payload.title,
            item_type=payload.item_type,
            payload=payload.payload,
            created_by_user_id=user_id,
            updated_by_user_id=user_id,
        )

    def update_item(self, item_id: int, payload, user_id: int):
        type(self).updated_payload = (item_id, payload, user_id)
        return _item_read(id=item_id, title=payload.title or "Python Placement Bootcamp")

    def archive_item(self, item_id: int, user_id: int):
        return _item_read(id=item_id, status="inactive", updated_by_user_id=user_id)


@pytest.fixture(autouse=True)
def _clear_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


def test_admin_can_manage_items(monkeypatch) -> None:
    monkeypatch.setattr(
        admin_management_routes,
        "AdminManagementService",
        _FakeAdminManagementService,
    )
    app.dependency_overrides[deps.get_current_admin] = _override_admin
    app.dependency_overrides[deps.get_db] = _override_db
    client = TestClient(app)

    listed = client.get("/api/v1/admin/management/items")
    created = client.post(
        "/api/v1/admin/management/items",
        json={
            "item_type": "training_program",
            "slug": "python-placement-bootcamp",
            "title": "Python Placement Bootcamp",
            "summary": "Four-week training plan",
            "payload": {"focus_skills": ["Python"]},
        },
    )
    archived = client.delete("/api/v1/admin/management/items/10")

    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert created.status_code == 201
    assert created.json()["created_by_user_id"] == 7
    assert archived.status_code == 200
    assert archived.json()["status"] == "inactive"


def test_admin_can_create_policy_management_item(monkeypatch) -> None:
    monkeypatch.setattr(
        admin_management_routes,
        "AdminManagementService",
        _FakeAdminManagementService,
    )
    app.dependency_overrides[deps.get_current_admin] = _override_admin
    app.dependency_overrides[deps.get_db] = _override_db
    client = TestClient(app)

    response = client.post(
        "/api/v1/admin/management/items",
        json={
            "item_type": "institution_policy",
            "slug": "placement-policy",
            "title": "Placement policy",
            "payload": {
                "policy_area": "placement",
                "rules": ["Students must keep resumes updated."],
            },
        },
    )

    assert response.status_code == 201
    assert response.json()["item_type"] == "institution_policy"
    assert _FakeAdminManagementService.created_payload[0].payload["policy_area"] == (
        "placement"
    )


def test_non_admin_cannot_manage_items(monkeypatch) -> None:
    monkeypatch.setattr(
        admin_management_routes,
        "AdminManagementService",
        _FakeAdminManagementService,
    )
    app.dependency_overrides[deps.get_current_admin] = _override_user
    app.dependency_overrides[deps.get_db] = _override_db

    response = TestClient(app).get("/api/v1/admin/management/items")

    assert response.status_code == 403
