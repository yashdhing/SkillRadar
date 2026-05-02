"""End-to-end tests for the generation orchestration wiring (TASK-010).

These tests exercise the planner → retrieval → composer → persistence chain
through the public `POST /api/v1/lessons/generate` endpoint and verify that
each stage's output is reflected in the persisted lesson + sources rather
than collapsed into one opaque step.
"""

from __future__ import annotations

from skillradar_api.db.enums import LessonStatus
from skillradar_api.db.models import Lesson, LessonSource


def _generate(client, *, mode: str = "discover_new_topic", phrase: str | None = None):
    response = client.post(
        "/api/v1/lessons/generate",
        json={"mode": mode, "seedPhrase": phrase},
    )
    assert response.status_code == 201
    return response.json()


def test_generated_lesson_persists_composed_title_and_summary(client, session) -> None:
    payload = _generate(client, mode="phrase_seeded", phrase="Kafka exactly-once")
    lesson = session.get(Lesson, payload["lessonId"])

    assert lesson is not None
    assert lesson.status == LessonStatus.GENERATED
    assert lesson.title == payload["lessonTitle"]
    assert "Kafka exactly-once" in lesson.title
    assert "kafka exactly-once" in lesson.summary.lower()
    assert lesson.estimated_study_minutes == 60


def test_generated_lesson_metadata_carries_brief_and_retrieval_trace(client, session) -> None:
    payload = _generate(client, mode="phrase_seeded", phrase="distributed tracing")
    lesson = session.get(Lesson, payload["lessonId"])
    assert lesson is not None

    metadata = lesson.metadata_json
    assert metadata["briefTargetTopic"] == "distributed tracing"
    assert metadata["briefShape"] == "practical_walkthrough"
    assert metadata["briefNovelty"] == "deep_dive"
    assert metadata["briefSearchQueries"]
    assert metadata["briefDesiredSections"]
    assert metadata["learningObjectives"]
    assert metadata["practicalTakeaways"]
    assert metadata["composerMetadata"]["agent"] == "mock"

    retrieval = metadata["retrieval"]
    assert retrieval["hitCount"] >= 1
    assert retrieval["fetchCount"] == retrieval["hitCount"]
    assert retrieval["sourceCount"] >= 1


def test_generated_lesson_persists_grounded_lesson_sources(client, session) -> None:
    payload = _generate(client, mode="phrase_seeded", phrase="event sourcing")
    lesson_id = payload["lessonId"]

    sources = (
        session.query(LessonSource)
        .filter(LessonSource.lesson_id == lesson_id)
        .all()
    )

    assert len(sources) >= 1
    for source in sources:
        assert source.url.startswith("https://")
        assert source.title
        assert source.metadata_json["agentSourceId"]
        # Per-stage scores from the ranker survive into persistence.
        assert source.relevance_score is not None
        assert source.quality_score is not None
        assert source.novelty_score is not None
        assert source.metadata_json["combined_score"] is not None


def test_lesson_content_markdown_matches_toc_anchor_order(client, session) -> None:
    payload = _generate(client, mode="discover_new_topic")
    lesson = session.get(Lesson, payload["lessonId"])
    assert lesson is not None

    content = lesson.content_markdown
    toc_titles = [entry["title"] for entry in lesson.toc_json]

    # Composer output should at minimum include "Why this matters", learning
    # objectives, the planner-driven sections, and references when grounded.
    assert "## Why this matters" in content
    assert toc_titles[0] == "Why this matters"
    assert any(title.startswith("Learning objectives") for title in toc_titles)
    assert "References" in toc_titles  # mock retrieval always supplies sources
    assert "## References" in content

    # Each TOC heading must appear as a `## ` section in the markdown so the
    # reader's parser can resolve every TOC anchor to a real section.
    for title in toc_titles:
        assert f"## {title}" in content


def test_continue_mode_with_active_lesson_persists_parent_link_and_no_fallback(
    client, session
) -> None:
    first = _generate(client, mode="discover_new_topic")
    activate = client.post(f"/api/v1/lessons/{first['lessonId']}/activate")
    assert activate.status_code == 200

    follow_up = _generate(client, mode="continue_active_lesson")
    assert follow_up["fallbackReason"] is None

    follow_up_lesson = session.get(Lesson, follow_up["lessonId"])
    assert follow_up_lesson is not None
    assert follow_up_lesson.parent_lesson_id == first["lessonId"]
    assert follow_up_lesson.metadata_json["fallbackReason"] is None
    # Continue-mode briefs should pull the active lesson title into target topic.
    assert first["lessonTitle"] in follow_up_lesson.metadata_json["briefTargetTopic"]


def test_continue_mode_without_active_lesson_records_fallback_in_metadata(
    client, session
) -> None:
    payload = _generate(client, mode="continue_active_lesson")
    assert payload["fallbackReason"] == "no_active_lesson"

    lesson = session.get(Lesson, payload["lessonId"])
    assert lesson is not None
    assert lesson.parent_lesson_id is None
    assert lesson.metadata_json["fallbackReason"] == "no_active_lesson"


def test_recent_lessons_inform_planner_input_context(client, session) -> None:
    first = _generate(client, mode="phrase_seeded", phrase="Kafka exactly-once")
    second = _generate(client, mode="phrase_seeded", phrase="event sourcing")

    second_lesson = session.get(Lesson, second["lessonId"])
    assert second_lesson is not None
    # The first lesson should appear in the recent_lessons context that the
    # service passes to the planner.
    from skillradar_api.db.models import GenerationRequest

    request_row = session.get(GenerationRequest, second["generationRequestId"])
    assert request_row is not None
    assert first["lessonId"] in request_row.input_context_json["recentLessonIds"]
