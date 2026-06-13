from __future__ import annotations

from app.schemas.rag import RAGEmbeddingIndexSummary
from app.services import rag_indexing_service


class _Settings:
    celery_task_always_eager = True


def test_dispatch_rag_embedding_reindex_runs_inline_when_eager(monkeypatch) -> None:
    calls: list[dict[str, object]] = []

    def _run(*, source_id=None, limit=100, retry_failed=True):
        calls.append(
            {
                "source_id": source_id,
                "limit": limit,
                "retry_failed": retry_failed,
            }
        )
        return RAGEmbeddingIndexSummary(
            source_id=source_id,
            limit=limit,
            examined=1,
            indexed=1,
        )

    monkeypatch.setattr(rag_indexing_service, "get_settings", lambda: _Settings())
    monkeypatch.setattr(rag_indexing_service, "run_rag_embedding_reindex", _run)

    summary = rag_indexing_service.dispatch_rag_embedding_reindex(
        source_id=7,
        limit=25,
        retry_failed=False,
    )

    assert summary.queued is False
    assert summary.indexed == 1
    assert calls == [
        {
            "source_id": 7,
            "limit": 25,
            "retry_failed": False,
        }
    ]


def test_dispatch_rag_embedding_reindex_queues_when_not_eager(monkeypatch) -> None:
    class _QueuedSettings:
        celery_task_always_eager = False

    class _Task:
        calls: list[dict[str, object]] = []

        @classmethod
        def delay(cls, **kwargs):
            cls.calls.append(kwargs)

    monkeypatch.setattr(rag_indexing_service, "get_settings", lambda: _QueuedSettings())
    monkeypatch.setattr(
        "app.services.rag_indexing_worker.run_rag_embedding_reindex_task",
        _Task,
    )

    summary = rag_indexing_service.dispatch_rag_embedding_reindex(
        source_id=7,
        limit=25,
        retry_failed=True,
    )

    assert summary == RAGEmbeddingIndexSummary(
        queued=True,
        source_id=7,
        limit=25,
    )
    assert _Task.calls == [
        {
            "source_id": 7,
            "limit": 25,
            "retry_failed": True,
        }
    ]
