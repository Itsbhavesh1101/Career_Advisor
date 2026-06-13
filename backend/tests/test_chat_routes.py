from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.api import deps
from app.api.routes import chat as chat_route
from app.models.student_profile import StudentProfile
from main import app


class _FakeDB:
    def __init__(self, profile) -> None:
        self.profile = profile

    def get(self, model, row_id: int):
        if model is StudentProfile and row_id == self.profile.id:
            return self.profile
        return None

    def close(self) -> None:
        pass


def _override_user_context():
    return SimpleNamespace(id=10, email="student@example.com"), "user"


class _FakeCareerAnalysisService:
    def __init__(self, db) -> None:
        self.db = db

    def get_analysis_by_profile_id(
        self,
        profile_id: int,
        user_id: int,
        allow_admin: bool = False,
    ):
        del profile_id, user_id, allow_admin
        return SimpleNamespace(
            program_fit_summary={
                "recommended_program_name": "B.Tech CSE - AIML",
                "summary": "Strong fit with weekly practice.",
            },
            program_recommendations=[
                {
                    "program_name": "B.Tech CSE - AIML",
                    "priority_skills": ["Python", "Mathematics"],
                }
            ],
            expectation_reality_checks=[
                {
                    "expectation": "AI tools should become advanced work quickly.",
                    "reality": "First year needs Python and mathematics.",
                }
            ],
            career_recommendations=[{"role": "AI Product Engineer", "score": 86}],
            skill_gaps=[{"skill": "Python projects", "priority": "high"}],
            learning_roadmap=[{"stage": "Foundation", "topics": ["Python"]}],
        )


class _FakeLLMClient:
    calls: list[dict] = []

    def generate_chat_response(self, **kwargs):
        type(self).calls.append(kwargs)
        return "Review Python weekly and discuss AIML workload with a counselor."


@pytest.fixture(autouse=True)
def _clear_overrides():
    app.dependency_overrides.clear()
    _FakeLLMClient.calls.clear()
    yield
    app.dependency_overrides.clear()


def test_twelfth_chat_uses_counselor_context(monkeypatch: pytest.MonkeyPatch) -> None:
    profile = SimpleNamespace(
        id=1,
        user_id=10,
        user_type="twelfth_student",
        name="Aditi",
        degree="B.Tech",
        specialization="CSE AIML",
        twelfth_percentage=91.2,
        cgpa=0.0,
        subjects=["Mathematics", "Computer Science"],
        current_skills=["Python"],
        interests=["AI tools"],
        target_industry="Technology",
    )

    def _override_db():
        db = _FakeDB(profile)
        try:
            yield db
        finally:
            db.close()

    monkeypatch.setattr(
        chat_route,
        "CareerAnalysisService",
        _FakeCareerAnalysisService,
    )
    monkeypatch.setattr(chat_route, "LLMClient", _FakeLLMClient)
    app.dependency_overrides[deps.get_db] = _override_db
    app.dependency_overrides[deps.get_current_user_context] = _override_user_context

    response = TestClient(app).post(
        "/api/v1/chat/1",
        json={"message": "Should I choose AIML?"},
    )

    assert response.status_code == 200
    call = _FakeLLMClient.calls[0]
    assert "admissions counselor for a 12th student" in call["system_prompt"]
    assert "Program Fit Summary" in call["user_prompt"]
    assert "Expectation Reality Checks" in call["user_prompt"]


def test_college_chat_uses_placement_copilot_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile = SimpleNamespace(
        id=2,
        user_id=10,
        user_type="college_student",
        name="Rohan",
        degree="B.Tech",
        specialization="Computer Science",
        twelfth_percentage=84.5,
        cgpa=8.1,
        subjects=["DBMS"],
        current_skills=["Python", "SQL"],
        interests=["backend development"],
        target_industry="Software Engineering",
    )

    def _override_db():
        db = _FakeDB(profile)
        try:
            yield db
        finally:
            db.close()

    monkeypatch.setattr(
        chat_route,
        "CareerAnalysisService",
        _FakeCareerAnalysisService,
    )
    monkeypatch.setattr(chat_route, "LLMClient", _FakeLLMClient)
    app.dependency_overrides[deps.get_db] = _override_db
    app.dependency_overrides[deps.get_current_user_context] = _override_user_context

    response = TestClient(app).post(
        "/api/v1/chat/2",
        json={"message": "What should I improve for placements?"},
    )

    assert response.status_code == 200
    call = _FakeLLMClient.calls[0]
    assert "placement readiness copilot" in call["system_prompt"]
    assert "Skill Gaps" in call["user_prompt"]
    assert "Learning Roadmap" in call["user_prompt"]
