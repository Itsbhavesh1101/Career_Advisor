from __future__ import annotations

import csv
from io import StringIO

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.analysis_job import AnalysisJob
from app.models.career_analysis import CareerAnalysis
from app.models.employability_score import EmployabilityScore
from app.models.placement_risk import PlacementRisk
from app.models.rag_document import RAGDocumentChunk, RAGDocumentSource
from app.models.resume_analysis import ResumeAnalysis
from app.models.student_profile import StudentProfile
from app.schemas.admin_dashboard import (
    AdminMetricsRead,
    AdminReadinessSummaryRead,
    AdminStudentFilters,
    AdminStudentRead,
    SystemReadinessRead,
)


class AdminDashboardService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_metrics(self) -> AdminMetricsRead:
        latest_scores = self._latest_employability_score_values_subquery()
        latest_risks = self._latest_placement_risk_values_subquery()

        high_risk_condition = (latest_risks.c.risk_level == "High") | (
            latest_scores.c.overall_score < 50
        )
        placement_ready_condition = (latest_risks.c.risk_level == "Low") & (
            latest_scores.c.overall_score >= 70
        )

        aggregate = self.db.execute(
            select(
                func.count(StudentProfile.id).label("total_profiles"),
                func.count(func.distinct(StudentProfile.user_id)).label("total_students"),
                func.sum(
                    case(
                        (placement_ready_condition, 1),
                        else_=0,
                    )
                ).label("placement_ready"),
                func.sum(
                    case(
                        (high_risk_condition, 1),
                        else_=0,
                    )
                ).label("high_risk"),
            )
            .select_from(StudentProfile)
            .outerjoin(latest_scores, latest_scores.c.profile_id == StudentProfile.id)
            .outerjoin(latest_risks, latest_risks.c.profile_id == StudentProfile.id)
        ).one()

        total_profiles = int(aggregate.total_profiles or 0)
        total_students = int(aggregate.total_students or 0)
        placement_ready = int(aggregate.placement_ready or 0)
        high_risk = int(aggregate.high_risk or 0)
        needs_training = max(total_profiles - placement_ready - high_risk, 0)

        return AdminMetricsRead(
            total_profiles=total_profiles,
            total_students=total_students,
            placement_ready=placement_ready,
            needs_training=needs_training,
            high_risk=high_risk,
        )

    def get_readiness_summary(self) -> AdminReadinessSummaryRead:
        return AdminReadinessSummaryRead(
            pending_rag_reviews=self._count_pending_rag_reviews(),
            stale_rag_sources=self._count_stale_rag_sources(),
            failed_embeddings=self._count_failed_embeddings(),
            chunks_without_embeddings=self._count_chunks_without_embeddings(),
            failed_analysis_jobs=self._count_failed_analysis_jobs(),
            missing_analysis=self._count_missing_analysis(),
            missing_resume=self._count_missing_resume(),
        )

    def get_system_readiness(self) -> SystemReadinessRead:
        settings = get_settings()
        embedding_configured = settings.rag_embedding_provider != "bedrock" or bool(
            settings.rag_embedding_bedrock_region or settings.bedrock_region
        )
        hints: list[str] = []
        if settings.celery_task_always_eager:
            hints.append("Eager job mode is acceptable for first launch; add Redis and workers when traffic grows.")
        if settings.rag_embedding_provider == "hash":
            hints.append("Hash embeddings are deterministic but production should use Bedrock embeddings.")
        if self._count_pending_rag_reviews():
            hints.append("Approve pending RAG sources before relying on them in student guidance.")
        return SystemReadinessRead(
            llm_provider=settings.llm_provider,
            llm_configured=settings.llm_provider != "bedrock" or bool(settings.bedrock_region),
            embedding_provider=settings.rag_embedding_provider,
            embedding_configured=embedding_configured,
            vector_search_enabled=settings.rag_vector_search_enabled,
            celery_task_always_eager=settings.celery_task_always_eager,
            failed_analysis_jobs=self._count_failed_analysis_jobs(),
            failed_embedding_jobs=self._count_failed_embeddings(),
            pending_rag_reviews=self._count_pending_rag_reviews(),
            stale_rag_sources=self._count_stale_rag_sources(),
            hints=hints,
        )

    def _latest_employability_score_values_subquery(self):
        rank = func.row_number().over(
            partition_by=EmployabilityScore.student_profile_id,
            order_by=(EmployabilityScore.created_at.desc(), EmployabilityScore.id.desc()),
        ).label("rank")
        ranked = (
            select(
                EmployabilityScore.student_profile_id.label("profile_id"),
                EmployabilityScore.overall_score.label("overall_score"),
                rank,
            )
            .subquery()
        )
        return (
            select(
                ranked.c.profile_id,
                ranked.c.overall_score,
            )
            .where(ranked.c.rank == 1)
            .subquery()
        )

    def _latest_placement_risk_values_subquery(self):
        rank = func.row_number().over(
            partition_by=PlacementRisk.student_profile_id,
            order_by=(PlacementRisk.created_at.desc(), PlacementRisk.id.desc()),
        ).label("rank")
        ranked = (
            select(
                PlacementRisk.student_profile_id.label("profile_id"),
                PlacementRisk.risk_level.label("risk_level"),
                rank,
            )
            .subquery()
        )
        return (
            select(
                ranked.c.profile_id,
                ranked.c.risk_level,
            )
            .where(ranked.c.rank == 1)
            .subquery()
        )

    def list_students(
        self,
        page: int = 1,
        page_size: int = 25,
        filters: AdminStudentFilters | None = None,
    ) -> tuple[list[AdminStudentRead], int, int]:
        page = max(1, page)
        page_size = max(1, min(page_size, 100))
        filters = filters or AdminStudentFilters()

        stmt = self._filtered_profiles_stmt(filters)
        total = int(
            self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        )
        total_pages = max(1, (total + page_size - 1) // page_size)
        offset = (page - 1) * page_size

        profiles = list(
            self.db.scalars(
                self._apply_sort(stmt, filters).offset(offset).limit(page_size)
            )
        )
        profile_ids = [profile.id for profile in profiles]
        latest_scores = self._latest_employability_scores(profile_ids)
        latest_risks = self._latest_placement_risks(profile_ids)
        analysis_ids = self._profiles_with_analysis(profile_ids)
        resume_ids = self._profiles_with_resume(profile_ids)

        results: list[AdminStudentRead] = []
        for profile in profiles:
            score = latest_scores.get(profile.id)
            risk = latest_risks.get(profile.id)
            readiness_band = self._readiness_band(score.overall_score if score else None, risk.risk_level if risk else None)
            results.append(
                AdminStudentRead(
                    profile_id=profile.id,
                    user_id=profile.user_id,
                    name=profile.name,
                    user_type=profile.user_type,
                    degree=profile.degree,
                    specialization=profile.specialization,
                    cgpa=profile.cgpa,
                    created_at=profile.created_at,
                    employability_score=score.overall_score if score else None,
                    placement_risk=risk.risk_level if risk else None,
                    has_analysis=profile.id in analysis_ids,
                    has_resume=profile.id in resume_ids,
                    readiness_band=readiness_band,
                )
            )
        return results, total, total_pages

    def export_students_csv(self, filters: AdminStudentFilters | None = None) -> str:
        filters = filters or AdminStudentFilters()
        buffer = StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            [
                "profile_id",
                "name",
                "user_type",
                "degree",
                "specialization",
                "cgpa",
                "employability_score",
                "placement_risk",
                "readiness_band",
                "has_analysis",
                "has_resume",
            ]
        )
        page = 1
        while True:
            items, _total, total_pages = self.list_students(
                page=page,
                page_size=100,
                filters=filters,
            )
            for item in items:
                writer.writerow(
                    [
                        item.profile_id,
                        item.name,
                        item.user_type or "",
                        item.degree,
                        item.specialization,
                        item.cgpa,
                        item.employability_score if item.employability_score is not None else "",
                        item.placement_risk or "",
                        item.readiness_band,
                        item.has_analysis,
                        item.has_resume,
                    ]
                )
            if page >= total_pages:
                break
            page += 1
        return buffer.getvalue()

    def _filtered_profiles_stmt(self, filters: AdminStudentFilters):
        stmt = select(StudentProfile)
        if filters.student_type:
            stmt = stmt.where(StudentProfile.user_type == filters.student_type)
        if filters.specialization:
            stmt = stmt.where(StudentProfile.specialization.ilike(f"%{filters.specialization}%"))
        if filters.placement_risk:
            risk_subq = self._latest_placement_risk_values_subquery()
            stmt = stmt.join(risk_subq, risk_subq.c.profile_id == StudentProfile.id)
            stmt = stmt.where(risk_subq.c.risk_level == filters.placement_risk)
        if filters.missing_analysis is not None:
            analysis_exists = (
                select(CareerAnalysis.id)
                .where(CareerAnalysis.student_profile_id == StudentProfile.id)
                .exists()
            )
            stmt = stmt.where(~analysis_exists if filters.missing_analysis else analysis_exists)
        if filters.missing_resume is not None:
            resume_exists = (
                select(ResumeAnalysis.id)
                .where(ResumeAnalysis.student_profile_id == StudentProfile.id)
                .exists()
            )
            stmt = stmt.where(~resume_exists if filters.missing_resume else resume_exists)
        if filters.readiness_band:
            score_subq = self._latest_employability_score_values_subquery()
            risk_subq = self._latest_placement_risk_values_subquery()
            stmt = stmt.outerjoin(score_subq, score_subq.c.profile_id == StudentProfile.id)
            stmt = stmt.outerjoin(risk_subq, risk_subq.c.profile_id == StudentProfile.id)
            stmt = stmt.where(self._readiness_condition(filters.readiness_band, score_subq, risk_subq))
        return stmt

    def _apply_sort(self, stmt, filters: AdminStudentFilters):
        if filters.sort == "created_asc":
            return stmt.order_by(StudentProfile.created_at.asc(), StudentProfile.id.asc())
        if filters.sort in {"readiness_desc", "readiness_asc"}:
            score_subq = self._latest_employability_score_values_subquery()
            stmt = stmt.outerjoin(score_subq, score_subq.c.profile_id == StudentProfile.id)
            order = score_subq.c.overall_score.asc() if filters.sort == "readiness_asc" else score_subq.c.overall_score.desc()
            return stmt.order_by(order.nullslast(), StudentProfile.created_at.desc())
        return stmt.order_by(StudentProfile.created_at.desc(), StudentProfile.id.desc())

    def _readiness_condition(self, band: str, score_subq, risk_subq):
        score = score_subq.c.overall_score
        risk = risk_subq.c.risk_level
        if band == "ready":
            return (score >= 70) & (risk == "Low")
        if band == "risk":
            return or_(score < 50, risk == "High")
        if band == "watch":
            return (score >= 50) & (score < 70)
        return score.is_(None)

    def _readiness_band(self, score: int | None, risk: str | None) -> str:
        if score is None and risk is None:
            return "unknown"
        if risk == "High" or (score is not None and score < 50):
            return "risk"
        if risk == "Low" and score is not None and score >= 70:
            return "ready"
        return "watch"

    def _latest_employability_scores(self, profile_ids: list[int]) -> dict[int, EmployabilityScore]:
        if not profile_ids:
            return {}

        rank = func.row_number().over(
            partition_by=EmployabilityScore.student_profile_id,
            order_by=(EmployabilityScore.created_at.desc(), EmployabilityScore.id.desc()),
        ).label("rank")
        subq = (
            select(EmployabilityScore.id.label("id"), rank)
            .where(EmployabilityScore.student_profile_id.in_(profile_ids))
            .subquery()
        )
        latest_rows = self.db.scalars(
            select(EmployabilityScore)
            .join(subq, EmployabilityScore.id == subq.c.id)
            .where(subq.c.rank == 1)
        ).all()
        return {row.student_profile_id: row for row in latest_rows}

    def _profiles_with_analysis(self, profile_ids: list[int]) -> set[int]:
        if not profile_ids:
            return set()
        return set(
            self.db.scalars(
                select(CareerAnalysis.student_profile_id).where(
                    CareerAnalysis.student_profile_id.in_(profile_ids)
                )
            ).all()
        )

    def _profiles_with_resume(self, profile_ids: list[int]) -> set[int]:
        if not profile_ids:
            return set()
        return set(
            self.db.scalars(
                select(ResumeAnalysis.student_profile_id).where(
                    ResumeAnalysis.student_profile_id.in_(profile_ids)
                )
            ).all()
        )

    def _count_pending_rag_reviews(self) -> int:
        return int(
            self.db.scalar(
                select(func.count()).select_from(RAGDocumentSource).where(
                    RAGDocumentSource.status == "active",
                    RAGDocumentSource.review_status == "pending_review",
                )
            )
            or 0
        )

    def _count_stale_rag_sources(self) -> int:
        return int(
            self.db.scalar(
                select(func.count()).select_from(RAGDocumentSource).where(
                    RAGDocumentSource.status == "active",
                    RAGDocumentSource.expires_at.is_not(None),
                    RAGDocumentSource.expires_at <= func.now(),
                )
            )
            or 0
        )

    def _count_failed_embeddings(self) -> int:
        return int(
            self.db.scalar(
                select(func.count()).select_from(RAGDocumentChunk).where(
                    RAGDocumentChunk.embedding_status == "failed"
                )
            )
            or 0
        )

    def _count_chunks_without_embeddings(self) -> int:
        return int(
            self.db.scalar(
                select(func.count()).select_from(RAGDocumentChunk).where(
                    RAGDocumentChunk.is_active.is_(True),
                    or_(
                        RAGDocumentChunk.embedding.is_(None),
                        RAGDocumentChunk.embedding_status != "indexed",
                    ),
                )
            )
            or 0
        )

    def _count_failed_analysis_jobs(self) -> int:
        return int(
            self.db.scalar(
                select(func.count()).select_from(AnalysisJob).where(
                    AnalysisJob.status == "failed"
                )
            )
            or 0
        )

    def _count_missing_analysis(self) -> int:
        analysis_exists = (
            select(CareerAnalysis.id)
            .where(CareerAnalysis.student_profile_id == StudentProfile.id)
            .exists()
        )
        return int(
            self.db.scalar(
                select(func.count()).select_from(StudentProfile).where(~analysis_exists)
            )
            or 0
        )

    def _count_missing_resume(self) -> int:
        resume_exists = (
            select(ResumeAnalysis.id)
            .where(ResumeAnalysis.student_profile_id == StudentProfile.id)
            .exists()
        )
        return int(
            self.db.scalar(
                select(func.count()).select_from(StudentProfile).where(
                    or_(
                        StudentProfile.user_type.is_(None),
                        StudentProfile.user_type != "twelfth_student",
                    ),
                    ~resume_exists,
                )
            )
            or 0
        )

    def _latest_placement_risks(self, profile_ids: list[int]) -> dict[int, PlacementRisk]:
        if not profile_ids:
            return {}

        rank = func.row_number().over(
            partition_by=PlacementRisk.student_profile_id,
            order_by=(PlacementRisk.created_at.desc(), PlacementRisk.id.desc()),
        ).label("rank")
        subq = (
            select(PlacementRisk.id.label("id"), rank)
            .where(PlacementRisk.student_profile_id.in_(profile_ids))
            .subquery()
        )
        latest_rows = self.db.scalars(
            select(PlacementRisk)
            .join(subq, PlacementRisk.id == subq.c.id)
            .where(subq.c.rank == 1)
        ).all()
        return {row.student_profile_id: row for row in latest_rows}
