from __future__ import annotations

import asyncio

import pytest

from skillradar_api.agents import (
    ComposeLessonInput,
    ComposedLesson,
    LessonBrief,
    LessonComposerAgent,
    LessonShape,
    NoveltyTarget,
    RankedSource,
    RecentLessonSummary,
    TopicPlannerAgent,
    TopicPlannerInput,
    UserProfileSummary,
    get_default_lesson_composer,
    get_default_topic_planner,
)
from skillradar_api.db.enums import LessonMode


def _profile() -> UserProfileSummary:
    return UserProfileSummary(
        name="Yash Dhing",
        role_title="SDE3",
        skills=("Java", "Kafka"),
        career_themes=("reliability", "trust and safety"),
        topic_priorities=("Java/JVM performance", "Kafka event-driven architecture"),
    )


def test_factory_returns_protocol_compatible_agents() -> None:
    planner = get_default_topic_planner()
    composer = get_default_lesson_composer()

    assert isinstance(planner, TopicPlannerAgent)
    assert isinstance(composer, LessonComposerAgent)


def test_topic_planner_phrase_seeded_uses_phrase_as_target_topic() -> None:
    planner = get_default_topic_planner()
    brief = asyncio.run(
        planner.plan_topic(
            TopicPlannerInput(
                mode=LessonMode.PHRASE_SEEDED,
                profile=_profile(),
                seed_phrase="  Kafka exactly-once in practice  ",
            )
        )
    )

    assert isinstance(brief, LessonBrief)
    assert brief.target_topic == "Kafka exactly-once in practice"
    assert brief.shape == LessonShape.PRACTICAL_WALKTHROUGH
    assert brief.novelty == NoveltyTarget.DEEP_DIVE
    assert "Kafka exactly-once in practice" in brief.search_queries[0]
    assert any("phrase" in section.lower() for section in brief.desired_section_titles)


def test_topic_planner_continue_uses_active_lesson_title() -> None:
    planner = get_default_topic_planner()
    active = RecentLessonSummary(
        lesson_id="lesson-1",
        title="JVM Latency Investigation Patterns",
        mode=LessonMode.DISCOVER_NEW_TOPIC,
    )

    brief = asyncio.run(
        planner.plan_topic(
            TopicPlannerInput(
                mode=LessonMode.CONTINUE_ACTIVE_LESSON,
                profile=_profile(),
                active_lesson=active,
            )
        )
    )

    assert active.title in brief.target_topic
    assert brief.novelty == NoveltyTarget.FOLLOW_UP
    assert any("Recap" in section for section in brief.desired_section_titles)


def test_topic_planner_discover_uses_first_topic_priority() -> None:
    planner = get_default_topic_planner()

    brief = asyncio.run(
        planner.plan_topic(
            TopicPlannerInput(
                mode=LessonMode.DISCOVER_NEW_TOPIC,
                profile=_profile(),
            )
        )
    )

    assert brief.target_topic == "Java/JVM performance"
    assert brief.novelty == NoveltyTarget.ADJACENT
    assert brief.notes == ""


def test_topic_planner_flags_novelty_overlap_with_recent_lessons() -> None:
    planner = get_default_topic_planner()
    recent = (
        RecentLessonSummary(
            lesson_id="r1",
            title="Java/JVM performance",
            mode=LessonMode.DISCOVER_NEW_TOPIC,
        ),
    )

    brief = asyncio.run(
        planner.plan_topic(
            TopicPlannerInput(
                mode=LessonMode.DISCOVER_NEW_TOPIC,
                profile=_profile(),
                recent_lessons=recent,
            )
        )
    )

    assert "novel" in brief.notes.lower() or "fresh" in brief.notes.lower()


def test_topic_planner_is_deterministic_for_identical_inputs() -> None:
    planner = get_default_topic_planner()
    inputs = TopicPlannerInput(
        mode=LessonMode.DISCOVER_NEW_TOPIC,
        profile=_profile(),
    )

    first = asyncio.run(planner.plan_topic(inputs))
    second = asyncio.run(planner.plan_topic(inputs))

    assert first == second


def test_lesson_composer_returns_structured_lesson_with_sections_and_references() -> None:
    composer = get_default_lesson_composer()
    brief = LessonBrief(
        intent="Lesson on Kafka exactly-once for SDE3.",
        target_topic="Kafka exactly-once in practice",
        search_queries=("Kafka exactly-once",),
        shape=LessonShape.PRACTICAL_WALKTHROUGH,
        novelty=NoveltyTarget.DEEP_DIVE,
        desired_section_titles=(
            "Why this phrase matters now",
            "Core concepts",
            "Applied walkthrough",
        ),
    )
    sources = (
        RankedSource(
            source_id="src-1",
            url="https://example.com/kafka-eo",
            title="Kafka Exactly-Once Reference",
            domain="example.com",
            snippet="Reference walkthrough.",
        ),
    )

    lesson = asyncio.run(
        composer.compose_lesson(
            ComposeLessonInput(
                profile=_profile(),
                brief=brief,
                sources=sources,
                target_minutes=60,
            )
        )
    )

    assert isinstance(lesson, ComposedLesson)
    assert lesson.title.startswith("Kafka exactly-once in practice")
    assert lesson.estimated_study_minutes == 60
    assert len(lesson.sections) == len(brief.desired_section_titles)

    anchors = [section.anchor for section in lesson.sections]
    assert len(anchors) == len(set(anchors))
    assert all(section.body_markdown for section in lesson.sections)

    assert len(lesson.references) == 1
    assert lesson.references[0].url == "https://example.com/kafka-eo"
    assert lesson.metadata["source_count"] == 1
    assert lesson.metadata["shape"] == LessonShape.PRACTICAL_WALKTHROUGH.value


def test_lesson_composer_handles_no_sources_without_breaking_contract() -> None:
    composer = get_default_lesson_composer()
    brief = LessonBrief(
        intent="Discover topic.",
        target_topic="Distributed tracing",
        search_queries=("distributed tracing",),
        shape=LessonShape.CONCEPTUAL_OVERVIEW,
        novelty=NoveltyTarget.ADJACENT,
        desired_section_titles=("Why this topic", "Core concepts"),
    )

    lesson = asyncio.run(
        composer.compose_lesson(
            ComposeLessonInput(profile=_profile(), brief=brief)
        )
    )

    assert lesson.references == ()
    assert len(lesson.sections) == 2
    assert lesson.metadata["source_count"] == 0


def test_lesson_composer_disambiguates_duplicate_section_titles() -> None:
    composer = get_default_lesson_composer()
    brief = LessonBrief(
        intent="Test duplicate anchors.",
        target_topic="Tradeoffs",
        search_queries=("tradeoffs",),
        shape=LessonShape.CONCEPTUAL_OVERVIEW,
        novelty=NoveltyTarget.ADJACENT,
        desired_section_titles=("Tradeoffs", "Tradeoffs", "Tradeoffs"),
    )

    lesson = asyncio.run(
        composer.compose_lesson(
            ComposeLessonInput(profile=_profile(), brief=brief)
        )
    )

    anchors = [section.anchor for section in lesson.sections]
    assert anchors == ["tradeoffs", "tradeoffs-2", "tradeoffs-3"]


def test_topic_planner_rotates_past_recently_covered_priorities() -> None:
    planner = get_default_topic_planner()
    profile = _profile()
    recent = (
        RecentLessonSummary(
            lesson_id="r1",
            title="Java/JVM performance deep dive",
            mode=LessonMode.DISCOVER_NEW_TOPIC,
        ),
    )

    brief = asyncio.run(
        planner.plan_topic(
            TopicPlannerInput(
                mode=LessonMode.DISCOVER_NEW_TOPIC,
                profile=profile,
                recent_lessons=recent,
            )
        )
    )

    assert brief.target_topic == "Kafka event-driven architecture"
    assert "rotated" in brief.notes.lower()
    assert "fresh" in brief.notes.lower()


def test_topic_planner_falls_back_when_all_priorities_covered_recently() -> None:
    planner = get_default_topic_planner()
    profile = UserProfileSummary(
        name="Yash Dhing",
        role_title="SDE3",
        topic_priorities=("Java/JVM performance", "Kafka event-driven"),
    )
    recent = (
        RecentLessonSummary(
            lesson_id="r1",
            title="Java/JVM performance overview",
            mode=LessonMode.DISCOVER_NEW_TOPIC,
        ),
        RecentLessonSummary(
            lesson_id="r2",
            title="Kafka deep dive",
            mode=LessonMode.DISCOVER_NEW_TOPIC,
        ),
    )

    brief = asyncio.run(
        planner.plan_topic(
            TopicPlannerInput(
                mode=LessonMode.DISCOVER_NEW_TOPIC,
                profile=profile,
                recent_lessons=recent,
            )
        )
    )

    assert brief.target_topic == "Java/JVM performance"
    assert "covered recently" in brief.notes.lower()
    assert "novel" in brief.notes.lower() or "fresh" in brief.notes.lower()


def test_topic_planner_phrase_overlap_with_recent_lesson_emits_novelty_note() -> None:
    planner = get_default_topic_planner()
    recent = (
        RecentLessonSummary(
            lesson_id="r1",
            title="Kafka exactly-once internals",
            mode=LessonMode.PHRASE_SEEDED,
        ),
    )

    brief = asyncio.run(
        planner.plan_topic(
            TopicPlannerInput(
                mode=LessonMode.PHRASE_SEEDED,
                profile=_profile(),
                seed_phrase="Kafka exactly-once retries",
                recent_lessons=recent,
            )
        )
    )

    assert brief.target_topic == "Kafka exactly-once retries"
    assert "novel" in brief.notes.lower() or "tradeoffs" in brief.notes.lower()
    assert "Kafka exactly-once internals" in brief.notes


def test_topic_planner_continue_mode_flags_continuation_saturation() -> None:
    planner = get_default_topic_planner()
    active = RecentLessonSummary(
        lesson_id="active",
        title="JVM Latency Investigation Patterns",
        mode=LessonMode.DISCOVER_NEW_TOPIC,
    )
    recent = (
        RecentLessonSummary(
            lesson_id="r1",
            title="JVM Latency Investigation Patterns deep dive",
            mode=LessonMode.CONTINUE_ACTIVE_LESSON,
        ),
        RecentLessonSummary(
            lesson_id="r2",
            title="JVM Latency Investigation Patterns case study",
            mode=LessonMode.CONTINUE_ACTIVE_LESSON,
        ),
    )

    brief = asyncio.run(
        planner.plan_topic(
            TopicPlannerInput(
                mode=LessonMode.CONTINUE_ACTIVE_LESSON,
                profile=_profile(),
                active_lesson=active,
                recent_lessons=recent,
            )
        )
    )

    assert "rotating" in brief.notes.lower() or "adjacent" in brief.notes.lower()


def test_topic_planner_appends_skill_anchored_search_query() -> None:
    planner = get_default_topic_planner()
    profile = UserProfileSummary(
        name="Yash Dhing",
        role_title="SDE3",
        skills=("Java", "Kafka"),
        topic_priorities=("Reliability engineering",),
    )

    brief = asyncio.run(
        planner.plan_topic(
            TopicPlannerInput(mode=LessonMode.DISCOVER_NEW_TOPIC, profile=profile)
        )
    )

    queries = [query.lower() for query in brief.search_queries]
    assert any(query.endswith(" java") for query in queries), queries


def test_topic_planner_skips_skill_anchor_when_skill_already_in_root() -> None:
    planner = get_default_topic_planner()
    profile = UserProfileSummary(
        name="Yash Dhing",
        role_title="SDE3",
        skills=("Kafka",),
    )

    brief = asyncio.run(
        planner.plan_topic(
            TopicPlannerInput(
                mode=LessonMode.PHRASE_SEEDED,
                profile=profile,
                seed_phrase="Kafka exactly-once",
            )
        )
    )

    # Without any skill that contributes a *new* token to the root, the
    # skill-anchored query should be omitted entirely rather than producing
    # a redundant duplicate of the root.
    skill_anchored = [
        query
        for query in brief.search_queries
        if query.lower().endswith(" kafka")
        and query.lower() != "kafka exactly-once"
    ]
    assert skill_anchored == []


def test_topic_planner_continue_clean_history_leaves_notes_empty() -> None:
    planner = get_default_topic_planner()
    active = RecentLessonSummary(
        lesson_id="active",
        title="Distributed caching tradeoffs",
        mode=LessonMode.DISCOVER_NEW_TOPIC,
    )

    brief = asyncio.run(
        planner.plan_topic(
            TopicPlannerInput(
                mode=LessonMode.CONTINUE_ACTIVE_LESSON,
                profile=_profile(),
                active_lesson=active,
            )
        )
    )

    assert brief.notes == ""


@pytest.mark.parametrize(
    "mode",
    [
        LessonMode.DISCOVER_NEW_TOPIC,
        LessonMode.PHRASE_SEEDED,
        LessonMode.CONTINUE_ACTIVE_LESSON,
    ],
)
def test_topic_planner_emits_search_queries_for_every_mode(mode: LessonMode) -> None:
    planner = get_default_topic_planner()
    brief = asyncio.run(
        planner.plan_topic(
            TopicPlannerInput(
                mode=mode,
                profile=_profile(),
                seed_phrase="event sourcing" if mode == LessonMode.PHRASE_SEEDED else None,
                active_lesson=(
                    RecentLessonSummary(
                        lesson_id="x",
                        title="Active Topic",
                        mode=LessonMode.DISCOVER_NEW_TOPIC,
                    )
                    if mode == LessonMode.CONTINUE_ACTIVE_LESSON
                    else None
                ),
            )
        )
    )

    assert len(brief.search_queries) >= 2
    assert all(query.strip() for query in brief.search_queries)
