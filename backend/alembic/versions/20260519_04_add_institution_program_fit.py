"""add institution overrides and program fit analysis fields

Revision ID: 20260519_04
Revises: 20260405_03
Create Date: 2026-05-19 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260519_04"
down_revision = "20260405_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "institution_overrides",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(length=120), nullable=False),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_institution_overrides_id"),
        "institution_overrides",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_institution_overrides_key"),
        "institution_overrides",
        ["key"],
        unique=True,
    )

    op.add_column(
        "career_analyses",
        sa.Column("institution_config_version", sa.String(length=80), nullable=True),
    )
    op.add_column("career_analyses", sa.Column("program_fit_summary", sa.JSON(), nullable=True))
    op.add_column(
        "career_analyses",
        sa.Column("program_recommendations", sa.JSON(), nullable=True),
    )
    op.add_column(
        "career_analyses",
        sa.Column("expectation_reality_checks", sa.JSON(), nullable=True),
    )
    op.add_column("career_analyses", sa.Column("first_year_roadmap", sa.JSON(), nullable=True))
    op.add_column("career_analyses", sa.Column("counselor_summary", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("career_analyses", "counselor_summary")
    op.drop_column("career_analyses", "first_year_roadmap")
    op.drop_column("career_analyses", "expectation_reality_checks")
    op.drop_column("career_analyses", "program_recommendations")
    op.drop_column("career_analyses", "program_fit_summary")
    op.drop_column("career_analyses", "institution_config_version")

    op.drop_index(
        op.f("ix_institution_overrides_key"),
        table_name="institution_overrides",
    )
    op.drop_index(
        op.f("ix_institution_overrides_id"),
        table_name="institution_overrides",
    )
    op.drop_table("institution_overrides")
