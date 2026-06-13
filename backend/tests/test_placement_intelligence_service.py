from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models.career_analysis import CareerAnalysis
from app.models.company_fit import CompanyFit
from app.models.employability_score import EmployabilityScore
from app.models.internship_readiness import InternshipReadiness
from app.models.placement_risk import PlacementRisk
from app.models.role_gap_analysis import RoleGapAnalysis
from app.models.student_profile import StudentProfile
from app.models.user import User
from app.services.placement_intelligence_service import (
    PlacementIntelligenceService,
    _top_company,
)


def _record_time(record_id: int) -> datetime:
    return datetime(2026, 5, min(record_id, 28), tzinfo=timezone.utc)


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
        EmployabilityScore.__table__,
        PlacementRisk.__table__,
        CompanyFit.__table__,
        RoleGapAnalysis.__table__,
        CareerAnalysis.__table__,
        InternshipReadiness.__table__,
    ]
    Base.metadata.create_all(bind=engine, tables=tables)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine, tables=reversed(tables))


def _user(session: Session, user_id: int) -> User:
    user = User(
        id=user_id,
        email=f"user{user_id}@example.com",
        password_hash="hashed",
        student_type="college_student",
    )
    session.add(user)
    return user


def _profile(
    session: Session,
    *,
    profile_id: int,
    user_type: str | None = "college_student",
    name: str | None = None,
    projects: int = 0,
    internships: int = 0,
    certifications: int = 0,
    created_at: datetime | None = None,
) -> StudentProfile:
    _user(session, profile_id)
    profile = StudentProfile(
        id=profile_id,
        user_id=profile_id,
        name=name or f"Student {profile_id}",
        twelfth_percentage=82,
        cgpa=8.1,
        degree="B.Tech",
        specialization="CSE",
        current_skills=["Python"],
        interests=["AI"],
        target_industry="Technology",
        projects=projects,
        internships=internships,
        certifications=certifications,
        user_type=user_type,
        created_at=created_at or datetime(2026, 5, profile_id, tzinfo=timezone.utc),
    )
    session.add(profile)
    return profile


def _employability(
    session: Session,
    *,
    record_id: int,
    profile_id: int,
    score: int,
    resume_quality: int = 70,
    created_at: datetime | None = None,
) -> EmployabilityScore:
    record = EmployabilityScore(
        id=record_id,
        student_profile_id=profile_id,
        overall_score=score,
        academic_strength=70,
        technical_skills=70,
        industry_readiness=70,
        resume_quality=resume_quality,
        created_at=created_at or _record_time(record_id),
    )
    session.add(record)
    return record


def _risk(
    session: Session,
    *,
    record_id: int,
    profile_id: int,
    level: str,
    reasons: list[str] | None = None,
    created_at: datetime | None = None,
) -> PlacementRisk:
    record = PlacementRisk(
        id=record_id,
        student_profile_id=profile_id,
        risk_level=level,
        reasons=reasons or [],
        created_at=created_at or _record_time(record_id),
    )
    session.add(record)
    return record


def _company_fit(
    session: Session,
    *,
    record_id: int,
    profile_id: int,
    matches: list[dict],
    created_at: datetime | None = None,
) -> CompanyFit:
    record = CompanyFit(
        id=record_id,
        student_profile_id=profile_id,
        matches=matches,
        created_at=created_at or _record_time(record_id),
    )
    session.add(record)
    return record


def _role_gap(
    session: Session,
    *,
    record_id: int,
    profile_id: int,
    gaps: list[dict],
    created_at: datetime | None = None,
) -> RoleGapAnalysis:
    record = RoleGapAnalysis(
        id=record_id,
        student_profile_id=profile_id,
        role_gaps=gaps,
        created_at=created_at or _record_time(record_id),
    )
    session.add(record)
    return record


def _career_analysis(
    session: Session,
    *,
    record_id: int,
    profile_id: int,
    skill_gaps: list[dict] | None = None,
    career_recommendations: list[dict] | None = None,
    created_at: datetime | None = None,
) -> CareerAnalysis:
    record = CareerAnalysis(
        id=record_id,
        student_profile_id=profile_id,
        career_recommendations=career_recommendations or [],
        skill_gaps=skill_gaps or [],
        learning_roadmap=[],
        salary_insights={},
        industry_trends=[],
        created_at=created_at or _record_time(record_id),
    )
    session.add(record)
    return record


def _internship(
    session: Session,
    *,
    record_id: int,
    profile_id: int,
    score: int,
    level: str = "Ready",
    actions: list[str] | None = None,
    created_at: datetime | None = None,
) -> InternshipReadiness:
    record = InternshipReadiness(
        id=record_id,
        student_profile_id=profile_id,
        readiness_score=score,
        readiness_level=level,
        action_plan=actions or [],
        created_at=created_at or _record_time(record_id),
    )
    session.add(record)
    return record


def _seed_ready_student(session: Session, profile_id: int, *, score: int = 82) -> None:
    _profile(
        session,
        profile_id=profile_id,
        projects=3,
        internships=1,
        certifications=2,
    )
    _employability(session, record_id=profile_id * 10 + 1, profile_id=profile_id, score=score)
    _risk(session, record_id=profile_id * 10 + 2, profile_id=profile_id, level="Low")
    _company_fit(
        session,
        record_id=profile_id * 10 + 3,
        profile_id=profile_id,
        matches=[{"company": "Infosys", "score": 80, "missing_skills": ["SQL"]}],
    )
    _role_gap(session, record_id=profile_id * 10 + 4, profile_id=profile_id, gaps=[])
    _career_analysis(session, record_id=profile_id * 10 + 5, profile_id=profile_id)
    _internship(session, record_id=profile_id * 10 + 6, profile_id=profile_id, score=80)


def test_dashboard_metrics_count_only_college_student_profiles(
    db_session: Session,
) -> None:
    _seed_ready_student(db_session, 1)
    _seed_ready_student(db_session, 2)
    _profile(db_session, profile_id=3, user_type=None, projects=1)
    _employability(db_session, record_id=31, profile_id=3, score=42, resume_quality=20)
    _risk(db_session, record_id=32, profile_id=3, level="High")
    _company_fit(db_session, record_id=33, profile_id=3, matches=[])
    _role_gap(db_session, record_id=34, profile_id=3, gaps=[])
    _career_analysis(db_session, record_id=35, profile_id=3)
    _internship(db_session, record_id=36, profile_id=3, score=20)
    _profile(db_session, profile_id=4, user_type="twelfth_student", projects=5)
    _employability(db_session, record_id=41, profile_id=4, score=95)
    _risk(db_session, record_id=42, profile_id=4, level="Low")
    _internship(db_session, record_id=46, profile_id=4, score=95)
    db_session.commit()

    dashboard = PlacementIntelligenceService(db_session).get_dashboard(limit=10)

    assert dashboard.metrics.total_college_profiles == 3
    assert dashboard.metrics.placement_ready == 2
    assert dashboard.metrics.needs_training == 0
    assert dashboard.metrics.high_risk == 1
    assert dashboard.metrics.company_ready == 2
    assert dashboard.metrics.evidence_complete == 2
    assert dashboard.metrics.average_employability == 69


def test_latest_records_selected_by_newest_created_at_then_highest_id(
    db_session: Session,
) -> None:
    _profile(db_session, profile_id=1)
    same_time = datetime(2026, 5, 2, 12, tzinfo=timezone.utc)
    _employability(
        db_session,
        record_id=1,
        profile_id=1,
        score=45,
        created_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
    )
    _employability(db_session, record_id=2, profile_id=1, score=70, created_at=same_time)
    _employability(db_session, record_id=3, profile_id=1, score=88, created_at=same_time)
    db_session.commit()

    latest = PlacementIntelligenceService(db_session)._latest_records(
        EmployabilityScore, [1]
    )

    assert latest[1].id == 3
    assert latest[1].overall_score == 88


def test_evidence_ledger_combines_student_activity_and_analysis_gaps(
    db_session: Session,
) -> None:
    profile = _profile(
        db_session,
        profile_id=1,
        projects=2,
        internships=1,
        certifications=1,
    )
    employability = _employability(
        db_session,
        record_id=1,
        profile_id=1,
        score=68,
        resume_quality=80,
    )
    role_gap = _role_gap(
        db_session,
        record_id=2,
        profile_id=1,
        gaps=[
            {"role": "Data Analyst", "missing_skills": ["SQL", "Tableau"]},
            {"role": "ML Engineer", "skill_gaps": ["MLOps"]},
        ],
    )
    career = _career_analysis(
        db_session,
        record_id=3,
        profile_id=1,
        skill_gaps=[{"skill": "Communication"}],
        career_recommendations=[{"role": "Data Analyst"}],
    )
    internship = _internship(db_session, record_id=4, profile_id=1, score=60)
    db_session.commit()

    ledger = PlacementIntelligenceService(db_session)._evidence_ledger(
        profile, employability, role_gap, career, internship
    )

    assert ledger.evidence_score == 68
    assert ledger.project_count == 2
    assert ledger.internship_count == 1
    assert ledger.certification_count == 1
    assert ledger.resume_quality == 80
    assert ledger.internship_readiness == 60
    assert "Project portfolio" in ledger.strengths
    assert "SQL" in ledger.gaps
    assert "Tableau" in ledger.gaps
    assert "MLOps" in ledger.gaps
    assert "Communication" in ledger.gaps


def test_company_readiness_radar_aggregates_latest_company_fit_matches(
    db_session: Session,
) -> None:
    _profile(db_session, profile_id=1)
    _profile(db_session, profile_id=2)
    _profile(db_session, profile_id=3)
    older = datetime(2026, 5, 1, tzinfo=timezone.utc)
    newer = datetime(2026, 5, 2, tzinfo=timezone.utc)
    _company_fit(
        db_session,
        record_id=1,
        profile_id=1,
        matches=[{"company": "Infosys", "score": 50}],
        created_at=older,
    )
    _company_fit(
        db_session,
        record_id=2,
        profile_id=1,
        matches=[{"company": "Infosys", "score": 82, "missing_skills": ["SQL"]}],
        created_at=newer,
    )
    _company_fit(
        db_session,
        record_id=3,
        profile_id=2,
        matches=[{"company": "Infosys", "score": 68, "missing_skills": ["Cloud"]}],
    )
    _company_fit(
        db_session,
        record_id=4,
        profile_id=3,
        matches=[{"company": "Infosys", "score": 52, "missing_skills": ["SQL"]}],
    )
    db_session.commit()
    service = PlacementIntelligenceService(db_session)
    company_fits = service._latest_records(CompanyFit, [1, 2, 3])

    [radar] = service._company_radar([], company_fits, {}, {})

    assert radar.company == "Infosys"
    assert radar.average_score == 67
    assert radar.ready_count == 1
    assert radar.watch_count == 1
    assert radar.blocked_count == 1
    assert radar.missing_skills == ["SQL", "Cloud"]


def test_company_match_normalization_keeps_zero_score_and_employer_alias(
    db_session: Session,
) -> None:
    _profile(db_session, profile_id=1)
    company_fit = _company_fit(
        db_session,
        record_id=1,
        profile_id=1,
        matches=[
            {
                "employer": "TCS",
                "score": 0,
                "fit_score": 92,
                "missing_skills": ["Java"],
            }
        ],
    )
    db_session.commit()
    service = PlacementIntelligenceService(db_session)
    company_fits = service._latest_records(CompanyFit, [1])

    [radar] = service._company_radar([], company_fits, {}, {})
    top_company, top_score = _top_company(company_fit)

    assert radar.company == "TCS"
    assert radar.average_score == 0
    assert radar.blocked_count == 1
    assert top_company == "TCS"
    assert top_score == 0


def test_war_room_sorts_urgent_and_high_before_medium_and_low(
    db_session: Session,
) -> None:
    _seed_ready_student(db_session, 1, score=92)
    _seed_ready_student(db_session, 2, score=72)
    _seed_ready_student(db_session, 3, score=64)
    _seed_ready_student(db_session, 4, score=40)
    _risk(db_session, record_id=999, profile_id=4, level="High")
    _profile(
        db_session,
        profile_id=5,
        projects=2,
        internships=0,
        certifications=1,
        created_at=datetime(2026, 5, 6, tzinfo=timezone.utc),
    )
    _employability(db_session, record_id=51, profile_id=5, score=61, resume_quality=55)
    _risk(db_session, record_id=52, profile_id=5, level="Medium")
    _company_fit(db_session, record_id=53, profile_id=5, matches=[])
    _role_gap(
        db_session,
        record_id=54,
        profile_id=5,
        gaps=[{"missing_skills": ["Aptitude"]}],
    )
    _career_analysis(db_session, record_id=55, profile_id=5)
    _internship(db_session, record_id=56, profile_id=5, score=40)
    db_session.commit()

    dashboard = PlacementIntelligenceService(db_session).get_dashboard(limit=10)

    assert [student.priority for student in dashboard.students] == [
        "urgent",
        "high",
        "medium",
        "low",
        "low",
    ]
    assert [student.profile_id for student in dashboard.students] == [4, 5, 3, 2, 1]


def test_training_roi_aggregates_missing_skills_from_role_and_career_gaps(
    db_session: Session,
) -> None:
    _profile(db_session, profile_id=1)
    _profile(db_session, profile_id=2)
    _role_gap(
        db_session,
        record_id=1,
        profile_id=1,
        gaps=[{"missing_skills": ["SQL", "Cloud"]}],
    )
    _role_gap(
        db_session,
        record_id=2,
        profile_id=2,
        gaps=[{"skill_gaps": ["SQL"]}],
    )
    _career_analysis(
        db_session,
        record_id=3,
        profile_id=1,
        skill_gaps=[{"skill": "Communication"}, {"name": "SQL"}],
    )
    db_session.commit()
    service = PlacementIntelligenceService(db_session)
    role_gaps = service._latest_records(RoleGapAnalysis, [1, 2])
    career_analyses = service._latest_records(CareerAnalysis, [1, 2])

    roi = service._training_roi(role_gaps, career_analyses)

    assert [(item.skill, item.affected_students) for item in roi[:3]] == [
        ("SQL", 2),
        ("Cloud", 1),
        ("Communication", 1),
    ]
    assert roi[0].expected_readiness_lift == 14
    assert roi[0].priority == "high"


def test_faculty_notes_include_focus_areas_and_action_text_for_high_risk_students(
    db_session: Session,
) -> None:
    _profile(db_session, profile_id=1, name="Risky Student", projects=0)
    employability = _employability(
        db_session,
        record_id=1,
        profile_id=1,
        score=38,
        resume_quality=25,
    )
    risk = _risk(
        db_session,
        record_id=2,
        profile_id=1,
        level="High",
        reasons=["Low employability", "Weak resume"],
    )
    company_fit = _company_fit(
        db_session,
        record_id=3,
        profile_id=1,
        matches=[{"company": "TCS", "score": 58}],
    )
    role_gap = _role_gap(
        db_session,
        record_id=4,
        profile_id=1,
        gaps=[{"missing_skills": ["SQL"]}],
    )
    career = _career_analysis(
        db_session,
        record_id=5,
        profile_id=1,
        skill_gaps=[{"skill": "Communication"}],
    )
    internship = _internship(db_session, record_id=6, profile_id=1, score=20)
    db_session.commit()
    service = PlacementIntelligenceService(db_session)
    signal = service._student_signal(
        db_session.get(StudentProfile, 1),
        employability,
        risk,
        company_fit,
        role_gap,
        career,
        internship,
    )

    [note] = service._faculty_notes([signal])

    assert note.profile_id == 1
    assert note.escalation_level == "urgent"
    assert "SQL" in note.focus_areas
    assert "Communication" in note.focus_areas
    assert "Risky Student needs urgent placement intervention" in note.note
