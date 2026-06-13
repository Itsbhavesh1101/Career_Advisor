"""add rag document sources and chunks

Revision ID: 20260520_06
Revises: 20260520_05
Create Date: 2026-05-20 00:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260520_06"
down_revision = "20260520_05"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "rag_document_sources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=220), nullable=False),
        sa.Column("source_type", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("program_ids", sa.JSON(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"], ["users.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_rag_document_sources_id"),
        "rag_document_sources",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_rag_document_sources_title"),
        "rag_document_sources",
        ["title"],
        unique=False,
    )
    op.create_index(
        op.f("ix_rag_document_sources_source_type"),
        "rag_document_sources",
        ["source_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_rag_document_sources_status"),
        "rag_document_sources",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_rag_document_sources_content_hash"),
        "rag_document_sources",
        ["content_hash"],
        unique=False,
    )
    op.create_index(
        op.f("ix_rag_document_sources_created_by_user_id"),
        "rag_document_sources",
        ["created_by_user_id"],
        unique=False,
    )

    op.create_table(
        "rag_document_chunks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("chunk_id", sa.String(length=180), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("source_title", sa.String(length=220), nullable=False),
        sa.Column("source_type", sa.String(length=40), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("program_ids", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["source_id"], ["rag_document_sources.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chunk_id"),
    )
    op.create_index(
        op.f("ix_rag_document_chunks_id"),
        "rag_document_chunks",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_rag_document_chunks_source_id"),
        "rag_document_chunks",
        ["source_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_rag_document_chunks_chunk_id"),
        "rag_document_chunks",
        ["chunk_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_rag_document_chunks_source_type"),
        "rag_document_chunks",
        ["source_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_rag_document_chunks_is_active"),
        "rag_document_chunks",
        ["is_active"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_rag_document_chunks_is_active"), table_name="rag_document_chunks"
    )
    op.drop_index(
        op.f("ix_rag_document_chunks_source_type"), table_name="rag_document_chunks"
    )
    op.drop_index(
        op.f("ix_rag_document_chunks_chunk_id"), table_name="rag_document_chunks"
    )
    op.drop_index(
        op.f("ix_rag_document_chunks_source_id"), table_name="rag_document_chunks"
    )
    op.drop_index(op.f("ix_rag_document_chunks_id"), table_name="rag_document_chunks")
    op.drop_table("rag_document_chunks")

    op.drop_index(
        op.f("ix_rag_document_sources_created_by_user_id"),
        table_name="rag_document_sources",
    )
    op.drop_index(
        op.f("ix_rag_document_sources_content_hash"),
        table_name="rag_document_sources",
    )
    op.drop_index(
        op.f("ix_rag_document_sources_status"), table_name="rag_document_sources"
    )
    op.drop_index(
        op.f("ix_rag_document_sources_source_type"),
        table_name="rag_document_sources",
    )
    op.drop_index(
        op.f("ix_rag_document_sources_title"), table_name="rag_document_sources"
    )
    op.drop_index(op.f("ix_rag_document_sources_id"), table_name="rag_document_sources")
    op.drop_table("rag_document_sources")
