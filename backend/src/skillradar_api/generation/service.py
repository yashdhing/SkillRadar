"""HTTP-facing generation service.

This module is the only place that mixes:
- request validation,
- pipeline orchestration (planner → retrieval → composer),
- and SQLAlchemy persistence.

Each of those concerns is reached through a dedicated seam (`agents.factory`,
`retrieval.factory`, repository helpers, the orchestrator). Keep the
boundaries: do not pull retrieval or agent internals into the request handler
and do not push persistence into the orchestrator.
"""

from __future__ import annotations

import asyncio
import re
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from skillradar_api.agents.factory import (
    get_default_lesson_composer,
    get_default_topic_planner,
)
from skillradar_api.agents.protocols import LessonComposerAgent, TopicPlannerAgent
from skillradar_api.agents.types import (
    ComposedLesson,
    RankedSource,
    RecentLessonSummary,
    TopicPlannerInput,
    UserProfileSummary,
)
from skillradar_api.api.schemas import GenerateLessonRequest, GenerateLessonResponse
from skillradar_api.db.enums import GenerationRequestStatus, LessonMode, LessonStatus
from skillradar_api.db.models import (
    GenerationRequest,
    Lesson,
    LessonSource,
    UserProfile,
)
from skillradar_api.db.repositories import (
    GenerationRequestRepository,
    LessonRepository,
    UserProfileRepository,
)
from skillradar_api.generation.orchestrator import (
    GenerationOutcome,
    run_generation_pipeline,
)
from skillradar_api.retrieval.factory import build_default_retrieval_pipeline
from skillradar_api.retrieval.pipeline import RetrievalPipeline

RECENT_LESSON_LIMIT = 5
TARGET_STUDY_MINUTES = 60


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or f"lesson-{uuid4().hex[:8]}"


def _profile_summary(profile: UserProfile | None) -> UserProfileSummary:
    if profile is None:
        return UserProfileSummary(name="SkillRadar User", role_title="senior engineer")

    skills = tuple(skill for skill in profile.skills_json if isinstance(skill, str))
    career_themes = tuple(
        entry["theme"]
        for entry in profile.experience_json
        if isinstance(entry, dict) and isinstance(entry.get("theme"), str)
    )
    topic_priorities = tuple(
        entry["topic"]
        for entry in profile.topic_preferences_json
        if isinstance(entry, dict) and isinstance(entry.get("topic"), str)
    )
    return UserProfileSummary(
        name=profile.name,
        role_title=profile.role_title,
        skills=skills,
        career_themes=career_themes,
        topic_priorities=topic_priorities,
    )


def _to_recent_lesson_summary(lesson: Lesson) -> RecentLessonSummary:
    return RecentLessonSummary(
        lesson_id=lesson.id,
        title=lesson.title,
        mode=lesson.mode,
        seed_phrase=lesson.seed_phrase,
    )


def _build_planner_input(
    *,
    request: GenerateLessonRequest,
    profile: UserProfileSummary,
    active_lesson: Lesson | None,
    recent_lessons: tuple[Lesson, ...],
) -> TopicPlannerInput:
    active_summary = (
        _to_recent_lesson_summary(active_lesson)
        if active_lesson is not None and request.mode == LessonMode.CONTINUE_ACTIVE_LESSON
        else None
    )
    recent_summaries = tuple(
        _to_recent_lesson_summary(lesson)
        for lesson in recent_lessons
        if active_lesson is None or lesson.id != active_lesson.id
    )
    return TopicPlannerInput(
        mode=request.mode,
        profile=profile,
        seed_phrase=request.seed_phrase,
        active_lesson=active_summary,
        recent_lessons=recent_summaries,
    )


def _toc_entries(composed: ComposedLesson) -> list[dict[str, Any]]:
    """Build the toc_json array. Ordering must match `_assemble_markdown`."""
    entries: list[dict[str, Any]] = [
        {"title": "Why this matters", "anchor": "why-this-matters", "depth": 1},
    ]
    if composed.learning_objectives:
        entries.append(
            {
                "title": "Learning objectives",
                "anchor": "learning-objectives",
                "depth": 1,
            }
        )
    for section in composed.sections:
        entries.append(
            {
                "title": section.heading,
                "anchor": section.anchor,
                "depth": section.depth,
            }
        )
    if composed.practical_takeaways:
        entries.append(
            {
                "title": "Practical takeaways",
                "anchor": "practical-takeaways",
                "depth": 1,
            }
        )
    if composed.references:
        entries.append(
            {"title": "References", "anchor": "references", "depth": 1}
        )
    return entries


def _assemble_markdown(composed: ComposedLesson) -> str:
    """Render the composed lesson to markdown.

    Section ordering must mirror `_toc_entries` so the reader's TOC anchors
    resolve to the right `## ` blocks regardless of which composer wrote the
    sections.
    """
    lines: list[str] = [
        f"# {composed.title}",
        "",
        composed.summary,
        "",
        "## Why this matters",
        "",
        composed.why_this_matters,
        "",
    ]
    if composed.learning_objectives:
        lines.append("## Learning objectives")
        lines.append("")
        for objective in composed.learning_objectives:
            lines.append(f"- {objective}")
        lines.append("")
    for section in composed.sections:
        lines.append(f"## {section.heading}")
        lines.append("")
        lines.append(section.body_markdown)
        lines.append("")
    if composed.practical_takeaways:
        lines.append("## Practical takeaways")
        lines.append("")
        for takeaway in composed.practical_takeaways:
            lines.append(f"- {takeaway}")
        lines.append("")
    if composed.references:
        lines.append("## References")
        lines.append("")
        for reference in composed.references:
            lines.append(f"- [{reference.title}]({reference.url})")
        lines.append("")
    return "\n".join(lines)


def _lesson_metadata(
    *,
    outcome: GenerationOutcome,
    generation_request_id: str,
    fallback_reason: str | None,
    active_lesson_available: bool,
) -> dict[str, Any]:
    return {
        "generationRequestId": generation_request_id,
        "fallbackReason": fallback_reason,
        "activeLessonAvailable": active_lesson_available,
        "briefShape": outcome.brief.shape.value,
        "briefNovelty": outcome.brief.novelty.value,
        "briefIntent": outcome.brief.intent,
        "briefTargetTopic": outcome.brief.target_topic,
        "briefSearchQueries": list(outcome.brief.search_queries),
        "briefDesiredSections": list(outcome.brief.desired_section_titles),
        "briefNotes": outcome.brief.notes,
        "learningObjectives": list(outcome.composed.learning_objectives),
        "practicalTakeaways": list(outcome.composed.practical_takeaways),
        "composerMetadata": dict(outcome.composed.metadata),
        "retrieval": {
            "hitCount": len(outcome.retrieval.hits),
            "fetchCount": len(outcome.retrieval.fetches),
            "fetchFailureCount": len(outcome.retrieval.fetch_failures),
            "extractCount": len(outcome.retrieval.extracts),
            "rankedCount": len(outcome.retrieval.ranked),
            "sourceCount": len(outcome.retrieval.sources),
        },
    }


def _build_lesson_sources(sources: tuple[RankedSource, ...]) -> list[LessonSource]:
    rows: list[LessonSource] = []
    for source in sources:
        rows.append(
            LessonSource(
                url=source.url,
                title=source.title,
                domain=source.domain,
                author=source.author,
                published_at=source.published_at,
                relevance_score=source.relevance_score,
                quality_score=source.quality_score,
                novelty_score=source.novelty_score,
                content_snapshot=source.snippet,
                metadata_json={
                    "agentSourceId": source.source_id,
                    **dict(source.metadata),
                },
            )
        )
    return rows


def create_generation_request(
    session: Session,
    request: GenerateLessonRequest,
    *,
    planner: TopicPlannerAgent | None = None,
    composer: LessonComposerAgent | None = None,
    retrieval_pipeline: RetrievalPipeline | None = None,
) -> GenerateLessonResponse:
    """Create a generation request, run the modular pipeline, and persist results.

    Optional `planner`/`composer`/`retrieval_pipeline` arguments exist purely
    to allow tests and future feature flags to swap a stage in without
    monkey-patching the factory module.
    """
    generation_request_repo = GenerationRequestRepository(session)
    lesson_repo = LessonRepository(session)
    profile_repo = UserProfileRepository(session)

    profile_row = profile_repo.get_first()
    profile = _profile_summary(profile_row)
    active_lesson = lesson_repo.get_active()
    fallback_reason = (
        "no_active_lesson"
        if request.mode == LessonMode.CONTINUE_ACTIVE_LESSON and active_lesson is None
        else None
    )
    recent_lessons_all = tuple(lesson_repo.list_all()[:RECENT_LESSON_LIMIT])

    planner_input = _build_planner_input(
        request=request,
        profile=profile,
        active_lesson=active_lesson,
        recent_lessons=recent_lessons_all,
    )

    generation_request = generation_request_repo.add(
        GenerationRequest(
            mode=request.mode,
            seed_phrase=request.seed_phrase,
            input_context_json={
                "profileId": profile_row.id if profile_row else None,
                "activeLessonId": active_lesson.id if active_lesson else None,
                "activeLessonAvailable": active_lesson is not None,
                "recentLessonIds": [lesson.id for lesson in recent_lessons_all],
                "fallbackReason": fallback_reason,
            },
            status=GenerationRequestStatus.RUNNING,
        )
    )
    session.flush()

    pipeline = retrieval_pipeline or build_default_retrieval_pipeline()
    planner_agent = planner or get_default_topic_planner()
    composer_agent = composer or get_default_lesson_composer()

    try:
        outcome = asyncio.run(
            run_generation_pipeline(
                planner_input=planner_input,
                retrieval_pipeline=pipeline,
                planner=planner_agent,
                composer=composer_agent,
                target_minutes=TARGET_STUDY_MINUTES,
            )
        )
    except Exception as error:  # pragma: no cover - defensive guard
        generation_request.status = GenerationRequestStatus.FAILED
        generation_request.error_message = str(error)
        session.flush()
        raise

    composed = outcome.composed
    slug = f"{_slugify(composed.title)}-{generation_request.id[:8]}"
    lesson = lesson_repo.add(
        Lesson(
            title=composed.title,
            slug=slug,
            status=LessonStatus.GENERATED,
            mode=request.mode,
            seed_phrase=request.seed_phrase,
            summary=composed.summary,
            estimated_study_minutes=composed.estimated_study_minutes,
            why_this_matters=composed.why_this_matters,
            content_markdown=_assemble_markdown(composed),
            toc_json=_toc_entries(composed),
            metadata_json=_lesson_metadata(
                outcome=outcome,
                generation_request_id=generation_request.id,
                fallback_reason=fallback_reason,
                active_lesson_available=active_lesson is not None,
            ),
            is_active=False,
            parent_lesson_id=(
                active_lesson.id
                if request.mode == LessonMode.CONTINUE_ACTIVE_LESSON and active_lesson
                else None
            ),
        )
    )
    session.flush()

    for source_row in _build_lesson_sources(outcome.retrieval.sources):
        source_row.lesson_id = lesson.id
        session.add(source_row)
    session.flush()

    generation_request.status = GenerationRequestStatus.COMPLETED
    session.flush()

    return GenerateLessonResponse(
        generationRequestId=generation_request.id,
        lessonId=lesson.id,
        lessonTitle=lesson.title,
        lessonSummary=lesson.summary,
        status=generation_request.status,
        mode=lesson.mode,
        seedPhrase=lesson.seed_phrase,
        fallbackReason=fallback_reason,
    )
