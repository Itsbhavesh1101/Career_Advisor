from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models.career_analysis import CareerAnalysis
from app.models.student_profile import StudentProfile
from app.models.user import User
from app.services.admission_intelligence_service import AdmissionIntelligenceService


@pytest.fixture()
def db_session() -> Session:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    tables = [User.__table__, StudentProfile.__table__, CareerAnalysis.__table__]
    Base.metadata.create_all(bind=engine, tables=tables)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine, tables=reversed(tables))


def _user(session: Session, user_id: int, student_type: str = "twelfth_student") -> User:
    user = User(
        id=user_id,
        email=f"user{user_id}@example.com",
        password_hash="hashed",
        student_type=student_type,
    )
    session.add(user)
    return user


def _profile(
    session: Session,
    *,
    profile_id: int,
    user_id: int,
    name: str,
    user_type: str = "twelfth_student",
    created_at: datetime | None = None,
    interests: list[str] | None = None,
    subjects: list[str] | None = None,
    current_skills: list[str] | None = None,
    programming_interest: str | None = None,
    math_strength: str | None = None,
) -> StudentProfile:
    profile = StudentProfile(
        id=profile_id,
        user_id=user_id,
        name=name,
        twelfth_percentage=82,
        cgpa=0,
        degree="Class 12",
        specialization="Science",
        current_skills=current_skills or [],
        interests=interests or [],
        target_industry="Technology",
        subjects=subjects or [],
        math_strength=math_strength,
        logical_reasoning=None,
        programming_interest=programming_interest,
        user_type=user_type,
        created_at=created_at or datetime(2026, 5, profile_id, tzinfo=timezone.utc),
    )
    session.add(profile)
    return profile


def _analysis(
    session: Session,
    *,
    analysis_id: int,
    profile_id: int,
    created_at: datetime,
    program_fit_summary: object | None,
    program_recommendations: object | None = None,
    expectation_reality_checks: object | None = None,
    first_year_roadmap: object | None = None,
    counselor_summary: object | None = None,
    rag_evidence: object | None = None,
) -> CareerAnalysis:
    analysis = CareerAnalysis(
        id=analysis_id,
        student_profile_id=profile_id,
        career_recommendations=[],
        skill_gaps=[],
        learning_roadmap=[],
        salary_insights={},
        industry_trends=[],
        program_fit_summary=program_fit_summary,
        program_recommendations=program_recommendations,
        expectation_reality_checks=expectation_reality_checks,
        first_year_roadmap=first_year_roadmap,
        counselor_summary=counselor_summary,
        rag_evidence=rag_evidence,
        created_at=created_at,
    )
    session.add(analysis)
    return analysis


def test_dashboard_filters_twelfth_profiles_and_computes_metrics(
    db_session: Session,
) -> None:
    _user(db_session, 1)
    _user(db_session, 2)
    _user(db_session, 3)
    _user(db_session, 4, student_type="college_student")
    _profile(
        db_session,
        profile_id=1,
        user_id=1,
        name="Ready Student",
        interests=["AI"],
        subjects=["Math"],
        created_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
    )
    _profile(
        db_session,
        profile_id=2,
        user_id=2,
        name="Needs Analysis",
        interests=["AI"],
        subjects=["Math"],
        math_strength="high",
        programming_interest="medium",
        created_at=datetime(2026, 5, 3, tzinfo=timezone.utc),
    )
    _profile(
        db_session,
        profile_id=3,
        user_id=3,
        name="Risk Student",
        interests=["Gaming"],
        created_at=datetime(2026, 5, 4, tzinfo=timezone.utc),
    )
    _profile(
        db_session,
        profile_id=4,
        user_id=4,
        name="College Student",
        user_type="college_student",
        interests=["AI", "Data"],
        created_at=datetime(2026, 5, 5, tzinfo=timezone.utc),
    )
    same_time = datetime(2026, 5, 6, 12, tzinfo=timezone.utc)
    _analysis(
        db_session,
        analysis_id=10,
        profile_id=1,
        created_at=same_time,
        program_fit_summary={
            "recommended_program_name": "Old Program",
            "confidence": 55,
        },
        rag_evidence=[],
    )
    _analysis(
        db_session,
        analysis_id=11,
        profile_id=1,
        created_at=same_time,
        program_fit_summary={
            "recommended_program_name": "B.Tech CSE - AIML",
            "confidence": 82,
        },
        rag_evidence=[{"source_title": "AIML Handbook"}],
    )
    _analysis(
        db_session,
        analysis_id=12,
        profile_id=3,
        created_at=datetime(2026, 5, 6, tzinfo=timezone.utc),
        program_fit_summary={
            "recommended_program_name": None,
            "confidence": 58,
        },
        expectation_reality_checks=[
            {"student_expectation": "Only coding", "reality_check": "Includes math"}
        ],
        rag_evidence=[],
    )
    _analysis(
        db_session,
        analysis_id=13,
        profile_id=4,
        created_at=datetime(2026, 5, 7, tzinfo=timezone.utc),
        program_fit_summary={
            "recommended_program_name": "Ignored Program",
            "confidence": 95,
        },
        rag_evidence=[{"source_title": "Ignored Evidence"}],
    )
    db_session.commit()

    dashboard = AdmissionIntelligenceService(db_session).get_dashboard(limit=10)

    assert dashboard.metrics.total_twelfth_profiles == 3
    assert dashboard.metrics.analyzed_profiles == 2
    assert dashboard.metrics.needs_analysis == 1
    assert dashboard.metrics.high_intent == 2
    assert dashboard.metrics.wrong_branch_risk == 2
    assert dashboard.metrics.ready_for_counseling == 1
    assert [lead.profile_id for lead in dashboard.leads] == [3, 2, 1]
    assert dashboard.leads[0].priority == "urgent"
    assert dashboard.leads[0].status == "wrong_branch_risk"
    assert dashboard.leads[1].status == "needs_analysis"
    assert dashboard.leads[2].recommended_program == "B.Tech CSE - AIML"
    assert dashboard.leads[2].confidence == 82


def test_counselor_brief_draws_from_existing_analysis_fields(
    db_session: Session,
) -> None:
    _user(db_session, 10)
    _profile(
        db_session,
        profile_id=10,
        user_id=10,
        name="Brief Student",
        interests=["AI", "Robotics"],
        subjects=["Math"],
    )
    _analysis(
        db_session,
        analysis_id=20,
        profile_id=10,
        created_at=datetime(2026, 5, 8, tzinfo=timezone.utc),
        program_fit_summary={
            "recommended_program_name": "B.Tech CSE - AIML",
            "confidence": 91,
        },
        program_recommendations=[
            {
                "program_name": "B.Tech CSE - AIML",
                "reasons": ["Strong math base", "AI interest"],
            }
        ],
        expectation_reality_checks=[
            {
                "expectation": "Only AI tools",
                "reality": "Includes programming foundations",
                "counselor_note": "Set expectations early.",
            }
        ],
        first_year_roadmap=[
            {
                "term": "Semester 1",
                "focus": ["Practice Python", "Revise calculus"],
                "evidence_to_build": ["Mini project"],
            },
            {"action": "Join coding club"},
        ],
        counselor_summary={
            "best_fit": "AIML with foundation bridge",
            "talking_points": ["Discuss weekly lab load"],
            "follow_up_questions": ["Can you commit to math practice?"],
        },
        rag_evidence=[
            {"source_title": "AIML Curriculum"},
            {"title": "First Year Guide"},
        ],
    )
    db_session.commit()

    [lead] = AdmissionIntelligenceService(db_session).get_dashboard().leads

    assert lead.counselor_brief.best_fit == "AIML with foundation bridge"
    assert lead.counselor_brief.confidence == 91
    assert lead.counselor_brief.talking_points == ["Discuss weekly lab load"]
    assert lead.counselor_brief.expectation_checks == [
        "Only AI tools -> Includes programming foundations"
    ]
    assert lead.counselor_brief.first_year_actions == [
        "Practice Python",
        "Revise calculus",
        "Mini project",
        "Join coding club",
    ]
    assert lead.counselor_brief.evidence_titles == [
        "AIML Curriculum",
        "First Year Guide",
    ]
    assert lead.counselor_brief.follow_up_questions == [
        "Can you commit to math practice?"
    ]


def test_dashboard_is_defensive_against_malformed_analysis_json(
    db_session: Session,
) -> None:
    _user(db_session, 30)
    _profile(
        db_session,
        profile_id=30,
        user_id=30,
        name="Malformed Student",
        interests=["AI"],
        subjects=["Physics"],
    )
    _analysis(
        db_session,
        analysis_id=30,
        profile_id=30,
        created_at=datetime(2026, 5, 9, tzinfo=timezone.utc),
        program_fit_summary="not-a-dict",
        program_recommendations="not-a-list",
        expectation_reality_checks={"bad": "shape"},
        first_year_roadmap="bad",
        counselor_summary="bad",
        rag_evidence="bad",
    )
    db_session.commit()

    [lead] = AdmissionIntelligenceService(db_session).get_dashboard().leads

    assert lead.recommended_program is None
    assert lead.confidence is None
    assert lead.priority == "urgent"
    assert "unclear_fit" in lead.lost_reason_signals
    assert "weak_evidence" in lead.lost_reason_signals
    assert lead.counselor_brief.talking_points
