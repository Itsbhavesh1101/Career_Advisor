from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class InstitutionBranch(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    branch_id: str = Field(min_length=3, max_length=120)
    branch_name: str = Field(min_length=2, max_length=180)
    is_active: bool = True
    priority_skills: list[str] = Field(default_factory=list, max_length=30)
    expectation_notes: list[str] = Field(default_factory=list, max_length=20)
    placement_roles: list[str] = Field(default_factory=list, max_length=30)


class InstitutionProgram(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    program_id: str = Field(min_length=3, max_length=120)
    program_name: str = Field(min_length=2, max_length=180)
    degree_level: Literal["undergraduate", "postgraduate", "diploma", "certificate"]
    duration_years: float = Field(gt=0, le=6)
    is_active: bool = True
    branches: list[InstitutionBranch] = Field(default_factory=list, max_length=80)
    priority_skills: list[str] = Field(default_factory=list, max_length=40)
    career_paths: list[str] = Field(default_factory=list, max_length=40)
    admission_fit_signals: list[str] = Field(default_factory=list, max_length=30)
    reality_checks: list[str] = Field(default_factory=list, max_length=30)

    @model_validator(mode="after")
    def _validate_unique_branch_ids(self) -> "InstitutionProgram":
        seen: set[str] = set()
        for branch in self.branches:
            if branch.branch_id in seen:
                raise ValueError(f"Duplicate branch_id: {branch.branch_id}")
            seen.add(branch.branch_id)
        return self


class InstitutionSchool(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    school_id: str = Field(min_length=3, max_length=120)
    school_name: str = Field(min_length=2, max_length=180)
    campus: str = Field(min_length=2, max_length=180)
    is_active: bool = True
    programs: list[InstitutionProgram] = Field(min_length=1, max_length=120)


class InstitutionCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    version: str = Field(min_length=3, max_length=80)
    institution_name: str = Field(min_length=2, max_length=180)
    schools: list[InstitutionSchool] = Field(min_length=1, max_length=80)

    @model_validator(mode="after")
    def _validate_unique_ids(self) -> "InstitutionCatalog":
        seen_schools: set[str] = set()
        seen_programs: set[str] = set()
        for school in self.schools:
            if school.school_id in seen_schools:
                raise ValueError(f"Duplicate school_id: {school.school_id}")
            seen_schools.add(school.school_id)
            for program in school.programs:
                if program.program_id in seen_programs:
                    raise ValueError(f"Duplicate program_id: {program.program_id}")
                seen_programs.add(program.program_id)
        return self


class InstitutionBranding(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    mode: Literal["sage", "generic"]
    product_name: str = Field(min_length=2, max_length=120)
    institution_name: str = Field(min_length=2, max_length=180)
    institution_short_name: str = Field(min_length=2, max_length=80)
    homepage: dict[str, str] = Field(default_factory=dict)
    auth: dict[str, str] = Field(default_factory=dict)
    branch_guidance: dict[str, str] = Field(default_factory=dict)
    placement_readiness: dict[str, str] = Field(default_factory=dict)
    admin_command: dict[str, str] = Field(default_factory=dict)


class InstitutionProgramDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    school: InstitutionSchool
    program: InstitutionProgram


class InstitutionOverridePayload(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    placement_ready_threshold: int = Field(default=75, ge=0, le=100)
    admission_high_intent_threshold: int = Field(default=70, ge=0, le=100)
    priority_skills_by_program: dict[str, list[str]] = Field(default_factory=dict)
    counselor_notes_by_program: dict[str, list[str]] = Field(default_factory=dict)
