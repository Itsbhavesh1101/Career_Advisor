from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import create_session
from app.models.analysis_job import AnalysisJob
from app.models.student_profile import StudentProfile
from app.services.analysis_snapshot_service import AnalysisSnapshotService


class AnalysisJobService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_job(self, profile_id: int, user_id: int, *, allow_admin: bool = False) -> AnalysisJob:
        profile = self.db.get(StudentProfile, profile_id)
        if profile is None or (profile.user_id != user_id and not allow_admin):
            raise ValueError("Profile not found")

        job = AnalysisJob(
            id=str(uuid4()),
            student_profile_id=profile_id,
            user_id=user_id,
            status="queued",
            progress=0,
            message="Job queued",
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def get_job(self, job_id: str, user_id: int, *, allow_admin: bool = False) -> AnalysisJob | None:
        job = self.db.get(AnalysisJob, job_id)
        if job is None:
            return None
        if not allow_admin and job.user_id != user_id:
            return None
        return job

    def mark_job_failed(self, job_id: str, error: str, *, message: str = "Analysis job failed") -> None:
        job = self.db.get(AnalysisJob, job_id)
        if job is None:
            return
        job.status = "failed"
        job.progress = 100
        job.error = error
        job.message = message
        job.updated_at = datetime.now(timezone.utc)
        self.db.commit()


def run_analysis_job_by_id(job_id: str) -> None:
    db = create_session()
    try:
        job = db.get(AnalysisJob, job_id)
        if job is None:
            return

        profile = db.get(StudentProfile, job.student_profile_id)
        allow_admin_context = bool(profile is not None and profile.user_id != job.user_id)

        job.status = "running"
        job.progress = 15
        job.message = "Generating coherent analysis snapshot"
        job.updated_at = datetime.now(timezone.utc)
        db.commit()

        snapshot = AnalysisSnapshotService(db).generate_snapshot(
            job.student_profile_id,
            job.user_id,
            allow_admin=allow_admin_context,
        )

        job.status = "completed"
        job.progress = 100
        job.message = "Analysis snapshot completed"
        job.analysis_id = int(snapshot["career_analysis_id"])
        job.snapshot_summary = snapshot
        job.error = None
        job.updated_at = datetime.now(timezone.utc)
        db.commit()
    except Exception as exc:
        db.rollback()
        failed = db.get(AnalysisJob, job_id)
        if failed is not None:
            failed.status = "failed"
            failed.progress = 100
            failed.error = str(exc)
            failed.message = "Analysis job failed"
            failed.updated_at = datetime.now(timezone.utc)
            db.commit()
    finally:
        db.close()


def dispatch_analysis_job(job_id: str) -> None:
    settings = get_settings()
    if settings.celery_task_always_eager:
        run_analysis_job_by_id(job_id)
        return

    from app.services.analysis_jobs_worker import run_analysis_job_task

    run_analysis_job_task.delay(job_id)
