"""Extend placement operations fields

Revision ID: 20260525_12
Revises: 20260525_11
Create Date: 2026-05-25
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260525_12"
down_revision = "20260525_11"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "placement_opportunities",
        sa.Column("package_label", sa.String(length=120), nullable=True),
    )
    op.add_column(
        "placement_opportunities",
        sa.Column("vacancies", sa.Integer(), nullable=True),
    )
    op.add_column(
        "placement_opportunities",
        sa.Column("contact_name", sa.String(length=160), nullable=True),
    )
    op.add_column(
        "placement_opportunities",
        sa.Column("contact_email", sa.String(length=254), nullable=True),
    )
    op.add_column(
        "placement_opportunities",
        sa.Column(
            "hiring_stages",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'"),
        ),
    )
    op.add_column(
        "placement_applications",
        sa.Column("next_step", sa.String(length=500), nullable=True),
    )
    op.add_column(
        "placement_applications",
        sa.Column("next_step_due_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_placement_applications_next_step_due_at",
        "placement_applications",
        ["next_step_due_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_placement_applications_next_step_due_at",
        table_name="placement_applications",
    )
    op.drop_column("placement_applications", "next_step_due_at")
    op.drop_column("placement_applications", "next_step")
    op.drop_column("placement_opportunities", "hiring_stages")
    op.drop_column("placement_opportunities", "contact_email")
    op.drop_column("placement_opportunities", "contact_name")
    op.drop_column("placement_opportunities", "vacancies")
    op.drop_column("placement_opportunities", "package_label")
