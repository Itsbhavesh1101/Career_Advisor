from __future__ import annotations

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from starlette.requests import Request

from app.api import deps
from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.models.user import User
from main import app


@pytest.fixture(autouse=True)
def _reset_rate_limits() -> None:
    limiter.reset()
    yield
    limiter.reset()


def test_extract_bearer_token_ignores_legacy_cookie() -> None:
    settings = get_settings()
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "query_string": b"",
        "headers": [
            (b"cookie", f"{settings.auth_cookie_name}=cookie-token".encode("utf-8")),
            (b"authorization", b"Bearer header-token"),
        ],
        "client": ("127.0.0.1", 54321),
        "server": ("testserver", 80),
        "scheme": "http",
    }

    request = Request(scope)
    assert deps._extract_bearer_token(request) == "header-token"


def test_authenticate_request_requires_supabase_bearer_when_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SUPABASE_AUTH_ENABLED", "true")
    monkeypatch.setenv("SUPABASE_URL", "https://project-ref.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test-anon-key")
    get_settings.cache_clear()
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "query_string": b"",
        "headers": [
            (
                b"cookie",
                f"{get_settings().auth_cookie_name}=legacy-cookie-token".encode("utf-8"),
            ),
        ],
        "client": ("127.0.0.1", 54321),
        "server": ("testserver", 80),
        "scheme": "http",
    }
    request = Request(scope)

    try:
        with pytest.raises(HTTPException) as exc_info:
            deps._authenticate_request(request, object())  # type: ignore[arg-type]
    finally:
        get_settings.cache_clear()

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Supabase authentication required"


def test_authenticate_request_accepts_supabase_bearer_when_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SUPABASE_AUTH_ENABLED", "true")
    monkeypatch.setenv("SUPABASE_URL", "https://project-ref.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test-anon-key")
    get_settings.cache_clear()
    expected_user = User(
        id=8,
        email="supabase@example.com",
        password_hash="supabase-auth",
        student_type="college_student",
        supabase_user_id="supabase-user",
    )
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "query_string": b"",
        "headers": [
            (
                b"cookie",
                f"{get_settings().auth_cookie_name}=legacy-cookie-token".encode("utf-8"),
            ),
            (b"authorization", b"Bearer supabase-bearer-token"),
        ],
        "client": ("127.0.0.1", 54321),
        "server": ("testserver", 80),
        "scheme": "http",
    }
    request = Request(scope)

    class _FakeSupabaseService:
        def verify_access_token(self, token: str):
            assert token == "supabase-bearer-token"
            return "claims"

    monkeypatch.setattr(deps, "SupabaseAuthService", lambda: _FakeSupabaseService())
    monkeypatch.setattr(
        deps,
        "upsert_supabase_user",
        lambda _db, claims: expected_user if claims == "claims" else None,
    )

    try:
        assert deps._authenticate_request(request, object()) is expected_user
    finally:
        get_settings.cache_clear()


def test_get_user_role_uses_server_side_admin_emails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ADMIN_EMAILS", "admin@example.com")
    get_settings.cache_clear()
    try:
        admin_user = User(
            email="admin@example.com",
            password_hash="hash",
            student_type="college_student",
        )
        regular_user = User(
            email="user@example.com",
            password_hash="hash",
            student_type="college_student",
        )

        assert deps.get_user_role(admin_user) == "admin"
        assert deps.get_user_role(regular_user) == "user"
    finally:
        get_settings.cache_clear()


def test_get_current_admin_rejects_non_admin_context() -> None:
    user = User(email="user@example.com", password_hash="hash", student_type="college_student")
    with pytest.raises(HTTPException) as exc_info:
        deps.get_current_admin((user, "user"))

    assert exc_info.value.status_code == 403


def test_legacy_login_endpoint_is_disabled() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "student@example.com", "password": "secret123"},
    )

    assert response.status_code == 410
    assert (
        response.json()["error"]["message"]
        == "Backend password login is disabled. Use Supabase Auth."
    )


def test_legacy_register_endpoint_is_disabled() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "student@example.com",
            "password": "secret123",
            "student_type": "college_student",
        },
    )

    assert response.status_code == 410
    assert (
        response.json()["error"]["message"]
        == "Backend password signup is disabled. Use Supabase Auth."
    )


def test_logout_clears_cookie_with_matching_security_attributes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "true")
    monkeypatch.setenv("AUTH_COOKIE_SAMESITE", "none")
    monkeypatch.setenv(
        "AUTH_COOKIE_DOMAIN",
        "ai-career-advisor-agent-production.up.railway.app",
    )
    get_settings.cache_clear()

    try:
        client = TestClient(app)
        response = client.post("/api/v1/auth/logout")
        settings = get_settings()
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    set_cookie = response.headers.get("set-cookie", "")
    set_cookie_lower = set_cookie.lower()
    assert f"{settings.auth_cookie_name}=" in set_cookie
    assert "max-age=0" in set_cookie_lower
    assert "httponly" in set_cookie_lower
    assert "secure" in set_cookie_lower
    assert "samesite=none" in set_cookie_lower
    assert f"domain={settings.auth_cookie_domain}".lower() in set_cookie_lower


def test_me_endpoint_allows_normal_polling_without_429() -> None:
    user = User(
        id=3,
        email="polling@example.com",
        password_hash="hash",
        student_type="college_student",
    )
    app.dependency_overrides[deps.get_current_user] = lambda: user

    try:
        client = TestClient(app)
        statuses: list[int] = []
        for _ in range(30):
            response = client.get("/api/v1/auth/me")
            statuses.append(response.status_code)
    finally:
        app.dependency_overrides.clear()

    assert 429 not in statuses
    assert all(status == 200 for status in statuses)
