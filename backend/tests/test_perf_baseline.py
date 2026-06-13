from __future__ import annotations

import os
import time
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.api import deps
from main import app


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_PERF_BASELINE") != "1",
    reason="Set RUN_PERF_BASELINE=1 to execute concurrency baseline checks.",
)


def _override_auth_context():
    user = SimpleNamespace(id=1, email="admin@example.com", student_type="college_student")

    def _current_user_context():
        return user, "admin"

    def _current_user():
        return user

    def _current_admin():
        return user

    app.dependency_overrides[deps.get_current_user_context] = _current_user_context
    app.dependency_overrides[deps.get_current_user] = _current_user
    app.dependency_overrides[deps.get_current_admin] = _current_admin


def _override_fake_db_for_mocked_services() -> None:
    class FakeDB:
        def expire_all(self):
            return None

        def close(self):
            return None

    def _get_db():
        yield FakeDB()

    app.dependency_overrides[deps.get_db] = _get_db


def _override_fake_db_for_chat():
    profile = SimpleNamespace(
        id=1,
        user_id=1,
        name="Student",
        degree="B.Tech",
        specialization="AI",
        current_skills=["Python", "SQL"],
        interests=["AI"],
        target_industry="AI",
    )

    class FakeDB:
        def get(self, model, profile_id):
            del model
            return profile if profile_id == 1 else None

        def close(self):
            return None

    def _get_db():
        yield FakeDB()

    app.dependency_overrides[deps.get_db] = _get_db


def _cleanup_overrides() -> None:
    app.dependency_overrides.clear()


def _run_concurrent(
    client: TestClient,
    method: str,
    url: str,
    *,
    body: dict | None = None,
    request_count: int = 24,
):
    def _single_call() -> float:
        start = time.perf_counter()
        if method == "GET":
            response = client.get(url)
        else:
            response = client.post(url, json=body)
        assert response.status_code in {200, 201, 202}
        return (time.perf_counter() - start) * 1000

    with ThreadPoolExecutor(max_workers=12) as executor:
        samples = list(executor.map(lambda _: _single_call(), range(request_count)))
    return max(samples), sum(samples) / len(samples)


def test_admin_students_concurrency_baseline(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.api.routes import admin_dashboard as admin_route

    _override_auth_context()
    _override_fake_db_for_mocked_services()

    class FakeService:
        def __init__(self, db):
            del db

        def get_metrics(self):
            return {
                "total_profiles": 120,
                "total_students": 100,
                "placement_ready": 40,
                "needs_training": 45,
                "high_risk": 15,
            }

        def list_students(self, page: int = 1, page_size: int = 25):
            del page
            items = [
                {
                    "profile_id": i,
                    "user_id": i,
                    "name": f"Student {i}",
                    "degree": "B.Tech",
                    "specialization": "AI",
                    "cgpa": 8.0,
                    "created_at": "2026-01-01T00:00:00Z",
                    "employability_score": 72,
                    "placement_risk": "Low",
                }
                for i in range(1, page_size + 1)
            ]
            return items, 120, 5

    monkeypatch.setattr(admin_route, "AdminDashboardService", FakeService)

    try:
        client = TestClient(app)
        max_ms, avg_ms = _run_concurrent(
            client,
            "GET",
            "/api/v1/admin/students?page=1&page_size=25",
        )
    finally:
        _cleanup_overrides()

    assert avg_ms < 400
    assert max_ms < 1500


def test_analysis_dispatch_concurrency_baseline(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.api.routes import career_analysis as analysis_route

    _override_auth_context()
    _override_fake_db_for_mocked_services()

    class FakeAnalysisJobService:
        def __init__(self, db):
            del db

        def create_job(self, profile_id: int, user_id: int, *, allow_admin: bool = False):
            del profile_id, user_id, allow_admin
            return SimpleNamespace(id="job-123", status="queued")

        def get_job(self, job_id: str, user_id: int, *, allow_admin: bool = False):
            del user_id, allow_admin
            return SimpleNamespace(id=job_id, status="completed")

    monkeypatch.setattr(analysis_route, "AnalysisJobService", FakeAnalysisJobService)
    monkeypatch.setattr(analysis_route, "dispatch_analysis_job", lambda _job_id: None)

    try:
        client = TestClient(app)
        max_ms, avg_ms = _run_concurrent(
            client,
            "POST",
            "/api/v1/analysis/1",
            body={},
            request_count=16,
        )
    finally:
        _cleanup_overrides()

    assert avg_ms < 400
    assert max_ms < 1500


def test_chat_concurrency_baseline(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.api.routes import chat as chat_route

    _override_auth_context()
    _override_fake_db_for_chat()

    class FakeCareerAnalysisService:
        def __init__(self, db):
            del db

        def get_analysis_by_profile_id(self, profile_id: int, user_id: int, allow_admin: bool = False):
            del profile_id, user_id, allow_admin
            return SimpleNamespace(
                career_recommendations=[{"role": "AI Engineer", "score": 80}],
                skill_gaps=[{"skill": "ML", "priority": "high"}],
                learning_roadmap=[{"stage": "Foundations", "topics": ["Python"]}],
            )

    class FakeLLMClient:
        def generate_chat_response(self, **kwargs):
            del kwargs
            return "Keep building role-aligned projects and close your top skill gaps."

    monkeypatch.setattr(chat_route, "CareerAnalysisService", FakeCareerAnalysisService)
    monkeypatch.setattr(chat_route, "LLMClient", FakeLLMClient)

    try:
        client = TestClient(app)
        max_ms, avg_ms = _run_concurrent(
            client,
            "POST",
            "/api/v1/chat/1",
            body={"message": "How should I improve?"},
        )
    finally:
        _cleanup_overrides()

    assert avg_ms < 500
    assert max_ms < 2000
