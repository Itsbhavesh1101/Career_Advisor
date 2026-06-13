"""Add placement interview rounds

Revision ID: 20260525_14
Revises: 20260525_13
Create Date: 2026-05-25 20:40:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260525_14"
down_revision = "20260525_13"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "placement_interview_rounds",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("application_id", sa.Integer(), nullable=False),
        sa.Column("round_name", sa.String(length=160), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("mode", sa.String(length=60), nullable=True),
        sa.Column("location", sa.String(length=300), nullable=True),
        sa.Column("interviewer", sa.String(length=220), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
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
            ["application_id"],
            ["placement_applications.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["updated_by_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_placement_interview_rounds_id"),
        "placement_interview_rounds",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_placement_interview_rounds_application_id"),
        "placement_interview_rounds",
        ["application_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_placement_interview_rounds_status"),
        "placement_interview_rounds",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_placement_interview_rounds_scheduled_at"),
        "placement_interview_rounds",
        ["scheduled_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_placement_interview_rounds_created_by_user_id"),
        "placement_interview_rounds",
        ["created_by_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_placement_interview_rounds_updated_by_user_id"),
        "placement_interview_rounds",
        ["updated_by_user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_placement_interview_rounds_updated_by_user_id"),
        table_name="placement_interview_rounds",
    )
    op.drop_index(
        op.f("ix_placement_interview_rounds_created_by_user_id"),
        table_name="placement_interview_rounds",
    )
    op.drop_index(
        op.f("ix_placement_interview_rounds_scheduled_at"),
        table_name="placement_interview_rounds",
    )
    op.drop_index(
        op.f("ix_placement_interview_rounds_status"),
        table_name="placement_interview_rounds",
    )
    op.drop_index(
        op.f("ix_placement_interview_rounds_application_id"),
        table_name="placement_interview_rounds",
    )
    op.drop_index(
        op.f("ix_placement_interview_rounds_id"),
        table_name="placement_interview_rounds",
    )
    op.drop_table("placement_interview_rounds")
