"""add pgvector embeddings to rag document chunks

Revision ID: 20260523_07
Revises: 20260520_06
Create Date: 2026-05-23 00:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260523_07"
down_revision = "20260520_06"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS extensions")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA extensions")
    op.execute(
        "ALTER TABLE rag_document_chunks "
        "ADD COLUMN embedding extensions.vector(256)"
    )
    op.add_column(
        "rag_document_chunks",
        sa.Column("embedding_provider", sa.String(length=40), nullable=True),
    )
    op.add_column(
        "rag_document_chunks",
        sa.Column("embedding_model", sa.String(length=120), nullable=True),
    )
    op.add_column(
        "rag_document_chunks",
        sa.Column("embedding_dimensions", sa.Integer(), nullable=True),
    )
    op.add_column(
        "rag_document_chunks",
        sa.Column(
            "embedding_status",
            sa.String(length=20),
            nullable=False,
            server_default="pending",
        ),
    )
    op.add_column(
        "rag_document_chunks",
        sa.Column("embedding_error", sa.Text(), nullable=True),
    )
    op.add_column(
        "rag_document_chunks",
        sa.Column(
            "embedding_attempts",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "rag_document_chunks",
        sa.Column("embedding_updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_rag_document_chunks_embedding_provider",
        "rag_document_chunks",
        ["embedding_provider"],
        unique=False,
    )
    op.create_index(
        "ix_rag_document_chunks_embedding_dimensions",
        "rag_document_chunks",
        ["embedding_dimensions"],
        unique=False,
    )
    op.create_index(
        "ix_rag_document_chunks_embedding_status",
        "rag_document_chunks",
        ["embedding_status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_rag_document_chunks_embedding_status",
        table_name="rag_document_chunks",
    )
    op.drop_index(
        "ix_rag_document_chunks_embedding_dimensions",
        table_name="rag_document_chunks",
    )
    op.drop_index(
        "ix_rag_document_chunks_embedding_provider",
        table_name="rag_document_chunks",
    )
    op.drop_column("rag_document_chunks", "embedding_updated_at")
    op.drop_column("rag_document_chunks", "embedding_attempts")
    op.drop_column("rag_document_chunks", "embedding_error")
    op.drop_column("rag_document_chunks", "embedding_status")
    op.drop_column("rag_document_chunks", "embedding_dimensions")
    op.drop_column("rag_document_chunks", "embedding_model")
    op.drop_column("rag_document_chunks", "embedding_provider")
    op.drop_column("rag_document_chunks", "embedding")
