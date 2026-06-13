"""Add admin managed items

Revision ID: 20260525_10
Revises: 20260524_09
Create Date: 2026-05-25
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260525_10"
down_revision = "20260524_09"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "admin_managed_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("item_type", sa.String(length=40), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("title", sa.String(length=220), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
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
        sa.UniqueConstraint("item_type", "slug", name="uq_admin_managed_item_type_slug"),
    )
    op.create_index("ix_admin_managed_items_id", "admin_managed_items", ["id"])
    op.create_index("ix_admin_managed_items_item_type", "admin_managed_items", ["item_type"])
    op.create_index("ix_admin_managed_items_slug", "admin_managed_items", ["slug"])
    op.create_index("ix_admin_managed_items_title", "admin_managed_items", ["title"])
    op.create_index("ix_admin_managed_items_status", "admin_managed_items", ["status"])
    op.create_index(
        "ix_admin_managed_items_created_by_user_id",
        "admin_managed_items",
        ["created_by_user_id"],
    )
    op.create_index(
        "ix_admin_managed_items_updated_by_user_id",
        "admin_managed_items",
        ["updated_by_user_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_admin_managed_items_updated_by_user_id",
        table_name="admin_managed_items",
    )
    op.drop_index(
        "ix_admin_managed_items_created_by_user_id",
        table_name="admin_managed_items",
    )
    op.drop_index("ix_admin_managed_items_status", table_name="admin_managed_items")
    op.drop_index("ix_admin_managed_items_title", table_name="admin_managed_items")
    op.drop_index("ix_admin_managed_items_slug", table_name="admin_managed_items")
    op.drop_index("ix_admin_managed_items_item_type", table_name="admin_managed_items")
    op.drop_index("ix_admin_managed_items_id", table_name="admin_managed_items")
    op.drop_table("admin_managed_items")
