from __future__ import annotations

import asyncio
import logging

from app.core.config import get_settings
from app.db.session import create_session
from app.services.data_retention_service import DataRetentionService

logger = logging.getLogger(__name__)


def run_retention_cleanup_once() -> dict[str, int]:
    settings = get_settings()
    db = create_session()
    try:
        service = DataRetentionService(db)
        summary = service.cleanup(
            retention_days=settings.data_retention_days,
            keep_latest_per_profile=settings.data_retention_keep_latest_per_profile,
        )
        logger.info("Retention cleanup completed: %s", summary)
        return summary
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


async def run_retention_loop(stop_event: asyncio.Event) -> None:
    settings = get_settings()
    interval_seconds = max(60, settings.data_retention_cleanup_interval_minutes * 60)

    if settings.data_retention_run_on_startup:
        try:
            await asyncio.to_thread(run_retention_cleanup_once)
        except Exception as exc:
            logger.exception("Startup retention cleanup failed: %s", exc)

    while not stop_event.is_set():
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval_seconds)
            break
        except TimeoutError:
            try:
                await asyncio.to_thread(run_retention_cleanup_once)
            except Exception as exc:
                logger.exception("Scheduled retention cleanup failed: %s", exc)