from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PsychometricQuestion(Base):
    __tablename__ = "psychometric_questions"
    __table_args__ = (
        UniqueConstraint("session_id", "position", name="uq_psychometric_question_session_position"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("psychometric_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="llm")
    trait_tag: Mapped[str | None] = mapped_column(String(80), nullable=True)

    question_text: Mapped[str] = mapped_column(String(280), nullable=False)
    options: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)

    schema_version: Mapped[str] = mapped_column(String(20), nullable=False, default="v1")
    prompt_version: Mapped[str] = mapped_column(String(20), nullable=False, default="v1")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
