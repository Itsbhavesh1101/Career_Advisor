from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, timezone
from types import SimpleNamespace

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
        def commit(self) -> None:
            return None

    def _get_db():
        yield FakeDB()

    app.dependency_overrides[deps.get_db] = _get_db


def _fake_question():
    return SimpleNamespace(
        id="q-1",
        session_id="s-1",
        position=1,
        source="fallback",
        trait_tag="analytical",
        question_text="How do you solve a difficult problem?",
        options=[
            {"option_id": "a", "text": "Break it down", "trait_effect": {"analytical": 0.2}},
            {"option_id": "b", "text": "Discuss with peers", "trait_effect": {"collaboration": 0.14}},
            {"option_id": "c", "text": "Try quickly", "trait_effect": {"risk_tolerance": 0.1}},
        ],
        schema_version="v1",
        prompt_version="v1",
    )


def _fake_session(status: str = "in_progress"):
    return SimpleNamespace(
        id="s-1",
        status=status,
        fallback_mode=True,
        breaker_open=False,
        questions_answered=1,
        min_questions=8,
        max_questions=15,
        confidence=0.32,
        current_traits={"analytical": 0.62},
        current_state={
            "recent_answers": [],
            "ai_status": "guided_adaptive",
            "adaptation_reason": "Testing analytical reasoning because confidence is still forming.",
            "next_focus": "Analytical reasoning",
        },
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def test_start_quiz_session_success(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.api.routes import psychometric_quiz as quiz_route

    _override_auth_context()
    _override_db()

    class FakeService:
        def __init__(self, db):
            del db

        def start_session(self, profile_id: int, user_id: int, *, allow_admin: bool = False):
            del profile_id, user_id, allow_admin
            return _fake_session()

        def get_current_question(self, session):
            del session
            return _fake_question()

    monkeypatch.setattr(quiz_route, "PsychometricSessionService", FakeService)

    client = TestClient(app)
    response = client.post("/api/v1/psychometric-quiz/start/1")

    assert response.status_code == 200
    body = response.json()
    assert body["session"]["session_id"] == "s-1"
    assert body["session"]["current_question"]["source"] == "fallback"
    assert body["session"]["ai_status"] == "guided_adaptive"
    assert body["session"]["next_focus"] == "Analytical reasoning"


def test_submit_quiz_answer_duplicate(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.api.routes import psychometric_quiz as quiz_route

    _override_auth_context()
    _override_db()

    class FakeService:
        def __init__(self, db):
            del db

        def submit_answer(self, session_id, payload, user_id: int, *, allow_admin: bool = False):
            del session_id, payload, user_id, allow_admin
            return _fake_session(), True

        def get_current_question(self, session):
            del session
            return _fake_question()

    monkeypatch.setattr(quiz_route, "PsychometricSessionService", FakeService)

    client = TestClient(app)
    response = client.post(
        "/api/v1/psychometric-quiz/s-1/answer",
        json={
            "question_id": "q-1",
            "option_id": "a",
            "answer_id": "ans-1",
            "idempotency_key": "q-1:a",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["accepted"] is False
    assert body["duplicate"] is True


def test_get_quiz_status_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.api.routes import psychometric_quiz as quiz_route

    _override_auth_context()
    _override_db()

    class FakeService:
        def __init__(self, db):
            del db

        def get_session(self, session_id: str, user_id: int, *, allow_admin: bool = False):
            del session_id, user_id, allow_admin
            return None

        def get_current_question(self, session):
            del session
            return None

    monkeypatch.setattr(quiz_route, "PsychometricSessionService", FakeService)

    client = TestClient(app)
    response = client.get("/api/v1/psychometric-quiz/s-missing/status")

    assert response.status_code == 404


def test_report_quiz_abandonment_success(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.api.routes import psychometric_quiz as quiz_route

    _override_auth_context()
    _override_db()

    class FakeService:
        def __init__(self, db):
            del db

        def record_abandonment(
            self,
            session_id: str,
            user_id: int,
            *,
            reason: str | None = None,
            allow_admin: bool = False,
        ):
            del session_id, user_id, reason, allow_admin
            return _fake_session()

        def get_current_question(self, session):
            del session
            return _fake_question()

    monkeypatch.setattr(quiz_route, "PsychometricSessionService", FakeService)

    client = TestClient(app)
    response = client.post(
        "/api/v1/psychometric-quiz/s-1/abandon",
        json={"reason": "route_change"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] == "s-1"
    assert body["status"] == "in_progress"


def test_start_quiz_session_respects_feature_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.api.routes import psychometric_quiz as quiz_route

    _override_auth_context()
    _override_db()
    monkeypatch.setattr(
        quiz_route,
        "get_settings",
        lambda: SimpleNamespace(psychometric_quiz_enabled=False),
    )

    client = TestClient(app)
    response = client.post("/api/v1/psychometric-quiz/start/1")

    assert response.status_code == 503
    assert response.json()["error"]["message"] == "Psychometric quiz is temporarily disabled"


def test_start_quiz_session_rate_limit_returns_429(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.api.routes import psychometric_quiz as quiz_route

    _override_auth_context()
    _override_db()

    class FakeService:
        def __init__(self, db):
            del db

        def start_session(self, profile_id: int, user_id: int, *, allow_admin: bool = False):
            del profile_id, user_id, allow_admin
            return _fake_session()

        def get_current_question(self, session):
            del session
            return _fake_question()

    monkeypatch.setattr(quiz_route, "PsychometricSessionService", FakeService)

    client = TestClient(app)
    statuses: list[int] = []
    for _ in range(18):
        response = client.post("/api/v1/psychometric-quiz/start/1")
        statuses.append(response.status_code)
        if response.status_code == 429:
            break

    assert 429 in statuses
