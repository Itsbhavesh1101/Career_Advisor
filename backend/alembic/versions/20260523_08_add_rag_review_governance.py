"""add rag review governance fields

Revision ID: 20260523_08
Revises: 20260523_07
Create Date: 2026-05-23 20:30:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260523_08"
down_revision = "20260523_07"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "rag_document_sources",
        sa.Column(
            "review_status",
            sa.String(length=20),
            nullable=False,
            server_default="approved",
        ),
    )
    op.add_column("rag_document_sources", sa.Column("review_notes", sa.Text(), nullable=True))
    op.add_column(
        "rag_document_sources",
        sa.Column("reviewed_by_user_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "rag_document_sources",
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "rag_document_sources",
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        op.f("ix_rag_document_sources_review_status"),
        "rag_document_sources",
        ["review_status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_rag_document_sources_reviewed_by_user_id"),
        "rag_document_sources",
        ["reviewed_by_user_id"],
        unique=False,
    )
    op.create_foreign_key(
        op.f("fk_rag_document_sources_reviewed_by_user_id_users"),
        "rag_document_sources",
        "users",
        ["reviewed_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.alter_column("rag_document_sources", "review_status", server_default=None)


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk_rag_document_sources_reviewed_by_user_id_users"),
        "rag_document_sources",
        type_="foreignkey",
    )
    op.drop_index(
        op.f("ix_rag_document_sources_reviewed_by_user_id"),
        table_name="rag_document_sources",
    )
    op.drop_index(
        op.f("ix_rag_document_sources_review_status"),
        table_name="rag_document_sources",
    )
    op.drop_column("rag_document_sources", "expires_at")
    op.drop_column("rag_document_sources", "reviewed_at")
    op.drop_column("rag_document_sources", "reviewed_by_user_id")
    op.drop_column("rag_document_sources", "review_notes")
    op.drop_column("rag_document_sources", "review_status")
