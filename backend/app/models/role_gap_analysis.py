from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import ForeignKey, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RoleGapAnalysis(Base):
    __tablename__ = "role_gap_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_profile_id: Mapped[int] = mapped_column(
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role_gaps: Mapped[list[dict]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
