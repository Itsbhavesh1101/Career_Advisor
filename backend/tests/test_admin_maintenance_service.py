from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models.analysis_job import AnalysisJob
from app.models.admin_management import AdminManagedItem
from app.models.career_analysis import CareerAnalysis
from app.models.company_fit import CompanyFit
from app.models.employability_score import EmployabilityScore
from app.models.internship_readiness import InternshipReadiness
from app.models.placement_risk import PlacementRisk
from app.models.notification import UserNotification
from app.models.placement_opportunity import PlacementCompany, PlacementOpportunity
from app.models.psychometric_answer import PsychometricAnswer
from app.models.psychometric_question import PsychometricQuestion
from app.models.psychometric_result import PsychometricResult
from app.models.psychometric_session import PsychometricSession
from app.models.rag_document import RAGDocumentChunk, RAGDocumentSource
from app.models.resume_analysis import ResumeAnalysis
from app.models.role_gap_analysis import RoleGapAnalysis
from app.models.student_profile import StudentProfile
from app.models.user import User
from app.services.admin_maintenance_service import (
    AdminMaintenanceService,
    PRESENTATION_DEMO_SEED_CONFIRMATION,
    SMOKE_CLEANUP_CONFIRMATION,
)


@pytest.fixture()
def db_session() -> Session:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    tables = [
        User.__table__,
        AdminManagedItem.__table__,
        StudentProfile.__table__,
        CareerAnalysis.__table__,
        AnalysisJob.__table__,
        ResumeAnalysis.__table__,
        EmployabilityScore.__table__,
        PlacementRisk.__table__,
        CompanyFit.__table__,
        RoleGapAnalysis.__table__,
        InternshipReadiness.__table__,
        PsychometricSession.__table__,
        PsychometricQuestion.__table__,
        PsychometricAnswer.__table__,
        PsychometricResult.__table__,
        PlacementCompany.__table__,
        PlacementOpportunity.__table__,
        UserNotification.__table__,
        RAGDocumentSource.__table__,
        RAGDocumentChunk.__table__,
    ]
    Base.metadata.create_all(bind=engine, tables=tables)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine, tables=reversed(tables))


def _add_user(session: Session, *, user_id: int, email: str) -> None:
    session.add(
        User(
            id=user_id,
            email=email,
            password_hash="supabase-only",
            student_type="college_student",
        )
    )


def _add_profile(session: Session, *, profile_id: int, user_id: int) -> None:
    session.add(
        StudentProfile(
            id=profile_id,
            user_id=user_id,
            name=f"Student {profile_id}",
            twelfth_percentage=82,
            cgpa=8.2,
            degree="B.Tech",
            specialization="CSE",
            current_skills=["Python"],
            interests=["AI"],
            target_industry="Technology",
            projects=2,
            internships=1,
            certifications=1,
            user_type="college_student",
            created_at=datetime(2026, 5, 25, tzinfo=timezone.utc),
        )
    )


def _add_dependent_student_records(session: Session, *, user_id: int, profile_id: int) -> None:
    analysis = CareerAnalysis(
        id=profile_id + 100,
        student_profile_id=profile_id,
        career_recommendations=[],
        skill_gaps=[],
        learning_roadmap=[],
        salary_insights={},
        industry_trends=[],
    )
    session.add(analysis)
    session.add(
        AnalysisJob(
            id=f"job-{profile_id}",
            student_profile_id=profile_id,
            user_id=user_id,
            status="completed",
            progress=100,
            analysis_id=analysis.id,
        )
    )
    session.add(
        ResumeAnalysis(
            id=profile_id + 200,
            student_profile_id=profile_id,
            file_name="resume.pdf",
            extracted_skills=[],
            projects=[],
            experience=[],
            education=[],
            resume_score=70,
            missing_keywords=[],
            weak_sections=[],
            suggestions=[],
        )
    )
    session.add(
        EmployabilityScore(
            id=profile_id + 300,
            student_profile_id=profile_id,
            overall_score=72,
            academic_strength=70,
            technical_skills=72,
            industry_readiness=68,
            resume_quality=71,
        )
    )
    session.add(
        PlacementRisk(
            id=profile_id + 400,
            student_profile_id=profile_id,
            risk_level="medium",
            reasons=["Needs project depth"],
        )
    )
    session.add(CompanyFit(id=profile_id + 500, student_profile_id=profile_id, matches=[]))
    session.add(
        RoleGapAnalysis(id=profile_id + 600, student_profile_id=profile_id, role_gaps=[])
    )
    session.add(
        InternshipReadiness(
            id=profile_id + 700,
            student_profile_id=profile_id,
            readiness_score=65,
            readiness_level="building",
            action_plan=["Build one project"],
        )
    )
    quiz = PsychometricSession(
        id=f"quiz-{profile_id}",
        student_profile_id=profile_id,
        user_id=user_id,
        user_type="college_student",
        status="completed",
    )
    session.add(quiz)
    question = PsychometricQuestion(
        id=f"question-{profile_id}",
        session_id=quiz.id,
        position=1,
        question_text="Which activity fits you best?",
        options=[{"id": "a", "text": "Build"}],
    )
    session.add(question)
    session.flush()
    quiz.current_question_id = question.id
    session.add(
        PsychometricAnswer(
            id=f"answer-{profile_id}",
            session_id=quiz.id,
            question_id=question.id,
            selected_option_id="a",
            selected_option_text="Build",
            trait_effect={},
        )
    )
    session.add(
        PsychometricResult(
            id=profile_id + 800,
            session_id=quiz.id,
            student_profile_id=profile_id,
            user_id=user_id,
            trait_scores={},
            confidence=0.8,
            question_count=1,
            scoring_config_hash="hash",
        )
    )


def _add_rag_source(
    session: Session,
    *,
    source_id: int,
    title: str,
    tags: list[str],
) -> None:
    source = RAGDocumentSource(
        id=source_id,
        title=title,
        source_type="placement",
        status="active",
        tags=tags,
        program_ids=[],
        content_hash=f"hash-{source_id}",
        review_status="approved",
    )
    session.add(source)
    session.flush()
    session.add(
        RAGDocumentChunk(
            id=source_id + 1000,
            source_id=source.id,
            chunk_id=f"chunk-{source_id}",
            chunk_index=0,
            source_title=source.title,
            source_type=source.source_type,
            text="Knowledge text",
            tags=tags,
            program_ids=[],
        )
    )


def test_preview_counts_only_safe_smoke_users_and_rag_sources(
    db_session: Session,
) -> None:
    _add_user(db_session, user_id=1, email="admin@institution.edu")
    _add_user(db_session, user_id=2, email="sage-smoke-college@example.com")
    _add_user(db_session, user_id=3, email="real.student@gmail.com")
    _add_profile(db_session, profile_id=20, user_id=2)
    _add_dependent_student_records(db_session, user_id=2, profile_id=20)
    _add_profile(db_session, profile_id=30, user_id=3)
    _add_rag_source(
        db_session,
        source_id=10,
        title="Smoke browser upload",
        tags=["smoke"],
    )
    _add_rag_source(
        db_session,
        source_id=11,
        title="Approved placement guide",
        tags=["placement"],
    )
    db_session.commit()

    preview = AdminMaintenanceService(db_session).preview_smoke_data_cleanup()

    assert preview.users == 1
    assert preview.profiles == 1
    assert preview.analysis_jobs == 1
    assert preview.career_analyses == 1
    assert preview.resume_analyses == 1
    assert preview.quiz_sessions == 1
    assert preview.rag_sources == 1
    assert preview.rag_chunks == 1
    assert preview.sample_emails == ["sage-smoke-college@example.com"]
    assert preview.sample_rag_titles == ["Smoke browser upload"]


def test_cleanup_requires_confirmation_and_preserves_real_records(
    db_session: Session,
) -> None:
    _add_user(db_session, user_id=1, email="admin@institution.edu")
    _add_user(db_session, user_id=2, email="sage.live.student@example.com")
    _add_user(db_session, user_id=3, email="real.student@gmail.com")
    _add_profile(db_session, profile_id=20, user_id=2)
    _add_dependent_student_records(db_session, user_id=2, profile_id=20)
    _add_profile(db_session, profile_id=30, user_id=3)
    _add_rag_source(
        db_session,
        source_id=10,
        title="Demo upload for launch smoke",
        tags=["demo"],
    )
    _add_rag_source(
        db_session,
        source_id=11,
        title="Approved placement guide",
        tags=["placement"],
    )
    db_session.commit()

    service = AdminMaintenanceService(db_session)
    with pytest.raises(ValueError):
        service.cleanup_smoke_data(confirm="delete")

    result = service.cleanup_smoke_data(confirm=SMOKE_CLEANUP_CONFIRMATION)

    assert result.deleted is True
    assert result.users == 1
    assert db_session.scalar(select(func.count(User.id))) == 2
    assert db_session.get(User, 2) is None
    assert db_session.get(User, 3) is not None
    assert db_session.get(StudentProfile, 20) is None
    assert db_session.get(StudentProfile, 30) is not None
    assert db_session.get(RAGDocumentSource, 10) is None
    assert db_session.get(RAGDocumentSource, 11) is not None


def test_presentation_demo_seed_is_idempotent_and_realistic(
    db_session: Session,
) -> None:
    admin = User(
        id=1,
        email="admin@institution.edu",
        password_hash="supabase-only",
        student_type="college_student",
    )
    db_session.add(admin)
    db_session.commit()

    service = AdminMaintenanceService(db_session)
    with pytest.raises(ValueError):
        service.seed_presentation_demo_data(confirm="seed")

    first = service.seed_presentation_demo_data(
        confirm=PRESENTATION_DEMO_SEED_CONFIRMATION,
        created_by_user_id=admin.id,
    )
    second = service.seed_presentation_demo_data(
        confirm=PRESENTATION_DEMO_SEED_CONFIRMATION,
        created_by_user_id=admin.id,
    )
    preview = service.preview_presentation_demo_data()

    assert first.seeded is True
    assert second.seeded is False
    assert preview.users == 2
    assert preview.profiles == 2
    assert preview.admin_managed_items >= 6
    assert preview.placement_companies >= 1
    assert preview.placement_opportunities >= 1
    assert preview.notifications >= 2
    assert "demo.presentation.twelfth@example.com" in preview.sample_emails
    assert db_session.scalar(select(func.count(StudentProfile.id))) == 2
    assert db_session.scalar(select(func.count(AdminManagedItem.id))) >= 6
    assert db_session.scalar(select(func.count(PlacementOpportunity.id))) >= 1
