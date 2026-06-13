from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class InternshipReadiness(Base):
    __tablename__ = "internship_readiness"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_profile_id: Mapped[int] = mapped_column(
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    readiness_score: Mapped[int] = mapped_column(Integer, nullable=False)
    readiness_level: Mapped[str] = mapped_column(String, nullable=False)
    action_plan: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
