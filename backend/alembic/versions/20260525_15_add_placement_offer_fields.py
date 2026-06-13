"""Add placement offer fields

Revision ID: 20260525_15
Revises: 20260525_14
Create Date: 2026-05-25 22:30:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260525_15"
down_revision = "20260525_14"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "placement_applications",
        sa.Column("offer_status", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "placement_applications",
        sa.Column("offer_role", sa.String(length=220), nullable=True),
    )
    op.add_column(
        "placement_applications",
        sa.Column("offer_package", sa.String(length=120), nullable=True),
    )
    op.add_column(
        "placement_applications",
        sa.Column("offer_location", sa.String(length=200), nullable=True),
    )
    op.add_column(
        "placement_applications",
        sa.Column("offer_joining_date", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "placement_applications",
        sa.Column("offer_notes", sa.Text(), nullable=True),
    )
    op.add_column(
        "placement_applications",
        sa.Column("offer_updated_by_user_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "placement_applications",
        sa.Column("offer_updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_placement_applications_offer_updated_by_user_id_users",
        "placement_applications",
        "users",
        ["offer_updated_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        op.f("ix_placement_applications_offer_status"),
        "placement_applications",
        ["offer_status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_placement_applications_offer_joining_date"),
        "placement_applications",
        ["offer_joining_date"],
        unique=False,
    )
    op.create_index(
        op.f("ix_placement_applications_offer_updated_by_user_id"),
        "placement_applications",
        ["offer_updated_by_user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_placement_applications_offer_updated_by_user_id"),
        table_name="placement_applications",
    )
    op.drop_index(
        op.f("ix_placement_applications_offer_joining_date"),
        table_name="placement_applications",
    )
    op.drop_index(
        op.f("ix_placement_applications_offer_status"),
        table_name="placement_applications",
    )
    op.drop_constraint(
        "fk_placement_applications_offer_updated_by_user_id_users",
        "placement_applications",
        type_="foreignkey",
    )
    op.drop_column("placement_applications", "offer_updated_at")
    op.drop_column("placement_applications", "offer_updated_by_user_id")
    op.drop_column("placement_applications", "offer_notes")
    op.drop_column("placement_applications", "offer_joining_date")
    op.drop_column("placement_applications", "offer_location")
    op.drop_column("placement_applications", "offer_package")
    op.drop_column("placement_applications", "offer_role")
    op.drop_column("placement_applications", "offer_status")
