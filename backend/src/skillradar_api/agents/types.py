"""Typed data contracts for the agent layer.

These are deliberately framework-agnostic dataclasses (not Pydantic models or
SQLAlchemy rows) so they can flow between pipeline stages, tests, mock
implementations, and future hosted-model adapters without dragging persistence
or API concerns along with them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from skillradar_api.db.enums import LessonMode


class NoveltyTarget(str, Enum):
    """How much the planner wants the lesson to diverge from prior content."""

    DEEP_DIVE = "deep_dive"
    FOLLOW_UP = "follow_up"
    ADJACENT = "adjacent"
    EXPLORATORY = "exploratory"


class LessonShape(str, Enum):
    """Coarse structural intent for the lesson the composer should produce."""

    CONCEPTUAL_OVERVIEW = "conceptual_overview"
    PRACTICAL_WALKTHROUGH = "practical_walkthrough"
    CASE_STUDY = "case_study"
    TOOLING_REVIEW = "tooling_review"


@dataclass(frozen=True)
class UserProfileSummary:
    """Subset of the user profile relevant to topic planning and composition.

    Kept narrow on purpose so the agent layer never has to know about the full
    persistence row or any future profile-source plumbing.
    """

    name: str
    role_title: str
    skills: tuple[str, ...] = ()
    career_themes: tuple[str, ...] = ()
    topic_priorities: tuple[str, ...] = ()


@dataclass(frozen=True)
class RecentLessonSummary:
    """Compact lesson reference used for novelty / continuation reasoning."""

    lesson_id: str
    title: str
    mode: LessonMode
    seed_phrase: str | None = None


@dataclass(frozen=True)
class TopicPlannerInput:
    """Everything the topic planner needs to produce a lesson brief."""

    mode: LessonMode
    profile: UserProfileSummary
    seed_phrase: str | None = None
    active_lesson: RecentLessonSummary | None = None
    recent_lessons: tuple[RecentLessonSummary, ...] = ()


@dataclass(frozen=True)
class LessonBrief:
    """Planner output consumed by retrieval and composition stages.

    `search_queries` are intentionally a separate field from `target_topic` so
    the search stage can iterate on query construction without forcing the
    planner to be re-run.
    """

    intent: str
    target_topic: str
    search_queries: tuple[str, ...]
    shape: LessonShape
    novelty: NoveltyTarget
    desired_section_titles: tuple[str, ...]
    notes: str = ""


@dataclass(frozen=True)
class RankedSource:
    """Single grounded evidence item handed to the composer.

    This mirrors the persistence-layer `LessonSource` row but stays decoupled:
    the agent layer never needs to know how sources were stored or retrieved.
    """

    source_id: str
    url: str
    title: str
    domain: str | None = None
    author: str | None = None
    published_at: datetime | None = None
    snippet: str | None = None
    relevance_score: float | None = None
    quality_score: float | None = None
    novelty_score: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ComposeLessonInput:
    """Inputs to the lesson composer."""

    profile: UserProfileSummary
    brief: LessonBrief
    sources: tuple[RankedSource, ...] = ()
    target_minutes: int = 60


@dataclass(frozen=True)
class ComposedLessonSection:
    """Single section in a composed lesson, in markdown."""

    heading: str
    anchor: str
    body_markdown: str
    depth: int = 1


@dataclass(frozen=True)
class ComposedLessonReference:
    """Citation surfaced by the composer back to a grounding source."""

    source_id: str
    url: str
    title: str
    note: str | None = None


@dataclass(frozen=True)
class ComposedLesson:
    """Composer output consumed by the persistence + reader stages."""

    title: str
    summary: str
    why_this_matters: str
    learning_objectives: tuple[str, ...]
    sections: tuple[ComposedLessonSection, ...]
    references: tuple[ComposedLessonReference, ...]
    estimated_study_minutes: int
    practical_takeaways: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
