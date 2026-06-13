from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.api.routes.auth import RegisterRequest
from app.services.ai_engine import CareerAIEngine


def test_register_request_defaults_student_type() -> None:
    payload = RegisterRequest(email="student@example.com", password="secret123")
    assert payload.student_type == "college_student"


def test_register_request_accepts_twelfth_student_type() -> None:
    payload = RegisterRequest(
        email="twelfth@example.com",
        password="secret123",
        student_type="twelfth_student",
    )
    assert payload.student_type == "twelfth_student"


def test_register_request_rejects_unknown_student_type() -> None:
    try:
        RegisterRequest(
            email="unknown@example.com",
            password="secret123",
            student_type="school_student",
        )
    except ValidationError:
        pass
    else:
        raise AssertionError("Expected validation error for invalid student_type")


def test_salary_generation_requires_llm() -> None:
    profile = SimpleNamespace(
        id=1,
        user_id=1,
        specialization="AI and Machine Learning",
        current_skills=["Python", "SQL"],
    )
    engine = CareerAIEngine(use_llm=False)
    with pytest.raises(RuntimeError, match="LLM-only mode"):
        engine.generate_salary_insights(profile)  # type: ignore[arg-type]
