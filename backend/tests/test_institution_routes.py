from __future__ import annotations

from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api import deps
from main import app


class _FakeDB:
    def __init__(self, saved: object | None = None) -> None:
        self.saved = saved
        self.added = None
        self.committed = False
        self.refreshed = None
        self.closed = False

    def scalar(self, _stmt):
        return self.saved

    def add(self, row) -> None:
        self.added = row
        self.saved = row

    def commit(self) -> None:
        self.committed = True

    def refresh(self, row) -> None:
        row.id = getattr(row, "id", 1)
        self.refreshed = row

    def close(self) -> None:
        self.closed = True


def _override_auth(role: str):
    def _auth():
        return SimpleNamespace(id=1, email=f"{role}@sage.local"), role

    return _auth


def _override_db(db: _FakeDB):
    def _db():
        try:
            yield db
        finally:
            db.close()

    return _db


def _reset_overrides() -> None:
    app.dependency_overrides.clear()


def test_list_institution_programs_requires_auth() -> None:
    _reset_overrides()
    db = _FakeDB()
    app.dependency_overrides[deps.get_db] = _override_db(db)
    try:
        client = TestClient(app)
        response = client.get("/api/v1/institution/programs")
    finally:
        _reset_overrides()

    assert response.status_code == 401


def test_get_branding_is_public() -> None:
    _reset_overrides()
    try:
        client = TestClient(app)
        response = client.get("/api/v1/institution/branding")
    finally:
        _reset_overrides()

    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "sage"
    assert data["product_name"] == "SAGE Career Navigator"
    assert data["institution_short_name"] == "SAGE/SIRT"


def test_get_branding_can_return_generic(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.api.routes.institution.InstitutionConfigService",
        lambda: SimpleNamespace(
            get_branding=lambda: {
                "mode": "generic",
                "product_name": "Student Success Navigator",
                "institution_name": "Partner Institution",
                "institution_short_name": "Partner Institution",
                "homepage": {},
                "auth": {},
                "branch_guidance": {},
                "placement_readiness": {},
                "admin_command": {},
            }
        ),
    )

    _reset_overrides()
    try:
        client = TestClient(app)
        response = client.get("/api/v1/institution/branding")
    finally:
        _reset_overrides()

    assert response.status_code == 200
    assert response.json()["product_name"] == "Student Success Navigator"


def test_list_institution_programs_returns_catalog() -> None:
    db = _FakeDB()
    app.dependency_overrides[deps.get_db] = _override_db(db)
    app.dependency_overrides[deps.get_current_user_context] = _override_auth("user")
    try:
        client = TestClient(app)
        response = client.get("/api/v1/institution/programs")
    finally:
        _reset_overrides()

    assert response.status_code == 200
    data = response.json()
    assert data["institution_name"] == "SAGE Group of Institutions"
    assert any(
        program["program_id"] == "sirt-btech-cse-aiml"
        for school in data["schools"]
        for program in school["programs"]
    )


def test_get_institution_program_returns_active_program_detail() -> None:
    db = _FakeDB()
    app.dependency_overrides[deps.get_db] = _override_db(db)
    app.dependency_overrides[deps.get_current_user_context] = _override_auth("user")
    try:
        client = TestClient(app)
        response = client.get("/api/v1/institution/programs/sirt-btech-cse-aiml")
    finally:
        _reset_overrides()

    assert response.status_code == 200
    data = response.json()
    assert data["school"]["school_id"] == "sirt-engineering"
    assert data["program"]["program_id"] == "sirt-btech-cse-aiml"


def test_get_institution_program_returns_404_for_inactive_program() -> None:
    db = _FakeDB()
    app.dependency_overrides[deps.get_db] = _override_db(db)
    app.dependency_overrides[deps.get_current_user_context] = _override_auth("user")
    try:
        client = TestClient(app)
        response = client.get("/api/v1/institution/programs/sirt-btech-civil-legacy")
    finally:
        _reset_overrides()

    assert response.status_code == 404


def test_admin_can_read_effective_overrides() -> None:
    saved = SimpleNamespace(
        key="default",
        value={
            "placement_ready_threshold": 84,
            "admission_high_intent_threshold": 71,
            "priority_skills_by_program": {"sirt-btech-cse-aiml": ["Python"]},
            "counselor_notes_by_program": {},
        },
    )
    db = _FakeDB(saved=saved)
    app.dependency_overrides[deps.get_db] = _override_db(db)
    app.dependency_overrides[deps.get_current_user_context] = _override_auth("admin")
    try:
        client = TestClient(app)
        response = client.get("/api/v1/institution/admin/overrides")
    finally:
        _reset_overrides()

    assert response.status_code == 200
    assert response.json()["placement_ready_threshold"] == 84


def test_admin_can_update_overrides() -> None:
    db = _FakeDB()
    app.dependency_overrides[deps.get_db] = _override_db(db)
    app.dependency_overrides[deps.get_current_user_context] = _override_auth("admin")
    try:
        client = TestClient(app)
        response = client.put(
            "/api/v1/institution/admin/overrides",
            json={
                "placement_ready_threshold": 82,
                "admission_high_intent_threshold": 73,
                "priority_skills_by_program": {
                    "sirt-btech-cse-aiml": ["Python", "Applied AI"]
                },
                "counselor_notes_by_program": {},
            },
        )
    finally:
        _reset_overrides()

    assert response.status_code == 200
    assert response.json()["placement_ready_threshold"] == 82
    assert db.committed is True


def test_non_admin_cannot_update_overrides() -> None:
    db = _FakeDB()
    app.dependency_overrides[deps.get_db] = _override_db(db)
    app.dependency_overrides[deps.get_current_user_context] = _override_auth("user")
    try:
        client = TestClient(app)
        response = client.put(
            "/api/v1/institution/admin/overrides",
            json={
                "placement_ready_threshold": 82,
                "admission_high_intent_threshold": 73,
                "priority_skills_by_program": {},
                "counselor_notes_by_program": {},
            },
        )
    finally:
        _reset_overrides()

    assert response.status_code == 403
