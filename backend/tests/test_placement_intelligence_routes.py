from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.api import deps
from app.api.routes import placement_intelligence as placement_routes
from app.schemas.placement_intelligence import (
    CompanyReadinessRead,
    FacultyAdvisorNoteRead,
    PlacementDashboardRead,
    PlacementMetricsRead,
    PlacementStudentSignalRead,
    SkillEvidenceLedgerRead,
    TrainingROISignalRead,
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


def _dashboard(limit: int) -> PlacementDashboardRead:
    return PlacementDashboardRead(
        metrics=PlacementMetricsRead(
            total_college_profiles=1,
            placement_ready=1,
            needs_training=0,
            high_risk=0,
            company_ready=1,
            evidence_complete=1,
            average_employability=88,
        ),
        students=[
            PlacementStudentSignalRead(
                profile_id=9,
                student_name="Placement Student",
                program="B.Tech - CSE",
                employability_score=88,
                placement_risk="Low",
                top_company="Infosys",
                top_company_score=82,
                status="placement_ready",
                priority="low",
                recommended_actions=[f"Requested limit {limit}"],
                evidence=SkillEvidenceLedgerRead(
                    evidence_score=84,
                    project_count=3,
                    internship_count=1,
                    certification_count=2,
                    resume_quality=90,
                    internship_readiness=80,
                    strengths=["Project portfolio"],
                    gaps=[],
                ),
                created_at=datetime(2026, 5, 20, tzinfo=timezone.utc),
            )
        ],
        company_radar=[
            CompanyReadinessRead(
                company="Infosys",
                average_score=82,
                ready_count=1,
                watch_count=0,
                blocked_count=0,
                missing_skills=[],
            )
        ],
        training_roi=[
            TrainingROISignalRead(
                skill="SQL",
                affected_students=1,
                expected_readiness_lift=11,
                priority="medium",
            )
        ],
        faculty_notes=[
            FacultyAdvisorNoteRead(
                profile_id=9,
                student_name="Placement Student",
                escalation_level="low",
                focus_areas=["SQL"],
                note="Review company interview practice.",
            )
        ],
    )


class _FakePlacementIntelligenceService:
    last_db = None
    last_limit = None

    def __init__(self, db) -> None:
        type(self).last_db = db

    def get_dashboard(self, limit: int = 12) -> PlacementDashboardRead:
        type(self).last_limit = limit
        return _dashboard(limit)


@pytest.fixture(autouse=True)
def _clear_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()
    _FakePlacementIntelligenceService.last_db = None
    _FakePlacementIntelligenceService.last_limit = None


def test_placement_dashboard_requires_authentication() -> None:
    app.dependency_overrides[deps.get_db] = _override_db

    client = TestClient(app)
    response = client.get("/api/v1/placement-intelligence/dashboard")

    assert response.status_code == 401


def test_non_admin_users_cannot_read_placement_dashboard(monkeypatch) -> None:
    monkeypatch.setattr(
        placement_routes,
        "PlacementIntelligenceService",
        _FakePlacementIntelligenceService,
    )
    app.dependency_overrides[deps.get_db] = _override_db
    app.dependency_overrides[deps.get_current_user_context] = _override_auth("user")

    client = TestClient(app)
    response = client.get("/api/v1/placement-intelligence/dashboard")

    assert response.status_code == 403


def test_admin_can_read_placement_dashboard(monkeypatch) -> None:
    monkeypatch.setattr(
        placement_routes,
        "PlacementIntelligenceService",
        _FakePlacementIntelligenceService,
    )
    app.dependency_overrides[deps.get_db] = _override_db
    app.dependency_overrides[deps.get_current_user_context] = _override_auth("admin")

    client = TestClient(app)
    response = client.get("/api/v1/placement-intelligence/dashboard?limit=3")

    assert response.status_code == 200
    data = response.json()
    assert data["metrics"]["total_college_profiles"] == 1
    assert data["students"][0]["profile_id"] == 9
    assert data["students"][0]["recommended_actions"] == ["Requested limit 3"]
    assert _FakePlacementIntelligenceService.last_limit == 3


@pytest.mark.parametrize("limit", [0, 51])
def test_placement_dashboard_limit_is_bounded_by_validation(
    monkeypatch,
    limit: int,
) -> None:
    monkeypatch.setattr(
        placement_routes,
        "PlacementIntelligenceService",
        _FakePlacementIntelligenceService,
    )
    app.dependency_overrides[deps.get_db] = _override_db
    app.dependency_overrides[deps.get_current_user_context] = _override_auth("admin")

    client = TestClient(app)
    response = client.get(f"/api/v1/placement-intelligence/dashboard?limit={limit}")

    assert response.status_code == 422
    assert _FakePlacementIntelligenceService.last_limit is None
