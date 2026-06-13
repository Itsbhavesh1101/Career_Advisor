"""add source_url to resume analyses

Revision ID: 20260404_02
Revises: 20260404_01
Create Date: 2026-04-04 00:30:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = "20260404_02"
down_revision = "20260404_01"
branch_labels = None
depends_on = None


def _has_column(table_name: str, column_name: str) -> bool:
    inspector = inspect(op.get_bind())
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def upgrade() -> None:
    if not _has_column("resume_analyses", "source_url"):
        op.add_column(
            "resume_analyses",
            sa.Column("source_url", sa.String(length=2048), nullable=True),
        )


def downgrade() -> None:
    if _has_column("resume_analyses", "source_url"):
        op.drop_column("resume_analyses", "source_url")
