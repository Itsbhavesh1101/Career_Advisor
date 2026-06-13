from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx
from jose import JWTError, jwt
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.user import User


class SupabaseAuthError(ValueError):
    pass


@dataclass(frozen=True)
class SupabaseAuthClaims:
    supabase_user_id: str
    email: str
    student_type: str


class SupabaseAuthService:
    def verify_access_token(self, token: str) -> SupabaseAuthClaims:
        settings = get_settings()
        if not settings.supabase_auth_enabled:
            raise SupabaseAuthError("Supabase Auth is not enabled.")
        if settings.supabase_auth_verify_mode == "jwt_secret":
            return self._verify_with_jwt_secret(token)
        return self._verify_with_auth_server(token)

    def _verify_with_jwt_secret(self, token: str) -> SupabaseAuthClaims:
        settings = get_settings()
        if not settings.supabase_jwt_secret or not settings.supabase_url:
            raise SupabaseAuthError("Supabase JWT verification is not configured.")
        try:
            payload = jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
                issuer=f"{settings.supabase_url}/auth/v1",
            )
        except JWTError as exc:
            raise SupabaseAuthError("Invalid Supabase access token.") from exc
        return _claims_from_payload(payload)

    def _verify_with_auth_server(self, token: str) -> SupabaseAuthClaims:
        settings = get_settings()
        if not settings.supabase_url or not settings.supabase_anon_key:
            raise SupabaseAuthError("Supabase remote verification is not configured.")
        try:
            response = httpx.get(
                f"{settings.supabase_url}/auth/v1/user",
                headers={
                    "apikey": settings.supabase_anon_key,
                    "Authorization": f"Bearer {token}",
                },
                timeout=8,
            )
        except httpx.HTTPError as exc:
            raise SupabaseAuthError("Unable to verify Supabase access token.") from exc
        if response.status_code != 200:
            raise SupabaseAuthError("Invalid Supabase access token.")
        return _claims_from_payload(response.json())


def upsert_supabase_user(db: Session, claims: SupabaseAuthClaims) -> User:
    user = db.scalar(
        select(User).where(
            or_(
                User.supabase_user_id == claims.supabase_user_id,
                User.email == claims.email,
            )
        )
    )
    if user is None:
        user = User(
            supabase_user_id=claims.supabase_user_id,
            email=claims.email,
            password_hash="supabase-auth",
            student_type=claims.student_type,
        )
        db.add(user)
    else:
        user.supabase_user_id = claims.supabase_user_id
        user.email = claims.email
        user.student_type = claims.student_type

    db.commit()
    db.refresh(user)
    return user


def _claims_from_payload(payload: dict[str, Any]) -> SupabaseAuthClaims:
    supabase_user_id = str(payload.get("id") or payload.get("sub") or "").strip()
    email = str(payload.get("email") or "").strip().lower()
    metadata = payload.get("user_metadata") or {}
    app_metadata = payload.get("app_metadata") or {}
    student_type = str(
        metadata.get("student_type")
        or app_metadata.get("student_type")
        or "college_student"
    ).strip()
    if student_type not in {"twelfth_student", "college_student"}:
        student_type = "college_student"
    if not supabase_user_id or not email:
        raise SupabaseAuthError("Supabase access token is missing required user claims.")
    return SupabaseAuthClaims(
        supabase_user_id=supabase_user_id,
        email=email,
        student_type=student_type,
    )
