from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from skillradar_api.db.base import Base
from skillradar_api.db.enums import GenerationRequestStatus, LessonMode, LessonStatus


def uuid_str() -> str:
    return str(uuid4())


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class UserProfile(TimestampMixin, Base):
    __tablename__ = "user_profile"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role_title: Mapped[str] = mapped_column(String(255), nullable=False)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    skills_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    experience_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    topic_preferences_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )


class Lesson(TimestampMixin, Base):
    __tablename__ = "lessons"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_lessons_slug"),
        Index(
            "ix_lessons_single_active",
            "is_active",
            unique=True,
            sqlite_where=text("is_active = 1"),
            postgresql_where=text("is_active = true"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[LessonStatus] = mapped_column(
        Enum(LessonStatus, name="lesson_status"),
        nullable=False,
        default=LessonStatus.GENERATED,
    )
    mode: Mapped[LessonMode] = mapped_column(
        Enum(LessonMode, name="lesson_mode"),
        nullable=False,
    )
    seed_phrase: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    estimated_study_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    why_this_matters: Mapped[str] = mapped_column(Text, nullable=False)
    content_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    toc_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    parent_lesson_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("lessons.id", ondelete="SET NULL"),
        nullable=True,
    )
    saved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    parent_lesson: Mapped[Lesson | None] = relationship(
        "Lesson",
        remote_side="Lesson.id",
        back_populates="child_lessons",
    )
    child_lessons: Mapped[list[Lesson]] = relationship(
        "Lesson",
        back_populates="parent_lesson",
    )
    sources: Mapped[list[LessonSource]] = relationship(
        "LessonSource",
        back_populates="lesson",
        cascade="all, delete-orphan",
    )


class LessonSource(Base):
    __tablename__ = "lesson_sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    lesson_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("lessons.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retrieved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    relevance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    novelty_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    content_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    lesson: Mapped[Lesson] = relationship("Lesson", back_populates="sources")


class GenerationRequest(TimestampMixin, Base):
    __tablename__ = "generation_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    mode: Mapped[LessonMode] = mapped_column(
        Enum(LessonMode, name="lesson_mode"),
        nullable=False,
    )
    seed_phrase: Mapped[str | None] = mapped_column(Text, nullable=True)
    input_context_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    status: Mapped[GenerationRequestStatus] = mapped_column(
        Enum(GenerationRequestStatus, name="generation_request_status"),
        nullable=False,
        default=GenerationRequestStatus.QUEUED,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
