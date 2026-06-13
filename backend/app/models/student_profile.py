from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    twelfth_percentage: Mapped[float] = mapped_column(Float, nullable=False)
    cgpa: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    degree: Mapped[str] = mapped_column(String(200), nullable=False)
    specialization: Mapped[str] = mapped_column(String(200), nullable=False)
    current_skills: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=list
    )
    interests: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    target_industry: Mapped[str] = mapped_column(String(200), nullable=False)
    projects: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    internships: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    certifications: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    subjects: Mapped[list[str] | None] = mapped_column(
        JSON, nullable=True, default=list
    )
    math_strength: Mapped[str | None] = mapped_column(String(20), nullable=True)
    logical_reasoning: Mapped[str | None] = mapped_column(String(20), nullable=True)
    programming_interest: Mapped[str | None] = mapped_column(String(20), nullable=True)
    user_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
