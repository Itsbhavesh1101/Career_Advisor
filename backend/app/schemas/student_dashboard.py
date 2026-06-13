from __future__ import annotations

from pydantic import BaseModel


class StudentDashboardSummaryRead(BaseModel):
    profile_id: int
    student_type: str
    profile_completeness: int
    analysis_status: str
    quiz_status: str
    resume_status: str
    readiness_summary: str
    next_actions: list[str]
