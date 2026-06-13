from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models.analysis_job import AnalysisJob
from app.models.career_analysis import CareerAnalysis
from app.models.psychometric_result import PsychometricResult
from app.models.psychometric_session import PsychometricSession
from app.models.resume_analysis import ResumeAnalysis
from app.models.student_profile import StudentProfile
from app.models.user import User
from app.services.student_dashboard_service import StudentDashboardService


@pytest.fixture()
def db_session() -> Session:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    tables = [
        User.__table__,
        StudentProfile.__table__,
        CareerAnalysis.__table__,
        ResumeAnalysis.__table__,
        PsychometricSession.__table__,
        PsychometricResult.__table__,
        AnalysisJob.__table__,
    ]
    Base.metadata.create_all(bind=engine, tables=tables)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine, tables=reversed(tables))


def _user(session: Session) -> User:
    user = User(
        id=1,
        email="student@example.com",
        password_hash="hashed",
        student_type="college_student",
    )
    session.add(user)
    return user


def _profile(session: Session, *, user_type: str = "college_student") -> StudentProfile:
    profile = StudentProfile(
        id=10,
        user_id=1,
        name="Launch Student",
        twelfth_percentage=88,
        cgpa=8.1 if user_type == "college_student" else 0,
        degree="B.Tech" if user_type == "college_student" else "Class 12",
        specialization="CSE" if user_type == "college_student" else "Science",
        current_skills=["Python"] if user_type == "college_student" else [],
        interests=["AI"],
        target_industry="Technology",
        projects=2,
        internships=0,
        certifications=1,
        subjects=["Maths", "Physics"] if user_type == "twelfth_student" else [],
        math_strength="high" if user_type == "twelfth_student" else None,
        logical_reasoning="medium" if user_type == "twelfth_student" else None,
        programming_interest="high" if user_type == "twelfth_student" else None,
        user_type=user_type,
        created_at=datetime(2026, 5, 20, tzinfo=timezone.utc),
    )
    session.add(profile)
    return profile


def test_student_dashboard_summary_surfaces_next_actions(db_session: Session) -> None:
    _user(db_session)
    _profile(db_session)
    db_session.commit()

    summary = StudentDashboardService(db_session).get_summary(10, 1)

    assert summary.profile_id == 10
    assert summary.student_type == "college_student"
    assert summary.profile_completeness < 100
    assert summary.analysis_status == "missing"
    assert summary.quiz_status == "not_started"
    assert summary.resume_status == "missing"
    assert summary.readiness_summary.startswith("Complete the readiness")
    assert summary.next_actions[:3] == [
        "Complete the adaptive quiz.",
        "Run career and placement analysis.",
        "Add a resume for evidence-backed guidance.",
    ]


def test_student_dashboard_summary_for_twelfth_uses_admission_language(
    db_session: Session,
) -> None:
    _user(db_session)
    _profile(db_session, user_type="twelfth_student")
    analysis = CareerAnalysis(
        id=20,
        student_profile_id=10,
        career_recommendations=[],
        skill_gaps=[],
        learning_roadmap=[],
        salary_insights={},
        industry_trends=[],
        program_fit_summary={"confidence": 87},
        program_recommendations=[{"program_name": "B.Tech CSE - AIML"}],
        rag_evidence=[{"source_title": "Program Guide"}],
        created_at=datetime(2026, 5, 21, tzinfo=timezone.utc),
    )
    db_session.add(analysis)
    db_session.commit()

    summary = StudentDashboardService(db_session).get_summary(10, 1)

    assert summary.student_type == "twelfth_student"
    assert summary.analysis_status == "ready"
    assert summary.resume_status == "not_applicable"
    assert "admission counseling" in summary.readiness_summary.lower()
    assert "Review your program-fit recommendation." in summary.next_actions
