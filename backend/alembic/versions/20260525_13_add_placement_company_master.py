"""Add placement company master and drive linkage

Revision ID: 20260525_13
Revises: 20260525_12
Create Date: 2026-05-25 18:25:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260525_13"
down_revision = "20260525_12"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "placement_companies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=220), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("website", sa.String(length=500), nullable=True),
        sa.Column("industry", sa.String(length=160), nullable=True),
        sa.Column("location", sa.String(length=200), nullable=True),
        sa.Column("contact_name", sa.String(length=160), nullable=True),
        sa.Column("contact_email", sa.String(length=254), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("updated_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_placement_company_name"),
    )
    op.create_index(op.f("ix_placement_companies_id"), "placement_companies", ["id"], unique=False)
    op.create_index(op.f("ix_placement_companies_name"), "placement_companies", ["name"], unique=False)
    op.create_index(op.f("ix_placement_companies_status"), "placement_companies", ["status"], unique=False)
    op.create_index(
        op.f("ix_placement_companies_created_by_user_id"),
        "placement_companies",
        ["created_by_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_placement_companies_updated_by_user_id"),
        "placement_companies",
        ["updated_by_user_id"],
        unique=False,
    )
    op.add_column("placement_opportunities", sa.Column("company_id", sa.Integer(), nullable=True))
    op.create_index(
        op.f("ix_placement_opportunities_company_id"),
        "placement_opportunities",
        ["company_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_placement_opportunities_company_id",
        "placement_opportunities",
        "placement_companies",
        ["company_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_placement_opportunities_company_id",
        "placement_opportunities",
        type_="foreignkey",
    )
    op.drop_index(op.f("ix_placement_opportunities_company_id"), table_name="placement_opportunities")
    op.drop_column("placement_opportunities", "company_id")
    op.drop_index(op.f("ix_placement_companies_updated_by_user_id"), table_name="placement_companies")
    op.drop_index(op.f("ix_placement_companies_created_by_user_id"), table_name="placement_companies")
    op.drop_index(op.f("ix_placement_companies_status"), table_name="placement_companies")
    op.drop_index(op.f("ix_placement_companies_name"), table_name="placement_companies")
    op.drop_index(op.f("ix_placement_companies_id"), table_name="placement_companies")
    op.drop_table("placement_companies")
