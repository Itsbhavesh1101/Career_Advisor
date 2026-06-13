from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.api import deps
from app.api.routes import admin_dashboard as admin_routes
from app.schemas.admin_dashboard import (
    AdminMetricsRead,
    AdminReadinessSummaryRead,
    AdminStudentPageRead,
    AdminStudentRead,
    SystemReadinessRead,
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


def _override_auth(role: str):
    def _auth():
        return SimpleNamespace(id=1, email=f"{role}@sage.local"), role

    return _auth


class _FakeAdminDashboardService:
    last_filters = None
    last_export_filters = None

    def __init__(self, db) -> None:
        self.db = db

    def get_metrics(self) -> AdminMetricsRead:
        return AdminMetricsRead(
            total_profiles=2,
            total_students=2,
            placement_ready=1,
            needs_training=1,
            high_risk=0,
        )

    def get_readiness_summary(self) -> AdminReadinessSummaryRead:
        return AdminReadinessSummaryRead(
            pending_rag_reviews=2,
            stale_rag_sources=1,
            failed_embeddings=3,
            chunks_without_embeddings=4,
            failed_analysis_jobs=5,
            missing_analysis=6,
            missing_resume=7,
        )

    def get_system_readiness(self) -> SystemReadinessRead:
        return SystemReadinessRead(
            llm_provider="bedrock",
            llm_configured=True,
            embedding_provider="bedrock",
            embedding_configured=True,
            vector_search_enabled=True,
            celery_task_always_eager=True,
            failed_analysis_jobs=5,
            failed_embedding_jobs=3,
            pending_rag_reviews=2,
            stale_rag_sources=1,
            hints=["Eager mode is acceptable for first launch."],
        )

    def list_students(self, page=1, page_size=25, filters=None):
        type(self).last_filters = filters
        item = AdminStudentRead(
            profile_id=8,
            user_id=2,
            name="Filtered Student",
            user_type="college_student",
            degree="B.Tech",
            specialization="CSE",
            cgpa=8.2,
            created_at=datetime(2026, 5, 20, tzinfo=timezone.utc),
            employability_score=82,
            placement_risk="Low",
            has_analysis=True,
            has_resume=False,
            readiness_band="ready",
        )
        return [item], 1, 1

    def export_students_csv(self, filters=None) -> str:
        type(self).last_export_filters = filters
        return (
            "profile_id,name,user_type,specialization,readiness_band\n"
            "8,Filtered Student,college_student,CSE,ready\n"
        )


@pytest.fixture(autouse=True)
def _clear_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()
    _FakeAdminDashboardService.last_filters = None
    _FakeAdminDashboardService.last_export_filters = None


def test_admin_students_accepts_launch_filters(monkeypatch) -> None:
    monkeypatch.setattr(
        admin_routes,
        "AdminDashboardService",
        _FakeAdminDashboardService,
    )
    app.dependency_overrides[deps.get_db] = _override_db
    app.dependency_overrides[deps.get_current_user_context] = _override_auth("admin")

    client = TestClient(app)
    response = client.get(
        "/api/v1/admin/students",
        params={
            "student_type": "college_student",
            "specialization": "CSE",
            "readiness_band": "ready",
            "placement_risk": "Low",
            "missing_resume": "true",
            "missing_analysis": "false",
            "sort": "readiness_desc",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["items"][0]["readiness_band"] == "ready"
    assert data["items"][0]["has_resume"] is False
    assert _FakeAdminDashboardService.last_filters.student_type == "college_student"
    assert _FakeAdminDashboardService.last_filters.missing_resume is True
    assert _FakeAdminDashboardService.last_filters.sort == "readiness_desc"


def test_admin_student_export_returns_csv(monkeypatch) -> None:
    monkeypatch.setattr(
        admin_routes,
        "AdminDashboardService",
        _FakeAdminDashboardService,
    )
    app.dependency_overrides[deps.get_db] = _override_db
    app.dependency_overrides[deps.get_current_user_context] = _override_auth("admin")

    client = TestClient(app)
    response = client.get(
        "/api/v1/admin/students/export",
        params={"student_type": "college_student", "missing_resume": "true"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "Filtered Student" in response.text
    assert _FakeAdminDashboardService.last_export_filters.missing_resume is True


def test_system_readiness_is_admin_only(monkeypatch) -> None:
    monkeypatch.setattr(
        admin_routes,
        "AdminDashboardService",
        _FakeAdminDashboardService,
    )
    app.dependency_overrides[deps.get_db] = _override_db
    app.dependency_overrides[deps.get_current_user_context] = _override_auth("user")

    client = TestClient(app)
    response = client.get("/api/v1/admin/system-readiness")

    assert response.status_code == 403


def test_admin_can_read_system_readiness(monkeypatch) -> None:
    monkeypatch.setattr(
        admin_routes,
        "AdminDashboardService",
        _FakeAdminDashboardService,
    )
    app.dependency_overrides[deps.get_db] = _override_db
    app.dependency_overrides[deps.get_current_user_context] = _override_auth("admin")

    client = TestClient(app)
    response = client.get("/api/v1/admin/system-readiness")

    assert response.status_code == 200
    data = response.json()
    assert data["llm_provider"] == "bedrock"
    assert data["embedding_configured"] is True
    assert data["pending_rag_reviews"] == 2


def test_admin_metrics_include_readiness_summary(monkeypatch) -> None:
    monkeypatch.setattr(
        admin_routes,
        "AdminDashboardService",
        _FakeAdminDashboardService,
    )
    app.dependency_overrides[deps.get_db] = _override_db
    app.dependency_overrides[deps.get_current_user_context] = _override_auth("admin")

    client = TestClient(app)
    response = client.get("/api/v1/admin/readiness-summary")

    assert response.status_code == 200
    data = response.json()
    assert data["pending_rag_reviews"] == 2
    assert data["missing_resume"] == 7
