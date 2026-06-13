from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
from pathlib import Path
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.career_analysis import CareerAnalysis
from app.models.company_fit import CompanyFit
from app.models.employability_score import EmployabilityScore
from app.models.internship_readiness import InternshipReadiness
from app.models.placement_risk import PlacementRisk
from app.models.psychometric_session import PsychometricSession
from app.models.resume_analysis import ResumeAnalysis
from app.models.role_gap_analysis import RoleGapAnalysis
from app.services.resume_service import STORAGE_ROOT

logger = logging.getLogger(__name__)


class DataRetentionService:
    def __init__(self, db: Session, storage_root: Path | None = None) -> None:
        self.db = db
        self.storage_root = storage_root or STORAGE_ROOT

    def cleanup(self, retention_days: int, keep_latest_per_profile: int) -> dict[str, int]:
        if retention_days < 1:
            raise ValueError("Retention days must be >= 1.")

        keep_latest = max(1, keep_latest_per_profile)
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)

        summary: dict[str, int] = {}
        summary["career_analyses"] = self._prune_by_profile(
            CareerAnalysis,
            cutoff,
            keep_latest,
        )
        summary["company_fits"] = self._prune_by_profile(CompanyFit, cutoff, keep_latest)
        summary["employability_scores"] = self._prune_by_profile(
            EmployabilityScore,
            cutoff,
            keep_latest,
        )
        summary["internship_readiness"] = self._prune_by_profile(
            InternshipReadiness,
            cutoff,
            keep_latest,
        )
        summary["placement_risks"] = self._prune_by_profile(
            PlacementRisk,
            cutoff,
            keep_latest,
        )
        summary["role_gap_analyses"] = self._prune_by_profile(
            RoleGapAnalysis,
            cutoff,
            keep_latest,
        )
        summary["psychometric_sessions"] = self._prune_by_profile(
            PsychometricSession,
            cutoff,
            keep_latest,
        )

        deleted_resume_rows, deleted_refs = self._prune_resume_analyses(cutoff, keep_latest)
        summary["resume_analyses"] = deleted_resume_rows

        # Persist DB pruning first so file cleanup cannot rollback record retention changes.
        self.db.commit()

        deleted_resume_files = self._delete_resume_files(deleted_refs)
        deleted_orphaned_files = self._delete_orphaned_resume_files(cutoff)
        self._delete_empty_resume_directories()
        summary["resume_files"] = deleted_resume_files + deleted_orphaned_files
        return summary

    def _prune_by_profile(self, model: type[Any], cutoff: datetime, keep_latest: int) -> int:
        rows = self.db.scalars(
            select(model).order_by(model.student_profile_id, model.created_at.desc(), model.id.desc())
        ).all()

        kept_per_profile: dict[int, int] = {}
        delete_ids: list[int] = []
        for row in rows:
            profile_id = int(row.student_profile_id)
            kept_per_profile[profile_id] = kept_per_profile.get(profile_id, 0) + 1

            if kept_per_profile[profile_id] <= keep_latest:
                continue

            if self._normalize_timestamp(row.created_at) < cutoff:
                delete_ids.append(int(row.id))

        if not delete_ids:
            return 0

        self.db.execute(delete(model).where(model.id.in_(delete_ids)))
        return len(delete_ids)

    def _prune_resume_analyses(
        self, cutoff: datetime, keep_latest: int
    ) -> tuple[int, list[tuple[int, str]]]:
        rows = self.db.scalars(
            select(ResumeAnalysis).order_by(
                ResumeAnalysis.student_profile_id,
                ResumeAnalysis.created_at.desc(),
                ResumeAnalysis.id.desc(),
            )
        ).all()

        kept_per_profile: dict[int, int] = {}
        delete_ids: list[int] = []
        deleted_refs: list[tuple[int, str]] = []
        for row in rows:
            profile_id = int(row.student_profile_id)
            kept_per_profile[profile_id] = kept_per_profile.get(profile_id, 0) + 1

            if kept_per_profile[profile_id] <= keep_latest:
                continue

            if self._normalize_timestamp(row.created_at) < cutoff:
                delete_ids.append(int(row.id))
                deleted_refs.append((profile_id, row.file_name))

        if not delete_ids:
            return 0, []

        self.db.execute(delete(ResumeAnalysis).where(ResumeAnalysis.id.in_(delete_ids)))
        return len(delete_ids), deleted_refs

    def _delete_resume_files(self, refs: list[tuple[int, str]]) -> int:
        deleted = 0
        for profile_id, file_name in refs:
            target = self._safe_resume_path(profile_id, file_name)
            if target is None:
                continue
            try:
                if target.exists() and target.is_file():
                    target.unlink()
                    deleted += 1
            except OSError as exc:
                logger.warning("Failed to delete stale resume file '%s': %s", target, exc)
        return deleted

    def _delete_orphaned_resume_files(self, cutoff: datetime) -> int:
        if not self.storage_root.exists():
            return 0

        tracked_refs = {
            (int(row.student_profile_id), row.file_name)
            for row in self.db.scalars(select(ResumeAnalysis)).all()
        }

        deleted = 0
        for profile_dir in self.storage_root.iterdir():
            if not profile_dir.is_dir() or not profile_dir.name.isdigit():
                continue

            profile_id = int(profile_dir.name)
            for file_path in profile_dir.iterdir():
                if not file_path.is_file():
                    continue

                if (profile_id, file_path.name) in tracked_refs:
                    continue

                modified_at = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc)
                if modified_at >= cutoff:
                    continue

                try:
                    file_path.unlink()
                    deleted += 1
                except OSError as exc:
                    logger.warning("Failed to delete orphaned resume file '%s': %s", file_path, exc)

        return deleted

    def _delete_empty_resume_directories(self) -> None:
        if not self.storage_root.exists():
            return

        for profile_dir in self.storage_root.iterdir():
            if not profile_dir.is_dir():
                continue
            try:
                next(profile_dir.iterdir())
            except StopIteration:
                try:
                    profile_dir.rmdir()
                except OSError:
                    continue

    def _safe_resume_path(self, profile_id: int, file_name: str) -> Path | None:
        root = self.storage_root.resolve()
        target = (self.storage_root / str(profile_id) / file_name).resolve()
        if root not in target.parents:
            logger.warning("Blocked unsafe resume path during retention cleanup: %s", target)
            return None
        return target

    def _normalize_timestamp(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)