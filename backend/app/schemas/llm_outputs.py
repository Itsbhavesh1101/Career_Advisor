from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, RootModel, model_validator


class StrictSchemaModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class CareerRecommendationItem(StrictSchemaModel):
    role: str = Field(min_length=1, max_length=120)
    score: int = Field(ge=0, le=100)


class SkillGapItem(StrictSchemaModel):
    skill: str = Field(min_length=1, max_length=120)
    priority: Literal["high", "medium", "low"]


class LearningRoadmapItem(StrictSchemaModel):
    stage: str = Field(min_length=1, max_length=120)
    topics: list[str] = Field(min_length=1, max_length=20)


class SalaryInsights(StrictSchemaModel):
    currency: str = Field(min_length=1, max_length=10)
    estimate_min: int = Field(ge=0)
    estimate_max: int = Field(ge=0)

    @model_validator(mode="after")
    def _validate_salary_range(self) -> "SalaryInsights":
        if self.estimate_max < self.estimate_min:
            raise ValueError("estimate_max must be >= estimate_min")
        return self


class IndustryTrendItem(StrictSchemaModel):
    trend: str = Field(min_length=1, max_length=160)
    impact: Literal["high", "medium", "low"]


class CareerAnalysisLLMOutput(StrictSchemaModel):
    career_recommendations: list[CareerRecommendationItem] = Field(min_length=1, max_length=8)
    skill_gaps: list[SkillGapItem] = Field(min_length=1, max_length=20)
    learning_roadmap: list[LearningRoadmapItem] = Field(min_length=1, max_length=8)
    salary_insights: SalaryInsights
    industry_trends: list[IndustryTrendItem] = Field(min_length=1, max_length=20)


class CompanyFitAdjustments(RootModel[dict[str, int]]):
    @model_validator(mode="after")
    def _validate_root(self) -> "CompanyFitAdjustments":
        if not self.root:
            raise ValueError("Company fit adjustments cannot be empty")
        for key, value in self.root.items():
            if not key or not key.strip():
                raise ValueError("Company fit adjustment key cannot be empty")
            if value < -40 or value > 40:
                raise ValueError("Company fit adjustment deltas must be within -40..40")
        return self


class EmployabilityAdjustments(StrictSchemaModel):
    academic_delta: int = Field(default=0, ge=-20, le=20)
    technical_delta: int = Field(default=0, ge=-20, le=20)
    industry_delta: int = Field(default=0, ge=-20, le=20)
    resume_delta: int = Field(default=0, ge=-20, le=20)


class EmployabilityScoreLLMOutput(StrictSchemaModel):
    overall_score: int = Field(ge=0, le=100)
    academic_strength: int = Field(ge=0, le=100)
    technical_skills: int = Field(ge=0, le=100)
    industry_readiness: int = Field(ge=0, le=100)
    resume_quality: int = Field(ge=0, le=100)


class CompanyFitMatchItem(StrictSchemaModel):
    company: str = Field(min_length=1, max_length=120)
    company_type: str = Field(min_length=2, max_length=80)
    target_roles: list[str] = Field(min_length=1, max_length=8)
    score: int = Field(ge=0, le=100)
    rationale: str = Field(min_length=1, max_length=360)
    matched_evidence: list[str] = Field(min_length=1, max_length=8)
    missing_requirements: list[str] = Field(min_length=1, max_length=8)
    preparation_plan: list[str] = Field(min_length=1, max_length=8)
    hiring_signal_summary: str = Field(min_length=1, max_length=280)


class CompanyFitLLMOutput(StrictSchemaModel):
    matches: list[CompanyFitMatchItem] = Field(min_length=1, max_length=20)

    @model_validator(mode="after")
    def _validate_unique_companies(self) -> "CompanyFitLLMOutput":
        seen: set[str] = set()
        for item in self.matches:
            key = item.company.strip().lower()
            if key in seen:
                raise ValueError("Company matches must be unique by company name")
            seen.add(key)
        return self


class RoleGapLLMItem(StrictSchemaModel):
    role: str = Field(min_length=1, max_length=120)
    missing_skills: list[str] = Field(min_length=1, max_length=20)
    learning_plan: list[str] = Field(min_length=1, max_length=10)
    current_evidence: list[str] = Field(min_length=1, max_length=10)
    gap_reason: str = Field(min_length=1, max_length=320)
    next_project: str = Field(min_length=1, max_length=240)
    proof_to_build: list[str] = Field(min_length=1, max_length=10)
    priority: Literal["high", "medium", "low"]


class RoleGapAnalysisLLMOutput(StrictSchemaModel):
    role_gaps: list[RoleGapLLMItem] = Field(min_length=1, max_length=12)


class PlacementRiskLLMOutput(StrictSchemaModel):
    risk_level: Literal["Low", "Medium", "High"]
    reasons: list[str] = Field(min_length=1, max_length=10)


class InternshipReadinessLLMOutput(StrictSchemaModel):
    readiness_score: int = Field(ge=0, le=100)
    readiness_level: Literal["Low", "Medium", "High"]
    action_plan: list[str] = Field(min_length=1, max_length=10)

    @model_validator(mode="after")
    def _validate_readiness_consistency(self) -> "InternshipReadinessLLMOutput":
        if self.readiness_score >= 70 and self.readiness_level == "Low":
            raise ValueError("readiness_level is inconsistent with readiness_score")
        if self.readiness_score < 40 and self.readiness_level == "High":
            raise ValueError("readiness_level is inconsistent with readiness_score")
        return self


class ResumeAnalysisLLMOutput(StrictSchemaModel):
    extracted_skills: list[str] = Field(min_length=1, max_length=50)
    projects: list[str] = Field(min_length=0, max_length=20)
    experience: list[str] = Field(min_length=0, max_length=20)
    education: list[str] = Field(min_length=1, max_length=20)
    resume_score: int = Field(ge=0, le=100)
    missing_keywords: list[str] = Field(min_length=0, max_length=20)
    weak_sections: list[str] = Field(min_length=0, max_length=10)
    suggestions: list[str] = Field(min_length=1, max_length=12)


class WeakSkillCountItem(StrictSchemaModel):
    skill: str = Field(min_length=1, max_length=120)
    count: int = Field(ge=0, le=100000)


class TrainingProgramLLMItem(StrictSchemaModel):
    title: str = Field(min_length=1, max_length=180)
    focus_skills: list[str] = Field(min_length=1, max_length=12)
    description: str = Field(min_length=1, max_length=400)


class TrainingRecommendationsLLMOutput(StrictSchemaModel):
    programs: list[TrainingProgramLLMItem] = Field(min_length=1, max_length=8)


class IndustryTrendsOutput(StrictSchemaModel):
    trends: list[IndustryTrendItem] = Field(min_length=1, max_length=20)


class BranchReasoningItem(StrictSchemaModel):
    reason: str = Field(min_length=1, max_length=180)


class RoleScoreItem(StrictSchemaModel):
    role: str = Field(min_length=1, max_length=120)
    score: int = Field(ge=0, le=100)


class RoadmapYearItem(StrictSchemaModel):
    year: int = Field(ge=1, le=8)
    topics: list[str] = Field(min_length=1, max_length=20)


class BranchInsightItem(StrictSchemaModel):
    branch: str = Field(min_length=1, max_length=80)
    insight: str = Field(min_length=1, max_length=200)


class ProgramFitSummary(StrictSchemaModel):
    recommended_program_id: str = Field(min_length=3, max_length=120)
    recommended_program_name: str = Field(min_length=2, max_length=180)
    confidence: int = Field(ge=0, le=100)
    summary: str = Field(min_length=1, max_length=400)


class ProgramRecommendationItem(StrictSchemaModel):
    program_id: str = Field(min_length=3, max_length=120)
    program_name: str = Field(min_length=2, max_length=180)
    school: str = Field(min_length=2, max_length=180)
    fit_score: int = Field(ge=0, le=100)
    fit_level: Literal["High", "Medium", "Low"]
    reasons: list[str] = Field(min_length=1, max_length=8)
    career_paths: list[str] = Field(min_length=1, max_length=12)
    priority_skills: list[str] = Field(min_length=1, max_length=20)
    first_year_focus: list[str] = Field(min_length=1, max_length=12)


class ExpectationRealityCheckItem(StrictSchemaModel):
    expectation: str = Field(min_length=1, max_length=220)
    reality: str = Field(min_length=1, max_length=320)
    counselor_note: str = Field(min_length=1, max_length=320)


class FirstYearRoadmapItem(StrictSchemaModel):
    term: str = Field(min_length=1, max_length=80)
    focus: list[str] = Field(min_length=1, max_length=12)
    evidence_to_build: list[str] = Field(min_length=1, max_length=12)


class CounselorSummary(StrictSchemaModel):
    best_fit: str = Field(min_length=1, max_length=180)
    risk_flags: list[str] = Field(default_factory=list, max_length=12)
    talking_points: list[str] = Field(min_length=1, max_length=12)
    follow_up_questions: list[str] = Field(min_length=1, max_length=12)


class ProgramFitLLMOutput(StrictSchemaModel):
    program_fit_summary: ProgramFitSummary
    program_recommendations: list[ProgramRecommendationItem] = Field(
        min_length=1,
        max_length=8,
    )
    expectation_reality_checks: list[ExpectationRealityCheckItem] = Field(
        min_length=1,
        max_length=8,
    )
    first_year_roadmap: list[FirstYearRoadmapItem] = Field(min_length=1, max_length=8)
    counselor_summary: CounselorSummary


class BranchAnalysisLLMOutput(StrictSchemaModel):
    aiml_score: int = Field(ge=0, le=100)
    cyber_security_score: int = Field(ge=0, le=100)
    recommended_branch: Literal["AIML", "Cyber Security"]
    branch_reasoning: list[BranchReasoningItem] = Field(min_length=1, max_length=10)
    aiml_roles: list[RoleScoreItem] = Field(min_length=1, max_length=10)
    cyber_roles: list[RoleScoreItem] = Field(min_length=1, max_length=10)
    aiml_skills: list[str] = Field(min_length=1, max_length=20)
    cyber_skills: list[str] = Field(min_length=1, max_length=20)
    aiml_roadmap: list[RoadmapYearItem] = Field(min_length=1, max_length=8)
    cyber_roadmap: list[RoadmapYearItem] = Field(min_length=1, max_length=8)
    industry_insights: list[BranchInsightItem] = Field(min_length=1, max_length=20)
