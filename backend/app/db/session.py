from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings, get_settings

SessionLocal: sessionmaker[Session] | None = None
_ENGINE: Engine | None = None


def init_engine(settings: Settings | None = None) -> Engine:
    global SessionLocal
    global _ENGINE
    settings = settings or get_settings()

    engine = create_engine(
        settings.database_url,
        echo=settings.db_echo,
        pool_pre_ping=True,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        connect_args=_build_connect_args(settings),
    )

    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    _ENGINE = engine
    return engine


def _build_connect_args(settings: Settings) -> dict[str, int | None]:
    connect_args: dict[str, int | None] = {
        "connect_timeout": settings.db_connect_timeout_seconds
    }
    if settings.database_url.lower().startswith("postgresql+psycopg://"):
        # Supabase's transaction pooler can discard server-side prepared statements
        # between requests. Disabling psycopg preparation avoids intermittent
        # InvalidSqlStatementName failures in long-lived Cloud Run instances.
        connect_args["prepare_threshold"] = None
    return connect_args


def _require_sessionmaker() -> sessionmaker[Session]:
    if SessionLocal is None:
        raise RuntimeError("DB not initialized. Call init_engine() during app startup.")
    return SessionLocal


def get_engine() -> Engine:
    if _ENGINE is None:
        raise RuntimeError("DB not initialized. Call init_engine() during app startup.")
    return _ENGINE


def create_session() -> Session:
    sm = _require_sessionmaker()
    return sm()
