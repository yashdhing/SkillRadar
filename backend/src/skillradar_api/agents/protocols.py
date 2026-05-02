"""Structural interfaces for SkillRadar agent providers.

These protocols are runtime-checkable so the factory can validate any future
provider adapter without forcing it to subclass a base class. Pipeline code
should depend on these protocols only — never on a concrete implementation.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from skillradar_api.agents.types import (
    ComposeLessonInput,
    ComposedLesson,
    LessonBrief,
    TopicPlannerInput,
)


@runtime_checkable
class TopicPlannerAgent(Protocol):
    """Decides what lesson to produce given mode, profile, and history."""

    async def plan_topic(self, input: TopicPlannerInput) -> LessonBrief:
        """Return a brief that downstream retrieval + composition stages use."""
        ...


@runtime_checkable
class LessonComposerAgent(Protocol):
    """Writes a structured lesson from a brief plus grounded sources."""

    async def compose_lesson(self, input: ComposeLessonInput) -> ComposedLesson:
        """Return a fully structured lesson ready for persistence + rendering."""
        ...
