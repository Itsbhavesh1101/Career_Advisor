from __future__ import annotations

from app.core.celery_app import celery_app
from app.services.rag_indexing_service import run_rag_embedding_reindex


@celery_app.task(name="rag.reindex_embeddings")
def run_rag_embedding_reindex_task(
    *,
    source_id: int | None = None,
    limit: int = 100,
    retry_failed: bool = True,
) -> dict[str, object]:
    summary = run_rag_embedding_reindex(
        source_id=source_id,
        limit=limit,
        retry_failed=retry_failed,
    )
    return summary.model_dump()
