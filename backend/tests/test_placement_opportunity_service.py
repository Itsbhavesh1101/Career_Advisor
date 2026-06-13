from __future__ import annotations

import csv
from datetime import datetime, timedelta, timezone
from io import StringIO

import pytest
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
from app.schemas.placement_opportunity import (
    PlacementApplicationCreate,
    PlacementApplicationBulkShortlistCreate,
    PlacementApplicationStudentUpdate,
    PlacementApplicationUpdate,
    PlacementCompanyCreate,
    PlacementCompanyUpdate,
    PlacementInterviewRoundCreate,
    PlacementInterviewRoundUpdate,
    PlacementOfferUpdate,
    PlacementOpportunityCreate,
)
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


def _seed_user_and_profile(db: Session) -> tuple[User, StudentProfile]:
    user = User(
        email="student@example.com",
        password_hash="unused",
        student_type="college_student",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    profile = StudentProfile(
        user_id=user.id,
        name="Student One",
        twelfth_percentage=80,
        cgpa=8.2,
        degree="B.Tech",
        specialization="CSE",
        current_skills=["Python", "SQL", "React"],
        interests=["AI", "Backend"],
        target_industry="Software",
        projects=2,
        internships=1,
        certifications=1,
        user_type="college_student",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return user, profile


def test_student_sees_only_active_eligible_opportunities_with_match_score() -> None:
    db = _db_session()
    try:
        user, profile = _seed_user_and_profile(db)
        service = PlacementOpportunityService(db)
        active = service.create_opportunity(
            PlacementOpportunityCreate(
                title="Backend Intern",
                company="Partner Tech",
                opportunity_type="internship",
                description="Build APIs and data tools.",
                required_skills=["Python", "SQL", "Docker"],
                eligibility={"student_types": ["college_student"], "min_cgpa": 7.0},
                deadline_at=datetime.now(timezone.utc) + timedelta(days=7),
            ),
            user_id=99,
        )
        service.create_opportunity(
            PlacementOpportunityCreate(
                title="12th Program Counselor",
                company="Admissions Team",
                opportunity_type="placement",
                status="active",
                required_skills=["Counseling"],
                eligibility={"student_types": ["twelfth_student"]},
            ),
            user_id=99,
        )
        service.create_opportunity(
            PlacementOpportunityCreate(
                title="Closed Drive",
                company="Old Company",
                opportunity_type="placement",
                status="closed",
                required_skills=["Python"],
                eligibility={"student_types": ["college_student"]},
            ),
            user_id=99,
        )

        matches = service.list_student_opportunities(profile_id=profile.id, user=user)

        assert matches.total == 1
        assert matches.items[0].id == active.id
        assert matches.items[0].match_score == 67
        assert matches.items[0].matched_skills == ["Python", "SQL"]
        assert matches.items[0].application_status is None
    finally:
        db.close()


def test_student_application_lifecycle_blocks_duplicates() -> None:
    db = _db_session()
    try:
        user, profile = _seed_user_and_profile(db)
        service = PlacementOpportunityService(db)
        opportunity = service.create_opportunity(
            PlacementOpportunityCreate(
                title="Software Engineer Trainee",
                company="Campus Recruiter",
                opportunity_type="placement",
                package_label="6-8 LPA",
                vacancies=12,
                contact_name="Placement Officer",
                contact_email="tnp@example.com",
                hiring_stages=["Resume screening", "Technical interview", "HR round"],
                required_skills=["Python"],
                eligibility={"student_types": ["college_student"]},
            ),
            user_id=99,
        )

        assert opportunity.package_label == "6-8 LPA"
        assert opportunity.vacancies == 12
        assert opportunity.contact_name == "Placement Officer"
        assert opportunity.contact_email == "tnp@example.com"
        assert opportunity.hiring_stages == [
            "Resume screening",
            "Technical interview",
            "HR round",
        ]

        application = service.apply_to_opportunity(
            opportunity.id,
            PlacementApplicationCreate(
                profile_id=profile.id,
                status="applied",
                interest_note="Ready for this drive.",
            ),
            user=user,
        )

        assert application.status == "applied"
        assert application.profile_id == profile.id
        assert application.opportunity_title == "Software Engineer Trainee"
        assert application.opportunity_company == "Campus Recruiter"
        assert application.opportunity_type == "placement"
        history = service.list_student_applications(profile_id=profile.id, user=user)
        assert history.total == 1
        assert history.items[0].opportunity_title == "Software Engineer Trainee"
        with pytest.raises(ValueError, match="already exists"):
            service.apply_to_opportunity(
                opportunity.id,
                PlacementApplicationCreate(profile_id=profile.id),
                user=user,
            )

        updated = service.update_application_status(
            application.id,
            PlacementApplicationUpdate(
                status="interview_scheduled",
                admin_notes="Cleared resume screening.",
                next_step="Technical interview with engineering panel.",
                next_step_due_at=datetime(2026, 6, 5, 10, 30, tzinfo=timezone.utc),
            ),
            user_id=99,
        )

        assert updated.status == "interview_scheduled"
        assert updated.admin_notes == "Cleared resume screening."
        assert updated.next_step == "Technical interview with engineering panel."
        assert updated.next_step_due_at == datetime(
            2026, 6, 5, 10, 30, tzinfo=timezone.utc
        )
        assert updated.opportunity_title == "Software Engineer Trainee"
    finally:
        db.close()


def test_student_can_update_or_withdraw_own_application() -> None:
    db = _db_session()
    try:
        user, profile = _seed_user_and_profile(db)
        service = PlacementOpportunityService(db)
        opportunity = service.create_opportunity(
            PlacementOpportunityCreate(
                title="Product Internship",
                company="Campus Builder",
                opportunity_type="internship",
                required_skills=["React"],
                eligibility={"student_types": ["college_student"]},
            ),
            user_id=99,
        )
        application = service.apply_to_opportunity(
            opportunity.id,
            PlacementApplicationCreate(
                profile_id=profile.id,
                status="interested",
                interest_note="I want to learn product engineering.",
            ),
            user=user,
        )

        updated = service.update_student_application(
            application.id,
            PlacementApplicationStudentUpdate(
                status="applied",
                interest_note="Resume updated and ready.",
            ),
            user=user,
        )

        assert updated.status == "applied"
        assert updated.interest_note == "Resume updated and ready."
        assert updated.admin_notes is None
        assert updated.opportunity_title == "Product Internship"

        withdrawn = service.update_student_application(
            application.id,
            PlacementApplicationStudentUpdate(
                status="withdrawn",
                interest_note="Withdrawing after schedule conflict.",
            ),
            user=user,
        )

        assert withdrawn.status == "withdrawn"
        assert withdrawn.interest_note == "Withdrawing after schedule conflict."
    finally:
        db.close()


def test_student_cannot_update_another_users_application() -> None:
    db = _db_session()
    try:
        user, profile = _seed_user_and_profile(db)
        other_user = User(
            email="other@example.com",
            password_hash="unused",
            student_type="college_student",
        )
        db.add(other_user)
        db.commit()
        db.refresh(other_user)
        service = PlacementOpportunityService(db)
        opportunity = service.create_opportunity(
            PlacementOpportunityCreate(
                title="Analyst Drive",
                company="Campus Analytics",
                opportunity_type="placement",
                required_skills=["SQL"],
                eligibility={"student_types": ["college_student"]},
            ),
            user_id=99,
        )
        application = service.apply_to_opportunity(
            opportunity.id,
            PlacementApplicationCreate(profile_id=profile.id, status="applied"),
            user=user,
        )

        with pytest.raises(ValueError, match="not found"):
            service.update_student_application(
                application.id,
                PlacementApplicationStudentUpdate(status="withdrawn"),
                user=other_user,
            )
    finally:
        db.close()


def test_admin_can_export_applications_csv_with_student_and_opportunity_context() -> None:
    db = _db_session()
    try:
        user, profile = _seed_user_and_profile(db)
        service = PlacementOpportunityService(db)
        opportunity = service.create_opportunity(
            PlacementOpportunityCreate(
                title="Data Analyst Drive",
                company="Campus Analytics",
                opportunity_type="placement",
                required_skills=["SQL"],
                eligibility={"student_types": ["college_student"]},
            ),
            user_id=99,
        )
        application = service.apply_to_opportunity(
            opportunity.id,
            PlacementApplicationCreate(
                profile_id=profile.id,
                status="applied",
                interest_note="Interested in analytics.",
            ),
            user=user,
        )
        service.update_application_status(
            application.id,
            PlacementApplicationUpdate(
                status="offer_made",
                admin_notes="Good SQL evidence.",
                next_step="Collect offer letter acknowledgement.",
                next_step_due_at=datetime(2026, 6, 7, 12, 0, tzinfo=timezone.utc),
            ),
            user_id=99,
        )

        csv_payload = service.export_admin_applications_csv()
        rows = list(csv.DictReader(StringIO(csv_payload)))

        assert len(rows) == 1
        assert rows[0]["id"] == str(application.id)
        assert rows[0]["opportunity_id"] == str(opportunity.id)
        assert rows[0]["opportunity_title"] == "Data Analyst Drive"
        assert rows[0]["opportunity_company"] == "Campus Analytics"
        assert rows[0]["opportunity_type"] == "placement"
        assert rows[0]["profile_id"] == str(profile.id)
        assert rows[0]["student_name"] == "Student One"
        assert rows[0]["student_email"] == "student@example.com"
        assert rows[0]["status"] == "offer_made"
        assert rows[0]["interest_note"] == "Interested in analytics."
        assert rows[0]["admin_notes"] == "Good SQL evidence."
        assert rows[0]["next_step"] == "Collect offer letter acknowledgement."
        assert rows[0]["next_step_due_at"] == "2026-06-07T12:00:00+00:00"
        assert rows[0]["created_at"] == application.created_at.isoformat()
        assert rows[0]["updated_at"]
    finally:
        db.close()


def test_admin_opportunities_csv_includes_drive_operations_fields() -> None:
    db = _db_session()
    try:
        service = PlacementOpportunityService(db)
        service.create_opportunity(
            PlacementOpportunityCreate(
                title="Graduate Engineer Trainee",
                company="Core Systems",
                opportunity_type="placement",
                package_label="4.5 LPA fixed",
                vacancies=8,
                contact_name="TnP Coordinator",
                contact_email="placements@example.com",
                hiring_stages=["Aptitude", "Technical", "HR"],
                required_skills=["Communication"],
                eligibility={"student_types": ["college_student"]},
            ),
            user_id=99,
        )

        csv_payload = service.export_admin_opportunities_csv()
        rows = list(csv.DictReader(StringIO(csv_payload)))

        assert rows[0]["package_label"] == "4.5 LPA fixed"
        assert rows[0]["vacancies"] == "8"
        assert rows[0]["contact_name"] == "TnP Coordinator"
        assert rows[0]["contact_email"] == "placements@example.com"
        assert rows[0]["hiring_stages"] == "Aptitude; Technical; HR"
    finally:
        db.close()


def test_admin_applications_csv_respects_status_and_opportunity_filters() -> None:
    db = _db_session()
    try:
        user, profile = _seed_user_and_profile(db)
        service = PlacementOpportunityService(db)
        shortlisted_opportunity = service.create_opportunity(
            PlacementOpportunityCreate(
                title="Backend Drive",
                company="Campus Recruiter",
                opportunity_type="placement",
                required_skills=["Python"],
                eligibility={"student_types": ["college_student"]},
            ),
            user_id=99,
        )
        applied_opportunity = service.create_opportunity(
            PlacementOpportunityCreate(
                title="Analytics Internship",
                company="Data Partner",
                opportunity_type="internship",
                required_skills=["SQL"],
                eligibility={"student_types": ["college_student"]},
            ),
            user_id=99,
        )
        shortlisted = service.apply_to_opportunity(
            shortlisted_opportunity.id,
            PlacementApplicationCreate(profile_id=profile.id, status="applied"),
            user=user,
        )
        service.update_application_status(
            shortlisted.id,
            PlacementApplicationUpdate(status="shortlisted"),
            user_id=99,
        )
        service.apply_to_opportunity(
            applied_opportunity.id,
            PlacementApplicationCreate(profile_id=profile.id, status="applied"),
            user=user,
        )

        csv_payload = service.export_admin_applications_csv(
            opportunity_id=shortlisted_opportunity.id,
            status="shortlisted",
        )
        rows = list(csv.DictReader(StringIO(csv_payload)))

        assert len(rows) == 1
        assert rows[0]["opportunity_title"] == "Backend Drive"
        assert rows[0]["status"] == "shortlisted"
    finally:
        db.close()


def test_admin_opportunities_csv_respects_status_and_type_filters() -> None:
    db = _db_session()
    try:
        service = PlacementOpportunityService(db)
        service.create_opportunity(
            PlacementOpportunityCreate(
                title="Backend Internship",
                company="Campus Partner",
                opportunity_type="internship",
                status="active",
                required_skills=["Python", "SQL"],
                eligibility={"student_types": ["college_student"]},
            ),
            user_id=99,
        )
        service.create_opportunity(
            PlacementOpportunityCreate(
                title="Closed Placement Drive",
                company="Old Recruiter",
                opportunity_type="placement",
                status="closed",
                required_skills=["Communication"],
                eligibility={"student_types": ["college_student"]},
            ),
            user_id=99,
        )

        csv_payload = service.export_admin_opportunities_csv(
            status="active",
            opportunity_type="internship",
        )
        rows = list(csv.DictReader(StringIO(csv_payload)))

        assert len(rows) == 1
        assert rows[0]["title"] == "Backend Internship"
        assert rows[0]["company"] == "Campus Partner"
        assert rows[0]["type"] == "internship"
        assert rows[0]["status"] == "active"
        assert rows[0]["required_skills"] == "Python; SQL"
    finally:
        db.close()


def test_admin_can_manage_company_master_and_link_drive() -> None:
    db = _db_session()
    try:
        service = PlacementOpportunityService(db)

        company = service.create_company(
            PlacementCompanyCreate(
                name="Campus Partner Labs",
                website="https://partner.example.com",
                industry="Software services",
                location="Bengaluru",
                contact_name="Recruiter One",
                contact_email="recruiter@example.com",
                notes="Preferred campus partner.",
            ),
            user_id=99,
        )

        listed = service.list_admin_companies()
        assert listed.total == 1
        assert listed.items[0].name == "Campus Partner Labs"
        assert listed.items[0].status == "active"

        opportunity = service.create_opportunity(
            PlacementOpportunityCreate(
                title="Graduate Engineer Trainee",
                company="Campus Partner Labs",
                company_id=company.id,
                opportunity_type="placement",
                required_skills=["Python"],
                eligibility={"student_types": ["college_student"]},
            ),
            user_id=99,
        )

        assert opportunity.company_id == company.id
        assert opportunity.company_master_name == "Campus Partner Labs"

        archived = service.update_company(
            company.id,
            PlacementCompanyUpdate(status="archived", notes="No current drives."),
            user_id=100,
        )
        assert archived.status == "archived"
        assert archived.notes == "No current drives."
        assert archived.updated_by_user_id == 100
    finally:
        db.close()


def test_admin_can_shortlist_eligible_students_for_drive() -> None:
    db = _db_session()
    try:
        user, profile = _seed_user_and_profile(db)
        ineligible_user = User(
            email="ineligible@example.com",
            password_hash="unused",
            student_type="college_student",
        )
        db.add(ineligible_user)
        db.commit()
        db.refresh(ineligible_user)
        ineligible_profile = StudentProfile(
            user_id=ineligible_user.id,
            name="Student Two",
            twelfth_percentage=80,
            cgpa=6.1,
            degree="B.Tech",
            specialization="ECE",
            current_skills=["Excel"],
            interests=["Hardware"],
            target_industry="Electronics",
            projects=1,
            internships=0,
            certifications=0,
            user_type="college_student",
        )
        db.add(ineligible_profile)
        db.commit()

        service = PlacementOpportunityService(db)
        opportunity = service.create_opportunity(
            PlacementOpportunityCreate(
                title="Backend Drive",
                company="Campus Recruiter",
                opportunity_type="placement",
                required_skills=["Python", "SQL", "Docker"],
                eligibility={
                    "student_types": ["college_student"],
                    "min_cgpa": 7.0,
                    "specializations": ["CSE"],
                },
            ),
            user_id=99,
        )
        application = service.apply_to_opportunity(
            opportunity.id,
            PlacementApplicationCreate(profile_id=profile.id, status="applied"),
            user=user,
        )

        shortlist = service.list_eligible_students_for_opportunity(opportunity.id)

        assert shortlist.total == 1
        item = shortlist.items[0]
        assert item.profile_id == profile.id
        assert item.student_name == "Student One"
        assert item.student_email == "student@example.com"
        assert item.match_score == 67
        assert item.matched_skills == ["Python", "SQL"]
        assert item.missing_skills == ["Docker"]
        assert item.application_status == "applied"
        assert item.application_id == application.id
    finally:
        db.close()


def test_admin_can_bulk_shortlist_eligible_students_for_drive() -> None:
    db = _db_session()
    try:
        user, profile = _seed_user_and_profile(db)
        service = PlacementOpportunityService(db)
        opportunity = service.create_opportunity(
            PlacementOpportunityCreate(
                title="Python Developer Drive",
                company="Campus Recruiter",
                opportunity_type="placement",
                required_skills=["Python", "SQL"],
                eligibility={"student_types": ["college_student"], "min_cgpa": 7.0},
            ),
            user_id=99,
        )

        result = service.bulk_shortlist_eligible_students(
            opportunity.id,
            PlacementApplicationBulkShortlistCreate(
                profile_ids=[profile.id],
                admin_notes="Shortlisted from eligible-student review.",
                next_step="Attend aptitude round.",
                next_step_due_at=datetime(2026, 6, 10, 9, 30, tzinfo=timezone.utc),
            ),
            user_id=99,
        )

        assert result.total == 1
        shortlisted = result.items[0]
        assert shortlisted.profile_id == profile.id
        assert shortlisted.user_id == user.id
        assert shortlisted.status == "shortlisted"
        assert shortlisted.admin_notes == "Shortlisted from eligible-student review."
        assert shortlisted.next_step == "Attend aptitude round."
        assert shortlisted.next_step_due_at == datetime(
            2026, 6, 10, 9, 30, tzinfo=timezone.utc
        )
        shortlist = service.list_eligible_students_for_opportunity(opportunity.id)
        assert shortlist.items[0].application_id == shortlisted.id
        assert shortlist.items[0].application_status == "shortlisted"
    finally:
        db.close()


def test_admin_can_schedule_interview_round_and_student_history_includes_it() -> None:
    db = _db_session()
    try:
        user, profile = _seed_user_and_profile(db)
        service = PlacementOpportunityService(db)
        opportunity = service.create_opportunity(
            PlacementOpportunityCreate(
                title="Graduate Engineer Trainee",
                company="Core Systems",
                opportunity_type="placement",
                required_skills=["Python"],
                eligibility={"student_types": ["college_student"]},
            ),
            user_id=99,
        )
        application = service.apply_to_opportunity(
            opportunity.id,
            PlacementApplicationCreate(profile_id=profile.id, status="applied"),
            user=user,
        )

        scheduled = service.create_interview_round(
            application.id,
            PlacementInterviewRoundCreate(
                round_name="Technical interview",
                scheduled_at=datetime(2026, 6, 12, 14, 0, tzinfo=timezone.utc),
                mode="offline",
                location="TnP Seminar Hall",
                interviewer="Engineering panel",
                notes="Bring resume and project proof.",
            ),
            user_id=99,
        )

        assert scheduled.status == "interview_scheduled"
        assert scheduled.next_step == "Technical interview"
        assert scheduled.next_step_due_at == datetime(
            2026, 6, 12, 14, 0, tzinfo=timezone.utc
        )
        assert len(scheduled.interview_rounds) == 1
        interview = scheduled.interview_rounds[0]
        assert interview.round_name == "Technical interview"
        assert interview.status == "scheduled"
        assert interview.mode == "offline"
        assert interview.location == "TnP Seminar Hall"
        assert interview.interviewer == "Engineering panel"

        history = service.list_student_applications(profile_id=profile.id, user=user)
        assert history.items[0].interview_rounds[0].round_name == "Technical interview"
    finally:
        db.close()


def test_admin_can_record_interview_outcome_and_reject_application() -> None:
    db = _db_session()
    try:
        user, profile = _seed_user_and_profile(db)
        service = PlacementOpportunityService(db)
        opportunity = service.create_opportunity(
            PlacementOpportunityCreate(
                title="Graduate Engineer Trainee",
                company="Core Systems",
                opportunity_type="placement",
                required_skills=["Python"],
                eligibility={"student_types": ["college_student"]},
            ),
            user_id=99,
        )
        application = service.apply_to_opportunity(
            opportunity.id,
            PlacementApplicationCreate(profile_id=profile.id, status="applied"),
            user=user,
        )
        scheduled = service.create_interview_round(
            application.id,
            PlacementInterviewRoundCreate(round_name="HR discussion"),
            user_id=99,
        )
        interview = scheduled.interview_rounds[0]

        updated = service.update_interview_round(
            interview.id,
            PlacementInterviewRoundUpdate(
                status="rejected",
                notes="Communication round did not clear.",
            ),
            user_id=99,
        )

        assert updated.status == "rejected"
        assert updated.notes == "Communication round did not clear."
        history = service.list_student_applications(profile_id=profile.id, user=user)
        assert history.items[0].status == "not_selected"
        assert history.items[0].admin_notes == "Communication round did not clear."
        assert history.items[0].next_step == "Placement process closed for this drive."
    finally:
        db.close()


def test_admin_can_record_offer_details_and_student_history_includes_offer() -> None:
    db = _db_session()
    try:
        user, profile = _seed_user_and_profile(db)
        service = PlacementOpportunityService(db)
        opportunity = service.create_opportunity(
            PlacementOpportunityCreate(
                title="Associate Software Engineer",
                company="Launch Partner",
                opportunity_type="placement",
                package_label="6 LPA",
                eligibility={"student_types": ["college_student"]},
            ),
            user_id=99,
        )
        application = service.apply_to_opportunity(
            opportunity.id,
            PlacementApplicationCreate(profile_id=profile.id, status="applied"),
            user=user,
        )

        offered = service.update_application_offer(
            application.id,
            PlacementOfferUpdate(
                offer_status="offered",
                offer_role="Associate Software Engineer",
                offer_package="6.5 LPA",
                offer_location="Bhopal",
                offer_joining_date=datetime(2026, 7, 1, 9, 0, tzinfo=timezone.utc),
                offer_notes="Offer letter pending final HR upload.",
                next_step="Confirm offer acceptance with placement cell.",
            ),
            user_id=99,
        )

        assert offered.status == "offer_made"
        assert offered.offer_status == "offered"
        assert offered.offer_role == "Associate Software Engineer"
        assert offered.offer_package == "6.5 LPA"
        assert offered.offer_location == "Bhopal"
        assert offered.offer_joining_date == datetime(
            2026, 7, 1, 9, 0, tzinfo=timezone.utc
        )
        assert offered.offer_notes == "Offer letter pending final HR upload."
        assert offered.next_step == "Confirm offer acceptance with placement cell."

        accepted = service.update_application_offer(
            application.id,
            PlacementOfferUpdate(offer_status="accepted"),
            user_id=99,
        )

        assert accepted.status == "placed"
        assert accepted.offer_status == "accepted"
        history = service.list_student_applications(profile_id=profile.id, user=user)
        assert history.items[0].offer_status == "accepted"
        assert history.items[0].offer_package == "6.5 LPA"
    finally:
        db.close()


def test_placement_activity_records_admin_and_student_operations() -> None:
    db = _db_session()
    try:
        user, profile = _seed_user_and_profile(db)
        service = PlacementOpportunityService(db)
        opportunity = service.create_opportunity(
            PlacementOpportunityCreate(
                title="Operations Drive",
                company="Timeline Partner",
                opportunity_type="placement",
                required_skills=["Python"],
                eligibility={"student_types": ["college_student"]},
            ),
            user_id=99,
        )
        application = service.apply_to_opportunity(
            opportunity.id,
            PlacementApplicationCreate(
                profile_id=profile.id,
                status="applied",
                interest_note="Ready for timeline validation.",
            ),
            user=user,
        )
        service.update_application_status(
            application.id,
            PlacementApplicationUpdate(
                status="screening",
                admin_notes="Resume under review.",
                next_step="Wait for screening result.",
                next_step_due_at=datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc),
            ),
            user_id=99,
        )
        service.create_interview_round(
            application.id,
            PlacementInterviewRoundCreate(
                round_name="Technical interview",
                scheduled_at=datetime(2026, 6, 4, 12, 0, tzinfo=timezone.utc),
            ),
            user_id=99,
        )
        service.update_application_offer(
            application.id,
            PlacementOfferUpdate(
                offer_status="offered",
                offer_role="Associate Engineer",
                next_step="Confirm offer acknowledgement.",
                next_step_due_at=datetime(2026, 6, 7, 12, 0, tzinfo=timezone.utc),
            ),
            user_id=99,
        )

        admin_activity = service.list_admin_activity(limit=20)
        student_activity = service.list_student_activity(profile_id=profile.id, user=user)

        assert admin_activity.total >= 5
        assert [item.event_type for item in admin_activity.items[:4]] == [
            "application_offer_updated",
            "interview_round_scheduled",
            "application_status_updated",
            "application_created",
        ]
        assert admin_activity.items[0].opportunity_title == "Operations Drive"
        assert admin_activity.items[0].student_name == "Student One"
        assert admin_activity.items[0].title == "Offer offered"
        assert student_activity.total == 4
        assert student_activity.items[0].event_type == "application_offer_updated"
        assert all(item.profile_id == profile.id for item in student_activity.items)
    finally:
        db.close()


def test_upcoming_actions_combine_deadlines_next_steps_interviews_and_offers() -> None:
    db = _db_session()
    try:
        user, profile = _seed_user_and_profile(db)
        service = PlacementOpportunityService(db)
        opportunity = service.create_opportunity(
            PlacementOpportunityCreate(
                title="Calendar Drive",
                company="Action Partner",
                opportunity_type="placement",
                deadline_at=datetime(2026, 6, 2, 10, 0, tzinfo=timezone.utc),
                required_skills=["Python"],
                eligibility={"student_types": ["college_student"]},
            ),
            user_id=99,
        )
        application = service.apply_to_opportunity(
            opportunity.id,
            PlacementApplicationCreate(profile_id=profile.id, status="applied"),
            user=user,
        )
        service.update_application_status(
            application.id,
            PlacementApplicationUpdate(
                status="screening",
                next_step="Upload updated resume evidence.",
                next_step_due_at=datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc),
            ),
            user_id=99,
        )
        service.create_interview_round(
            application.id,
            PlacementInterviewRoundCreate(
                round_name="Technical interview",
                scheduled_at=datetime(2026, 6, 3, 11, 0, tzinfo=timezone.utc),
            ),
            user_id=99,
        )
        service.update_application_offer(
            application.id,
            PlacementOfferUpdate(
                offer_status="offered",
                offer_role="Associate Engineer",
                offer_joining_date=datetime(2026, 7, 1, 9, 0, tzinfo=timezone.utc),
                next_step="Confirm offer acknowledgement.",
                next_step_due_at=datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc),
            ),
            user_id=99,
        )

        admin_actions = service.list_admin_upcoming_actions(limit=10)
        student_actions = service.list_student_upcoming_actions(
            profile_id=profile.id,
            user=user,
            limit=10,
        )

        assert [item.action_type for item in admin_actions.items] == [
            "application_next_step",
            "opportunity_deadline",
            "interview_round",
            "offer_joining",
        ]
        assert admin_actions.items[0].title == "Confirm offer acknowledgement."
        assert admin_actions.items[0].student_name == "Student One"
        assert admin_actions.items[1].title == "Calendar Drive deadline"
        assert admin_actions.items[2].title == "Technical interview"
        assert admin_actions.items[3].title == "Associate Engineer joining"
        assert [item.action_type for item in student_actions.items] == [
            "application_next_step",
            "opportunity_deadline",
            "interview_round",
            "offer_joining",
        ]
    finally:
        db.close()
