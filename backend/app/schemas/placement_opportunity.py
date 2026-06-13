from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

PlacementOpportunityType = Literal["placement", "internship"]
PlacementOpportunityStatus = Literal["draft", "active", "closed", "archived"]
PlacementCompanyStatus = Literal["active", "archived"]
PlacementApplicationStatus = Literal[
    "interested",
    "applied",
    "screening",
    "interview_scheduled",
    "shortlisted",
    "offer_made",
    "not_selected",
    "placed",
    "joined",
    "withdrawn",
]
PlacementInterviewStatus = Literal[
    "scheduled",
    "completed",
    "cancelled",
    "selected",
    "rejected",
    "hold",
    "no_show",
    "rescheduled",
]
PlacementOfferStatus = Literal["offered", "accepted", "declined", "withdrawn"]
PlacementUpcomingActionType = Literal[
    "application_next_step",
    "opportunity_deadline",
    "interview_round",
    "offer_joining",
]


def _clean_list(values: list[str] | None) -> list[str]:
    if not values:
        return []
    return [item.strip() for item in values if item and item.strip()]


class PlacementOpportunityBase(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(min_length=2, max_length=220)
    company: str = Field(min_length=2, max_length=220)
    company_id: int | None = None
    opportunity_type: PlacementOpportunityType = "placement"
    status: PlacementOpportunityStatus = "active"
    description: str | None = Field(default=None, max_length=5000)
    location: str | None = Field(default=None, max_length=200)
    work_mode: str | None = Field(default=None, max_length=40)
    deadline_at: datetime | None = None
    eligibility: dict[str, Any] = Field(default_factory=dict)
    required_skills: list[str] = Field(default_factory=list)
    apply_url: str | None = Field(default=None, max_length=500)
    package_label: str | None = Field(default=None, max_length=120)
    vacancies: int | None = Field(default=None, ge=0, le=10000)
    contact_name: str | None = Field(default=None, max_length=160)
    contact_email: str | None = Field(default=None, max_length=254)
    hiring_stages: list[str] = Field(default_factory=list)

    @field_validator("required_skills")
    @classmethod
    def _normalize_skills(cls, value: list[str]) -> list[str]:
        return _clean_list(value)

    @field_validator("hiring_stages")
    @classmethod
    def _normalize_hiring_stages(cls, value: list[str]) -> list[str]:
        return _clean_list(value)


class PlacementOpportunityCreate(PlacementOpportunityBase):
    pass


class PlacementOpportunityUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str | None = Field(default=None, min_length=2, max_length=220)
    company: str | None = Field(default=None, min_length=2, max_length=220)
    company_id: int | None = None
    opportunity_type: PlacementOpportunityType | None = None
    status: PlacementOpportunityStatus | None = None
    description: str | None = Field(default=None, max_length=5000)
    location: str | None = Field(default=None, max_length=200)
    work_mode: str | None = Field(default=None, max_length=40)
    deadline_at: datetime | None = None
    eligibility: dict[str, Any] | None = None
    required_skills: list[str] | None = None
    apply_url: str | None = Field(default=None, max_length=500)
    package_label: str | None = Field(default=None, max_length=120)
    vacancies: int | None = Field(default=None, ge=0, le=10000)
    contact_name: str | None = Field(default=None, max_length=160)
    contact_email: str | None = Field(default=None, max_length=254)
    hiring_stages: list[str] | None = None

    @field_validator("required_skills")
    @classmethod
    def _normalize_skills(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        return _clean_list(value)

    @field_validator("hiring_stages")
    @classmethod
    def _normalize_hiring_stages(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        return _clean_list(value)


class PlacementOpportunityRead(PlacementOpportunityBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_by_user_id: int | None = None
    updated_by_user_id: int | None = None
    created_at: datetime
    updated_at: datetime
    applicant_count: int = 0
    match_score: int | None = None
    matched_skills: list[str] = Field(default_factory=list)
    application_status: PlacementApplicationStatus | None = None
    company_master_name: str | None = None


class PlacementOpportunityListRead(BaseModel):
    items: list[PlacementOpportunityRead]
    total: int


class PlacementCompanyBase(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=2, max_length=220)
    status: PlacementCompanyStatus = "active"
    website: str | None = Field(default=None, max_length=500)
    industry: str | None = Field(default=None, max_length=160)
    location: str | None = Field(default=None, max_length=200)
    contact_name: str | None = Field(default=None, max_length=160)
    contact_email: str | None = Field(default=None, max_length=254)
    notes: str | None = Field(default=None, max_length=5000)


class PlacementCompanyCreate(PlacementCompanyBase):
    pass


class PlacementCompanyUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=2, max_length=220)
    status: PlacementCompanyStatus | None = None
    website: str | None = Field(default=None, max_length=500)
    industry: str | None = Field(default=None, max_length=160)
    location: str | None = Field(default=None, max_length=200)
    contact_name: str | None = Field(default=None, max_length=160)
    contact_email: str | None = Field(default=None, max_length=254)
    notes: str | None = Field(default=None, max_length=5000)


class PlacementCompanyRead(PlacementCompanyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_by_user_id: int | None = None
    updated_by_user_id: int | None = None
    created_at: datetime
    updated_at: datetime
    active_opportunity_count: int = 0


class PlacementCompanyListRead(BaseModel):
    items: list[PlacementCompanyRead]
    total: int


class PlacementApplicationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    profile_id: int
    status: Literal["interested", "applied"] = "interested"
    interest_note: str | None = Field(default=None, max_length=2000)


class PlacementApplicationUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    status: PlacementApplicationStatus
    admin_notes: str | None = Field(default=None, max_length=3000)
    next_step: str | None = Field(default=None, max_length=500)
    next_step_due_at: datetime | None = None


class PlacementApplicationBulkShortlistCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    profile_ids: list[int] = Field(min_length=1, max_length=500)
    admin_notes: str | None = Field(default=None, max_length=3000)
    next_step: str | None = Field(default=None, max_length=500)
    next_step_due_at: datetime | None = None

    @field_validator("profile_ids")
    @classmethod
    def _dedupe_profile_ids(cls, value: list[int]) -> list[int]:
        seen: set[int] = set()
        ordered: list[int] = []
        for profile_id in value:
            if profile_id <= 0:
                raise ValueError("Profile ids must be positive")
            if profile_id not in seen:
                seen.add(profile_id)
                ordered.append(profile_id)
        return ordered


class PlacementApplicationBulkStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    application_ids: list[int] = Field(min_length=1, max_length=500)
    status: PlacementApplicationStatus
    admin_notes: str | None = Field(default=None, max_length=3000)
    next_step: str | None = Field(default=None, max_length=500)
    next_step_due_at: datetime | None = None

    @field_validator("application_ids")
    @classmethod
    def _dedupe_application_ids(cls, value: list[int]) -> list[int]:
        seen: set[int] = set()
        ordered: list[int] = []
        for application_id in value:
            if application_id <= 0:
                raise ValueError("Application ids must be positive")
            if application_id not in seen:
                seen.add(application_id)
                ordered.append(application_id)
        return ordered


class PlacementOfferUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    offer_status: PlacementOfferStatus
    offer_role: str | None = Field(default=None, max_length=220)
    offer_package: str | None = Field(default=None, max_length=120)
    offer_location: str | None = Field(default=None, max_length=200)
    offer_joining_date: datetime | None = None
    offer_notes: str | None = Field(default=None, max_length=3000)
    next_step: str | None = Field(default=None, max_length=500)
    next_step_due_at: datetime | None = None


class PlacementApplicationStudentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    status: Literal["interested", "applied", "withdrawn"]
    interest_note: str | None = Field(default=None, max_length=2000)


class PlacementInterviewRoundCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    round_name: str = Field(min_length=2, max_length=160)
    scheduled_at: datetime | None = None
    mode: str | None = Field(default=None, max_length=60)
    location: str | None = Field(default=None, max_length=300)
    interviewer: str | None = Field(default=None, max_length=220)
    notes: str | None = Field(default=None, max_length=3000)


class PlacementInterviewRoundUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    round_name: str | None = Field(default=None, min_length=2, max_length=160)
    status: PlacementInterviewStatus | None = None
    scheduled_at: datetime | None = None
    mode: str | None = Field(default=None, max_length=60)
    location: str | None = Field(default=None, max_length=300)
    interviewer: str | None = Field(default=None, max_length=220)
    notes: str | None = Field(default=None, max_length=3000)


class PlacementInterviewRoundRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    application_id: int
    round_name: str
    status: PlacementInterviewStatus
    scheduled_at: datetime | None = None
    mode: str | None = None
    location: str | None = None
    interviewer: str | None = None
    notes: str | None = None
    created_by_user_id: int | None = None
    updated_by_user_id: int | None = None
    created_at: datetime
    updated_at: datetime


class PlacementApplicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    opportunity_id: int
    profile_id: int
    user_id: int
    student_name: str | None = None
    student_email: str | None = None
    opportunity_title: str | None = None
    opportunity_company: str | None = None
    opportunity_type: PlacementOpportunityType | None = None
    status: PlacementApplicationStatus
    interest_note: str | None = None
    admin_notes: str | None = None
    next_step: str | None = None
    next_step_due_at: datetime | None = None
    offer_status: PlacementOfferStatus | None = None
    offer_role: str | None = None
    offer_package: str | None = None
    offer_location: str | None = None
    offer_joining_date: datetime | None = None
    offer_notes: str | None = None
    offer_updated_by_user_id: int | None = None
    offer_updated_at: datetime | None = None
    interview_rounds: list[PlacementInterviewRoundRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class PlacementApplicationListRead(BaseModel):
    items: list[PlacementApplicationRead]
    total: int


class PlacementActivityEventRead(BaseModel):
    id: int
    event_type: str
    title: str
    message: str | None = None
    opportunity_id: int | None = None
    application_id: int | None = None
    profile_id: int | None = None
    company_id: int | None = None
    actor_user_id: int | None = None
    opportunity_title: str | None = None
    opportunity_company: str | None = None
    student_name: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class PlacementActivityEventListRead(BaseModel):
    items: list[PlacementActivityEventRead]
    total: int


class PlacementUpcomingActionRead(BaseModel):
    action_type: PlacementUpcomingActionType
    title: str
    due_at: datetime
    opportunity_id: int | None = None
    application_id: int | None = None
    profile_id: int | None = None
    interview_round_id: int | None = None
    opportunity_title: str | None = None
    opportunity_company: str | None = None
    student_name: str | None = None
    status: str | None = None


class PlacementUpcomingActionListRead(BaseModel):
    items: list[PlacementUpcomingActionRead]
    total: int


class PlacementEligibleStudentRead(BaseModel):
    profile_id: int
    student_name: str
    student_email: str | None = None
    specialization: str
    cgpa: float
    current_skills: list[str]
    match_score: int
    matched_skills: list[str]
    missing_skills: list[str]
    application_id: int | None = None
    application_status: PlacementApplicationStatus | None = None


class PlacementEligibleStudentListRead(BaseModel):
    items: list[PlacementEligibleStudentRead]
    total: int
