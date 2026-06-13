from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.api import deps
from main import app


@pytest.fixture(autouse=True)
def _cleanup_overrides() -> Generator[None, None, None]:
    yield
    app.dependency_overrides.clear()


def _override_auth_context(role: str = "user") -> None:
    user = SimpleNamespace(id=7, email="user@example.com", student_type="college_student")

    def _current_user_context():
        return user, role

    app.dependency_overrides[deps.get_current_user_context] = _current_user_context


def _override_db() -> None:
    class FakeDB:
        def expire_all(self) -> None:
            return None

    def _get_db():
        yield FakeDB()

    app.dependency_overrides[deps.get_db] = _get_db


def test_analysis_dispatch_returns_job_id(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.api.routes import career_analysis as analysis_route

    _override_auth_context()
    _override_db()

    class FakeService:
        def __init__(self, db):
            del db

        def create_job(self, profile_id: int, user_id: int, *, allow_admin: bool = False):
            del profile_id, user_id, allow_admin
            return SimpleNamespace(id="job-123", status="queued")

        def get_job(self, job_id: str, user_id: int, *, allow_admin: bool = False):
            del user_id, allow_admin
            return SimpleNamespace(id=job_id, status="queued")

        def mark_job_failed(self, job_id: str, error: str, *, message: str = "Analysis job failed"):
            del job_id, error, message
            return None

    dispatched: list[str] = []

    monkeypatch.setattr(analysis_route, "AnalysisJobService", FakeService)
    monkeypatch.setattr(analysis_route, "dispatch_analysis_job", lambda job_id: dispatched.append(job_id))

    client = TestClient(app)
    response = client.post("/api/v1/analysis/1")

    assert response.status_code == 202
    assert response.json() == {"job_id": "job-123", "status": "queued"}
    assert dispatched == ["job-123"]


def test_analysis_dispatch_failure_returns_503(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.api.routes import career_analysis as analysis_route

    _override_auth_context()
    _override_db()

    class FakeService:
        def __init__(self, db):
            del db
            self.marked: list[tuple[str, str, str]] = []

        def create_job(self, profile_id: int, user_id: int, *, allow_admin: bool = False):
            del profile_id, user_id, allow_admin
            return SimpleNamespace(id="job-err", status="queued")

        def get_job(self, job_id: str, user_id: int, *, allow_admin: bool = False):
            del job_id, user_id, allow_admin
            return None

        def mark_job_failed(self, job_id: str, error: str, *, message: str = "Analysis job failed"):
            self.marked.append((job_id, error, message))

    fake_service = FakeService(db=None)
    monkeypatch.setattr(analysis_route, "AnalysisJobService", lambda _db: fake_service)

    def _raise_dispatch(_job_id: str) -> None:
        raise RuntimeError("broker unavailable")

    monkeypatch.setattr(analysis_route, "dispatch_analysis_job", _raise_dispatch)

    client = TestClient(app)
    response = client.post("/api/v1/analysis/1")

    assert response.status_code == 503
    body = response.json()
    assert body["error"]["message"] == "Unable to queue analysis job at the moment. Please retry shortly."
    assert fake_service.marked and fake_service.marked[0][0] == "job-err"


def test_job_status_returns_envelope(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.api.routes import jobs as jobs_route

    _override_auth_context()
    _override_db()

    class FakeService:
        def __init__(self, db):
            del db

        def get_job(self, job_id: str, user_id: int, *, allow_admin: bool = False):
            del user_id, allow_admin
            return SimpleNamespace(
                id=job_id,
                student_profile_id=3,
                status="completed",
                progress=100,
                message="Completed",
                error=None,
                analysis_id=101,
                snapshot_summary={
                    "snapshot_version": "agentic-snapshot-v1",
                    "profile_id": 1,
                    "user_type": "college_student",
                    "career_analysis_id": 101,
                    "agent_stages": [
                        {
                            "stage": "verifier_agent",
                            "label": "Verifier Agent",
                            "status": "completed",
                            "source": "rule_engine",
                            "output_ref": None,
                            "notes": [],
                        }
                    ],
                    "verifier": {
                        "status": "approved",
                        "confidence": 92,
                        "blockers": [],
                        "warnings": [],
                        "evidence_count": 1,
                        "next_best_actions": ["Review next action."],
                    },
                },
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

    monkeypatch.setattr(jobs_route, "AnalysisJobService", FakeService)

    client = TestClient(app)
    response = client.get("/api/v1/jobs/job-777")

    assert response.status_code == 200
    assert response.json()["job"]["id"] == "job-777"
    assert response.json()["job"]["status"] == "completed"
    summary = response.json()["job"]["snapshot_summary"]
    assert summary["snapshot_version"] == "agentic-snapshot-v1"
    assert summary["verifier"]["status"] == "approved"
    assert summary["agent_stages"][0]["stage"] == "verifier_agent"


def test_job_status_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.api.routes import jobs as jobs_route

    _override_auth_context()
    _override_db()

    class FakeService:
        def __init__(self, db):
            del db

        def get_job(self, job_id: str, user_id: int, *, allow_admin: bool = False):
            del job_id, user_id, allow_admin
            return None

    monkeypatch.setattr(jobs_route, "AnalysisJobService", FakeService)

    client = TestClient(app)
    response = client.get("/api/v1/jobs/job-missing")

    assert response.status_code == 404
    assert response.json()["error"]["message"] == "Job not found"
