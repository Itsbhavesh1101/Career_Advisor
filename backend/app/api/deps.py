from collections.abc import Generator

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import create_session
from app.models.user import User
from app.services.supabase_auth_service import (
    SupabaseAuthError,
    SupabaseAuthService,
    upsert_supabase_user,
)


def get_db() -> Generator[Session, None, None]:
    db = create_session()
    try:
        yield db
    finally:
        db.close()


def get_user_role(user: User) -> str:
    settings = get_settings()
    return "admin" if user.email.lower() in settings.admin_emails else "user"


def _extract_bearer_token(request: Request) -> str | None:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.lower().startswith("bearer "):
        bearer = auth_header.split(" ", 1)[1].strip()
        return bearer or None
    return None


def _authenticate_request(request: Request, db: Session) -> User:
    settings = get_settings()
    bearer_token = _extract_bearer_token(request)
    if settings.supabase_auth_enabled:
        if not bearer_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Supabase authentication required",
            )
        try:
            claims = SupabaseAuthService().verify_access_token(bearer_token)
        except SupabaseAuthError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Supabase authentication token",
            ) from exc
        return upsert_supabase_user(db, claims)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Supabase authentication is not configured",
    )


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    return _authenticate_request(request, db)


def get_current_user_context(
    request: Request,
    db: Session = Depends(get_db),
) -> tuple[User, str]:
    user = _authenticate_request(request, db)
    role = get_user_role(user)
    return user, role


def get_current_admin(
    context: tuple[User, str] = Depends(get_current_user_context),
) -> User:
    user, role = context
    if role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user
