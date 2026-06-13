"""Add placement opportunities

Revision ID: 20260525_11
Revises: 20260525_10
Create Date: 2026-05-25
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260525_11"
down_revision = "20260525_10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "placement_opportunities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=220), nullable=False),
        sa.Column("company", sa.String(length=220), nullable=False),
        sa.Column("opportunity_type", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("location", sa.String(length=200), nullable=True),
        sa.Column("work_mode", sa.String(length=40), nullable=True),
        sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("eligibility", sa.JSON(), nullable=False),
        sa.Column("required_skills", sa.JSON(), nullable=False),
        sa.Column("apply_url", sa.String(length=500), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("updated_by_user_id", sa.Integer(), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["updated_by_user_id"], ["users.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_placement_opportunities_id", "placement_opportunities", ["id"])
    op.create_index(
        "ix_placement_opportunities_title", "placement_opportunities", ["title"]
    )
    op.create_index(
        "ix_placement_opportunities_company", "placement_opportunities", ["company"]
    )
    op.create_index(
        "ix_placement_opportunities_opportunity_type",
        "placement_opportunities",
        ["opportunity_type"],
    )
    op.create_index(
        "ix_placement_opportunities_status", "placement_opportunities", ["status"]
    )
    op.create_index(
        "ix_placement_opportunities_deadline_at",
        "placement_opportunities",
        ["deadline_at"],
    )
    op.create_index(
        "ix_placement_opportunities_created_by_user_id",
        "placement_opportunities",
        ["created_by_user_id"],
    )
    op.create_index(
        "ix_placement_opportunities_updated_by_user_id",
        "placement_opportunities",
        ["updated_by_user_id"],
    )

    op.create_table(
        "placement_applications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("opportunity_id", sa.Integer(), nullable=False),
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("interest_note", sa.Text(), nullable=True),
        sa.Column("admin_notes", sa.Text(), nullable=True),
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
            ["opportunity_id"], ["placement_opportunities.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["profile_id"], ["student_profiles.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "opportunity_id",
            "profile_id",
            name="uq_placement_application_opportunity_profile",
        ),
    )
    op.create_index("ix_placement_applications_id", "placement_applications", ["id"])
    op.create_index(
        "ix_placement_applications_opportunity_id",
        "placement_applications",
        ["opportunity_id"],
    )
    op.create_index(
        "ix_placement_applications_profile_id",
        "placement_applications",
        ["profile_id"],
    )
    op.create_index(
        "ix_placement_applications_user_id",
        "placement_applications",
        ["user_id"],
    )
    op.create_index(
        "ix_placement_applications_status", "placement_applications", ["status"]
    )


def downgrade() -> None:
    op.drop_index("ix_placement_applications_status", table_name="placement_applications")
    op.drop_index("ix_placement_applications_user_id", table_name="placement_applications")
    op.drop_index(
        "ix_placement_applications_profile_id", table_name="placement_applications"
    )
    op.drop_index(
        "ix_placement_applications_opportunity_id",
        table_name="placement_applications",
    )
    op.drop_index("ix_placement_applications_id", table_name="placement_applications")
    op.drop_table("placement_applications")
    op.drop_index(
        "ix_placement_opportunities_updated_by_user_id",
        table_name="placement_opportunities",
    )
    op.drop_index(
        "ix_placement_opportunities_created_by_user_id",
        table_name="placement_opportunities",
    )
    op.drop_index(
        "ix_placement_opportunities_deadline_at",
        table_name="placement_opportunities",
    )
    op.drop_index(
        "ix_placement_opportunities_status", table_name="placement_opportunities"
    )
    op.drop_index(
        "ix_placement_opportunities_opportunity_type",
        table_name="placement_opportunities",
    )
    op.drop_index(
        "ix_placement_opportunities_company", table_name="placement_opportunities"
    )
    op.drop_index(
        "ix_placement_opportunities_title", table_name="placement_opportunities"
    )
    op.drop_index("ix_placement_opportunities_id", table_name="placement_opportunities")
    op.drop_table("placement_opportunities")
