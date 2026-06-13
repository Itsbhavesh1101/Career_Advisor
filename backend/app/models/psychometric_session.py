from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PsychometricSession(Base):
    __tablename__ = "psychometric_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    student_profile_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="queued", index=True)

    fallback_mode: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    breaker_open: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    llm_failure_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    current_question_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("psychometric_questions.id", ondelete="SET NULL"),
        nullable=True,
    )
    current_question_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    questions_answered: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    min_questions: Mapped[int] = mapped_column(Integer, nullable=False, default=8)
    max_questions: Mapped[int] = mapped_column(Integer, nullable=False, default=15)

    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    current_traits: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    current_state: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    tokens_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    question_generation_lock: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    schema_version: Mapped[str] = mapped_column(String(20), nullable=False, default="v1")
    prompt_version: Mapped[str] = mapped_column(String(20), nullable=False, default="v1")

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
