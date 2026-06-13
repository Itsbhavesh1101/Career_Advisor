from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

AdminManagedItemType = Literal[
    "program",
    "training_program",
    "internship_opportunity",
    "placement_company",
    "institution_policy",
    "knowledge_template",
    "institution_content",
]
AdminManagedItemStatus = Literal["active", "inactive"]


class AdminManagedItemBase(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    item_type: AdminManagedItemType
    slug: str = Field(min_length=3, max_length=120)
    title: str = Field(min_length=2, max_length=220)
    summary: str | None = Field(default=None, max_length=2000)
    status: AdminManagedItemStatus = "active"
    payload: dict[str, Any] = Field(default_factory=dict)

    @field_validator("slug")
    @classmethod
    def _normalize_slug(cls, value: str) -> str:
        return value.strip().lower().replace(" ", "-")


class AdminManagedItemCreate(AdminManagedItemBase):
    pass


class AdminManagedItemUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    slug: str | None = Field(default=None, min_length=3, max_length=120)
    title: str | None = Field(default=None, min_length=2, max_length=220)
    summary: str | None = Field(default=None, max_length=2000)
    status: AdminManagedItemStatus | None = None
    payload: dict[str, Any] | None = None

    @field_validator("slug")
    @classmethod
    def _normalize_slug(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip().lower().replace(" ", "-")


class AdminManagedItemRead(AdminManagedItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_by_user_id: int | None = None
    updated_by_user_id: int | None = None
    created_at: datetime
    updated_at: datetime


class AdminManagedItemPageRead(BaseModel):
    items: list[AdminManagedItemRead]
    total: int


class ManagedInternshipOpportunityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    title: str
    summary: str | None = None
    company: str | None = None
    location: str | None = None
    duration: str | None = None
    skills: list[str] = Field(default_factory=list)
    eligibility: list[str] = Field(default_factory=list)
    apply_url: str | None = None
    deadline: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class ManagedInternshipOpportunityListRead(BaseModel):
    items: list[ManagedInternshipOpportunityRead]
    total: int
