"""Add Supabase Auth user mapping

Revision ID: 20260524_09
Revises: 20260523_08
Create Date: 2026-05-24
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260524_09"
down_revision = "20260523_08"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("supabase_user_id", sa.String(length=64), nullable=True),
    )
    op.create_index(
        "ix_users_supabase_user_id",
        "users",
        ["supabase_user_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_users_supabase_user_id", table_name="users")
    op.drop_column("users", "supabase_user_id")
