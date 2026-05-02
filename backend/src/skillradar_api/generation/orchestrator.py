"""End-to-end generation orchestrator.

Wires the modular pipeline stages together while keeping each stage
boundary explicit:

    UserProfile + active lesson + history
        ─► TopicPlannerAgent.plan_topic
        ─► RetrievalPipeline.run (search → fetch → extract → rank → package)
        ─► LessonComposerAgent.compose_lesson
        ─► GenerationOutcome (consumed by persistence layer)

The orchestrator deliberately does NOT touch SQLAlchemy. The service layer
owns persistence and calls this function with prepared inputs so each stage
remains independently testable and replaceable.
"""

from __future__ import annotations

from dataclasses import dataclass

from skillradar_api.agents.protocols import LessonComposerAgent, TopicPlannerAgent
from skillradar_api.agents.types import (
    ComposeLessonInput,
    ComposedLesson,
    LessonBrief,
    TopicPlannerInput,
)
from skillradar_api.retrieval.pipeline import RetrievalPipeline, RetrievalResult


@dataclass(frozen=True)
class GenerationOutcome:
    """Pipeline output ready for persistence + response shaping."""

    brief: LessonBrief
    retrieval: RetrievalResult
    composed: ComposedLesson


async def run_generation_pipeline(
    *,
    planner_input: TopicPlannerInput,
    retrieval_pipeline: RetrievalPipeline,
    planner: TopicPlannerAgent,
    composer: LessonComposerAgent,
    target_minutes: int = 60,
) -> GenerationOutcome:
    """Run the planner → retrieval → composer chain and return the trace."""
    brief = await planner.plan_topic(planner_input)
    retrieval_result = await retrieval_pipeline.run(brief)
    composed = await composer.compose_lesson(
        ComposeLessonInput(
            profile=planner_input.profile,
            brief=brief,
            sources=retrieval_result.sources,
            target_minutes=target_minutes,
        )
    )
    return GenerationOutcome(
        brief=brief,
        retrieval=retrieval_result,
        composed=composed,
    )
