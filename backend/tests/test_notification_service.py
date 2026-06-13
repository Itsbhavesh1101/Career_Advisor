from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models.notification import UserNotification
from app.models.placement_opportunity import (
    PlacementActivityEvent,
    PlacementApplication,
    PlacementCompany,
    PlacementInterviewRound,
    PlacementOpportunity,
)
from app.models.student_profile import StudentProfile
from app.models.user import User
from app.schemas.notification import PlacementAnnouncementCreate
from app.schemas.placement_opportunity import (
    PlacementApplicationCreate,
    PlacementApplicationUpdate,
    PlacementOpportunityCreate,
)
from app.services.notification_service import NotificationService
from app.services.placement_opportunity_service import PlacementOpportunityService


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
            UserNotification.__table__,
            PlacementCompany.__table__,
            PlacementOpportunity.__table__,
            PlacementApplication.__table__,
            PlacementInterviewRound.__table__,
            PlacementActivityEvent.__table__,
        ],
    )
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def _add_user_with_profile(
    db: Session,
    *,
    email: str,
    user_type: str,
    name: str,
    cgpa: float = 8.0,
) -> tuple[User, StudentProfile]:
    user = User(email=email, password_hash="unused", student_type=user_type)
    db.add(user)
    db.commit()
    db.refresh(user)
    profile = StudentProfile(
        user_id=user.id,
        name=name,
        twelfth_percentage=82,
        cgpa=cgpa,
        degree="B.Tech" if user_type == "college_student" else "12th",
        specialization="CSE" if user_type == "college_student" else "PCM",
        current_skills=["Python", "SQL"],
        interests=["AI"],
        target_industry="Software",
        projects=1,
        internships=0,
        certifications=1,
        user_type=user_type,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return user, profile


def test_admin_placement_announcement_targets_matching_students() -> None:
    db = _db_session()
    try:
        admin = User(email="admin@example.com", password_hash="unused")
        db.add(admin)
        db.commit()
        db.refresh(admin)
        college_user, _ = _add_user_with_profile(
            db,
            email="college@example.com",
            user_type="college_student",
            name="College Student",
        )
        twelfth_user, _ = _add_user_with_profile(
            db,
            email="twelfth@example.com",
            user_type="twelfth_student",
            name="Twelfth Student",
        )

        result = NotificationService(db).create_placement_announcement(
            PlacementAnnouncementCreate(
                title="Placement briefing",
                message="Attend the aptitude preparation briefing.",
                audience="college_student",
                action_url="/internship",
                priority="high",
            ),
            created_by_user_id=admin.id,
        )

        college_notifications = NotificationService(db).list_user_notifications(
            user=college_user
        )
        twelfth_notifications = NotificationService(db).list_user_notifications(
            user=twelfth_user
        )
        assert result.created_count == 1
        assert college_notifications.unread_count == 1
        assert college_notifications.items[0].title == "Placement briefing"
        assert college_notifications.items[0].priority == "high"
        assert twelfth_notifications.total == 0
    finally:
        db.close()


def test_user_can_mark_notification_read() -> None:
    db = _db_session()
    try:
        user, profile = _add_user_with_profile(
            db,
            email="student@example.com",
            user_type="college_student",
            name="Student One",
        )
        created = NotificationService(db).create_for_user(
            recipient_user_id=user.id,
            profile_id=profile.id,
            notification_type="placement",
            title="Interview scheduled",
            message="Round 1 is scheduled tomorrow.",
            action_url="/internship",
        )

        read = NotificationService(db).mark_read(
            notification_id=created.id,
            user=user,
        )
        listing = NotificationService(db).list_user_notifications(user=user)

        assert read.read_at is not None
        assert listing.unread_count == 0
        assert listing.items[0].read_at is not None
    finally:
        db.close()


def test_placement_admin_status_update_creates_student_notification() -> None:
    db = _db_session()
    try:
        user, profile = _add_user_with_profile(
            db,
            email="student@example.com",
            user_type="college_student",
            name="Student One",
        )
        placement = PlacementOpportunityService(db)
        opportunity = placement.create_opportunity(
            PlacementOpportunityCreate(
                title="Backend Drive",
                company="Partner Tech",
                opportunity_type="placement",
                required_skills=["Python"],
                eligibility={"student_types": ["college_student"]},
            ),
            user_id=99,
        )
        application = placement.apply_to_opportunity(
            opportunity.id,
            PlacementApplicationCreate(
                profile_id=profile.id,
                interest_note="Ready",
            ),
            user=user,
        )

        placement.update_application_status(
            application.id,
            PlacementApplicationUpdate(
                status="interview_scheduled",
                next_step="Prepare portfolio walkthrough",
            ),
            user_id=99,
        )

        notifications = NotificationService(db).list_user_notifications(user=user)
        assert notifications.unread_count == 1
        assert notifications.items[0].notification_type == "placement"
        assert "Interview" in notifications.items[0].title
        assert notifications.items[0].action_url == "/internship"
    finally:
        db.close()
