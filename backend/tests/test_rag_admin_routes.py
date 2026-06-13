from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.api import deps
from app.api.routes import rag as rag_routes
from app.schemas.rag import RAGDocumentSourceRead, RAGEmbeddingIndexSummary
from main import app


class _FakeDB:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


def _override_db():
    db = _FakeDB()
    try:
        yield db
    finally:
        db.close()


def _override_admin():
    return SimpleNamespace(id=10, email="admin@sage.local"), "admin"


def _override_user():
    return SimpleNamespace(id=11, email="student@sage.local"), "user"


def _source_read(*, status: str = "active") -> RAGDocumentSourceRead:
    now = datetime(2026, 5, 20, tzinfo=timezone.utc)
    return RAGDocumentSourceRead(
        id=7,
        title="Placement Handbook",
        source_type="placement",
        status=status,
        review_status="pending_review",
        review_notes=None,
        reviewed_by_user_id=None,
        reviewed_at=None,
        expires_at=None,
        freshness_status="current",
        tags=["placement"],
        program_ids=["aiml"],
        chunk_count=2 if status == "active" else 0,
        created_at=now,
        updated_at=now,
    )


class _FakeRAGDocumentService:
    last_db = None
    created_by_user_id = None
    created_payload = None
    updated_status = None
    updated_review = None

    def __init__(self, db) -> None:
        type(self).last_db = db

    def create_source(self, payload, created_by_user_id):
        type(self).created_payload = payload
        type(self).created_by_user_id = created_by_user_id
        return _source_read()

    def list_sources(self):
        return [_source_read()]

    def update_status(self, source_id, status):
        type(self).updated_status = (source_id, status)
        return _source_read(status=status)

    def update_review(self, source_id, payload, reviewed_by_user_id):
        type(self).updated_review = (source_id, payload, reviewed_by_user_id)
        source = _source_read()
        source.review_status = payload.review_status
        source.review_notes = payload.review_notes
        source.reviewed_by_user_id = reviewed_by_user_id
        source.reviewed_at = datetime(2026, 5, 21, tzinfo=timezone.utc)
        source.expires_at = payload.expires_at
        return source


class _FakeRAGFileService:
    last_file_name = None
    last_payload = None

    def extract_text(self, file_name, data):
        type(self).last_file_name = file_name
        type(self).last_payload = data
        return "Placement policy extracted from uploaded file. " * 2


def _fake_dispatch_reindex(*, source_id=None, limit=100, retry_failed=True):
    return RAGEmbeddingIndexSummary(
        queued=False,
        source_id=source_id,
        limit=limit,
        examined=3,
        indexed=2,
        failed=1,
        skipped=0,
    )


@pytest.fixture(autouse=True)
def _clear_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


def test_non_admin_users_cannot_create_knowledge_sources(monkeypatch) -> None:
    monkeypatch.setattr(rag_routes, "RAGDocumentService", _FakeRAGDocumentService)
    app.dependency_overrides[deps.get_current_user_context] = _override_user
    app.dependency_overrides[deps.get_db] = _override_db

    client = TestClient(app)
    response = client.post(
        "/api/v1/rag/admin/sources",
        json={
            "title": "Placement Handbook",
            "source_type": "placement",
            "text": "Placement preparation guidance for AIML students. " * 4,
            "tags": ["placement"],
            "program_ids": ["aiml"],
        },
    )

    assert response.status_code == 403


def test_admin_can_create_source_and_receives_chunk_count(monkeypatch) -> None:
    monkeypatch.setattr(rag_routes, "RAGDocumentService", _FakeRAGDocumentService)
    app.dependency_overrides[deps.get_current_user_context] = _override_admin
    app.dependency_overrides[deps.get_db] = _override_db

    client = TestClient(app)
    response = client.post(
        "/api/v1/rag/admin/sources",
        json={
            "title": "Placement Handbook",
            "source_type": "placement",
            "text": "Placement preparation guidance for AIML students. " * 4,
            "tags": ["placement"],
            "program_ids": ["aiml"],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 7
    assert data["chunk_count"] == 2
    assert data["review_status"] == "pending_review"
    assert _FakeRAGDocumentService.created_by_user_id == 10
    assert _FakeRAGDocumentService.created_payload.title == "Placement Handbook"


def test_admin_can_list_sources(monkeypatch) -> None:
    monkeypatch.setattr(rag_routes, "RAGDocumentService", _FakeRAGDocumentService)
    app.dependency_overrides[deps.get_current_user_context] = _override_admin
    app.dependency_overrides[deps.get_db] = _override_db

    client = TestClient(app)
    response = client.get("/api/v1/rag/admin/sources")

    assert response.status_code == 200
    data = response.json()
    assert data["items"][0]["title"] == "Placement Handbook"
    assert data["items"][0]["chunk_count"] == 2
    assert data["items"][0]["review_status"] == "pending_review"


def test_admin_can_deactivate_source(monkeypatch) -> None:
    monkeypatch.setattr(rag_routes, "RAGDocumentService", _FakeRAGDocumentService)
    app.dependency_overrides[deps.get_current_user_context] = _override_admin
    app.dependency_overrides[deps.get_db] = _override_db

    client = TestClient(app)
    response = client.patch(
        "/api/v1/rag/admin/sources/7/status",
        json={"status": "inactive"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "inactive"
    assert data["chunk_count"] == 0
    assert _FakeRAGDocumentService.updated_status == (7, "inactive")


def test_admin_can_approve_source_review(monkeypatch) -> None:
    monkeypatch.setattr(rag_routes, "RAGDocumentService", _FakeRAGDocumentService)
    app.dependency_overrides[deps.get_current_user_context] = _override_admin
    app.dependency_overrides[deps.get_db] = _override_db

    client = TestClient(app)
    response = client.patch(
        "/api/v1/rag/admin/sources/7/review",
        json={
            "review_status": "approved",
            "review_notes": "Approved for launch.",
            "expires_at": "2026-12-31T00:00:00Z",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["review_status"] == "approved"
    assert data["review_notes"] == "Approved for launch."
    assert data["reviewed_by_user_id"] == 10
    assert _FakeRAGDocumentService.updated_review[0] == 7
    assert _FakeRAGDocumentService.updated_review[2] == 10


def test_admin_can_dispatch_embedding_reindex(monkeypatch) -> None:
    monkeypatch.setattr(rag_routes, "dispatch_rag_embedding_reindex", _fake_dispatch_reindex)
    app.dependency_overrides[deps.get_current_user_context] = _override_admin
    app.dependency_overrides[deps.get_db] = _override_db

    client = TestClient(app)
    response = client.post(
        "/api/v1/rag/admin/embeddings/reindex",
        json={"source_id": 7, "limit": 25, "retry_failed": True},
    )

    assert response.status_code == 200
    assert response.json() == {
        "queued": False,
        "source_id": 7,
        "limit": 25,
        "examined": 3,
        "indexed": 2,
        "failed": 1,
        "skipped": 0,
    }


def test_non_admin_users_cannot_dispatch_embedding_reindex(monkeypatch) -> None:
    monkeypatch.setattr(rag_routes, "dispatch_rag_embedding_reindex", _fake_dispatch_reindex)
    app.dependency_overrides[deps.get_current_user_context] = _override_user
    app.dependency_overrides[deps.get_db] = _override_db

    client = TestClient(app)
    response = client.post(
        "/api/v1/rag/admin/embeddings/reindex",
        json={"limit": 25},
    )

    assert response.status_code == 403


def test_admin_can_upload_knowledge_file(monkeypatch) -> None:
    monkeypatch.setattr(rag_routes, "RAGDocumentService", _FakeRAGDocumentService)
    monkeypatch.setattr(rag_routes, "RAGFileService", _FakeRAGFileService)
    app.dependency_overrides[deps.get_current_user_context] = _override_admin
    app.dependency_overrides[deps.get_db] = _override_db

    client = TestClient(app)
    response = client.post(
        "/api/v1/rag/admin/sources/upload",
        data={
            "title": "Uploaded Placement Policy",
            "source_type": "placement",
            "tags": "placement, policy",
            "program_ids": "sirt-btech-cse-aiml",
        },
        files={
            "file": (
                "placement-policy.pdf",
                b"%PDF upload payload",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 200
    assert response.json()["id"] == 7
    assert response.json()["review_status"] == "pending_review"
    assert _FakeRAGFileService.last_file_name == "placement-policy.pdf"
    assert _FakeRAGFileService.last_payload == b"%PDF upload payload"
    assert _FakeRAGDocumentService.created_payload.title == "Uploaded Placement Policy"
    assert _FakeRAGDocumentService.created_payload.source_type == "placement"
    assert _FakeRAGDocumentService.created_payload.text.startswith("Placement policy")
    assert _FakeRAGDocumentService.created_payload.tags == ["placement", "policy"]
    assert _FakeRAGDocumentService.created_payload.program_ids == [
        "sirt-btech-cse-aiml"
    ]


def test_non_admin_users_cannot_upload_knowledge_file(monkeypatch) -> None:
    monkeypatch.setattr(rag_routes, "RAGDocumentService", _FakeRAGDocumentService)
    monkeypatch.setattr(rag_routes, "RAGFileService", _FakeRAGFileService)
    app.dependency_overrides[deps.get_current_user_context] = _override_user
    app.dependency_overrides[deps.get_db] = _override_db

    client = TestClient(app)
    response = client.post(
        "/api/v1/rag/admin/sources/upload",
        data={
            "title": "Uploaded Placement Policy",
            "source_type": "placement",
        },
        files={
            "file": (
                "placement-policy.pdf",
                b"%PDF upload payload",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 403
