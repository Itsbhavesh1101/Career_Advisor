from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.api import deps
from app.api.routes import admin_dashboard as admin_routes
from app.schemas.admin_maintenance import (
    AdminPresentationDemoDataPreviewRead,
    AdminPresentationDemoDataSeedResultRead,
    AdminSmokeDataCleanupPreviewRead,
    AdminSmokeDataCleanupResultRead,
)
from app.services.admin_maintenance_service import (
    PRESENTATION_DEMO_SEED_CONFIRMATION,
    SMOKE_CLEANUP_CONFIRMATION,
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


def _override_admin():
    return SimpleNamespace(id=1, email="admin@institution.edu")


class _FakeAdminMaintenanceService:
    last_confirm = None

    def __init__(self, db) -> None:
        self.db = db

    def preview_smoke_data_cleanup(self):
        return AdminSmokeDataCleanupPreviewRead(
            users=1,
            profiles=1,
            rag_sources=1,
            sample_emails=["sage-smoke-college@example.com"],
            sample_rag_titles=["Smoke upload"],
        )

    def cleanup_smoke_data(self, *, confirm: str):
        type(self).last_confirm = confirm
        if confirm != SMOKE_CLEANUP_CONFIRMATION:
            raise ValueError("Cleanup confirmation phrase does not match.")
        return AdminSmokeDataCleanupResultRead(
            users=1,
            profiles=1,
            rag_sources=1,
            sample_emails=["sage-smoke-college@example.com"],
            sample_rag_titles=["Smoke upload"],
            deleted=True,
        )

    def preview_presentation_demo_data(self):
        return AdminPresentationDemoDataPreviewRead(
            users=2,
            profiles=2,
            admin_managed_items=6,
            placement_companies=1,
            placement_opportunities=1,
            notifications=2,
            sample_emails=[
                "demo.presentation.twelfth@example.com",
                "demo.presentation.college@example.com",
            ],
            sample_items=["AI Foundation Bridge", "Aptitude Sprint"],
        )

    def seed_presentation_demo_data(
        self,
        *,
        confirm: str,
        created_by_user_id: int | None = None,
    ):
        type(self).last_confirm = confirm
        if created_by_user_id != 1:
            raise AssertionError("admin id should be forwarded")
        if confirm != PRESENTATION_DEMO_SEED_CONFIRMATION:
            raise ValueError("Demo seed confirmation phrase does not match.")
        return AdminPresentationDemoDataSeedResultRead(
            users=2,
            profiles=2,
            admin_managed_items=6,
            placement_companies=1,
            placement_opportunities=1,
            notifications=2,
            sample_emails=[
                "demo.presentation.twelfth@example.com",
                "demo.presentation.college@example.com",
            ],
            sample_items=["AI Foundation Bridge", "Aptitude Sprint"],
            seeded=True,
        )


@pytest.fixture(autouse=True)
def _clear_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


def test_admin_can_preview_safe_smoke_cleanup(monkeypatch) -> None:
    monkeypatch.setattr(
        admin_routes,
        "AdminMaintenanceService",
        _FakeAdminMaintenanceService,
    )
    app.dependency_overrides[deps.get_current_admin] = _override_admin
    app.dependency_overrides[deps.get_db] = _override_db

    response = TestClient(app).get("/api/v1/admin/maintenance/smoke-data/preview")

    assert response.status_code == 200
    data = response.json()
    assert data["users"] == 1
    assert data["profiles"] == 1
    assert data["sample_emails"] == ["sage-smoke-college@example.com"]


def test_admin_cleanup_requires_exact_confirmation(monkeypatch) -> None:
    monkeypatch.setattr(
        admin_routes,
        "AdminMaintenanceService",
        _FakeAdminMaintenanceService,
    )
    app.dependency_overrides[deps.get_current_admin] = _override_admin
    app.dependency_overrides[deps.get_db] = _override_db
    client = TestClient(app)

    rejected = client.post(
        "/api/v1/admin/maintenance/smoke-data/cleanup",
        json={"confirm": "delete"},
    )
    accepted = client.post(
        "/api/v1/admin/maintenance/smoke-data/cleanup",
        json={"confirm": SMOKE_CLEANUP_CONFIRMATION},
    )

    assert rejected.status_code == 400
    assert accepted.status_code == 200
    assert accepted.json()["deleted"] is True
    assert _FakeAdminMaintenanceService.last_confirm == SMOKE_CLEANUP_CONFIRMATION


def test_admin_can_preview_and_seed_presentation_demo_data(monkeypatch) -> None:
    monkeypatch.setattr(
        admin_routes,
        "AdminMaintenanceService",
        _FakeAdminMaintenanceService,
    )
    app.dependency_overrides[deps.get_current_admin] = _override_admin
    app.dependency_overrides[deps.get_db] = _override_db
    client = TestClient(app)

    preview = client.get("/api/v1/admin/maintenance/presentation-demo-data/preview")
    rejected = client.post(
        "/api/v1/admin/maintenance/presentation-demo-data/seed",
        json={"confirm": "seed"},
    )
    accepted = client.post(
        "/api/v1/admin/maintenance/presentation-demo-data/seed",
        json={"confirm": PRESENTATION_DEMO_SEED_CONFIRMATION},
    )

    assert preview.status_code == 200
    assert preview.json()["profiles"] == 2
    assert rejected.status_code == 400
    assert accepted.status_code == 200
    assert accepted.json()["seeded"] is True
    assert _FakeAdminMaintenanceService.last_confirm == PRESENTATION_DEMO_SEED_CONFIRMATION
