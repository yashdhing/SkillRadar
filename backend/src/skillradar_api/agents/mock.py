"""Deterministic in-process agent implementations.

These exist so the rest of the pipeline (orchestration, persistence, API,
tests) can depend on the protocols today, before any external model provider
is wired in. Behavior is intentionally simple and predictable so unit tests
can assert on its outputs without flakiness.

Replace with hosted-model adapters in TASK-010+ without touching call sites.
"""

from __future__ import annotations

import re

from skillradar_api.agents.types import (
    ComposeLessonInput,
    ComposedLesson,
    ComposedLessonReference,
    ComposedLessonSection,
    LessonBrief,
    LessonShape,
    NoveltyTarget,
    TopicPlannerInput,
)
from skillradar_api.db.enums import LessonMode


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "section"


def _shape_for_mode(mode: LessonMode, seed_phrase: str | None) -> LessonShape:
    if mode == LessonMode.PHRASE_SEEDED and seed_phrase:
        return LessonShape.PRACTICAL_WALKTHROUGH
    if mode == LessonMode.CONTINUE_ACTIVE_LESSON:
        return LessonShape.PRACTICAL_WALKTHROUGH
    return LessonShape.CONCEPTUAL_OVERVIEW


def _novelty_for_mode(mode: LessonMode) -> NoveltyTarget:
    if mode == LessonMode.CONTINUE_ACTIVE_LESSON:
        return NoveltyTarget.FOLLOW_UP
    if mode == LessonMode.PHRASE_SEEDED:
        return NoveltyTarget.DEEP_DIVE
    return NoveltyTarget.ADJACENT


class MockTopicPlannerAgent:
    """Returns a deterministic brief shaped by mode, profile, and seed phrase.

    The output is intentionally derived from the inputs so tests can assert on
    a stable contract: same input -> same brief. Real providers may return
    richer briefs but should preserve the same field semantics.
    """

    async def plan_topic(self, input: TopicPlannerInput) -> LessonBrief:
        mode = input.mode
        profile = input.profile
        seed_phrase = (input.seed_phrase or "").strip() or None

        if mode == LessonMode.CONTINUE_ACTIVE_LESSON and input.active_lesson:
            target_topic = f"Next layer of {input.active_lesson.title}"
            intent = (
                "Continue the current study track with the next practical "
                "layer that builds directly on the active lesson."
            )
            search_root = input.active_lesson.title
        elif mode == LessonMode.PHRASE_SEEDED and seed_phrase:
            target_topic = seed_phrase
            intent = (
                f"Produce a grounded {profile.role_title}-level lesson on "
                f"the user's phrase '{seed_phrase}'."
            )
            search_root = seed_phrase
        else:
            primary_priority = (
                profile.topic_priorities[0]
                if profile.topic_priorities
                else "backend and distributed systems growth"
            )
            target_topic = primary_priority
            intent = (
                f"Surface a fresh {profile.role_title}-level lesson aligned "
                f"to the user's priorities, focused on {primary_priority}."
            )
            search_root = primary_priority

        search_queries: tuple[str, ...] = (
            search_root,
            f"{search_root} case study",
            f"{search_root} failure modes",
            f"{search_root} {profile.role_title} guide",
        )

        recent_titles = {lesson.title.lower() for lesson in input.recent_lessons}
        if input.active_lesson:
            recent_titles.add(input.active_lesson.title.lower())
        if target_topic.lower() in recent_titles:
            notes = (
                "Target topic overlaps with recent lessons; lean toward novel "
                "angles, fresh case studies, or deeper tradeoffs."
            )
        else:
            notes = ""

        desired_sections: tuple[str, ...]
        if mode == LessonMode.CONTINUE_ACTIVE_LESSON:
            desired_sections = (
                "Recap and continuation",
                "Core concepts",
                "Applied walkthrough",
                "Tradeoffs and failure modes",
                "Next continuation questions",
            )
        elif mode == LessonMode.PHRASE_SEEDED:
            desired_sections = (
                "Why this phrase matters now",
                "Core concepts",
                "Applied walkthrough",
                "Tradeoffs and failure modes",
                "Phrase-specific angles",
            )
        else:
            desired_sections = (
                "Why this topic",
                "Core concepts",
                "Applied walkthrough",
                "Tradeoffs and failure modes",
                "Adjacent follow-ups",
            )

        return LessonBrief(
            intent=intent,
            target_topic=target_topic,
            search_queries=search_queries,
            shape=_shape_for_mode(mode, seed_phrase),
            novelty=_novelty_for_mode(mode),
            desired_section_titles=desired_sections,
            notes=notes,
        )


class MockLessonComposerAgent:
    """Produces a deterministic composed lesson from a brief and sources.

    The composer's output preserves all required `ComposedLesson` fields so
    persistence and rendering stages can be wired against the real interface
    today and swap in a hosted model later.
    """

    async def compose_lesson(self, input: ComposeLessonInput) -> ComposedLesson:
        brief = input.brief
        profile = input.profile

        title = (
            f"{brief.target_topic} for {profile.role_title}s"
            if profile.role_title
            else brief.target_topic
        )

        summary = (
            f"A {brief.shape.value.replace('_', ' ')} on {brief.target_topic}, "
            f"oriented toward {brief.novelty.value.replace('_', ' ')} value "
            f"for the user's current trajectory."
        )

        why_this_matters = (
            f"This connects {brief.target_topic} to the user's day-to-day "
            f"work as a {profile.role_title} and to their stated priorities."
        )

        learning_objectives = tuple(
            f"Be able to reason about {section.lower()} in {brief.target_topic}"
            for section in brief.desired_section_titles
        )

        sections: list[ComposedLessonSection] = []
        seen_anchors: set[str] = set()
        for index, section_title in enumerate(brief.desired_section_titles):
            base_anchor = _slugify(section_title)
            anchor = base_anchor
            disambiguator = 2
            while anchor in seen_anchors:
                anchor = f"{base_anchor}-{disambiguator}"
                disambiguator += 1
            seen_anchors.add(anchor)

            body_lines = [
                f"This section frames {section_title.lower()} for "
                f"{brief.target_topic} at a {profile.role_title} level.",
            ]
            if input.sources:
                citation_source = input.sources[index % len(input.sources)]
                body_lines.append(
                    f"Grounded by [{citation_source.title}]({citation_source.url})."
                )
            else:
                body_lines.append(
                    "No grounded sources were attached for this draft; the "
                    "real composer will refuse to produce unsupported claims."
                )
            sections.append(
                ComposedLessonSection(
                    heading=section_title,
                    anchor=anchor,
                    body_markdown="\n\n".join(body_lines),
                    depth=1,
                )
            )

        references = tuple(
            ComposedLessonReference(
                source_id=source.source_id,
                url=source.url,
                title=source.title,
                note=source.snippet,
            )
            for source in input.sources
        )

        practical_takeaways = (
            (
                "Look for one place in your current systems where "
                f"{brief.target_topic} already shows up and capture the gap."
            ),
            (
                "Translate one idea from this lesson into a concrete experiment "
                "or RFC sketch before the next study session."
            ),
        )

        return ComposedLesson(
            title=title,
            summary=summary,
            why_this_matters=why_this_matters,
            learning_objectives=learning_objectives,
            sections=tuple(sections),
            references=references,
            estimated_study_minutes=input.target_minutes,
            practical_takeaways=practical_takeaways,
            metadata={
                "agent": "mock",
                "shape": brief.shape.value,
                "novelty": brief.novelty.value,
                "source_count": len(input.sources),
            },
        )
