from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt

from app.core.config import get_settings
from app.models.user import User
from app.services.supabase_auth_service import (
    SupabaseAuthClaims,
    SupabaseAuthError,
    SupabaseAuthService,
    upsert_supabase_user,
)


def _configure_supabase_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SUPABASE_AUTH_ENABLED", "true")
    monkeypatch.setenv("SUPABASE_URL", "https://project-ref.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test-anon-key")
    monkeypatch.setenv("SUPABASE_AUTH_VERIFY_MODE", "jwt_secret")
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "supabase-jwt-secret-with-32-characters")
    get_settings.cache_clear()


def _supabase_jwt(*, email: str, sub: str, student_type: str | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "iss": "https://project-ref.supabase.co/auth/v1",
        "aud": "authenticated",
        "sub": sub,
        "email": email,
        "role": "authenticated",
        "iat": now,
        "exp": now + timedelta(minutes=10),
        "user_metadata": {"student_type": student_type} if student_type else {},
    }
    return jwt.encode(
        payload,
        "supabase-jwt-secret-with-32-characters",
        algorithm="HS256",
    )


def test_supabase_jwt_secret_verification_extracts_user_claims(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure_supabase_env(monkeypatch)
    try:
        token = _supabase_jwt(
            email="student@example.com",
            sub="4ed9f5be-4f8b-4f46-a42d-9ae9648accee",
            student_type="twelfth_student",
        )

        claims = SupabaseAuthService().verify_access_token(token)
    finally:
        get_settings.cache_clear()

    assert claims == SupabaseAuthClaims(
        supabase_user_id="4ed9f5be-4f8b-4f46-a42d-9ae9648accee",
        email="student@example.com",
        student_type="twelfth_student",
    )


def test_supabase_jwt_secret_verification_rejects_wrong_audience(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure_supabase_env(monkeypatch)
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "iss": "https://project-ref.supabase.co/auth/v1",
            "aud": "service_role",
            "sub": "4ed9f5be-4f8b-4f46-a42d-9ae9648accee",
            "email": "student@example.com",
            "iat": now,
            "exp": now + timedelta(minutes=10),
        },
        "supabase-jwt-secret-with-32-characters",
        algorithm="HS256",
    )

    try:
        with pytest.raises(SupabaseAuthError):
            SupabaseAuthService().verify_access_token(token)
    finally:
        get_settings.cache_clear()


class _FakeDB:
    def __init__(self, user: User | None = None) -> None:
        self.user = user
        self.added: User | None = None
        self.committed = False

    def scalar(self, _stmt):
        return self.user

    def add(self, user: User) -> None:
        self.added = user
        self.user = user

    def commit(self) -> None:
        self.committed = True

    def refresh(self, _user: User) -> None:
        return None


def test_upsert_supabase_user_creates_local_mapping() -> None:
    db = _FakeDB()
    claims = SupabaseAuthClaims(
        supabase_user_id="supabase-user-1",
        email="new@example.com",
        student_type="college_student",
    )

    user = upsert_supabase_user(db, claims)  # type: ignore[arg-type]

    assert user is db.added
    assert user.email == "new@example.com"
    assert user.supabase_user_id == "supabase-user-1"
    assert user.student_type == "college_student"
    assert user.password_hash == "supabase-auth"
    assert db.committed is True


def test_upsert_supabase_user_updates_existing_mapping() -> None:
    existing = User(
        id=10,
        email="old@example.com",
        password_hash="hash",
        student_type="college_student",
        supabase_user_id=None,
    )
    db = _FakeDB(existing)
    claims = SupabaseAuthClaims(
        supabase_user_id="supabase-user-2",
        email="updated@example.com",
        student_type="twelfth_student",
    )

    user = upsert_supabase_user(db, claims)  # type: ignore[arg-type]

    assert user is existing
    assert user.email == "updated@example.com"
    assert user.supabase_user_id == "supabase-user-2"
    assert user.student_type == "twelfth_student"
    assert db.added is None
    assert db.committed is True
