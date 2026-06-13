from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models.admin_management import AdminManagedItem
from app.models.career_analysis import CareerAnalysis
from app.models.student_profile import StudentProfile
from app.models.user import User
from app.schemas.admin_management import AdminManagedItemCreate, AdminManagedItemUpdate
from app.services.admin_management_service import AdminManagementService
from app.services.institution_config_service import InstitutionConfigService
from app.services.training_recommendation_service import TrainingRecommendationService


def _db_session() -> Session:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(
        bind=engine,
        tables=[
            User.__table__,
            StudentProfile.__table__,
            CareerAnalysis.__table__,
            AdminManagedItem.__table__,
        ],
    )
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def test_admin_management_crud_lifecycle() -> None:
    db = _db_session()
    try:
        service = AdminManagementService(db)
        created = service.create_item(
            AdminManagedItemCreate(
                item_type="placement_company",
                slug="tcs-digital",
                title="TCS Digital",
                summary="Digital engineering hiring track",
                payload={"target_skills": ["Java", "SQL"]},
            ),
            user_id=1,
        )

        assert created.id is not None
        assert created.status == "active"
        assert service.list_items(item_type="placement_company").total == 1

        updated = service.update_item(
            created.id,
            AdminManagedItemUpdate(
                title="TCS Digital NQT",
                payload={"target_skills": ["Java", "SQL", "Aptitude"]},
            ),
            user_id=2,
        )

        assert updated.title == "TCS Digital NQT"
        assert updated.updated_by_user_id == 2
        assert updated.payload["target_skills"] == ["Java", "SQL", "Aptitude"]

        archived = service.archive_item(created.id, user_id=3)

        assert archived.status == "inactive"
        assert archived.updated_by_user_id == 3
        assert service.list_items(item_type="placement_company", status="active").total == 0
    finally:
        db.close()


def test_managed_training_programs_feed_training_recommendations() -> None:
    db = _db_session()
    try:
        AdminManagementService(db).create_item(
            AdminManagedItemCreate(
                item_type="training_program",
                slug="python-placement-bootcamp",
                title="Python Placement Bootcamp",
                summary="Four-week Python plan for placement readiness",
                payload={"focus_skills": ["Python", "SQL"]},
            ),
            user_id=1,
        )

        recommendations = TrainingRecommendationService(db).get_recommendations()

        assert recommendations.programs[0].title == "Python Placement Bootcamp"
        assert recommendations.programs[0].focus_skills == ["Python", "SQL"]
        assert recommendations.programs[0].description == (
            "Four-week Python plan for placement readiness"
        )
    finally:
        db.close()


def test_managed_programs_extend_institution_catalog() -> None:
    db = _db_session()
    try:
        service = AdminManagementService(db)
        service.create_item(
            AdminManagedItemCreate(
                item_type="program",
                slug="btech-data-science",
                title="B.Tech Data Science",
                summary="Data-focused undergraduate program",
                payload={
                    "school_id": "school-engineering",
                    "school_name": "School of Engineering",
                    "campus": "Main Campus",
                    "degree_level": "undergraduate",
                    "duration_years": 4,
                    "priority_skills": ["Python", "Statistics"],
                    "career_paths": ["Data Analyst", "ML Engineer"],
                    "admission_fit_signals": ["Maths strength"],
                    "reality_checks": ["Requires continuous coding practice"],
                },
            ),
            user_id=1,
        )

        catalog = InstitutionConfigService(db).get_catalog()
        programs = [
            program
            for school in catalog.schools
            for program in school.programs
            if program.program_id == "btech-data-science"
        ]

        assert len(programs) == 1
        assert programs[0].program_name == "B.Tech Data Science"
        assert programs[0].priority_skills == ["Python", "Statistics"]
    finally:
        db.close()


def test_admin_management_accepts_institution_content_categories() -> None:
    db = _db_session()
    try:
        service = AdminManagementService(db)

        for item_type, slug, title, payload in [
            (
                "institution_policy",
                "attendance-placement-policy",
                "Attendance policy for placement drives",
                {
                    "policy_area": "placement",
                    "applies_to": ["college_student"],
                    "rules": ["Minimum attendance is required for drive eligibility."],
                    "owner": "Placement Cell",
                },
            ),
            (
                "knowledge_template",
                "program-faq-template",
                "Program FAQ knowledge template",
                {
                    "source_type": "faq",
                    "required_sections": ["eligibility", "fees", "career outcomes"],
                    "review_cadence_days": 90,
                },
            ),
            (
                "institution_content",
                "homepage-counselor-note",
                "Counselor homepage note",
                {
                    "content_area": "homepage",
                    "audience": "all",
                    "headline": "Personalized guidance with institutional context",
                    "body": "Students receive recommendations connected to their profile.",
                },
            ),
        ]:
            service.create_item(
                AdminManagedItemCreate(
                    item_type=item_type,
                    slug=slug,
                    title=title,
                    payload=payload,
                ),
                user_id=1,
            )

        policies = service.list_items(item_type="institution_policy")
        templates = service.list_items(item_type="knowledge_template")
        content = service.list_items(item_type="institution_content")

        assert policies.total == 1
        assert policies.items[0].payload["owner"] == "Placement Cell"
        assert templates.total == 1
        assert templates.items[0].payload["review_cadence_days"] == 90
        assert content.total == 1
        assert content.items[0].payload["audience"] == "all"
    finally:
        db.close()


def test_managed_internship_opportunities_feed_internship_catalog() -> None:
    db = _db_session()
    try:
        service = AdminManagementService(db)
        service.create_item(
            AdminManagedItemCreate(
                item_type="internship_opportunity",
                slug="ai-research-internship",
                title="AI Research Internship",
                summary="Research internship for students with Python project evidence.",
                payload={
                    "company": "Institution Innovation Lab",
                    "location": "Bhopal",
                    "duration": "8 weeks",
                    "skills": ["Python", "ML"],
                    "eligibility": ["Second year and above", "One ML project"],
                    "apply_url": "https://example.edu/internships/ai",
                    "deadline": "2026-07-01",
                },
            ),
            user_id=1,
        )
        inactive = service.create_item(
            AdminManagedItemCreate(
                item_type="internship_opportunity",
                slug="archived-internship",
                title="Archived Internship",
                status="inactive",
                payload={"company": "Old Partner"},
            ),
            user_id=1,
        )

        catalog = service.list_active_internship_opportunities()

        assert [item.slug for item in catalog.items] == ["ai-research-internship"]
        assert catalog.total == 1
        assert catalog.items[0].company == "Institution Innovation Lab"
        assert catalog.items[0].skills == ["Python", "ML"]
        assert inactive.status == "inactive"
    finally:
        db.close()
