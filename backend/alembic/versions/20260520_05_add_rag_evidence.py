"""add rag evidence to career analyses

Revision ID: 20260520_05
Revises: 20260519_04
Create Date: 2026-05-20 00:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260520_05"
down_revision = "20260519_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("career_analyses", sa.Column("rag_evidence", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("career_analyses", "rag_evidence")
