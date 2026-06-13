"""baseline schema

Revision ID: 20260404_01
Revises:
Create Date: 2026-04-04 00:00:00
"""

from __future__ import annotations

from alembic import op


# revision identifiers, used by Alembic.
revision = "20260404_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Baseline migration from current metadata state.
    from app.db.base import Base
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    from app.db.base import Base
    import app.models  # noqa: F401

    Base.metadata.drop_all(bind=op.get_bind())
