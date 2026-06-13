from __future__ import annotations

from app.core.celery_app import celery_app
from app.services.analysis_job_service import run_analysis_job_by_id


@celery_app.task(name="analysis.run_job")
def run_analysis_job_task(job_id: str) -> None:
    run_analysis_job_by_id(job_id)
