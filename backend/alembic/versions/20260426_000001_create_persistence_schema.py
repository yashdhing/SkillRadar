"""create persistence schema

Revision ID: 20260426_000001
Revises:
Create Date: 2026-04-26 00:00:01
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260426_000001"
down_revision = None
branch_labels = None
depends_on = None


lesson_status = postgresql.ENUM("generated", "saved", "archived", name="lesson_status")
lesson_mode = postgresql.ENUM(
    "continue_active_lesson",
    "discover_new_topic",
    "phrase_seeded",
    name="lesson_mode",
)
generation_request_status = postgresql.ENUM(
    "queued",
    "running",
    "completed",
    "failed",
    name="generation_request_status",
)

lesson_status_column = postgresql.ENUM(
    "generated",
    "saved",
    "archived",
    name="lesson_status",
    create_type=False,
)
lesson_mode_column = postgresql.ENUM(
    "continue_active_lesson",
    "discover_new_topic",
    "phrase_seeded",
    name="lesson_mode",
    create_type=False,
)
generation_request_status_column = postgresql.ENUM(
    "queued",
    "running",
    "completed",
    "failed",
    name="generation_request_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    lesson_status.create(bind, checkfirst=True)
    lesson_mode.create(bind, checkfirst=True)
    generation_request_status.create(bind, checkfirst=True)

    op.create_table(
        "user_profile",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("role_title", sa.String(length=255), nullable=False),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("skills_json", sa.JSON(), nullable=False),
        sa.Column("experience_json", sa.JSON(), nullable=False),
        sa.Column("topic_preferences_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "lessons",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("status", lesson_status_column, nullable=False),
        sa.Column("mode", lesson_mode_column, nullable=False),
        sa.Column("seed_phrase", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("estimated_study_minutes", sa.Integer(), nullable=False),
        sa.Column("why_this_matters", sa.Text(), nullable=False),
        sa.Column("content_markdown", sa.Text(), nullable=False),
        sa.Column("toc_json", sa.JSON(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("parent_lesson_id", sa.String(length=36), sa.ForeignKey("lessons.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("saved_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("slug", name="uq_lessons_slug"),
    )
    op.create_index(
        "ix_lessons_single_active",
        "lessons",
        ["is_active"],
        unique=True,
        postgresql_where=sa.text("is_active = true"),
        sqlite_where=sa.text("is_active = 1"),
    )

    op.create_table(
        "lesson_sources",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("lesson_id", sa.String(length=36), sa.ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("domain", sa.String(length=255), nullable=True),
        sa.Column("author", sa.String(length=255), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("relevance_score", sa.Float(), nullable=True),
        sa.Column("quality_score", sa.Float(), nullable=True),
        sa.Column("novelty_score", sa.Float(), nullable=True),
        sa.Column("content_snapshot", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
    )
    op.create_index("ix_lesson_sources_lesson_id", "lesson_sources", ["lesson_id"], unique=False)

    op.create_table(
        "generation_requests",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("mode", lesson_mode_column, nullable=False),
        sa.Column("seed_phrase", sa.Text(), nullable=True),
        sa.Column("input_context_json", sa.JSON(), nullable=False),
        sa.Column("status", generation_request_status_column, nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("generation_requests")
    op.drop_index("ix_lesson_sources_lesson_id", table_name="lesson_sources")
    op.drop_table("lesson_sources")
    op.drop_index("ix_lessons_single_active", table_name="lessons")
    op.drop_table("lessons")
    op.drop_table("user_profile")

    bind = op.get_bind()
    generation_request_status.drop(bind, checkfirst=True)
    lesson_mode.drop(bind, checkfirst=True)
    lesson_status.drop(bind, checkfirst=True)
