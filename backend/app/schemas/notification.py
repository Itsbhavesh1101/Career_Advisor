from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


NotificationPriority = Literal["normal", "high"]
NotificationAudience = Literal["all", "college_student", "twelfth_student"]


class NotificationRead(BaseModel):
    id: int
    recipient_user_id: int
    profile_id: int | None = None
    notification_type: str
    title: str
    message: str | None = None
    action_url: str | None = None
    priority: NotificationPriority
    read_at: datetime | None = None
    created_by_user_id: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationListRead(BaseModel):
    items: list[NotificationRead]
    total: int
    unread_count: int


class NotificationMarkAllResult(BaseModel):
    updated_count: int


class PlacementAnnouncementCreate(BaseModel):
    title: str = Field(min_length=3, max_length=220)
    message: str = Field(min_length=3, max_length=1000)
    audience: NotificationAudience = "college_student"
    action_url: str | None = Field(default="/internship", max_length=500)
    priority: NotificationPriority = "normal"


class NotificationAnnouncementResult(BaseModel):
    created_count: int
