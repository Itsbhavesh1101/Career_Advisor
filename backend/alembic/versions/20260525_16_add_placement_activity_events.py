"""Add placement activity events

Revision ID: 20260525_16
Revises: 20260525_15
Create Date: 2026-05-25 23:30:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260525_16"
down_revision = "20260525_15"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "placement_activity_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=220), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("opportunity_id", sa.Integer(), nullable=True),
        sa.Column("application_id", sa.Integer(), nullable=True),
        sa.Column("profile_id", sa.Integer(), nullable=True),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("event_metadata", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["actor_user_id"],
            ["users.id"],
            name="fk_placement_activity_events_actor_user_id_users",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["placement_applications.id"],
            name="fk_placement_activity_events_application_id_applications",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["placement_companies.id"],
            name="fk_placement_activity_events_company_id_companies",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["opportunity_id"],
            ["placement_opportunities.id"],
            name="fk_placement_activity_events_opportunity_id_opportunities",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["profile_id"],
            ["student_profiles.id"],
            name="fk_placement_activity_events_profile_id_profiles",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_placement_activity_events_id"),
        "placement_activity_events",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_placement_activity_events_event_type"),
        "placement_activity_events",
        ["event_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_placement_activity_events_opportunity_id"),
        "placement_activity_events",
        ["opportunity_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_placement_activity_events_application_id"),
        "placement_activity_events",
        ["application_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_placement_activity_events_profile_id"),
        "placement_activity_events",
        ["profile_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_placement_activity_events_company_id"),
        "placement_activity_events",
        ["company_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_placement_activity_events_actor_user_id"),
        "placement_activity_events",
        ["actor_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_placement_activity_events_created_at"),
        "placement_activity_events",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_placement_activity_events_created_at"),
        table_name="placement_activity_events",
    )
    op.drop_index(
        op.f("ix_placement_activity_events_actor_user_id"),
        table_name="placement_activity_events",
    )
    op.drop_index(
        op.f("ix_placement_activity_events_company_id"),
        table_name="placement_activity_events",
    )
    op.drop_index(
        op.f("ix_placement_activity_events_profile_id"),
        table_name="placement_activity_events",
    )
    op.drop_index(
        op.f("ix_placement_activity_events_application_id"),
        table_name="placement_activity_events",
    )
    op.drop_index(
        op.f("ix_placement_activity_events_opportunity_id"),
        table_name="placement_activity_events",
    )
    op.drop_index(
        op.f("ix_placement_activity_events_event_type"),
        table_name="placement_activity_events",
    )
    op.drop_index(
        op.f("ix_placement_activity_events_id"),
        table_name="placement_activity_events",
    )
    op.drop_table("placement_activity_events")
