from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class PlacementMetricsRead(BaseModel):
    total_college_profiles: int
    placement_ready: int
    needs_training: int
    high_risk: int
    company_ready: int
    evidence_complete: int
    average_employability: int | None = None


class SkillEvidenceLedgerRead(BaseModel):
    evidence_score: int
    project_count: int
    internship_count: int
    certification_count: int
    resume_quality: int | None = None
    internship_readiness: int | None = None
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)


class PlacementStudentSignalRead(BaseModel):
    profile_id: int
    student_name: str
    program: str
    employability_score: int | None = None
    placement_risk: str | None = None
    top_company: str | None = None
    top_company_score: int | None = None
    status: str
    priority: str
    recommended_actions: list[str] = Field(default_factory=list)
    evidence: SkillEvidenceLedgerRead
    created_at: datetime


class CompanyReadinessRead(BaseModel):
    company: str
    average_score: int
    ready_count: int
    watch_count: int
    blocked_count: int
    missing_skills: list[str] = Field(default_factory=list)


class TrainingROISignalRead(BaseModel):
    skill: str
    affected_students: int
    expected_readiness_lift: int
    priority: str


class FacultyAdvisorNoteRead(BaseModel):
    profile_id: int
    student_name: str
    escalation_level: str
    focus_areas: list[str] = Field(default_factory=list)
    note: str


class PlacementDashboardRead(BaseModel):
    metrics: PlacementMetricsRead
    students: list[PlacementStudentSignalRead]
    company_radar: list[CompanyReadinessRead]
    training_roi: list[TrainingROISignalRead]
    faculty_notes: list[FacultyAdvisorNoteRead]
