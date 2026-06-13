from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, HttpUrl


class ResumeURLRequest(BaseModel):
    resume_url: HttpUrl


class ResumeAnalysisRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_profile_id: int
    file_name: str
    source_url: str | None = None
    extracted_skills: list[str]
    projects: list[str]
    experience: list[str]
    education: list[str]
    resume_score: int
    missing_keywords: list[str]
    weak_sections: list[str]
    suggestions: list[str]
    created_at: datetime
