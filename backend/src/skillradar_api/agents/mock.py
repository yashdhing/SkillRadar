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
    RecentLessonSummary,
    TopicPlannerInput,
    UserProfileSummary,
)
from skillradar_api.db.enums import LessonMode

_TOKEN_RE = re.compile(r"[a-z0-9]+")
# Tokens that show up in almost every backend topic — including them in the
# overlap test makes everything look "recently covered" and would defeat the
# rotation. They stay searchable in queries; they just don't count for novelty.
_NOVELTY_STOPWORDS: frozenset[str] = frozenset(
    {
        "and",
        "in",
        "of",
        "the",
        "for",
        "to",
        "a",
        "an",
        "on",
        "at",
        "with",
        "by",
    }
)


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "section"


def _meaningful_tokens(value: str) -> set[str]:
    """Tokenize a string for novelty/overlap reasoning, dropping stopwords."""
    return {
        token
        for token in _TOKEN_RE.findall(value.lower())
        if token not in _NOVELTY_STOPWORDS and len(token) > 1
    }


def _has_meaningful_overlap(left: str, right: str) -> bool:
    """True iff `left` and `right` share at least one non-stopword token."""
    return bool(_meaningful_tokens(left) & _meaningful_tokens(right))


def _recent_corpus(input: TopicPlannerInput) -> tuple[str, ...]:
    """All recent lesson signal worth checking for novelty."""
    titles: list[str] = [lesson.title for lesson in input.recent_lessons]
    if input.active_lesson is not None:
        titles.append(input.active_lesson.title)
    seeds: list[str] = [
        lesson.seed_phrase
        for lesson in input.recent_lessons
        if lesson.seed_phrase
    ]
    if input.active_lesson is not None and input.active_lesson.seed_phrase:
        seeds.append(input.active_lesson.seed_phrase)
    return tuple(titles + seeds)


def _select_discover_topic(
    profile: UserProfileSummary,
    recent_corpus: tuple[str, ...],
) -> tuple[str, str | None]:
    """Pick the first topic priority not covered by recent lessons.

    Falls back to the first priority when every priority overlaps with the
    recent corpus, with a notes string flagging the saturation. Returns
    `(target_topic, notes_or_None)`.
    """
    priorities = profile.topic_priorities
    if not priorities:
        return ("backend and distributed systems growth", None)

    for index, priority in enumerate(priorities):
        if not any(
            _has_meaningful_overlap(priority, recent) for recent in recent_corpus
        ):
            note = None
            if index > 0:
                rotated_word = "priority" if index == 1 else "priorities"
                note = (
                    f"Rotated past {index} recently covered {rotated_word} "
                    "to keep this discover lesson fresh."
                )
            return (priority, note)

    return (
        priorities[0],
        "All topic priorities have been covered recently; lean into novel "
        "angles, fresh case studies, or deeper tradeoffs.",
    )


def _skill_anchored_query(search_root: str, profile: UserProfileSummary) -> str | None:
    """Append a skill the user already works with as a context term.

    Skips skills whose tokens are entirely contained in the search root
    (would be redundant) and skills that cannot contribute new tokens.
    """
    root_tokens = set(_TOKEN_RE.findall(search_root.lower()))
    for skill in profile.skills:
        skill_tokens = set(_TOKEN_RE.findall(skill.lower()))
        if not skill_tokens or skill_tokens.issubset(root_tokens):
            continue
        return f"{search_root} {skill}"
    return None


def _novelty_overlap_note(
    target_topic: str,
    recent_corpus: tuple[str, ...],
) -> str | None:
    for recent in recent_corpus:
        if _has_meaningful_overlap(target_topic, recent):
            return (
                f"Target topic overlaps with the recent '{recent}' lesson; "
                "lean toward novel angles, fresh case studies, or deeper "
                "tradeoffs."
            )
    return None


def _continuation_saturation_note(
    active_lesson: RecentLessonSummary | None,
    recent_lessons: tuple[RecentLessonSummary, ...],
) -> str | None:
    if active_lesson is None:
        return None
    related = [
        lesson
        for lesson in recent_lessons
        if lesson.lesson_id != active_lesson.lesson_id
        and _has_meaningful_overlap(lesson.title, active_lesson.title)
    ]
    if len(related) >= 2:
        return (
            f"Already {len(related)} recent lessons relate to '{active_lesson.title}'; "
            "consider rotating to an adjacent angle on the next generation."
        )
    return None


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
        recent_corpus = _recent_corpus(input)

        rotation_note: str | None = None

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
            target_topic, rotation_note = _select_discover_topic(
                profile, recent_corpus
            )
            intent = (
                f"Surface a fresh {profile.role_title}-level lesson aligned "
                f"to the user's priorities, focused on {target_topic}."
            )
            search_root = target_topic

        # Build queries: literal root, two angles, an optional skill-anchored
        # query that pairs the topic with a stack the user already works in,
        # and a role-anchored query. Skill anchoring is the personalization
        # seam — it biases retrieval without locking the planner contract to
        # any specific stack.
        queries: list[str] = [
            search_root,
            f"{search_root} case study",
            f"{search_root} failure modes",
        ]
        skill_query = _skill_anchored_query(search_root, profile)
        if skill_query:
            queries.append(skill_query)
        queries.append(f"{search_root} {profile.role_title} guide")

        # Notes describe the most actionable signal: a rotation we already
        # applied, otherwise a continuation-saturation hint, otherwise a
        # novelty-overlap warning. Empty notes mean the topic looks fresh.
        if rotation_note is not None:
            notes = rotation_note
        elif (
            mode == LessonMode.CONTINUE_ACTIVE_LESSON
            and input.active_lesson is not None
        ):
            notes = _continuation_saturation_note(
                input.active_lesson, input.recent_lessons
            ) or ""
        else:
            notes = _novelty_overlap_note(target_topic, recent_corpus) or ""

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
            search_queries=tuple(queries),
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
