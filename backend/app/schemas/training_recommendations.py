from __future__ import annotations

from pydantic import BaseModel


class WeakSkill(BaseModel):
    skill: str
    count: int


class TrainingProgram(BaseModel):
    title: str
    focus_skills: list[str]
    description: str


class TrainingRecommendationsRead(BaseModel):
    total_students: int
    weak_skills: list[WeakSkill]
    programs: list[TrainingProgram]
