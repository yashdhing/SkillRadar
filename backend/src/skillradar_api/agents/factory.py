"""Single seam for choosing the active agent provider.

Pipeline code should resolve agents through this factory so swapping the
mock for a hosted-model adapter is a one-line change rather than a hunt
through call sites.
"""

from __future__ import annotations

from skillradar_api.agents.mock import MockLessonComposerAgent, MockTopicPlannerAgent
from skillradar_api.agents.protocols import LessonComposerAgent, TopicPlannerAgent


def get_default_topic_planner() -> TopicPlannerAgent:
    """Return the default topic planner — currently the deterministic mock."""
    return MockTopicPlannerAgent()


def get_default_lesson_composer() -> LessonComposerAgent:
    """Return the default lesson composer — currently the deterministic mock."""
    return MockLessonComposerAgent()
