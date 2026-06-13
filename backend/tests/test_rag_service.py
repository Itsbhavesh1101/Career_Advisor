from __future__ import annotations

from app.schemas.rag import RAGDocumentSourceCreate, RAGDocumentSourceReviewUpdate
from app.schemas.rag import RAGEvidence
from app.services.rag_document_service import RAGDocumentService
from app.services.rag_service import RAGService


class _ScalarResult:
    def __init__(self, rows: list[object]) -> None:
        self._rows = rows

    def all(self) -> list[object]:
        return list(self._rows)


class _FakeDB:
    def __init__(self) -> None:
        self.sources: list[object] = []
        self._next_source_id = 1
        self._next_chunk_id = 1

    def add(self, row: object) -> None:
        if row not in self.sources:
            self.sources.append(row)

    def commit(self) -> None:
        for source in self.sources:
            if getattr(source, "id", None) is None:
                source.id = self._next_source_id
                self._next_source_id += 1
            for chunk in getattr(source, "chunks", []):
                if getattr(chunk, "id", None) is None:
                    chunk.id = self._next_chunk_id
                    self._next_chunk_id += 1
                chunk.source_id = source.id

    def refresh(self, _row: object) -> None:
        return None

    def get(self, _model: object, row_id: int) -> object | None:
        return next((source for source in self.sources if source.id == row_id), None)

    def scalars(self, _stmt: object) -> _ScalarResult:
        return _ScalarResult(self.sources)


def _document_payload(**overrides: object) -> RAGDocumentSourceCreate:
    data = {
        "title": "AIML Admin Placement Guide",
        "source_type": "program",
        "text": (
            "AIML admin placement readiness depends on Python projects, machine "
            "learning labs, portfolio reviews, and interview practice for students."
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
        reviewed_by_user_id=1,
    )


def test_rag_catalog_loads_seeded_chunks() -> None:
    service = RAGService()

    chunks = service.list_chunks()

    assert len(chunks) >= 8
    assert any(chunk.source_type == "program" for chunk in chunks)
    assert any(chunk.source_type == "counseling" for chunk in chunks)


def test_generic_mode_does_not_load_seeded_sage_chunks(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.rag_service.get_settings",
        lambda: type(
            "Settings",
            (),
            {"institution_mode": "generic", "rag_vector_search_enabled": True},
        )(),
    )

    service = RAGService()

    assert service.list_chunks() == []
    assert service.search("SAGE SIRT AIML admissions", limit=5) == []


def test_rag_search_returns_ranked_program_evidence() -> None:
    service = RAGService()

    results = service.search("AIML python mathematics machine learning", limit=3)

    assert results
    assert results[0].score > 0
    assert any("AIML" in item.source_title or "AI" in item.excerpt for item in results)


def test_rag_search_filters_source_types() -> None:
    service = RAGService()

    results = service.search(
        "counseling expectation reality branch confusion",
        source_types=["counseling"],
        limit=5,
    )

    assert results
    assert all(item.source_type == "counseling" for item in results)


def test_rag_search_filters_program_ids() -> None:
    service = RAGService()

    results = service.search(
        "linux networking systems cyber security readiness",
        program_ids=["sirt-btech-cse-cyber"],
        limit=5,
    )

    assert results
    assert any(item.chunk_id == "program-cyber-foundation" for item in results)
    assert all("sirt-btech-cse-cyber" in item.program_ids for item in results)


def test_rag_search_program_filter_excludes_generic_chunks() -> None:
    service = RAGService()

    results = service.search(
        "readiness",
        program_ids=["sirt-btech-cse-cyber"],
        limit=5,
    )

    assert all("sirt-btech-cse-cyber" in item.program_ids for item in results)


def test_rag_search_honors_limit_and_short_excerpts() -> None:
    service = RAGService()

    results = service.search("programming mathematics projects readiness", limit=2)

    assert len(results) <= 2
    assert all(1 <= len(item.excerpt) <= 360 for item in results)


def test_rag_knowledge_base_returns_deep_copies() -> None:
    service = RAGService()

    first = service.get_knowledge_base()
    first.chunks[0].tags.append("mutated")
    first.chunks[0].text = "This mutation should not leak into cached state."

    second = service.get_knowledge_base()

    assert "mutated" not in second.chunks[0].tags
    assert second.chunks[0].text != "This mutation should not leak into cached state."


def test_rag_search_returns_empty_for_blank_query() -> None:
    assert RAGService().search("   ") == []


def test_rag_service_with_db_returns_seeded_and_active_document_chunks() -> None:
    db = _FakeDB()
    document_service = RAGDocumentService(db)
    source = document_service.create_source(_document_payload(), created_by_user_id=1)
    _approve(document_service, source.id)
    service = RAGService(db)

    chunks = service.list_chunks()
    results = service.search(
        "AIML Python projects mathematics machine learning readiness",
        source_types=["program"],
        program_ids=["sirt-btech-cse-aiml"],
        limit=10,
    )

    assert any(chunk.chunk_id == "program-aiml-foundation" for chunk in chunks)
    assert any(chunk.chunk_id.startswith("doc-") for chunk in chunks)
    assert any(result.chunk_id == "program-aiml-foundation" for result in results)
    assert any(result.chunk_id.startswith("doc-") for result in results)
    assert all(result.source_type == "program" for result in results)
    assert all("sirt-btech-cse-aiml" in result.program_ids for result in results)


def test_rag_service_with_db_excludes_inactive_document_chunks() -> None:
    db = _FakeDB()
    document_service = RAGDocumentService(db)
    active = document_service.create_source(_document_payload(), created_by_user_id=1)
    _approve(document_service, active.id)
    inactive = document_service.create_source(
        _document_payload(
            title="Inactive Scholarship Pilot",
            source_type="policy",
            text=(
                "Aquamarine scholarship pilot guidance is archived and should not "
                "appear in active retrieval results for counselors."
            ),
            tags=["aquamarine"],
            program_ids=[],
        ),
        created_by_user_id=1,
    )
    document_service.update_status(inactive.id, "inactive")

    results = RAGService(db).search("aquamarine scholarship pilot", limit=10)

    assert active.status == "active"
    assert all(not result.chunk_id.startswith("doc-") for result in results)


def test_rag_service_prefers_semantic_document_results_when_available(monkeypatch) -> None:
    db = _FakeDB()
    RAGDocumentService(db).create_source(_document_payload(), created_by_user_id=1)

    def _semantic_search(self, query, *, source_types=None, program_ids=None, limit=5):
        assert query == "Python placement projects"
        assert source_types == ["program"]
        assert program_ids == ["sirt-btech-cse-aiml"]
        assert limit == 3
        return [
            RAGEvidence(
                chunk_id="doc-semantic-0001",
                source_title="Semantic Placement Guide",
                source_type="program",
                excerpt="Semantic match from pgvector.",
                score=0.91,
                tags=["placement"],
                program_ids=["sirt-btech-cse-aiml"],
            )
        ]

    monkeypatch.setattr(RAGDocumentService, "semantic_search", _semantic_search)

    results = RAGService(db).search(
        "Python placement projects",
        source_types=["program"],
        program_ids=["sirt-btech-cse-aiml"],
        limit=3,
    )

    assert results[0].chunk_id == "doc-semantic-0001"


def test_rag_service_falls_back_to_lexical_search_when_semantic_search_fails(
    monkeypatch,
) -> None:
    db = _FakeDB()
    RAGDocumentService(db).create_source(_document_payload(), created_by_user_id=1)

    def _semantic_search(self, query, *, source_types=None, program_ids=None, limit=5):
        raise RuntimeError("pgvector unavailable")

    monkeypatch.setattr(RAGDocumentService, "semantic_search", _semantic_search)

    results = RAGService(db).search(
        "AIML Python projects machine learning readiness",
        source_types=["program"],
        program_ids=["sirt-btech-cse-aiml"],
        limit=5,
    )

    assert results
    assert any(result.chunk_id == "program-aiml-foundation" for result in results)
