from datetime import datetime

from pydantic import BaseModel, ConfigDict, model_validator


class StudentProfileCreate(BaseModel):
    name: str
    twelfth_percentage: float | None = None
    cgpa: float | None = None
    degree: str | None = None
    specialization: str | None = None
    current_skills: list[str]
    interests: list[str]
    target_industry: str | None = None
    projects: int = 0
    internships: int = 0
    certifications: int = 0
    subjects: list[str] | None = None
    math_strength: str | None = None
    logical_reasoning: str | None = None
    programming_interest: str | None = None
    user_type: str | None = None

    @model_validator(mode="after")
    def validate_for_student_type(self) -> "StudentProfileCreate":
        user_type = self.user_type or "college_student"
        errors: list[str] = []

        if not self.name.strip():
            errors.append("Name is required")

        if user_type == "twelfth_student":
            if self.twelfth_percentage is None:
                errors.append("12th percentage is required for 12th student branch guidance")
            if not self.interests:
                errors.append("At least one interest is required for 12th student branch guidance")
            if not self.subjects:
                errors.append("Subjects are required for 12th student branch guidance")
            if not self.math_strength:
                errors.append("Math strength is required for 12th student branch guidance")
            if not self.logical_reasoning:
                errors.append("Logical reasoning strength is required for 12th student branch guidance")
        else:
            if self.cgpa is None:
                errors.append("CGPA is required for college placement guidance")
            if not (self.degree or "").strip():
                errors.append("Degree is required for college placement guidance")
            if not (self.specialization or "").strip():
                errors.append("Specialization is required for college placement guidance")
            if not (self.target_industry or "").strip():
                errors.append("Target industry is required for college placement guidance")

        if errors:
            raise ValueError("; ".join(errors))

        return self


class StudentProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    twelfth_percentage: float
    cgpa: float
    degree: str
    specialization: str
    current_skills: list[str]
    interests: list[str]
    target_industry: str
    projects: int
    internships: int
    certifications: int
    subjects: list[str] | None = None
    math_strength: str | None = None
    logical_reasoning: str | None = None
    programming_interest: str | None = None
    user_type: str | None = None
    created_at: datetime
