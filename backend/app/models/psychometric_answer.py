from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PsychometricAnswer(Base):
    __tablename__ = "psychometric_answers"
    __table_args__ = (
        UniqueConstraint("session_id", "question_id", name="uq_psychometric_answer_session_question"),
        UniqueConstraint("session_id", "idempotency_key", name="uq_psychometric_answer_session_key"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("psychometric_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("psychometric_questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    idempotency_key: Mapped[str | None] = mapped_column(String(80), nullable=True)

    selected_option_id: Mapped[str] = mapped_column(String(80), nullable=False)
    selected_option_text: Mapped[str | None] = mapped_column(String(280), nullable=True)
    trait_effect: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    response_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
