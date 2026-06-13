from __future__ import annotations

from app.core.config import get_settings
from app.db.session import create_session
from app.schemas.rag import RAGEmbeddingIndexSummary
from app.services.rag_document_service import RAGDocumentService


def run_rag_embedding_reindex(
    *,
    source_id: int | None = None,
    limit: int = 100,
    retry_failed: bool = True,
) -> RAGEmbeddingIndexSummary:
    db = create_session()
    try:
        return RAGDocumentService(db).reindex_embeddings(
            source_id=source_id,
            limit=limit,
            retry_failed=retry_failed,
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def dispatch_rag_embedding_reindex(
    *,
    source_id: int | None = None,
    limit: int = 100,
    retry_failed: bool = True,
) -> RAGEmbeddingIndexSummary:
    bounded_limit = max(1, min(limit, 1000))
    settings = get_settings()
    if settings.celery_task_always_eager:
        return run_rag_embedding_reindex(
            source_id=source_id,
            limit=bounded_limit,
            retry_failed=retry_failed,
        )

    from app.services.rag_indexing_worker import run_rag_embedding_reindex_task

    run_rag_embedding_reindex_task.delay(
        source_id=source_id,
        limit=bounded_limit,
        retry_failed=retry_failed,
    )
    return RAGEmbeddingIndexSummary(
        queued=True,
        source_id=source_id,
        limit=bounded_limit,
    )
