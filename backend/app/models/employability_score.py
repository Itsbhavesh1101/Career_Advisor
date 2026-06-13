from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EmployabilityScore(Base):
    __tablename__ = "employability_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_profile_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    overall_score: Mapped[int] = mapped_column(Integer, nullable=False)
    academic_strength: Mapped[int] = mapped_column(Integer, nullable=False)
    technical_skills: Mapped[int] = mapped_column(Integer, nullable=False)
    industry_readiness: Mapped[int] = mapped_column(Integer, nullable=False)
    resume_quality: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
