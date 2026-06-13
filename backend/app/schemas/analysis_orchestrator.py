from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

AgentStageStatus = Literal["completed", "skipped", "failed"]
VerifierStatus = Literal["approved", "approved_with_warnings", "blocked"]


class AgentStageSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    stage: str = Field(min_length=2, max_length=120)
    label: str = Field(min_length=2, max_length=160)
    status: AgentStageStatus
    source: str = Field(min_length=2, max_length=80)
    output_ref: str | None = Field(default=None, max_length=120)
    notes: list[str] = Field(default_factory=list, max_length=8)


class SnapshotVerifierResult(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    status: VerifierStatus
    confidence: int = Field(ge=0, le=100)
    blockers: list[str] = Field(default_factory=list, max_length=12)
    warnings: list[str] = Field(default_factory=list, max_length=12)
    evidence_count: int = Field(ge=0)
    next_best_actions: list[str] = Field(default_factory=list, max_length=8)


class AnalysisSnapshotSummary(BaseModel):
    model_config = ConfigDict(extra="allow", str_strip_whitespace=True)

    snapshot_version: str = "agentic-snapshot-v1"
    profile_id: int
    user_type: str
    career_analysis_id: int
    agent_stages: list[AgentStageSummary] = Field(default_factory=list)
    verifier: SnapshotVerifierResult
