from __future__ import annotations

from collections import Counter

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.admin_management import AdminManagedItem
from app.models.career_analysis import CareerAnalysis
from app.models.student_profile import StudentProfile
from app.schemas.training_recommendations import (
    TrainingProgram,
    TrainingRecommendationsRead,
    WeakSkill,
)
from app.services.llm_client import LLMClient


class TrainingRecommendationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.llm = LLMClient()

    def get_recommendations(
        self,
        limit: int = 8,
        *,
        user_id: int | None = None,
    ) -> TrainingRecommendationsRead:
        profiles = self._latest_profiles_per_user()
        total_students = len(profiles)
        profile_ids = [profile.id for profile in profiles]
        latest_analyses = self._latest_analyses_for_profiles(profile_ids)

        skill_counter: Counter[str] = Counter()
        for profile in profiles:
            analysis = latest_analyses.get(profile.id)
            if analysis is None:
                continue
            for item in analysis.skill_gaps or []:
                skill = item.get("skill")
                if skill:
                    skill_counter[skill] += 1

        weak_skills = [
            WeakSkill(skill=skill, count=count)
            for skill, count in skill_counter.most_common(limit)
        ]

        managed_programs = self._managed_training_programs(limit)
        if managed_programs:
            return TrainingRecommendationsRead(
                total_students=total_students,
                weak_skills=weak_skills,
                programs=managed_programs,
            )

        llm_programs = self.llm.generate_training_recommendations(
            total_students=total_students,
            weak_skills=[{"skill": item.skill, "count": item.count} for item in weak_skills],
            user_id=user_id,
        )
        programs = [TrainingProgram.model_validate(item) for item in llm_programs]

        return TrainingRecommendationsRead(
            total_students=total_students, weak_skills=weak_skills, programs=programs
        )

    def _latest_profiles_per_user(self) -> list[StudentProfile]:
        rank = func.row_number().over(
            partition_by=StudentProfile.user_id,
            order_by=(StudentProfile.created_at.desc(), StudentProfile.id.desc()),
        ).label("rank")
        subq = select(StudentProfile.id.label("id"), rank).subquery()
        return self.db.scalars(
            select(StudentProfile)
            .join(subq, StudentProfile.id == subq.c.id)
            .where(subq.c.rank == 1)
        ).all()

    def _latest_analyses_for_profiles(
        self, profile_ids: list[int]
    ) -> dict[int, CareerAnalysis]:
        if not profile_ids:
            return {}

        rank = func.row_number().over(
            partition_by=CareerAnalysis.student_profile_id,
            order_by=(CareerAnalysis.created_at.desc(), CareerAnalysis.id.desc()),
        ).label("rank")
        subq = (
            select(CareerAnalysis.id.label("id"), rank)
            .where(CareerAnalysis.student_profile_id.in_(profile_ids))
            .subquery()
        )
        rows = self.db.scalars(
            select(CareerAnalysis)
            .join(subq, CareerAnalysis.id == subq.c.id)
            .where(subq.c.rank == 1)
        ).all()
        return {row.student_profile_id: row for row in rows}

    def _managed_training_programs(self, limit: int) -> list[TrainingProgram]:
        rows = self.db.scalars(
            select(AdminManagedItem)
            .where(AdminManagedItem.item_type == "training_program")
            .where(AdminManagedItem.status == "active")
            .order_by(AdminManagedItem.title)
            .limit(limit)
        ).all()
        programs: list[TrainingProgram] = []
        for row in rows:
            payload = row.payload or {}
            programs.append(
                TrainingProgram(
                    title=row.title,
                    focus_skills=_string_list(payload.get("focus_skills")),
                    description=(
                        row.summary
                        or str(payload.get("description") or "")
                        or "Admin-managed training program."
                    ),
                )
            )
        return programs


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]
