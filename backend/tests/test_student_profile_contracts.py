import pytest
from pydantic import ValidationError

from app.schemas.student_profile import StudentProfileCreate


def test_twelfth_profile_requires_branch_decision_signals() -> None:
    with pytest.raises(ValidationError) as exc:
        StudentProfileCreate(
            name="Aarav Sharma",
            twelfth_percentage=84.5,
            cgpa=None,
            degree=None,
            specialization=None,
            current_skills=[],
            interests=[],
            target_industry="",
            projects=0,
            internships=0,
            certifications=0,
            user_type="twelfth_student",
        )

    message = str(exc.value)
    assert "At least one interest is required for 12th student branch guidance" in message
    assert "Subjects are required for 12th student branch guidance" in message
    assert "Math strength is required for 12th student branch guidance" in message
    assert "Logical reasoning strength is required for 12th student branch guidance" in message


def test_college_profile_requires_college_readiness_fields() -> None:
    with pytest.raises(ValidationError) as exc:
        StudentProfileCreate(
            name="Priya Verma",
            twelfth_percentage=None,
            cgpa=None,
            degree="",
            specialization="",
            current_skills=[],
            interests=["AI"],
            target_industry="",
            projects=0,
            internships=0,
            certifications=0,
            user_type="college_student",
        )

    message = str(exc.value)
    assert "CGPA is required for college placement guidance" in message
    assert "Degree is required for college placement guidance" in message
    assert "Specialization is required for college placement guidance" in message
    assert "Target industry is required for college placement guidance" in message


def test_valid_twelfth_profile_may_omit_college_only_fields() -> None:
    profile = StudentProfileCreate(
        name="Riya Patel",
        twelfth_percentage=88,
        cgpa=None,
        degree=None,
        specialization=None,
        current_skills=[],
        interests=["AI", "Robotics"],
        target_industry="Product engineering",
        projects=0,
        internships=0,
        certifications=0,
        subjects=["Physics", "Maths"],
        math_strength="strong",
        logical_reasoning="moderate",
        programming_interest="curious",
        user_type="twelfth_student",
    )

    assert profile.user_type == "twelfth_student"
    assert profile.cgpa is None
    assert profile.degree is None
