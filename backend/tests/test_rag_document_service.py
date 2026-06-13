from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import insert
from sqlalchemy.dialects import postgresql

from app.models.rag_document import RAGDocumentChunk
from app.services.embedding_service import HashEmbeddingProvider
from app.schemas.rag import RAGDocumentSourceCreate, RAGDocumentSourceReviewUpdate
from app.services.rag_document_service import RAGDocumentService


class _ScalarResult:
    def __init__(self, rows: list[object]) -> None:
        self._rows = rows

    def all(self) -> list[object]:
        return list(self._rows)


class _FakeDB:
    def __init__(self) -> None:
        self.sources: list[object] = []
        self.added: list[object] = []
        self.commits = 0
        self.refreshed: object | None = None
        self._next_source_id = 1
        self._next_chunk_id = 1

    def add(self, row: object) -> None:
        self.added.append(row)
        if row not in self.sources:
            self.sources.append(row)

    def commit(self) -> None:
        self.commits += 1
        for source in self.sources:
            if getattr(source, "id", None) is None:
                source.id = self._next_source_id
                self._next_source_id += 1
            for chunk in getattr(source, "chunks", []):
                if getattr(chunk, "id", None) is None:
                    chunk.id = self._next_chunk_id
                    self._next_chunk_id += 1
                chunk.source_id = source.id

    def refresh(self, row: object) -> None:
        self.refreshed = row

    def get(self, _model: object, row_id: int) -> object | None:
        return next((source for source in self.sources if source.id == row_id), None)

    def scalars(self, _stmt: object) -> _ScalarResult:
        return _ScalarResult(self.sources)


class _FailingEmbeddingProvider:
    provider = "bedrock"
    model = "failing-embedding-model"
    dimensions = 256

    def embed(self, _text: str):
        raise RuntimeError("embedding provider unavailable")


def _payload(**overrides: object) -> RAGDocumentSourceCreate:
    data = {
        "title": "AIML Placement Handbook",
        "source_type": "placement",
        "text": (
            "AIML placement readiness depends on Python projects, machine learning "
            "foundations, interview practice, and documented internships. Counselors "
            "should connect these students with capstone reviews and placement labs."
        ),
        "tags": ["aiml", "placement"],
        "program_ids": ["sirt-btech-cse-aiml"],
    }
    data.update(overrides)
    return RAGDocumentSourceCreate.model_validate(data)


def _approve(service: RAGDocumentService, source_id: int) -> None:
    service.update_review(
        source_id,
        RAGDocumentSourceReviewUpdate(review_status="approved"),
        reviewed_by_user_id=42,
    )


def test_chunk_text_splits_into_stable_chunks_under_limit_when_possible() -> None:
    text = " ".join(
        [
            "AIML students need Python projects and mathematics readiness.",
            "Placement mentors review internships and machine learning portfolios.",
            "Counselors map branch fit to realistic training plans.",
        ]
        * 12
    )
    service = RAGDocumentService(_FakeDB())

    first = service.chunk_text(text, max_chars=180)
    second = service.chunk_text(text, max_chars=180)

    assert first == second
    assert len(first) > 1
    assert all(len(chunk) <= 180 for chunk in first)
    assert "AIML students" in first[0]


def test_create_source_persists_source_and_generated_chunks() -> None:
    db = _FakeDB()
    service = RAGDocumentService(db)

    source = service.create_source(_payload(), created_by_user_id=42)

    assert source.id == 1
    assert source.status == "active"
    assert source.review_status == "pending_review"
    assert source.created_by_user_id == 42
    assert source.content_hash
    assert len(source.chunks) == 1
    assert source.chunks[0].chunk_id.startswith("doc-")
    assert source.chunks[0].source_title == source.title
    assert source.chunks[0].is_active is True
    assert source.chunks[0].embedding is not None
    assert source.chunks[0].embedding.startswith("[")
    assert source.chunks[0].embedding_provider == "hash"
    assert source.chunks[0].embedding_model == "local-token-hash-v1"
    assert source.chunks[0].embedding_dimensions == 256
    assert source.chunks[0].embedding_status == "indexed"
    assert source.chunks[0].embedding_error is None
    assert source.chunks[0].embedding_attempts == 1
    assert source.chunks[0].embedding_updated_at is not None
    assert db.added == [source]
    assert db.commits == 1
    assert db.refreshed is source


def test_pgvector_embedding_insert_casts_literal_for_postgres() -> None:
    statement = insert(RAGDocumentChunk).values(
        source_id=1,
        chunk_id="doc-test-0000",
        chunk_index=0,
        source_title="Vector Test",
        source_type="placement",
        text="Vector insert test.",
        embedding="[0.1,0.2,0.3]",
        tags=[],
        program_ids=[],
    )

    compiled = str(statement.compile(dialect=postgresql.dialect()))

    assert "CAST(" in compiled
    assert "AS extensions.vector(256)" in compiled


def test_create_source_keeps_source_when_embedding_provider_fails(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.rag_document_service.create_embedding_provider",
        lambda: _FailingEmbeddingProvider(),
    )
    db = _FakeDB()
    service = RAGDocumentService(db)

    source = service.create_source(_payload(), created_by_user_id=42)

    assert len(source.chunks) == 1
    chunk = source.chunks[0]
    assert chunk.embedding is None
    assert chunk.embedding_status == "failed"
    assert chunk.embedding_provider == "bedrock"
    assert chunk.embedding_model == "failing-embedding-model"
    assert chunk.embedding_dimensions == 256
    assert chunk.embedding_attempts == 1
    assert "embedding provider unavailable" in chunk.embedding_error
    assert db.commits == 1


def test_create_source_generates_unique_chunk_ids_for_duplicate_content() -> None:
    db = _FakeDB()
    service = RAGDocumentService(db)

    first = service.create_source(_payload(), created_by_user_id=42)
    second = service.create_source(_payload(), created_by_user_id=42)

    first_ids = {chunk.chunk_id for chunk in first.chunks}
    second_ids = {chunk.chunk_id for chunk in second.chunks}

    assert first_ids
    assert second_ids
    assert first_ids.isdisjoint(second_ids)


def test_list_sources_includes_chunk_count() -> None:
    db = _FakeDB()
    service = RAGDocumentService(db)
    source = service.create_source(_payload(), created_by_user_id=42)
    _approve(service, source.id)

    sources = service.list_sources()

    assert len(sources) == 1
    assert sources[0].review_status == "approved"
    assert sources[0].title == "AIML Placement Handbook"
    assert sources[0].chunk_count == 1
    assert isinstance(sources[0].created_at, datetime)


def test_update_status_deactivates_source_chunks() -> None:
    db = _FakeDB()
    service = RAGDocumentService(db)
    source = service.create_source(_payload(), created_by_user_id=42)

    updated = service.update_status(source.id, "inactive")

    assert updated.status == "inactive"
    assert all(chunk.is_active is False for chunk in updated.chunks)
    assert db.commits == 2


def test_search_returns_only_active_chunks_and_respects_filters() -> None:
    db = _FakeDB()
    service = RAGDocumentService(db)
    source = service.create_source(_payload(), created_by_user_id=42)
    _approve(service, source.id)
    inactive = service.create_source(
        _payload(
            title="Inactive Counseling Guide",
            source_type="counseling",
            tags=["counseling"],
            program_ids=["sirt-btech-cse-cyber"],
            text=(
                "Cyber counseling should mention Linux networking readiness and "
                "security labs, but this source is inactive and hidden from search."
            ),
        ),
        created_by_user_id=42,
    )
    service.update_status(inactive.id, "inactive")

    results = service.search(
        "Python machine learning placement",
        source_types=["placement"],
        program_ids=["sirt-btech-cse-aiml"],
        limit=5,
    )
    excluded = service.search("Linux security counseling", limit=5)

    assert [result.source_title for result in results] == ["AIML Placement Handbook"]
    assert results[0].score > 0
    assert results[0].source_type == "placement"
    assert results[0].program_ids == ["sirt-btech-cse-aiml"]
    assert excluded == []


def test_semantic_search_uses_stored_embeddings_with_filters() -> None:
    db = _FakeDB()
    service = RAGDocumentService(db)
    source = service.create_source(_payload(), created_by_user_id=42)
    _approve(service, source.id)
    second = service.create_source(
        _payload(
            title="Cyber Networking Handbook",
            source_type="placement",
            tags=["cyber", "networking"],
            program_ids=["sirt-btech-cse-cyber"],
            text=(
                "Cyber placement readiness depends on Linux networking labs, "
                "security projects, packet analysis, and defensive tooling practice."
            ),
        ),
        created_by_user_id=42,
    )
    _approve(service, second.id)

    results = service.semantic_search(
        "machine learning python capstone placement",
        source_types=["placement"],
        program_ids=["sirt-btech-cse-aiml"],
        limit=2,
    )

    assert results
    assert results[0].source_title == "AIML Placement Handbook"
    assert results[0].score > 0
    assert results[0].program_ids == ["sirt-btech-cse-aiml"]


def test_reindex_embeddings_backfills_missing_chunk_embeddings() -> None:
    db = _FakeDB()
    service = RAGDocumentService(db)
    source = service.create_source(_payload(), created_by_user_id=42)
    chunk = source.chunks[0]
    chunk.embedding = None
    chunk.embedding_provider = None
    chunk.embedding_model = None
    chunk.embedding_dimensions = None
    chunk.embedding_status = "pending"
    chunk.embedding_error = None
    chunk.embedding_attempts = 0

    summary = service.reindex_embeddings(limit=5)

    assert summary.examined == 1
    assert summary.indexed == 1
    assert summary.failed == 0
    assert summary.skipped == 0
    assert chunk.embedding is not None
    assert chunk.embedding_status == "indexed"
    assert chunk.embedding_provider == "hash"
    assert chunk.embedding_attempts == 1
    assert chunk.embedding_error is None


def test_reindex_embeddings_retries_failed_chunks(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.rag_document_service.create_embedding_provider",
        lambda: _FailingEmbeddingProvider(),
    )
    db = _FakeDB()
    service = RAGDocumentService(db)
    source = service.create_source(_payload(), created_by_user_id=42)
    failed_chunk = source.chunks[0]

    monkeypatch.setattr(
        "app.services.rag_document_service.create_embedding_provider",
        lambda: HashEmbeddingProvider(),
    )
    summary = service.reindex_embeddings(limit=5, retry_failed=True)

    assert summary.examined == 1
    assert summary.indexed == 1
    assert summary.failed == 0
    assert failed_chunk.embedding is not None
    assert failed_chunk.embedding_status == "indexed"
    assert failed_chunk.embedding_attempts == 2
    assert failed_chunk.embedding_error is None
