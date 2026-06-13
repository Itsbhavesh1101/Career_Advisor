from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.api import deps
from app.api.routes import admission_intelligence as admission_routes
from app.schemas.admission_intelligence import (
    AdmissionCounselorBriefRead,
    AdmissionDashboardRead,
    AdmissionLeadRead,
    AdmissionMetricsRead,
)
from main import app


class _FakeDB:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


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


def _dashboard(limit: int) -> AdmissionDashboardRead:
    return AdmissionDashboardRead(
        metrics=AdmissionMetricsRead(
            total_twelfth_profiles=1,
            analyzed_profiles=1,
            needs_analysis=0,
            high_intent=1,
            wrong_branch_risk=0,
            ready_for_counseling=1,
        ),
        leads=[
            AdmissionLeadRead(
                profile_id=7,
                student_name="Admission Lead",
                current_interest="AI",
                preferred_stream="Science",
                recommended_program="B.Tech CSE - AIML",
                confidence=88,
                status="ready_for_counseling",
                priority="low",
                lost_reason_signals=[],
                counselor_brief=AdmissionCounselorBriefRead(
                    best_fit="B.Tech CSE - AIML",
                    confidence=88,
                    talking_points=[f"Requested limit {limit}"],
                    expectation_checks=[],
                    first_year_actions=[],
                    evidence_titles=["AIML Handbook"],
                    follow_up_questions=["What outcome do you expect?"],
                ),
                created_at=datetime(2026, 5, 20, tzinfo=timezone.utc),
            )
        ],
    )


class _FakeAdmissionIntelligenceService:
    last_db = None
    last_limit = None

    def __init__(self, db) -> None:
        type(self).last_db = db

    def get_dashboard(self, limit: int = 12) -> AdmissionDashboardRead:
        type(self).last_limit = limit
        return _dashboard(limit)


@pytest.fixture(autouse=True)
def _clear_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()
    _FakeAdmissionIntelligenceService.last_db = None
    _FakeAdmissionIntelligenceService.last_limit = None


def test_admission_dashboard_requires_authentication() -> None:
    app.dependency_overrides[deps.get_db] = _override_db

    client = TestClient(app)
    response = client.get("/api/v1/admission-intelligence/dashboard")

    assert response.status_code == 401


def test_non_admin_users_cannot_read_admission_dashboard(monkeypatch) -> None:
    monkeypatch.setattr(
        admission_routes,
        "AdmissionIntelligenceService",
        _FakeAdmissionIntelligenceService,
    )
    app.dependency_overrides[deps.get_db] = _override_db
    app.dependency_overrides[deps.get_current_user_context] = _override_auth("user")

    client = TestClient(app)
    response = client.get("/api/v1/admission-intelligence/dashboard")

    assert response.status_code == 403


def test_admin_can_read_admission_dashboard(monkeypatch) -> None:
    monkeypatch.setattr(
        admission_routes,
        "AdmissionIntelligenceService",
        _FakeAdmissionIntelligenceService,
    )
    app.dependency_overrides[deps.get_db] = _override_db
    app.dependency_overrides[deps.get_current_user_context] = _override_auth("admin")

    client = TestClient(app)
    response = client.get("/api/v1/admission-intelligence/dashboard?limit=2")

    assert response.status_code == 200
    data = response.json()
    assert data["metrics"]["total_twelfth_profiles"] == 1
    assert data["leads"][0]["profile_id"] == 7
    assert data["leads"][0]["counselor_brief"]["talking_points"] == [
        "Requested limit 2"
    ]
    assert _FakeAdmissionIntelligenceService.last_limit == 2


@pytest.mark.parametrize("limit", [0, 51])
def test_admission_dashboard_limit_is_bounded_by_validation(
    monkeypatch,
    limit: int,
) -> None:
    monkeypatch.setattr(
        admission_routes,
        "AdmissionIntelligenceService",
        _FakeAdmissionIntelligenceService,
    )
    app.dependency_overrides[deps.get_db] = _override_db
    app.dependency_overrides[deps.get_current_user_context] = _override_auth("admin")

    client = TestClient(app)
    response = client.get(f"/api/v1/admission-intelligence/dashboard?limit={limit}")

    assert response.status_code == 422
    assert _FakeAdmissionIntelligenceService.last_limit is None
