from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ResumeAnalysis(Base):
    __tablename__ = "resume_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_profile_id: Mapped[int] = mapped_column(
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_name: Mapped[str] = mapped_column(String, nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    extracted_skills: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    projects: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    experience: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    education: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    resume_score: Mapped[int] = mapped_column(Integer, nullable=False)
    missing_keywords: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    weak_sections: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    suggestions: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
