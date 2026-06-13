from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.api import deps
from app.api.routes import placement_opportunities as placement_routes
from app.schemas.placement_opportunity import (
    PlacementActivityEventListRead,
    PlacementActivityEventRead,
    PlacementApplicationListRead,
    PlacementApplicationRead,
    PlacementCompanyListRead,
    PlacementCompanyRead,
    PlacementEligibleStudentListRead,
    PlacementEligibleStudentRead,
    PlacementOpportunityListRead,
    PlacementOpportunityRead,
    PlacementUpcomingActionListRead,
    PlacementUpcomingActionRead,
)
from main import app


class _FakeDB:
    def close(self) -> None:
        pass


def _override_db():
    db = _FakeDB()
    try:
        yield db
    finally:
        db.close()


def _override_admin():
    return SimpleNamespace(id=7, email="admin@institution.edu")


def _override_user():
    return SimpleNamespace(id=11, email="student@example.com", student_type="college_student")


def _opportunity_read(**overrides):
    data = {
        "id": 5,
        "title": "Backend Intern",
        "company": "Partner Tech",
        "company_id": None,
        "opportunity_type": "internship",
        "status": "active",
        "description": "Build APIs.",
        "location": "Bhopal",
        "work_mode": "hybrid",
        "deadline_at": "2026-06-01T00:00:00Z",
        "eligibility": {"student_types": ["college_student"]},
        "required_skills": ["Python", "SQL"],
        "apply_url": None,
        "package_label": "6 LPA",
        "vacancies": 3,
        "contact_name": "Placement Officer",
        "contact_email": "tnp@example.com",
        "hiring_stages": ["Resume", "Interview"],
        "created_by_user_id": 7,
        "updated_by_user_id": 7,
        "created_at": "2026-05-25T00:00:00Z",
        "updated_at": "2026-05-25T00:00:00Z",
        "applicant_count": 2,
        "match_score": 100,
        "matched_skills": ["Python", "SQL"],
        "application_status": None,
        "company_master_name": None,
    }
    data.update(overrides)
    return PlacementOpportunityRead.model_validate(data)


def _application_read(**overrides):
    data = {
        "id": 9,
        "opportunity_id": 5,
        "profile_id": 12,
        "user_id": 11,
        "student_name": "Student One",
        "student_email": "student@example.com",
        "opportunity_title": "Backend Intern",
        "opportunity_company": "Partner Tech",
        "opportunity_type": "internship",
        "status": "applied",
        "interest_note": "Ready.",
        "admin_notes": None,
        "next_step": None,
        "next_step_due_at": None,
        "created_at": "2026-05-25T00:00:00Z",
        "updated_at": "2026-05-25T00:00:00Z",
    }
    data.update(overrides)
    return PlacementApplicationRead.model_validate(data)


def _company_read(**overrides):
    data = {
        "id": 3,
        "name": "Partner Tech",
        "status": "active",
        "website": "https://partner.example.com",
        "industry": "Software",
        "location": "Bhopal",
        "contact_name": "Recruiter",
        "contact_email": "recruiter@example.com",
        "notes": "Campus partner.",
        "created_by_user_id": 7,
        "updated_by_user_id": 7,
        "created_at": "2026-05-25T00:00:00Z",
        "updated_at": "2026-05-25T00:00:00Z",
        "active_opportunity_count": 1,
    }
    data.update(overrides)
    return PlacementCompanyRead.model_validate(data)


def _eligible_student_read(**overrides):
    data = {
        "profile_id": 12,
        "student_name": "Student One",
        "student_email": "student@example.com",
        "specialization": "CSE",
        "cgpa": 8.2,
        "current_skills": ["Python", "SQL"],
        "match_score": 67,
        "matched_skills": ["Python", "SQL"],
        "missing_skills": ["Docker"],
        "application_id": 9,
        "application_status": "applied",
    }
    data.update(overrides)
    return PlacementEligibleStudentRead.model_validate(data)


def _activity_read(**overrides):
    data = {
        "id": 44,
        "event_type": "application_status_updated",
        "title": "Application moved to screening",
        "message": "Student One moved to screening for Backend Intern.",
        "opportunity_id": 5,
        "application_id": 9,
        "profile_id": 12,
        "company_id": None,
        "actor_user_id": 7,
        "opportunity_title": "Backend Intern",
        "opportunity_company": "Partner Tech",
        "student_name": "Student One",
        "metadata": {"status": "screening"},
        "created_at": "2026-05-25T00:00:00Z",
    }
    data.update(overrides)
    return PlacementActivityEventRead.model_validate(data)


def _upcoming_action_read(**overrides):
    data = {
        "action_type": "application_next_step",
        "title": "Attend technical interview.",
        "due_at": "2026-06-05T10:30:00Z",
        "opportunity_id": 5,
        "application_id": 9,
        "profile_id": 12,
        "interview_round_id": None,
        "opportunity_title": "Backend Intern",
        "opportunity_company": "Partner Tech",
        "student_name": "Student One",
        "status": "interview_scheduled",
    }
    data.update(overrides)
    return PlacementUpcomingActionRead.model_validate(data)


class _FakePlacementOpportunityService:
    created_payload = None
    exported_opportunity_filters = None
    updated_application_payload = None
    exported_application_filters = None
    created_company_payload = None
    updated_company_payload = None
    bulk_shortlist_payload = None
    bulk_status_payload = None
    created_interview_payload = None
    updated_interview_payload = None
    updated_offer_payload = None

    def __init__(self, db) -> None:
        self.db = db

    def list_admin_opportunities(self, **_kwargs):
        return PlacementOpportunityListRead(items=[_opportunity_read()], total=1)

    def list_admin_companies(self, **_kwargs):
        return PlacementCompanyListRead(items=[_company_read()], total=1)

    def create_company(self, payload, user_id: int):
        type(self).created_company_payload = (payload, user_id)
        return _company_read(name=payload.name, created_by_user_id=user_id)

    def update_company(self, company_id: int, payload, user_id: int):
        type(self).updated_company_payload = (company_id, payload, user_id)
        return _company_read(id=company_id, status=payload.status or "active")

    def archive_company(self, company_id: int, user_id: int):
        type(self).updated_company_payload = (company_id, "archive", user_id)
        return _company_read(id=company_id, status="archived")

    def create_opportunity(self, payload, user_id: int):
        type(self).created_payload = (payload, user_id)
        return _opportunity_read(
            title=payload.title,
            company=payload.company,
            opportunity_type=payload.opportunity_type,
        )

    def update_opportunity(self, opportunity_id: int, payload, user_id: int):
        return _opportunity_read(id=opportunity_id, title=payload.title or "Backend Intern")

    def list_eligible_students_for_opportunity(self, opportunity_id: int):
        return PlacementEligibleStudentListRead(
            items=[_eligible_student_read()],
            total=1,
        )

    def bulk_shortlist_eligible_students(self, opportunity_id: int, payload, user_id: int):
        type(self).bulk_shortlist_payload = (opportunity_id, payload, user_id)
        return PlacementApplicationListRead(
            items=[
                _application_read(
                    opportunity_id=opportunity_id,
                    profile_id=payload.profile_ids[0],
                    status="shortlisted",
                    admin_notes=payload.admin_notes,
                    next_step=payload.next_step,
                )
            ],
            total=1,
        )

    def list_student_opportunities(self, profile_id: int, user):
        return PlacementOpportunityListRead(items=[_opportunity_read()], total=1)

    def apply_to_opportunity(self, opportunity_id: int, payload, user):
        return _application_read(opportunity_id=opportunity_id, profile_id=payload.profile_id)

    def list_student_applications(self, profile_id: int, user):
        return PlacementApplicationListRead(
            items=[_application_read(profile_id=profile_id, user_id=user.id)],
            total=1,
        )

    def update_student_application(self, application_id: int, payload, user):
        type(self).updated_application_payload = (application_id, payload, user.id)
        return _application_read(
            id=application_id,
            status=payload.status,
            interest_note=payload.interest_note,
            user_id=user.id,
        )

    def list_admin_applications(self, **_kwargs):
        return PlacementApplicationListRead(items=[_application_read()], total=1)

    def list_admin_activity(self, **_kwargs):
        return PlacementActivityEventListRead(items=[_activity_read()], total=1)

    def list_student_activity(self, profile_id: int, user, **_kwargs):
        return PlacementActivityEventListRead(
            items=[_activity_read(profile_id=profile_id, actor_user_id=user.id)],
            total=1,
        )

    def list_admin_upcoming_actions(self, **_kwargs):
        return PlacementUpcomingActionListRead(items=[_upcoming_action_read()], total=1)

    def list_student_upcoming_actions(self, profile_id: int, user, **_kwargs):
        return PlacementUpcomingActionListRead(
            items=[_upcoming_action_read(profile_id=profile_id)],
            total=1,
        )

    def update_application_status(self, application_id: int, payload, user_id: int):
        type(self).updated_application_payload = (application_id, payload, user_id)
        return _application_read(id=application_id, status=payload.status)

    def bulk_update_applications(self, payload, user_id: int):
        type(self).bulk_status_payload = (payload, user_id)
        return PlacementApplicationListRead(
            items=[
                _application_read(
                    id=payload.application_ids[0],
                    status=payload.status,
                    admin_notes=payload.admin_notes,
                    next_step=payload.next_step,
                )
            ],
            total=1,
        )

    def create_interview_round(self, application_id: int, payload, user_id: int):
        type(self).created_interview_payload = (application_id, payload, user_id)
        return _application_read(
            id=application_id,
            status="interview_scheduled",
            next_step=payload.round_name,
            next_step_due_at=payload.scheduled_at,
            interview_rounds=[
                {
                    "id": 33,
                    "application_id": application_id,
                    "round_name": payload.round_name,
                    "status": "scheduled",
                    "scheduled_at": payload.scheduled_at,
                    "mode": payload.mode,
                    "location": payload.location,
                    "interviewer": payload.interviewer,
                    "notes": payload.notes,
                    "created_by_user_id": user_id,
                    "updated_by_user_id": user_id,
                    "created_at": "2026-05-25T00:00:00Z",
                    "updated_at": "2026-05-25T00:00:00Z",
                }
            ],
        )

    def update_interview_round(self, interview_id: int, payload, user_id: int):
        type(self).updated_interview_payload = (interview_id, payload, user_id)
        return {
            "id": interview_id,
            "application_id": 9,
            "round_name": payload.round_name or "Technical interview",
            "status": payload.status or "scheduled",
            "scheduled_at": payload.scheduled_at,
            "mode": payload.mode,
            "location": payload.location,
            "interviewer": payload.interviewer,
            "notes": payload.notes,
            "created_by_user_id": 7,
            "updated_by_user_id": user_id,
            "created_at": "2026-05-25T00:00:00Z",
            "updated_at": "2026-05-25T00:00:00Z",
        }

    def update_application_offer(self, application_id: int, payload, user_id: int):
        type(self).updated_offer_payload = (application_id, payload, user_id)
        return _application_read(
            id=application_id,
            status="offer_made" if payload.offer_status == "offered" else "placed",
            offer_status=payload.offer_status,
            offer_role=payload.offer_role,
            offer_package=payload.offer_package,
            offer_location=payload.offer_location,
            offer_joining_date=payload.offer_joining_date,
            offer_notes=payload.offer_notes,
            next_step=payload.next_step,
        )

    def export_admin_opportunities_csv(self, **kwargs) -> str:
        type(self).exported_opportunity_filters = kwargs
        return "id,title,company,status\n5,Backend Intern,Partner Tech,active\n"

    def export_admin_applications_csv(self, **kwargs) -> str:
        type(self).exported_application_filters = kwargs
        return (
            "id,opportunity_title,opportunity_company,student_name,status\n"
            "9,Backend Intern,Partner Tech,Student One,applied\n"
        )


@pytest.fixture(autouse=True)
def _clear_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


def test_admin_can_manage_opportunities_and_export(monkeypatch) -> None:
    monkeypatch.setattr(
        placement_routes,
        "PlacementOpportunityService",
        _FakePlacementOpportunityService,
    )
    app.dependency_overrides[deps.get_current_admin] = _override_admin
    app.dependency_overrides[deps.get_db] = _override_db
    client = TestClient(app)

    listed = client.get("/api/v1/placement-opportunities/admin/opportunities")
    created = client.post(
        "/api/v1/placement-opportunities/admin/opportunities",
        json={
            "title": "Backend Intern",
            "company": "Partner Tech",
            "opportunity_type": "internship",
            "required_skills": ["Python", "SQL"],
            "eligibility": {"student_types": ["college_student"]},
        },
    )
    exported = client.get("/api/v1/placement-opportunities/admin/export.csv")

    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert created.status_code == 201
    assert created.json()["created_by_user_id"] == 7
    assert exported.status_code == 200
    assert "Backend Intern" in exported.text


def test_admin_can_manage_company_master(monkeypatch) -> None:
    monkeypatch.setattr(
        placement_routes,
        "PlacementOpportunityService",
        _FakePlacementOpportunityService,
    )
    app.dependency_overrides[deps.get_current_admin] = _override_admin
    app.dependency_overrides[deps.get_db] = _override_db
    client = TestClient(app)

    listed = client.get("/api/v1/placement-opportunities/admin/companies")
    created = client.post(
        "/api/v1/placement-opportunities/admin/companies",
        json={
            "name": "Partner Tech",
            "website": "https://partner.example.com",
            "industry": "Software",
            "location": "Bhopal",
            "contact_name": "Recruiter",
            "contact_email": "recruiter@example.com",
            "notes": "Campus partner.",
        },
    )
    archived = client.delete("/api/v1/placement-opportunities/admin/companies/3")

    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["active_opportunity_count"] == 1
    assert created.status_code == 201
    assert created.json()["created_by_user_id"] == 7
    assert archived.status_code == 200
    assert archived.json()["status"] == "archived"
    payload, user_id = _FakePlacementOpportunityService.created_company_payload
    assert payload.name == "Partner Tech"
    assert user_id == 7


def test_admin_can_list_eligible_students_for_drive(monkeypatch) -> None:
    monkeypatch.setattr(
        placement_routes,
        "PlacementOpportunityService",
        _FakePlacementOpportunityService,
    )
    app.dependency_overrides[deps.get_current_admin] = _override_admin
    app.dependency_overrides[deps.get_db] = _override_db

    response = TestClient(app).get(
        "/api/v1/placement-opportunities/admin/opportunities/5/eligible-students"
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["match_score"] == 67
    assert response.json()["items"][0]["missing_skills"] == ["Docker"]
    assert response.json()["items"][0]["application_status"] == "applied"


def test_admin_can_bulk_shortlist_eligible_students_for_drive(monkeypatch) -> None:
    monkeypatch.setattr(
        placement_routes,
        "PlacementOpportunityService",
        _FakePlacementOpportunityService,
    )
    app.dependency_overrides[deps.get_current_admin] = _override_admin
    app.dependency_overrides[deps.get_db] = _override_db

    response = TestClient(app).post(
        "/api/v1/placement-opportunities/admin/opportunities/5/shortlist",
        json={
            "profile_ids": [12],
            "admin_notes": "Shortlisted from eligible review.",
            "next_step": "Attend aptitude round.",
            "next_step_due_at": "2026-06-10T09:30:00Z",
        },
    )

    assert response.status_code == 201
    assert response.json()["items"][0]["status"] == "shortlisted"
    opportunity_id, payload, user_id = _FakePlacementOpportunityService.bulk_shortlist_payload
    assert opportunity_id == 5
    assert payload.profile_ids == [12]
    assert payload.next_step == "Attend aptitude round."
    assert user_id == 7


def test_student_can_list_and_apply_to_opportunities(monkeypatch) -> None:
    monkeypatch.setattr(
        placement_routes,
        "PlacementOpportunityService",
        _FakePlacementOpportunityService,
    )
    app.dependency_overrides[deps.get_current_user] = _override_user
    app.dependency_overrides[deps.get_db] = _override_db
    client = TestClient(app)

    listed = client.get("/api/v1/placement-opportunities?profile_id=12")
    applied = client.post(
        "/api/v1/placement-opportunities/5/apply",
        json={"profile_id": 12, "status": "applied", "interest_note": "Ready."},
    )

    assert listed.status_code == 200
    assert listed.json()["items"][0]["match_score"] == 100
    assert applied.status_code == 201
    assert applied.json()["status"] == "applied"
    assert applied.json()["opportunity_title"] == "Backend Intern"


def test_student_can_list_application_history(monkeypatch) -> None:
    monkeypatch.setattr(
        placement_routes,
        "PlacementOpportunityService",
        _FakePlacementOpportunityService,
    )
    app.dependency_overrides[deps.get_current_user] = _override_user
    app.dependency_overrides[deps.get_db] = _override_db
    client = TestClient(app)

    response = client.get("/api/v1/placement-opportunities/applications?profile_id=12")

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["opportunity_title"] == "Backend Intern"
    assert response.json()["items"][0]["opportunity_company"] == "Partner Tech"


def test_student_can_list_activity_and_upcoming_actions(monkeypatch) -> None:
    monkeypatch.setattr(
        placement_routes,
        "PlacementOpportunityService",
        _FakePlacementOpportunityService,
    )
    app.dependency_overrides[deps.get_current_user] = _override_user
    app.dependency_overrides[deps.get_db] = _override_db
    client = TestClient(app)

    activity = client.get("/api/v1/placement-opportunities/activity?profile_id=12")
    upcoming = client.get("/api/v1/placement-opportunities/upcoming?profile_id=12")

    assert activity.status_code == 200
    assert activity.json()["items"][0]["event_type"] == "application_status_updated"
    assert activity.json()["items"][0]["profile_id"] == 12
    assert upcoming.status_code == 200
    assert upcoming.json()["items"][0]["action_type"] == "application_next_step"
    assert upcoming.json()["items"][0]["student_name"] == "Student One"


def test_student_can_update_own_application(monkeypatch) -> None:
    monkeypatch.setattr(
        placement_routes,
        "PlacementOpportunityService",
        _FakePlacementOpportunityService,
    )
    app.dependency_overrides[deps.get_current_user] = _override_user
    app.dependency_overrides[deps.get_db] = _override_db

    response = TestClient(app).patch(
        "/api/v1/placement-opportunities/applications/9",
        json={"status": "withdrawn", "interest_note": "Schedule conflict."},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "withdrawn"
    assert response.json()["interest_note"] == "Schedule conflict."
    application_id, payload, user_id = (
        _FakePlacementOpportunityService.updated_application_payload
    )
    assert application_id == 9
    assert payload.status == "withdrawn"
    assert payload.interest_note == "Schedule conflict."
    assert user_id == 11


def test_admin_can_update_application_status(monkeypatch) -> None:
    monkeypatch.setattr(
        placement_routes,
        "PlacementOpportunityService",
        _FakePlacementOpportunityService,
    )
    app.dependency_overrides[deps.get_current_admin] = _override_admin
    app.dependency_overrides[deps.get_db] = _override_db

    response = TestClient(app).patch(
        "/api/v1/placement-opportunities/admin/applications/9",
        json={
            "status": "interview_scheduled",
            "admin_notes": "Cleared resume screening.",
            "next_step": "Technical interview on campus.",
            "next_step_due_at": "2026-06-05T10:30:00Z",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "interview_scheduled"
    assert response.json()["opportunity_company"] == "Partner Tech"
    application_id, payload, user_id = (
        _FakePlacementOpportunityService.updated_application_payload
    )
    assert application_id == 9
    assert payload.next_step == "Technical interview on campus."
    assert payload.next_step_due_at.isoformat().startswith("2026-06-05T10:30:00")
    assert user_id == 7


def test_admin_can_bulk_update_application_status(monkeypatch) -> None:
    monkeypatch.setattr(
        placement_routes,
        "PlacementOpportunityService",
        _FakePlacementOpportunityService,
    )
    app.dependency_overrides[deps.get_current_admin] = _override_admin
    app.dependency_overrides[deps.get_db] = _override_db

    response = TestClient(app).patch(
        "/api/v1/placement-opportunities/admin/applications/bulk",
        json={
            "application_ids": [9],
            "status": "offer_made",
            "admin_notes": "Selected by recruiter.",
            "next_step": "Submit offer acknowledgement.",
        },
    )

    assert response.status_code == 200
    assert response.json()["items"][0]["status"] == "offer_made"
    payload, user_id = _FakePlacementOpportunityService.bulk_status_payload
    assert payload.application_ids == [9]
    assert payload.status == "offer_made"
    assert user_id == 7


def test_admin_can_schedule_interview_round(monkeypatch) -> None:
    monkeypatch.setattr(
        placement_routes,
        "PlacementOpportunityService",
        _FakePlacementOpportunityService,
    )
    app.dependency_overrides[deps.get_current_admin] = _override_admin
    app.dependency_overrides[deps.get_db] = _override_db

    response = TestClient(app).post(
        "/api/v1/placement-opportunities/admin/applications/9/interviews",
        json={
            "round_name": "Technical interview",
            "scheduled_at": "2026-06-12T14:00:00Z",
            "mode": "offline",
            "location": "TnP Seminar Hall",
            "interviewer": "Engineering panel",
            "notes": "Bring resume and project proof.",
        },
    )

    assert response.status_code == 201
    assert response.json()["status"] == "interview_scheduled"
    assert response.json()["interview_rounds"][0]["round_name"] == "Technical interview"
    application_id, payload, user_id = _FakePlacementOpportunityService.created_interview_payload
    assert application_id == 9
    assert payload.mode == "offline"
    assert user_id == 7


def test_admin_can_update_interview_round_outcome(monkeypatch) -> None:
    monkeypatch.setattr(
        placement_routes,
        "PlacementOpportunityService",
        _FakePlacementOpportunityService,
    )
    app.dependency_overrides[deps.get_current_admin] = _override_admin
    app.dependency_overrides[deps.get_db] = _override_db

    response = TestClient(app).patch(
        "/api/v1/placement-opportunities/admin/interviews/33",
        json={
            "status": "selected",
            "notes": "Cleared technical panel.",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "selected"
    interview_id, payload, user_id = (
        _FakePlacementOpportunityService.updated_interview_payload
    )
    assert interview_id == 33
    assert payload.status == "selected"
    assert payload.notes == "Cleared technical panel."
    assert user_id == 7


def test_admin_can_update_application_offer(monkeypatch) -> None:
    monkeypatch.setattr(
        placement_routes,
        "PlacementOpportunityService",
        _FakePlacementOpportunityService,
    )
    app.dependency_overrides[deps.get_current_admin] = _override_admin
    app.dependency_overrides[deps.get_db] = _override_db

    response = TestClient(app).patch(
        "/api/v1/placement-opportunities/admin/applications/9/offer",
        json={
            "offer_status": "offered",
            "offer_role": "Associate Software Engineer",
            "offer_package": "6.5 LPA",
            "offer_location": "Bhopal",
            "offer_joining_date": "2026-07-01T09:00:00Z",
            "offer_notes": "Offer letter pending final HR upload.",
            "next_step": "Confirm offer acceptance with placement cell.",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "offer_made"
    assert response.json()["offer_status"] == "offered"
    assert response.json()["offer_package"] == "6.5 LPA"
    application_id, payload, user_id = _FakePlacementOpportunityService.updated_offer_payload
    assert application_id == 9
    assert payload.offer_status == "offered"
    assert payload.offer_role == "Associate Software Engineer"
    assert user_id == 7


def test_admin_can_export_applications_csv(monkeypatch) -> None:
    monkeypatch.setattr(
        placement_routes,
        "PlacementOpportunityService",
        _FakePlacementOpportunityService,
    )
    app.dependency_overrides[deps.get_current_admin] = _override_admin
    app.dependency_overrides[deps.get_db] = _override_db

    response = TestClient(app).get(
        "/api/v1/placement-opportunities/admin/applications/export.csv"
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "Backend Intern" in response.text
    assert "Student One" in response.text


def test_admin_can_list_activity_and_upcoming_actions(monkeypatch) -> None:
    monkeypatch.setattr(
        placement_routes,
        "PlacementOpportunityService",
        _FakePlacementOpportunityService,
    )
    app.dependency_overrides[deps.get_current_admin] = _override_admin
    app.dependency_overrides[deps.get_db] = _override_db
    client = TestClient(app)

    activity = client.get("/api/v1/placement-opportunities/admin/activity?limit=10")
    upcoming = client.get("/api/v1/placement-opportunities/admin/upcoming?limit=10")

    assert activity.status_code == 200
    assert activity.json()["total"] == 1
    assert activity.json()["items"][0]["opportunity_title"] == "Backend Intern"
    assert upcoming.status_code == 200
    assert upcoming.json()["items"][0]["due_at"].startswith("2026-06-05T10:30:00")


def test_admin_applications_export_passes_filters(monkeypatch) -> None:
    monkeypatch.setattr(
        placement_routes,
        "PlacementOpportunityService",
        _FakePlacementOpportunityService,
    )
    app.dependency_overrides[deps.get_current_admin] = _override_admin
    app.dependency_overrides[deps.get_db] = _override_db

    response = TestClient(app).get(
        "/api/v1/placement-opportunities/admin/applications/export.csv"
        "?opportunity_id=5&status=applied"
    )

    assert response.status_code == 200
    assert _FakePlacementOpportunityService.exported_application_filters == {
        "opportunity_id": 5,
        "status": "applied",
    }


def test_admin_opportunities_export_passes_filters(monkeypatch) -> None:
    monkeypatch.setattr(
        placement_routes,
        "PlacementOpportunityService",
        _FakePlacementOpportunityService,
    )
    app.dependency_overrides[deps.get_current_admin] = _override_admin
    app.dependency_overrides[deps.get_db] = _override_db

    response = TestClient(app).get(
        "/api/v1/placement-opportunities/admin/export.csv"
        "?status=active&opportunity_type=internship"
    )

    assert response.status_code == 200
    assert _FakePlacementOpportunityService.exported_opportunity_filters == {
        "status": "active",
        "opportunity_type": "internship",
    }
