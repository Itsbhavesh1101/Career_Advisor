"""Add user notifications

Revision ID: 20260526_17
Revises: 20260525_16
Create Date: 2026-05-26 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260526_17"
down_revision: str | None = "20260525_16"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_notifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("recipient_user_id", sa.Integer(), nullable=False),
        sa.Column("profile_id", sa.Integer(), nullable=True),
        sa.Column("notification_type", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=220), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("action_url", sa.String(length=500), nullable=True),
        sa.Column("priority", sa.String(length=20), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("event_metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            name="fk_user_notifications_created_by_user_id_users",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["profile_id"],
            ["student_profiles.id"],
            name="fk_user_notifications_profile_id_student_profiles",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["recipient_user_id"],
            ["users.id"],
            name="fk_user_notifications_recipient_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_notifications_id"), "user_notifications", ["id"], unique=False)
    op.create_index(
        op.f("ix_user_notifications_recipient_user_id"),
        "user_notifications",
        ["recipient_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_user_notifications_profile_id"),
        "user_notifications",
        ["profile_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_user_notifications_notification_type"),
        "user_notifications",
        ["notification_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_user_notifications_priority"),
        "user_notifications",
        ["priority"],
        unique=False,
    )
    op.create_index(
        op.f("ix_user_notifications_created_by_user_id"),
        "user_notifications",
        ["created_by_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_user_notifications_created_at"),
        "user_notifications",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_user_notifications_created_at"), table_name="user_notifications")
    op.drop_index(
        op.f("ix_user_notifications_created_by_user_id"),
        table_name="user_notifications",
    )
    op.drop_index(op.f("ix_user_notifications_priority"), table_name="user_notifications")
    op.drop_index(
        op.f("ix_user_notifications_notification_type"),
        table_name="user_notifications",
    )
    op.drop_index(op.f("ix_user_notifications_profile_id"), table_name="user_notifications")
    op.drop_index(
        op.f("ix_user_notifications_recipient_user_id"),
        table_name="user_notifications",
    )
    op.drop_index(op.f("ix_user_notifications_id"), table_name="user_notifications")
    op.drop_table("user_notifications")
