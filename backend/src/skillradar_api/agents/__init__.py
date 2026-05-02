"""Agent abstractions for the SkillRadar lesson generation pipeline.

The agent layer is intentionally split into:

- `types`: pure data contracts (`TopicPlannerInput`, `LessonBrief`,
  `ComposeLessonInput`, `ComposedLesson`, etc.) so pipeline stages exchange
  typed payloads without depending on any provider.
- `protocols`: structural interfaces every agent implementation must satisfy.
- `mock`: deterministic in-process implementations for development and tests.
- `factory`: a single seam for swapping providers without touching call sites.

Generation, retrieval, and composition stages should depend on the protocols
plus the data contracts; concrete providers (mock today, hosted models later)
plug in through the factory.
"""

from skillradar_api.agents.factory import (
    get_default_lesson_composer,
    get_default_topic_planner,
)
from skillradar_api.agents.protocols import LessonComposerAgent, TopicPlannerAgent
from skillradar_api.agents.types import (
    ComposedLesson,
    ComposedLessonReference,
    ComposedLessonSection,
    ComposeLessonInput,
    LessonBrief,
    LessonShape,
    NoveltyTarget,
    RankedSource,
    RecentLessonSummary,
    TopicPlannerInput,
    UserProfileSummary,
)

__all__ = [
    "ComposeLessonInput",
    "ComposedLesson",
    "ComposedLessonReference",
    "ComposedLessonSection",
    "LessonBrief",
    "LessonComposerAgent",
    "LessonShape",
    "NoveltyTarget",
    "RankedSource",
    "RecentLessonSummary",
    "TopicPlannerAgent",
    "TopicPlannerInput",
    "UserProfileSummary",
    "get_default_lesson_composer",
    "get_default_topic_planner",
]
