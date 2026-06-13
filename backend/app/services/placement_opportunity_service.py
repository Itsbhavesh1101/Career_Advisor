from __future__ import annotations

import csv
from datetime import datetime, timezone
from io import StringIO
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

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
    PlacementActivityEventListRead,
    PlacementActivityEventRead,
    PlacementApplicationCreate,
    PlacementApplicationBulkShortlistCreate,
    PlacementApplicationBulkStatusUpdate,
    PlacementApplicationListRead,
    PlacementApplicationRead,
    PlacementApplicationStudentUpdate,
    PlacementApplicationUpdate,
    PlacementCompanyCreate,
    PlacementCompanyListRead,
    PlacementCompanyRead,
    PlacementCompanyStatus,
    PlacementCompanyUpdate,
    PlacementEligibleStudentListRead,
    PlacementEligibleStudentRead,
    PlacementInterviewRoundCreate,
    PlacementInterviewRoundRead,
    PlacementInterviewRoundUpdate,
    PlacementOfferUpdate,
    PlacementOpportunityCreate,
    PlacementOpportunityListRead,
    PlacementOpportunityRead,
    PlacementOpportunityStatus,
    PlacementOpportunityType,
    PlacementOpportunityUpdate,
    PlacementUpcomingActionListRead,
    PlacementUpcomingActionRead,
)
from app.services.notification_service import NotificationService

_FINAL_APPLICATION_STATUSES = {"placed", "joined", "not_selected", "withdrawn"}
_OFFER_STATUS_TO_APPLICATION_STATUS = {
    "offered": "offer_made",
    "accepted": "placed",
    "declined": "withdrawn",
    "withdrawn": "withdrawn",
}
_INTERVIEW_STATUS_TO_APPLICATION_UPDATE = {
    "selected": ("shortlisted", "Cleared interview round."),
    "rejected": ("not_selected", "Placement process closed for this drive."),
    "no_show": ("not_selected", "Placement process closed for this drive."),
    "rescheduled": ("interview_scheduled", "Attend the rescheduled interview round."),
    "hold": ("interview_scheduled", "Await placement-cell update for this round."),
}


class PlacementOpportunityService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_admin_companies(
        self,
        *,
        status: PlacementCompanyStatus | None = None,
        q: str | None = None,
    ) -> PlacementCompanyListRead:
        stmt: Select[tuple[PlacementCompany]] = select(PlacementCompany)
        count_stmt = select(func.count(PlacementCompany.id))
        if status:
            stmt = stmt.where(PlacementCompany.status == status)
            count_stmt = count_stmt.where(PlacementCompany.status == status)
        if q:
            pattern = f"%{q.strip()}%"
            stmt = stmt.where(PlacementCompany.name.ilike(pattern))
            count_stmt = count_stmt.where(PlacementCompany.name.ilike(pattern))
        stmt = stmt.order_by(PlacementCompany.status, PlacementCompany.name)
        rows = self.db.scalars(stmt).all()
        return PlacementCompanyListRead(
            items=[self._company_read(row) for row in rows],
            total=int(self.db.scalar(count_stmt) or 0),
        )

    def create_company(
        self,
        payload: PlacementCompanyCreate,
        *,
        user_id: int,
    ) -> PlacementCompanyRead:
        row = PlacementCompany(
            **payload.model_dump(),
            created_by_user_id=user_id,
            updated_by_user_id=user_id,
        )
        self.db.add(row)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("Placement company already exists") from exc
        self.db.refresh(row)
        return self._company_read(row)

    def update_company(
        self,
        company_id: int,
        payload: PlacementCompanyUpdate,
        *,
        user_id: int,
    ) -> PlacementCompanyRead:
        row = self._get_company(company_id)
        changes = payload.model_dump(exclude_unset=True)
        for key, value in changes.items():
            setattr(row, key, value)
        row.updated_by_user_id = user_id
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("Placement company already exists") from exc
        self.db.refresh(row)
        return self._company_read(row)

    def archive_company(self, company_id: int, *, user_id: int) -> PlacementCompanyRead:
        return self.update_company(
            company_id,
            PlacementCompanyUpdate(status="archived"),
            user_id=user_id,
        )

    def list_admin_opportunities(
        self,
        *,
        status: PlacementOpportunityStatus | None = None,
        opportunity_type: PlacementOpportunityType | None = None,
    ) -> PlacementOpportunityListRead:
        stmt: Select[tuple[PlacementOpportunity]] = select(PlacementOpportunity)
        count_stmt = select(func.count(PlacementOpportunity.id))
        if status:
            stmt = stmt.where(PlacementOpportunity.status == status)
            count_stmt = count_stmt.where(PlacementOpportunity.status == status)
        if opportunity_type:
            stmt = stmt.where(PlacementOpportunity.opportunity_type == opportunity_type)
            count_stmt = count_stmt.where(
                PlacementOpportunity.opportunity_type == opportunity_type
            )
        stmt = stmt.order_by(
            PlacementOpportunity.status,
            PlacementOpportunity.deadline_at.is_(None),
            PlacementOpportunity.deadline_at,
            PlacementOpportunity.company,
            PlacementOpportunity.title,
        )
        rows = self.db.scalars(stmt).all()
        return PlacementOpportunityListRead(
            items=[self._opportunity_read(row) for row in rows],
            total=int(self.db.scalar(count_stmt) or 0),
        )

    def create_opportunity(
        self,
        payload: PlacementOpportunityCreate,
        *,
        user_id: int,
    ) -> PlacementOpportunityRead:
        if payload.company_id is not None:
            self._get_company(payload.company_id)
        row = PlacementOpportunity(
            **payload.model_dump(),
            created_by_user_id=user_id,
            updated_by_user_id=user_id,
        )
        self.db.add(row)
        self.db.flush()
        self._record_activity(
            event_type="opportunity_created",
            title="Opportunity published",
            message=f"{row.title} was added for {row.company}.",
            opportunity_id=row.id,
            company_id=row.company_id,
            actor_user_id=user_id,
            metadata={"status": row.status, "type": row.opportunity_type},
        )
        self.db.commit()
        self.db.refresh(row)
        return self._opportunity_read(row)

    def update_opportunity(
        self,
        opportunity_id: int,
        payload: PlacementOpportunityUpdate,
        *,
        user_id: int,
    ) -> PlacementOpportunityRead:
        row = self._get_opportunity(opportunity_id)
        changes = payload.model_dump(exclude_unset=True)
        if "company_id" in changes and changes["company_id"] is not None:
            self._get_company(int(changes["company_id"]))
        for key, value in changes.items():
            setattr(row, key, value)
        row.updated_by_user_id = user_id
        self._record_activity(
            event_type="opportunity_updated",
            title="Opportunity updated",
            message=f"{row.title} was updated.",
            opportunity_id=row.id,
            company_id=row.company_id,
            actor_user_id=user_id,
            metadata={"status": row.status, "type": row.opportunity_type},
        )
        self.db.commit()
        self.db.refresh(row)
        return self._opportunity_read(row)

    def list_student_opportunities(
        self,
        *,
        profile_id: int,
        user: User,
    ) -> PlacementOpportunityListRead:
        profile = self._get_user_profile(profile_id, user.id)
        now = datetime.now(timezone.utc)
        rows = self.db.scalars(
            select(PlacementOpportunity)
            .where(PlacementOpportunity.status == "active")
            .order_by(
                PlacementOpportunity.deadline_at.is_(None),
                PlacementOpportunity.deadline_at,
                PlacementOpportunity.company,
                PlacementOpportunity.title,
            )
        ).all()
        applications = self._applications_for_profile(profile.id)
        items: list[PlacementOpportunityRead] = []
        for row in rows:
            if row.deadline_at and _to_aware(row.deadline_at) < now:
                continue
            if not _eligible_for_profile(row.eligibility, profile):
                continue
            items.append(
                self._opportunity_read(
                    row,
                    profile=profile,
                    application_status=applications.get(row.id),
                )
            )
        return PlacementOpportunityListRead(items=items, total=len(items))

    def apply_to_opportunity(
        self,
        opportunity_id: int,
        payload: PlacementApplicationCreate,
        *,
        user: User,
    ) -> PlacementApplicationRead:
        opportunity = self._get_opportunity(opportunity_id)
        if opportunity.status != "active":
            raise ValueError("Opportunity is not active")
        profile = self._get_user_profile(payload.profile_id, user.id)
        if not _eligible_for_profile(opportunity.eligibility, profile):
            raise ValueError("Profile is not eligible for this opportunity")
        row = PlacementApplication(
            opportunity_id=opportunity.id,
            profile_id=profile.id,
            user_id=user.id,
            status=payload.status,
            interest_note=payload.interest_note,
        )
        self.db.add(row)
        try:
            self.db.flush()
            self._record_activity(
                event_type="application_created",
                title=f"Application {payload.status}",
                message=f"{profile.name} marked {payload.status} for {opportunity.title}.",
                opportunity_id=opportunity.id,
                application_id=row.id,
                profile_id=profile.id,
                company_id=opportunity.company_id,
                actor_user_id=user.id,
                metadata={"status": payload.status},
            )
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("Placement application already exists") from exc
        self.db.refresh(row)
        return self._application_read(row)

    def list_student_applications(
        self,
        *,
        profile_id: int,
        user: User,
    ) -> PlacementApplicationListRead:
        profile = self._get_user_profile(profile_id, user.id)
        rows = self.db.scalars(
            select(PlacementApplication)
            .where(PlacementApplication.profile_id == profile.id)
            .order_by(PlacementApplication.created_at.desc())
        ).all()
        return PlacementApplicationListRead(
            items=[self._application_read(row) for row in rows],
            total=len(rows),
        )

    def update_student_application(
        self,
        application_id: int,
        payload: PlacementApplicationStudentUpdate,
        *,
        user: User,
    ) -> PlacementApplicationRead:
        row = self.db.get(PlacementApplication, application_id)
        if row is None or row.user_id != user.id:
            raise ValueError("Placement application not found")
        if row.status == "placed" or row.status == "not_selected":
            raise ValueError("Placement application is already finalized")
        if row.status == "shortlisted" and payload.status != "withdrawn":
            raise ValueError("Shortlisted applications can only be withdrawn")
        previous_status = row.status
        row.status = payload.status
        row.interest_note = payload.interest_note
        self._record_activity(
            event_type="student_application_updated",
            title=f"Student marked {payload.status}",
            message=f"Student updated application status from {previous_status} to {payload.status}.",
            opportunity_id=row.opportunity_id,
            application_id=row.id,
            profile_id=row.profile_id,
            actor_user_id=user.id,
            metadata={"previous_status": previous_status, "status": payload.status},
        )
        self.db.commit()
        self.db.refresh(row)
        return self._application_read(row)

    def list_admin_applications(
        self,
        *,
        opportunity_id: int | None = None,
        status: str | None = None,
    ) -> PlacementApplicationListRead:
        stmt: Select[tuple[PlacementApplication]] = select(PlacementApplication)
        count_stmt = select(func.count(PlacementApplication.id))
        if opportunity_id is not None:
            stmt = stmt.where(PlacementApplication.opportunity_id == opportunity_id)
            count_stmt = count_stmt.where(
                PlacementApplication.opportunity_id == opportunity_id
            )
        if status:
            stmt = stmt.where(PlacementApplication.status == status)
            count_stmt = count_stmt.where(PlacementApplication.status == status)
        stmt = stmt.order_by(PlacementApplication.created_at.desc())
        rows = self.db.scalars(stmt).all()
        return PlacementApplicationListRead(
            items=[self._application_read(row) for row in rows],
            total=int(self.db.scalar(count_stmt) or 0),
        )

    def list_admin_activity(
        self,
        *,
        opportunity_id: int | None = None,
        limit: int = 50,
    ) -> PlacementActivityEventListRead:
        stmt: Select[tuple[PlacementActivityEvent]] = select(PlacementActivityEvent)
        count_stmt = select(func.count(PlacementActivityEvent.id))
        if opportunity_id is not None:
            stmt = stmt.where(PlacementActivityEvent.opportunity_id == opportunity_id)
            count_stmt = count_stmt.where(
                PlacementActivityEvent.opportunity_id == opportunity_id
            )
        stmt = stmt.order_by(
            PlacementActivityEvent.created_at.desc(),
            PlacementActivityEvent.id.desc(),
        ).limit(limit)
        rows = self.db.scalars(stmt).all()
        return PlacementActivityEventListRead(
            items=[self._activity_read(row) for row in rows],
            total=int(self.db.scalar(count_stmt) or 0),
        )

    def list_student_activity(
        self,
        *,
        profile_id: int,
        user: User,
        limit: int = 50,
    ) -> PlacementActivityEventListRead:
        profile = self._get_user_profile(profile_id, user.id)
        stmt = (
            select(PlacementActivityEvent)
            .where(PlacementActivityEvent.profile_id == profile.id)
            .order_by(
                PlacementActivityEvent.created_at.desc(),
                PlacementActivityEvent.id.desc(),
            )
            .limit(limit)
        )
        count_stmt = select(func.count(PlacementActivityEvent.id)).where(
            PlacementActivityEvent.profile_id == profile.id
        )
        rows = self.db.scalars(stmt).all()
        return PlacementActivityEventListRead(
            items=[self._activity_read(row) for row in rows],
            total=int(self.db.scalar(count_stmt) or 0),
        )

    def list_admin_upcoming_actions(
        self,
        *,
        limit: int = 50,
    ) -> PlacementUpcomingActionListRead:
        items = self._upcoming_actions()
        return PlacementUpcomingActionListRead(items=items[:limit], total=len(items))

    def list_student_upcoming_actions(
        self,
        *,
        profile_id: int,
        user: User,
        limit: int = 50,
    ) -> PlacementUpcomingActionListRead:
        profile = self._get_user_profile(profile_id, user.id)
        items = [
            item
            for item in self._upcoming_actions(profile_id=profile.id)
            if item.profile_id in (None, profile.id)
        ]
        return PlacementUpcomingActionListRead(items=items[:limit], total=len(items))

    def list_eligible_students_for_opportunity(
        self,
        opportunity_id: int,
    ) -> PlacementEligibleStudentListRead:
        opportunity = self._get_opportunity(opportunity_id)
        applications = {
            row.profile_id: row
            for row in self.db.scalars(
                select(PlacementApplication).where(
                    PlacementApplication.opportunity_id == opportunity.id
                )
            ).all()
        }
        profiles = self.db.scalars(
            select(StudentProfile).order_by(StudentProfile.name, StudentProfile.id)
        ).all()
        items: list[PlacementEligibleStudentRead] = []
        for profile in profiles:
            if not _eligible_for_profile(opportunity.eligibility, profile):
                continue
            score, matched = _match_profile(
                opportunity.required_skills,
                profile.current_skills,
            )
            missing = _missing_skills(
                opportunity.required_skills,
                profile.current_skills,
            )
            user = self.db.get(User, profile.user_id)
            application = applications.get(profile.id)
            items.append(
                PlacementEligibleStudentRead(
                    profile_id=profile.id,
                    student_name=profile.name,
                    student_email=user.email if user else None,
                    specialization=profile.specialization,
                    cgpa=profile.cgpa,
                    current_skills=profile.current_skills,
                    match_score=score,
                    matched_skills=matched,
                    missing_skills=missing,
                    application_id=application.id if application else None,
                    application_status=application.status if application else None,
                )
            )
        return PlacementEligibleStudentListRead(items=items, total=len(items))

    def bulk_shortlist_eligible_students(
        self,
        opportunity_id: int,
        payload: PlacementApplicationBulkShortlistCreate,
        *,
        user_id: int,
    ) -> PlacementApplicationListRead:
        opportunity = self._get_opportunity(opportunity_id)
        changes = payload.model_dump(exclude_unset=True)
        items: list[PlacementApplication] = []
        for profile_id in payload.profile_ids:
            profile = self.db.get(StudentProfile, profile_id)
            if profile is None:
                raise ValueError("Profile not found")
            if not _eligible_for_profile(opportunity.eligibility, profile):
                raise ValueError(f"Profile {profile_id} is not eligible for this opportunity")
            row = self.db.scalar(
                select(PlacementApplication).where(
                    PlacementApplication.opportunity_id == opportunity.id,
                    PlacementApplication.profile_id == profile.id,
                )
            )
            if row is not None and row.status in _FINAL_APPLICATION_STATUSES:
                raise ValueError(
                    f"Placement application {row.id} is already finalized"
                )
            if row is None:
                row = PlacementApplication(
                    opportunity_id=opportunity.id,
                    profile_id=profile.id,
                    user_id=profile.user_id,
                    status="shortlisted",
                )
                self.db.add(row)
            row.status = "shortlisted"
            if "admin_notes" in changes:
                row.admin_notes = payload.admin_notes
            if "next_step" in changes:
                row.next_step = payload.next_step
            if "next_step_due_at" in changes:
                row.next_step_due_at = payload.next_step_due_at
            items.append(row)
        self.db.flush()
        for row in items:
            self._record_activity(
                event_type="application_shortlisted",
                title="Student shortlisted",
                message=f"Student profile {row.profile_id} was shortlisted for this drive.",
                opportunity_id=row.opportunity_id,
                application_id=row.id,
                profile_id=row.profile_id,
                actor_user_id=user_id,
                metadata={"status": row.status},
                notify_profile=True,
            )
        self.db.commit()
        for row in items:
            self.db.refresh(row)
        return PlacementApplicationListRead(
            items=[self._application_read(row) for row in items],
            total=len(items),
        )

    def update_application_status(
        self,
        application_id: int,
        payload: PlacementApplicationUpdate,
        *,
        user_id: int,
    ) -> PlacementApplicationRead:
        row = self.db.get(PlacementApplication, application_id)
        if row is None:
            raise ValueError("Placement application not found")
        for key, value in payload.model_dump().items():
            setattr(row, key, value)
        self._record_activity(
            event_type="application_status_updated",
            title=f"Application moved to {payload.status}",
            message=f"Placement-cell updated application {row.id} to {payload.status}.",
            opportunity_id=row.opportunity_id,
            application_id=row.id,
            profile_id=row.profile_id,
            actor_user_id=user_id,
            metadata={"status": payload.status},
            notify_profile=True,
        )
        self.db.commit()
        self.db.refresh(row)
        return self._application_read(row)

    def bulk_update_applications(
        self,
        payload: PlacementApplicationBulkStatusUpdate,
        *,
        user_id: int,
    ) -> PlacementApplicationListRead:
        changes = payload.model_dump(exclude_unset=True)
        items: list[PlacementApplication] = []
        for application_id in payload.application_ids:
            row = self.db.get(PlacementApplication, application_id)
            if row is None:
                raise ValueError("Placement application not found")
            row.status = payload.status
            if "admin_notes" in changes:
                row.admin_notes = payload.admin_notes
            if "next_step" in changes:
                row.next_step = payload.next_step
            if "next_step_due_at" in changes:
                row.next_step_due_at = payload.next_step_due_at
            items.append(row)
        for row in items:
            self._record_activity(
                event_type="application_status_updated",
                title=f"Application moved to {payload.status}",
                message=f"Placement-cell bulk updated application {row.id} to {payload.status}.",
                opportunity_id=row.opportunity_id,
                application_id=row.id,
                profile_id=row.profile_id,
                actor_user_id=user_id,
                metadata={"status": payload.status},
                notify_profile=True,
            )
        self.db.commit()
        for row in items:
            self.db.refresh(row)
        return PlacementApplicationListRead(
            items=[self._application_read(row) for row in items],
            total=len(items),
        )

    def create_interview_round(
        self,
        application_id: int,
        payload: PlacementInterviewRoundCreate,
        *,
        user_id: int,
    ) -> PlacementApplicationRead:
        application = self.db.get(PlacementApplication, application_id)
        if application is None:
            raise ValueError("Placement application not found")
        round_row = PlacementInterviewRound(
            application_id=application.id,
            round_name=payload.round_name,
            scheduled_at=payload.scheduled_at,
            mode=payload.mode,
            location=payload.location,
            interviewer=payload.interviewer,
            notes=payload.notes,
            created_by_user_id=user_id,
            updated_by_user_id=user_id,
        )
        self.db.add(round_row)
        application.status = "interview_scheduled"
        application.next_step = payload.round_name
        application.next_step_due_at = payload.scheduled_at
        self.db.flush()
        self._record_activity(
            event_type="interview_round_scheduled",
            title="Interview scheduled",
            message=f"{payload.round_name} scheduled for application {application.id}.",
            opportunity_id=application.opportunity_id,
            application_id=application.id,
            profile_id=application.profile_id,
            actor_user_id=user_id,
            metadata={
                "interview_round_id": round_row.id,
                "round_name": payload.round_name,
                "scheduled_at": payload.scheduled_at.isoformat()
                if payload.scheduled_at
                else None,
            },
            notify_profile=True,
        )
        self.db.commit()
        self.db.refresh(application)
        return self._application_read(application)

    def update_interview_round(
        self,
        interview_id: int,
        payload: PlacementInterviewRoundUpdate,
        *,
        user_id: int,
    ) -> PlacementInterviewRoundRead:
        row = self.db.get(PlacementInterviewRound, interview_id)
        if row is None:
            raise ValueError("Placement interview round not found")
        changes = payload.model_dump(exclude_unset=True)
        for key, value in changes.items():
            setattr(row, key, value)
        row.updated_by_user_id = user_id
        application = self.db.get(PlacementApplication, row.application_id)
        if payload.status in _INTERVIEW_STATUS_TO_APPLICATION_UPDATE:
            if application is not None:
                application.status, default_next_step = (
                    _INTERVIEW_STATUS_TO_APPLICATION_UPDATE[payload.status]
                )
                if payload.notes:
                    application.admin_notes = payload.notes
                application.next_step = default_next_step
                application.next_step_due_at = row.scheduled_at
        self._record_activity(
            event_type="interview_round_updated",
            title=f"Interview {payload.status or 'updated'}",
            message=f"{row.round_name} updated for application {row.application_id}.",
            opportunity_id=application.opportunity_id if application else None,
            application_id=row.application_id,
            profile_id=application.profile_id if application else None,
            actor_user_id=user_id,
            metadata={"interview_round_id": row.id, "status": payload.status},
            notify_profile=application is not None,
        )
        self.db.commit()
        self.db.refresh(row)
        return self._interview_round_read(row)

    def update_application_offer(
        self,
        application_id: int,
        payload: PlacementOfferUpdate,
        *,
        user_id: int,
    ) -> PlacementApplicationRead:
        row = self.db.get(PlacementApplication, application_id)
        if row is None:
            raise ValueError("Placement application not found")
        changes = payload.model_dump(exclude_unset=True)
        for key in (
            "offer_status",
            "offer_role",
            "offer_package",
            "offer_location",
            "offer_joining_date",
            "offer_notes",
        ):
            if key in changes:
                setattr(row, key, changes[key])
        row.status = _OFFER_STATUS_TO_APPLICATION_STATUS[payload.offer_status]
        if "next_step" in changes:
            row.next_step = payload.next_step
        elif payload.offer_status == "offered":
            row.next_step = "Review the offer and confirm acceptance with placement cell."
        elif payload.offer_status == "accepted":
            row.next_step = "Complete joining formalities with placement cell."
        else:
            row.next_step = "Offer process closed for this drive."
        if "next_step_due_at" in changes:
            row.next_step_due_at = payload.next_step_due_at
        row.offer_updated_by_user_id = user_id
        row.offer_updated_at = datetime.now(timezone.utc)
        self._record_activity(
            event_type="application_offer_updated",
            title=f"Offer {payload.offer_status}",
            message=f"Offer status updated to {payload.offer_status} for application {row.id}.",
            opportunity_id=row.opportunity_id,
            application_id=row.id,
            profile_id=row.profile_id,
            actor_user_id=user_id,
            metadata={
                "offer_status": payload.offer_status,
                "offer_role": row.offer_role,
            },
            notify_profile=True,
        )
        self.db.commit()
        self.db.refresh(row)
        return self._application_read(row)

    def export_admin_opportunities_csv(
        self,
        *,
        status: PlacementOpportunityStatus | None = None,
        opportunity_type: PlacementOpportunityType | None = None,
    ) -> str:
        rows = self.list_admin_opportunities(
            status=status,
            opportunity_type=opportunity_type,
        ).items
        buffer = StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            [
                "id",
                "title",
                "company",
                "type",
                "status",
                "deadline_at",
                "package_label",
                "vacancies",
                "contact_name",
                "contact_email",
                "hiring_stages",
                "required_skills",
                "applicant_count",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row.id,
                    row.title,
                    row.company,
                    row.opportunity_type,
                    row.status,
                    row.deadline_at.isoformat() if row.deadline_at else "",
                    row.package_label or "",
                    row.vacancies if row.vacancies is not None else "",
                    row.contact_name or "",
                    row.contact_email or "",
                    "; ".join(row.hiring_stages),
                    "; ".join(row.required_skills),
                    row.applicant_count,
                ]
            )
        return buffer.getvalue()

    def export_admin_applications_csv(
        self,
        *,
        opportunity_id: int | None = None,
        status: str | None = None,
    ) -> str:
        rows = self.list_admin_applications(
            opportunity_id=opportunity_id,
            status=status,
        ).items
        buffer = StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            [
                "id",
                "opportunity_id",
                "opportunity_title",
                "opportunity_company",
                "opportunity_type",
                "profile_id",
                "student_name",
                "student_email",
                "status",
                "interest_note",
                "admin_notes",
                "next_step",
                "next_step_due_at",
                "offer_status",
                "offer_role",
                "offer_package",
                "offer_location",
                "offer_joining_date",
                "offer_notes",
                "interview_rounds",
                "created_at",
                "updated_at",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row.id,
                    row.opportunity_id,
                    row.opportunity_title or "",
                    row.opportunity_company or "",
                    row.opportunity_type or "",
                    row.profile_id,
                    row.student_name or "",
                    row.student_email or "",
                    row.status,
                    row.interest_note or "",
                    row.admin_notes or "",
                    row.next_step or "",
                    row.next_step_due_at.isoformat() if row.next_step_due_at else "",
                    row.offer_status or "",
                    row.offer_role or "",
                    row.offer_package or "",
                    row.offer_location or "",
                    row.offer_joining_date.isoformat()
                    if row.offer_joining_date
                    else "",
                    row.offer_notes or "",
                    _format_interview_rounds(row.interview_rounds),
                    row.created_at.isoformat(),
                    row.updated_at.isoformat(),
                ]
            )
        return buffer.getvalue()

    def _record_activity(
        self,
        *,
        event_type: str,
        title: str,
        message: str | None = None,
        opportunity_id: int | None = None,
        application_id: int | None = None,
        profile_id: int | None = None,
        company_id: int | None = None,
        actor_user_id: int | None = None,
        metadata: dict[str, Any] | None = None,
        notify_profile: bool = False,
    ) -> None:
        self.db.add(
            PlacementActivityEvent(
                event_type=event_type,
                title=title,
                message=message,
                opportunity_id=opportunity_id,
                application_id=application_id,
                profile_id=profile_id,
                company_id=company_id,
                actor_user_id=actor_user_id,
                event_metadata=metadata or {},
            )
        )
        if notify_profile and profile_id is not None:
            notification_title = title
            status_value = (metadata or {}).get("status")
            if (
                event_type == "application_status_updated"
                and status_value == "interview_scheduled"
            ):
                notification_title = "Interview scheduled"
            elif event_type == "application_shortlisted":
                notification_title = "You were shortlisted"
            NotificationService(self.db).create_for_profile(
                profile_id=profile_id,
                notification_type="placement",
                title=notification_title,
                message=message,
                action_url="/internship",
                priority="high"
                if event_type in {"application_offer_updated", "interview_round_scheduled"}
                else "normal",
                created_by_user_id=actor_user_id,
                metadata={
                    "event_type": event_type,
                    "opportunity_id": opportunity_id,
                    "application_id": application_id,
                    **(metadata or {}),
                },
                commit=False,
            )

    def _activity_read(
        self,
        row: PlacementActivityEvent,
    ) -> PlacementActivityEventRead:
        opportunity = (
            self.db.get(PlacementOpportunity, row.opportunity_id)
            if row.opportunity_id
            else None
        )
        profile = (
            self.db.get(StudentProfile, row.profile_id) if row.profile_id else None
        )
        return PlacementActivityEventRead(
            id=row.id,
            event_type=row.event_type,
            title=row.title,
            message=row.message,
            opportunity_id=row.opportunity_id,
            application_id=row.application_id,
            profile_id=row.profile_id,
            company_id=row.company_id,
            actor_user_id=row.actor_user_id,
            opportunity_title=opportunity.title if opportunity else None,
            opportunity_company=opportunity.company if opportunity else None,
            student_name=profile.name if profile else None,
            metadata=row.event_metadata or {},
            created_at=_to_aware(row.created_at),
        )

    def _upcoming_actions(
        self,
        *,
        profile_id: int | None = None,
    ) -> list[PlacementUpcomingActionRead]:
        now = datetime.now(timezone.utc)
        profile = self.db.get(StudentProfile, profile_id) if profile_id else None
        items: list[PlacementUpcomingActionRead] = []

        opportunities = self.db.scalars(
            select(PlacementOpportunity).where(
                PlacementOpportunity.status == "active",
                PlacementOpportunity.deadline_at.is_not(None),
            )
        ).all()
        for opportunity in opportunities:
            if opportunity.deadline_at is None:
                continue
            due_at = _to_aware(opportunity.deadline_at)
            if due_at < now:
                continue
            if profile is not None and not _eligible_for_profile(
                opportunity.eligibility,
                profile,
            ):
                continue
            items.append(
                PlacementUpcomingActionRead(
                    action_type="opportunity_deadline",
                    title=f"{opportunity.title} deadline",
                    due_at=due_at,
                    opportunity_id=opportunity.id,
                    profile_id=profile.id if profile else None,
                    opportunity_title=opportunity.title,
                    opportunity_company=opportunity.company,
                    status=opportunity.status,
                )
            )

        application_stmt = select(PlacementApplication).where(
            PlacementApplication.next_step_due_at.is_not(None)
        )
        if profile is not None:
            application_stmt = application_stmt.where(
                PlacementApplication.profile_id == profile.id
            )
        applications = self.db.scalars(application_stmt).all()
        for application in applications:
            if not application.next_step_due_at:
                continue
            due_at = _to_aware(application.next_step_due_at)
            if due_at < now or application.status in _FINAL_APPLICATION_STATUSES:
                continue
            opportunity = self.db.get(PlacementOpportunity, application.opportunity_id)
            profile_row = self.db.get(StudentProfile, application.profile_id)
            items.append(
                PlacementUpcomingActionRead(
                    action_type="application_next_step",
                    title=application.next_step or "Placement-cell next step",
                    due_at=due_at,
                    opportunity_id=application.opportunity_id,
                    application_id=application.id,
                    profile_id=application.profile_id,
                    opportunity_title=opportunity.title if opportunity else None,
                    opportunity_company=opportunity.company if opportunity else None,
                    student_name=profile_row.name if profile_row else None,
                    status=application.status,
                )
            )

        interview_stmt = select(PlacementInterviewRound).where(
            PlacementInterviewRound.scheduled_at.is_not(None)
        )
        if profile is not None:
            interview_stmt = interview_stmt.join(
                PlacementApplication,
                PlacementApplication.id == PlacementInterviewRound.application_id,
            ).where(PlacementApplication.profile_id == profile.id)
        interviews = self.db.scalars(interview_stmt).all()
        for interview in interviews:
            if not interview.scheduled_at:
                continue
            due_at = _to_aware(interview.scheduled_at)
            if due_at < now or interview.status not in {"scheduled", "rescheduled"}:
                continue
            application = self.db.get(PlacementApplication, interview.application_id)
            opportunity = (
                self.db.get(PlacementOpportunity, application.opportunity_id)
                if application
                else None
            )
            profile_row = (
                self.db.get(StudentProfile, application.profile_id)
                if application
                else None
            )
            items.append(
                PlacementUpcomingActionRead(
                    action_type="interview_round",
                    title=interview.round_name,
                    due_at=due_at,
                    opportunity_id=application.opportunity_id if application else None,
                    application_id=application.id if application else None,
                    profile_id=application.profile_id if application else None,
                    interview_round_id=interview.id,
                    opportunity_title=opportunity.title if opportunity else None,
                    opportunity_company=opportunity.company if opportunity else None,
                    student_name=profile_row.name if profile_row else None,
                    status=interview.status,
                )
            )

        offer_stmt = select(PlacementApplication).where(
            PlacementApplication.offer_joining_date.is_not(None),
            PlacementApplication.offer_status.in_(["offered", "accepted"]),
        )
        if profile is not None:
            offer_stmt = offer_stmt.where(PlacementApplication.profile_id == profile.id)
        offer_applications = self.db.scalars(offer_stmt).all()
        for application in offer_applications:
            if not application.offer_joining_date:
                continue
            due_at = _to_aware(application.offer_joining_date)
            if due_at < now:
                continue
            opportunity = self.db.get(PlacementOpportunity, application.opportunity_id)
            profile_row = self.db.get(StudentProfile, application.profile_id)
            role = application.offer_role or (
                opportunity.title if opportunity else "Offer"
            )
            items.append(
                PlacementUpcomingActionRead(
                    action_type="offer_joining",
                    title=f"{role} joining",
                    due_at=due_at,
                    opportunity_id=application.opportunity_id,
                    application_id=application.id,
                    profile_id=application.profile_id,
                    opportunity_title=opportunity.title if opportunity else None,
                    opportunity_company=opportunity.company if opportunity else None,
                    student_name=profile_row.name if profile_row else None,
                    status=application.offer_status,
                )
            )

        return sorted(items, key=lambda item: (item.due_at, item.action_type, item.title))

    def _get_opportunity(self, opportunity_id: int) -> PlacementOpportunity:
        row = self.db.get(PlacementOpportunity, opportunity_id)
        if row is None:
            raise ValueError("Placement opportunity not found")
        return row

    def _get_company(self, company_id: int) -> PlacementCompany:
        row = self.db.get(PlacementCompany, company_id)
        if row is None:
            raise ValueError("Placement company not found")
        return row

    def _company_read(self, row: PlacementCompany) -> PlacementCompanyRead:
        data = PlacementCompanyRead.model_validate(row).model_dump()
        data["active_opportunity_count"] = int(
            self.db.scalar(
                select(func.count(PlacementOpportunity.id)).where(
                    PlacementOpportunity.company_id == row.id,
                    PlacementOpportunity.status == "active",
                )
            )
            or 0
        )
        return PlacementCompanyRead.model_validate(data)

    def _get_user_profile(self, profile_id: int, user_id: int) -> StudentProfile:
        profile = self.db.get(StudentProfile, profile_id)
        if profile is None or profile.user_id != user_id:
            raise ValueError("Profile not found")
        return profile

    def _applications_for_profile(self, profile_id: int) -> dict[int, str]:
        rows = self.db.scalars(
            select(PlacementApplication).where(
                PlacementApplication.profile_id == profile_id
            )
        ).all()
        return {row.opportunity_id: row.status for row in rows}

    def _opportunity_read(
        self,
        row: PlacementOpportunity,
        *,
        profile: StudentProfile | None = None,
        application_status: str | None = None,
    ) -> PlacementOpportunityRead:
        data = PlacementOpportunityRead.model_validate(row).model_dump()
        data["applicant_count"] = int(
            self.db.scalar(
                select(func.count(PlacementApplication.id)).where(
                    PlacementApplication.opportunity_id == row.id
                )
            )
            or 0
        )
        if profile is not None:
            score, matched = _match_profile(row.required_skills, profile.current_skills)
            data["match_score"] = score
            data["matched_skills"] = matched
            data["application_status"] = application_status
        if row.company_id is not None:
            company = self.db.get(PlacementCompany, row.company_id)
            data["company_master_name"] = company.name if company else None
        return PlacementOpportunityRead.model_validate(data)

    def _application_read(self, row: PlacementApplication) -> PlacementApplicationRead:
        data = PlacementApplicationRead.model_validate(row).model_dump()
        profile = self.db.get(StudentProfile, row.profile_id)
        user = self.db.get(User, row.user_id)
        opportunity = self.db.get(PlacementOpportunity, row.opportunity_id)
        data["student_name"] = profile.name if profile else None
        data["student_email"] = user.email if user else None
        data["opportunity_title"] = opportunity.title if opportunity else None
        data["opportunity_company"] = opportunity.company if opportunity else None
        data["next_step_due_at"] = (
            _to_aware(row.next_step_due_at) if row.next_step_due_at else None
        )
        data["offer_joining_date"] = (
            _to_aware(row.offer_joining_date) if row.offer_joining_date else None
        )
        data["offer_updated_at"] = (
            _to_aware(row.offer_updated_at) if row.offer_updated_at else None
        )
        data["opportunity_type"] = (
            opportunity.opportunity_type if opportunity else None
        )
        data["interview_rounds"] = [
            self._interview_round_read(interview).model_dump()
            for interview in self._application_interview_rounds(row.id)
        ]
        return PlacementApplicationRead.model_validate(data)

    def _application_interview_rounds(
        self,
        application_id: int,
    ) -> list[PlacementInterviewRound]:
        return self.db.scalars(
            select(PlacementInterviewRound)
            .where(PlacementInterviewRound.application_id == application_id)
            .order_by(
                PlacementInterviewRound.scheduled_at.is_(None),
                PlacementInterviewRound.scheduled_at,
                PlacementInterviewRound.created_at,
                PlacementInterviewRound.id,
            )
        ).all()

    def _interview_round_read(
        self,
        row: PlacementInterviewRound,
    ) -> PlacementInterviewRoundRead:
        data = PlacementInterviewRoundRead.model_validate(row).model_dump()
        data["scheduled_at"] = _to_aware(row.scheduled_at) if row.scheduled_at else None
        return PlacementInterviewRoundRead.model_validate(data)


def _match_profile(
    required_skills: list[str], profile_skills: list[str]
) -> tuple[int, list[str]]:
    required = [_normalize_skill(skill) for skill in required_skills if skill]
    profile = {_normalize_skill(skill): skill for skill in profile_skills if skill}
    if not required:
        return 100, []
    matched = [profile[skill] for skill in required if skill in profile]
    score = round((len(matched) / len(required)) * 100)
    return score, matched


def _missing_skills(required_skills: list[str], profile_skills: list[str]) -> list[str]:
    profile = {_normalize_skill(skill) for skill in profile_skills if skill}
    missing: list[str] = []
    for skill in required_skills:
        if _normalize_skill(skill) not in profile:
            missing.append(skill)
    return missing


def _eligible_for_profile(
    eligibility: dict[str, Any] | None, profile: StudentProfile
) -> bool:
    eligibility = eligibility or {}
    student_types = _string_list(eligibility.get("student_types"))
    profile_type = profile.user_type or "college_student"
    if student_types and profile_type not in student_types:
        return False
    min_cgpa = _number_or_none(eligibility.get("min_cgpa"))
    if min_cgpa is not None and float(profile.cgpa or 0) < min_cgpa:
        return False
    specializations = [
        _normalize_skill(item)
        for item in _string_list(eligibility.get("specializations"))
    ]
    if specializations and _normalize_skill(profile.specialization) not in specializations:
        return False
    return True


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def _number_or_none(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_skill(value: str | None) -> str:
    return (value or "").strip().lower()


def _to_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _format_interview_rounds(rounds: list[Any]) -> str:
    labels: list[str] = []
    for item in rounds:
        round_name = getattr(item, "round_name", None) or ""
        status = getattr(item, "status", None) or ""
        scheduled_at = getattr(item, "scheduled_at", None)
        when = scheduled_at.isoformat() if scheduled_at else ""
        parts = [part for part in [round_name, status, when] if part]
        if parts:
            labels.append(" / ".join(parts))
    return "; ".join(labels)
