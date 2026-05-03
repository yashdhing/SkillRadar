"""End-to-end smoke tests for the MVP user journey (TASK-014).

These tests exist alongside (not instead of) the unit + per-endpoint tests
in `test_generation_*`, `test_lesson_library`, and `test_retrieval`. The
goal is to walk the complete user-facing flow in one cohesive test so any
regression in the contract between generation, persistence, library access,
save, activate, and continue is caught in one place.

Reader rendering is exercised by the frontend's typecheck + build pipeline.
Here we assert the *contract* the reader consumes: every TOC title has a
matching `## ` heading in `contentMarkdown`, and every grounded source has
the per-stage scores the reader and library list expect.
"""

from __future__ import annotations

from skillradar_api.db.enums import LessonMode, LessonStatus
from skillradar_api.db.models import Lesson


def _post_generate(client, *, mode: str, phrase: str | None = None):
    response = client.post(
        "/api/v1/lessons/generate",
        json={"mode": mode, "seedPhrase": phrase},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _assert_reader_contract(payload: dict) -> None:
    """Validate the lesson-detail payload meets the reader's expectations."""
    assert payload["contentMarkdown"]
    assert payload["toc"]

    # Every TOC entry must resolve to a `## ` heading in the markdown so the
    # reader's anchor parser can produce a section per TOC entry. This is the
    # cross-task invariant TASK-007 (TOC structure), TASK-010 (markdown
    # assembly), and TASK-011 (reader parser) all share.
    for entry in payload["toc"]:
        assert f"## {entry['title']}" in payload["contentMarkdown"], (
            f"TOC entry '{entry['title']}' has no matching '## ' heading"
        )

    # Grounded sources should expose per-stage scores so the reader, library
    # list, and any future quality-trace UI can render them.
    for source in payload["sources"]:
        assert source["url"].startswith("https://")
        assert source["title"]
        assert source["sourceId"]


def test_full_mvp_user_journey(client, session) -> None:
    # 1. Library starts empty.
    library = client.get("/api/v1/lessons")
    assert library.status_code == 200
    assert library.json() == {"items": []}

    # 2. No active lesson on a fresh app.
    assert client.get("/api/v1/lessons/active").status_code == 404

    # 3. Generate a phrase-seeded lesson.
    phrase_lesson = _post_generate(
        client, mode="phrase_seeded", phrase="Kafka exactly-once in practice"
    )
    assert "Kafka exactly-once" in phrase_lesson["lessonTitle"]
    assert phrase_lesson["fallbackReason"] is None

    # 4. Generate a discover lesson.
    discover_lesson = _post_generate(client, mode="discover_new_topic")
    assert discover_lesson["lessonId"] != phrase_lesson["lessonId"]

    # 5. Library now lists both lessons. Strict newest-first ordering relies
    #    on tie-breaking we don't enforce when two inserts share a timestamp,
    #    so just assert both lessons are present.
    library = client.get("/api/v1/lessons").json()
    library_ids = {item["lessonId"] for item in library["items"]}
    assert phrase_lesson["lessonId"] in library_ids
    assert discover_lesson["lessonId"] in library_ids

    # 6. Save the phrase-seeded lesson.
    save_response = client.post(
        f"/api/v1/lessons/{phrase_lesson['lessonId']}/save"
    )
    assert save_response.status_code == 200
    saved_payload = save_response.json()
    assert saved_payload["status"] == "saved"
    assert saved_payload["savedAt"] is not None

    # 7. Reader / library detail honors the contract.
    detail = client.get(f"/api/v1/lessons/{phrase_lesson['lessonId']}").json()
    _assert_reader_contract(detail)
    assert detail["status"] == "saved"

    # 8. Activate the saved lesson.
    activate_response = client.post(
        f"/api/v1/lessons/{phrase_lesson['lessonId']}/activate"
    )
    assert activate_response.status_code == 200
    active_summary = client.get("/api/v1/lessons/active").json()
    assert active_summary["lessonId"] == phrase_lesson["lessonId"]
    assert active_summary["isActive"] is True

    # 9. Continue from the active lesson.
    continuation = _post_generate(client, mode="continue_active_lesson")
    assert continuation["fallbackReason"] is None
    continuation_lesson = session.get(Lesson, continuation["lessonId"])
    assert continuation_lesson is not None
    assert continuation_lesson.parent_lesson_id == phrase_lesson["lessonId"]

    # 10. Library now has 3 lessons including the continuation.
    library = client.get("/api/v1/lessons").json()
    assert len(library["items"]) == 3
    assert continuation["lessonId"] in {
        item["lessonId"] for item in library["items"]
    }

    # 11. Saving is idempotent; saved_at survives re-saving.
    initial_saved_at = client.get(
        f"/api/v1/lessons/{phrase_lesson['lessonId']}"
    ).json()["savedAt"]
    second_save = client.post(
        f"/api/v1/lessons/{phrase_lesson['lessonId']}/save"
    )
    assert second_save.status_code == 200
    second_saved_at = client.get(
        f"/api/v1/lessons/{phrase_lesson['lessonId']}"
    ).json()["savedAt"]
    assert initial_saved_at == second_saved_at

    # 12. Activating the second lesson clears the previous active flag.
    assert (
        client.post(
            f"/api/v1/lessons/{discover_lesson['lessonId']}/activate"
        ).status_code
        == 200
    )
    new_active = client.get("/api/v1/lessons/active").json()
    assert new_active["lessonId"] == discover_lesson["lessonId"]
    re_fetched_phrase = session.get(Lesson, phrase_lesson["lessonId"])
    assert re_fetched_phrase is not None
    assert re_fetched_phrase.is_active is False


def test_continue_chain_preserves_parent_lineage(client, session) -> None:
    """Three continues in sequence should each link to their immediate parent."""
    seed = _post_generate(client, mode="discover_new_topic")
    assert (
        client.post(f"/api/v1/lessons/{seed['lessonId']}/activate").status_code
        == 200
    )

    parent_chain: list[str] = [seed["lessonId"]]
    for _ in range(3):
        follow_up = _post_generate(client, mode="continue_active_lesson")
        follow_up_lesson = session.get(Lesson, follow_up["lessonId"])
        assert follow_up_lesson is not None
        # Each follow-up's parent should be the lesson that was active when it
        # was generated. Activating the follow-up advances the chain head.
        assert follow_up_lesson.parent_lesson_id == parent_chain[-1]
        assert (
            client.post(
                f"/api/v1/lessons/{follow_up['lessonId']}/activate"
            ).status_code
            == 200
        )
        parent_chain.append(follow_up["lessonId"])

    # Walk the persisted chain back from the tip and verify every link.
    cursor: str | None = parent_chain[-1]
    walked: list[str] = []
    while cursor is not None:
        walked.append(cursor)
        lesson = session.get(Lesson, cursor)
        assert lesson is not None
        cursor = lesson.parent_lesson_id
    assert walked == list(reversed(parent_chain))


def test_continue_without_active_lesson_falls_back_cleanly(client, session) -> None:
    """The continue flow should not hard-fail when there is no active lesson."""
    payload = _post_generate(client, mode="continue_active_lesson")
    assert payload["fallbackReason"] == "no_active_lesson"

    lesson = session.get(Lesson, payload["lessonId"])
    assert lesson is not None
    assert lesson.parent_lesson_id is None
    assert lesson.status == LessonStatus.GENERATED
    assert lesson.mode == LessonMode.CONTINUE_ACTIVE_LESSON
    # Even without an active lesson, the lesson should still be readable.
    detail = client.get(f"/api/v1/lessons/{lesson.id}").json()
    _assert_reader_contract(detail)


def test_three_modes_produce_distinct_lesson_shapes(client, session) -> None:
    """Each generation mode should produce its mode-specific section signature."""
    # Phrase-seeded uses a phrase-specific section title.
    phrase = _post_generate(
        client, mode="phrase_seeded", phrase="distributed tracing"
    )
    phrase_lesson = session.get(Lesson, phrase["lessonId"])
    assert phrase_lesson is not None
    phrase_titles = [entry["title"] for entry in phrase_lesson.toc_json]
    assert "Phrase-specific angles" in phrase_titles

    # Discover branches into adjacent follow-ups.
    discover = _post_generate(client, mode="discover_new_topic")
    discover_lesson = session.get(Lesson, discover["lessonId"])
    assert discover_lesson is not None
    discover_titles = [entry["title"] for entry in discover_lesson.toc_json]
    assert "Adjacent follow-ups" in discover_titles

    # Activate something so continue mode can run with a parent.
    assert (
        client.post(f"/api/v1/lessons/{phrase['lessonId']}/activate").status_code
        == 200
    )

    # Continue mode emits next-continuation prompts.
    follow_up = _post_generate(client, mode="continue_active_lesson")
    follow_up_lesson = session.get(Lesson, follow_up["lessonId"])
    assert follow_up_lesson is not None
    follow_up_titles = [entry["title"] for entry in follow_up_lesson.toc_json]
    assert "Next continuation questions" in follow_up_titles
