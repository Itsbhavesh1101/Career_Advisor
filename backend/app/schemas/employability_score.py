from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EmployabilityScoreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_profile_id: int
    overall_score: int
    academic_strength: int
    technical_skills: int
    industry_readiness: int
    resume_quality: int
    created_at: datetime
