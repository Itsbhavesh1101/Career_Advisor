from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CareerAnalysis(Base):
    __tablename__ = "career_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_profile_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    career_recommendations: Mapped[list[dict]] = mapped_column(
        JSON, nullable=False, default=list
    )
    skill_gaps: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    learning_roadmap: Mapped[list[dict]] = mapped_column(
        JSON, nullable=False, default=list
    )
    salary_insights: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    industry_trends: Mapped[list[dict]] = mapped_column(
        JSON, nullable=False, default=list
    )
    aiml_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cyber_security_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    recommended_branch: Mapped[str | None] = mapped_column(String(50), nullable=True)
    branch_reasoning: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    aiml_roles: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    cyber_roles: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    aiml_skills: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    cyber_skills: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    aiml_roadmap: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    cyber_roadmap: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    industry_insights: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    institution_config_version: Mapped[str | None] = mapped_column(String(80), nullable=True)
    program_fit_summary: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    program_recommendations: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    expectation_reality_checks: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    first_year_roadmap: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    counselor_summary: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    rag_evidence: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
