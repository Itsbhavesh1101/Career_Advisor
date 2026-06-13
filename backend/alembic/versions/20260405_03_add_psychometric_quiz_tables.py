"""add psychometric quiz tables

Revision ID: 20260405_03
Revises: 20260404_02
Create Date: 2026-04-05 09:30:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = "20260405_03"
down_revision = "20260404_02"
branch_labels = None
depends_on = None


def _has_table(table_name: str) -> bool:
    inspector = inspect(op.get_bind())
    return table_name in inspector.get_table_names()


def _has_index(table_name: str, index_name: str) -> bool:
    inspector = inspect(op.get_bind())
    return any(idx["name"] == index_name for idx in inspector.get_indexes(table_name))


def upgrade() -> None:
    if not _has_table("psychometric_sessions"):
        op.create_table(
            "psychometric_sessions",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("student_profile_id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("user_type", sa.String(length=20), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="queued"),
            sa.Column("fallback_mode", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("breaker_open", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("llm_failure_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("current_question_id", sa.String(length=36), nullable=True),
            sa.Column("current_question_index", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("questions_answered", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("min_questions", sa.Integer(), nullable=False, server_default="8"),
            sa.Column("max_questions", sa.Integer(), nullable=False, server_default="15"),
            sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
            sa.Column("current_traits", sa.JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
            sa.Column("current_state", sa.JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
            sa.Column("tokens_used", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("question_generation_lock", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("schema_version", sa.String(length=20), nullable=False, server_default="v1"),
            sa.Column("prompt_version", sa.String(length=20), nullable=False, server_default="v1"),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.ForeignKeyConstraint(["student_profile_id"], ["student_profiles.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        )

    if not _has_table("psychometric_questions"):
        op.create_table(
            "psychometric_questions",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("session_id", sa.String(length=36), nullable=False),
            sa.Column("position", sa.Integer(), nullable=False),
            sa.Column("source", sa.String(length=20), nullable=False, server_default="llm"),
            sa.Column("trait_tag", sa.String(length=80), nullable=True),
            sa.Column("question_text", sa.String(length=280), nullable=False),
            sa.Column("options", sa.JSON(), nullable=False, server_default=sa.text("'[]'::jsonb")),
            sa.Column("schema_version", sa.String(length=20), nullable=False, server_default="v1"),
            sa.Column("prompt_version", sa.String(length=20), nullable=False, server_default="v1"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.ForeignKeyConstraint(["session_id"], ["psychometric_sessions.id"], ondelete="CASCADE"),
            sa.UniqueConstraint("session_id", "position", name="uq_psychometric_question_session_position"),
        )

    if not _has_table("psychometric_answers"):
        op.create_table(
            "psychometric_answers",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("session_id", sa.String(length=36), nullable=False),
            sa.Column("question_id", sa.String(length=36), nullable=False),
            sa.Column("idempotency_key", sa.String(length=80), nullable=True),
            sa.Column("selected_option_id", sa.String(length=80), nullable=False),
            sa.Column("selected_option_text", sa.String(length=280), nullable=True),
            sa.Column("trait_effect", sa.JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
            sa.Column("response_ms", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.ForeignKeyConstraint(["session_id"], ["psychometric_sessions.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["question_id"], ["psychometric_questions.id"], ondelete="CASCADE"),
            sa.UniqueConstraint("session_id", "question_id", name="uq_psychometric_answer_session_question"),
            sa.UniqueConstraint("session_id", "idempotency_key", name="uq_psychometric_answer_session_key"),
        )

    if not _has_table("psychometric_results"):
        op.create_table(
            "psychometric_results",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("session_id", sa.String(length=36), nullable=False),
            sa.Column("student_profile_id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("trait_scores", sa.JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
            sa.Column("confidence", sa.Float(), nullable=False),
            sa.Column("question_count", sa.Integer(), nullable=False),
            sa.Column("fallback_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("trait_version", sa.String(length=20), nullable=False, server_default="v1"),
            sa.Column("schema_version", sa.String(length=20), nullable=False, server_default="v1"),
            sa.Column("prompt_version", sa.String(length=20), nullable=False, server_default="v1"),
            sa.Column("scoring_config_hash", sa.String(length=64), nullable=False),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.ForeignKeyConstraint(["session_id"], ["psychometric_sessions.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["student_profile_id"], ["student_profiles.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.UniqueConstraint("session_id", name="uq_psychometric_result_session"),
        )

    if not _has_index("psychometric_sessions", "ix_psychometric_sessions_student_profile_id"):
        op.create_index(
            "ix_psychometric_sessions_student_profile_id",
            "psychometric_sessions",
            ["student_profile_id"],
        )
    if not _has_index("psychometric_sessions", "ix_psychometric_sessions_user_id"):
        op.create_index("ix_psychometric_sessions_user_id", "psychometric_sessions", ["user_id"])
    if not _has_index("psychometric_sessions", "ix_psychometric_sessions_status"):
        op.create_index("ix_psychometric_sessions_status", "psychometric_sessions", ["status"])

    if not _has_index("psychometric_questions", "ix_psychometric_questions_session_id"):
        op.create_index("ix_psychometric_questions_session_id", "psychometric_questions", ["session_id"])

    if not _has_index("psychometric_answers", "ix_psychometric_answers_session_id"):
        op.create_index("ix_psychometric_answers_session_id", "psychometric_answers", ["session_id"])
    if not _has_index("psychometric_answers", "ix_psychometric_answers_question_id"):
        op.create_index("ix_psychometric_answers_question_id", "psychometric_answers", ["question_id"])

    if not _has_index("psychometric_results", "ix_psychometric_results_session_id"):
        op.create_index("ix_psychometric_results_session_id", "psychometric_results", ["session_id"])
    if not _has_index("psychometric_results", "ix_psychometric_results_student_profile_id"):
        op.create_index(
            "ix_psychometric_results_student_profile_id",
            "psychometric_results",
            ["student_profile_id"],
        )
    if not _has_index("psychometric_results", "ix_psychometric_results_user_id"):
        op.create_index("ix_psychometric_results_user_id", "psychometric_results", ["user_id"])

    op.create_foreign_key(
        "fk_psychometric_sessions_current_question",
        "psychometric_sessions",
        "psychometric_questions",
        ["current_question_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    if _has_table("psychometric_sessions"):
        op.drop_constraint("fk_psychometric_sessions_current_question", "psychometric_sessions", type_="foreignkey")

    if _has_table("psychometric_results"):
        op.drop_table("psychometric_results")
    if _has_table("psychometric_answers"):
        op.drop_table("psychometric_answers")
    if _has_table("psychometric_questions"):
        op.drop_table("psychometric_questions")
    if _has_table("psychometric_sessions"):
        op.drop_table("psychometric_sessions")
