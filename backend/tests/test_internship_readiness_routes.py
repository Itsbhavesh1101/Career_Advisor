from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.api import deps
from app.api.routes import internship_readiness as internship_routes
from app.schemas.admin_management import (
    ManagedInternshipOpportunityListRead,
    ManagedInternshipOpportunityRead,
)
from main import app


class _FakeDB:
    def __init__(self, profile: object | None = None) -> None:
        self.profile = profile

    def get(self, _model, _id):
        return self.profile

    def close(self) -> None:
        pass


def _override_db():
    db = _FakeDB(profile=SimpleNamespace(id=11, user_id=1))
    try:
        yield db
    finally:
        db.close()


def _override_user():
    return SimpleNamespace(id=1, email="student@example.edu"), "user"


class _FakeAdminManagementService:
    def __init__(self, db) -> None:
        self.db = db

    def list_active_internship_opportunities(self):
        return ManagedInternshipOpportunityListRead(
            total=1,
            items=[
                ManagedInternshipOpportunityRead(
                    id=5,
                    slug="ai-lab",
                    title="AI Lab Internship",
                    summary="Build applied AI project evidence.",
                    company="Innovation Lab",
                    location="Campus",
                    duration="8 weeks",
                    skills=["Python", "ML"],
                    eligibility=["One project"],
                    apply_url="https://example.edu/apply",
                    deadline="2026-07-01",
                    payload={"company": "Innovation Lab"},
                )
            ],
        )


@pytest.fixture(autouse=True)
def _clear_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


def test_student_can_list_managed_internship_catalog(monkeypatch) -> None:
    monkeypatch.setattr(
        internship_routes,
        "AdminManagementService",
        _FakeAdminManagementService,
    )
    app.dependency_overrides[deps.get_current_user_context] = _override_user
    app.dependency_overrides[deps.get_db] = _override_db

    response = TestClient(app).get(
        "/api/v1/internship-readiness/11/managed-opportunities"
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["title"] == "AI Lab Internship"
