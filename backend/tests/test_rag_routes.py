from __future__ import annotations

from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api import deps
from app.api.routes import rag as rag_routes
from app.schemas.rag import RAGEvidence
from main import app


class _FakeDB:
    def __init__(self) -> None:
        self.closed = False

    def get(self, *_args):
        return None

    def scalars(self, *_args):
        return _EmptyScalarResult()

    def close(self) -> None:
        self.closed = True


class _EmptyScalarResult:
    def all(self):
        return []


def _override_auth():
    return SimpleNamespace(id=1, email="student@sage.local"), "user"


def _override_db():
    db = _FakeDB()
    try:
        yield db
    finally:
        db.close()


def test_rag_search_requires_auth() -> None:
    app.dependency_overrides.clear()
    app.dependency_overrides[deps.get_db] = _override_db
    try:
        client = TestClient(app)
        response = client.get("/api/v1/rag/search", params={"q": "AIML"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 401


def test_rag_search_returns_evidence() -> None:
    app.dependency_overrides[deps.get_current_user_context] = _override_auth
    app.dependency_overrides[deps.get_db] = _override_db
    try:
        client = TestClient(app)
        response = client.get("/api/v1/rag/search", params={"q": "AIML Python", "limit": 3})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "AIML Python"
    assert data["results"]
    assert data["results"][0]["source_title"]


def test_rag_search_accepts_source_type_filter() -> None:
    app.dependency_overrides[deps.get_current_user_context] = _override_auth
    app.dependency_overrides[deps.get_db] = _override_db
    try:
        client = TestClient(app)
        response = client.get(
            "/api/v1/rag/search",
            params={"q": "expectation reality", "source_type": "counseling"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["results"]
    assert all(item["source_type"] == "counseling" for item in data["results"])


def test_rag_search_uses_db_backed_service(monkeypatch) -> None:
    captured = {}

    class _FakeRAGService:
        def __init__(self, db=None) -> None:
            captured["db"] = db

        def search(self, query, *, source_types=None, limit=5):
            captured["query"] = query
            captured["source_types"] = source_types
            captured["limit"] = limit
            return [
                RAGEvidence(
                    chunk_id="doc-placement-0001",
                    source_title="Placement Handbook",
                    source_type="placement",
                    excerpt="AIML placement preparation uses DB-backed knowledge.",
                    score=3.0,
                    tags=["placement"],
                    program_ids=["aiml"],
                )
            ]

    monkeypatch.setattr(rag_routes, "RAGService", _FakeRAGService)
    app.dependency_overrides[deps.get_current_user_context] = _override_auth
    app.dependency_overrides[deps.get_db] = _override_db
    try:
        client = TestClient(app)
        response = client.get(
            "/api/v1/rag/search",
            params={"q": "AIML placement", "source_type": "placement", "limit": 1},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert isinstance(captured["db"], _FakeDB)
    assert captured["query"] == "AIML placement"
    assert captured["source_types"] == ["placement"]
    assert captured["limit"] == 1
    assert response.json()["results"][0]["chunk_id"] == "doc-placement-0001"
