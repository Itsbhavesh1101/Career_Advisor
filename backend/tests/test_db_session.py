from __future__ import annotations

from app.core.config import Settings
from app.db.session import _build_connect_args


def _settings(database_url: str) -> Settings:
    return Settings(
        database_url=database_url,
        jwt_secret="x" * 32,
    )


def test_psycopg_engine_disables_prepared_statements_for_pooler() -> None:
    args = _build_connect_args(
        _settings("postgresql+psycopg://user:pass@db.example.com:5432/postgres")
    )

    assert args["connect_timeout"] == 5
    assert args["prepare_threshold"] is None


def test_non_psycopg_engine_keeps_standard_connection_args() -> None:
    args = _build_connect_args(
        _settings("postgresql://user:pass@db.example.com:5432/postgres")
    )

    assert args == {"connect_timeout": 5}
