from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CareerAnalysisCreate(BaseModel):
    career_recommendations: list[dict]
    skill_gaps: list[dict]
    learning_roadmap: list[dict]
    salary_insights: dict
    industry_trends: list[dict]
    institution_config_version: str | None = None
    program_fit_summary: dict | None = None
    program_recommendations: list[dict] | None = None
    expectation_reality_checks: list[dict] | None = None
    first_year_roadmap: list[dict] | None = None
    counselor_summary: dict | None = None
    rag_evidence: list[dict] | None = None
    aiml_score: int | None = None
    cyber_security_score: int | None = None
    recommended_branch: str | None = None
    branch_reasoning: list[dict] | None = None
    aiml_roles: list[dict] | None = None
    cyber_roles: list[dict] | None = None
    aiml_skills: list[str] | None = None
    cyber_skills: list[str] | None = None
    aiml_roadmap: list[dict] | None = None
    cyber_roadmap: list[dict] | None = None
    industry_insights: list[dict] | None = None


class CareerAnalysisRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_profile_id: int
    career_recommendations: list[dict]
    skill_gaps: list[dict]
    learning_roadmap: list[dict]
    salary_insights: dict
    industry_trends: list[dict]
    institution_config_version: str | None = None
    program_fit_summary: dict | None = None
    program_recommendations: list[dict] | None = None
    expectation_reality_checks: list[dict] | None = None
    first_year_roadmap: list[dict] | None = None
    counselor_summary: dict | None = None
    rag_evidence: list[dict] | None = None
    aiml_score: int | None = None
    cyber_security_score: int | None = None
    recommended_branch: str | None = None
    branch_reasoning: list[dict] | None = None
    aiml_roles: list[dict] | None = None
    cyber_roles: list[dict] | None = None
    aiml_skills: list[str] | None = None
    cyber_skills: list[str] | None = None
    aiml_roadmap: list[dict] | None = None
    cyber_roadmap: list[dict] | None = None
    industry_insights: list[dict] | None = None
    created_at: datetime
