from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PsychometricResult(Base):
    __tablename__ = "psychometric_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("psychometric_sessions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
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

    trait_scores: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    question_count: Mapped[int] = mapped_column(Integer, nullable=False)
    fallback_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    trait_version: Mapped[str] = mapped_column(String(20), nullable=False, default="v1")
    schema_version: Mapped[str] = mapped_column(String(20), nullable=False, default="v1")
    prompt_version: Mapped[str] = mapped_column(String(20), nullable=False, default="v1")
    scoring_config_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
