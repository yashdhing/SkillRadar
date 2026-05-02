from skillradar_api.db.enums import LessonStatus
from skillradar_api.db.models import Lesson, LessonSource


def _generate_lesson(client, *, mode: str = "discover_new_topic", phrase: str | None = None) -> dict:
    response = client.post(
        "/api/v1/lessons/generate",
        json={"mode": mode, "seedPhrase": phrase},
    )
    assert response.status_code == 201
    return response.json()


def test_list_lessons_returns_empty_when_none_exist(client) -> None:
    response = client.get("/api/v1/lessons")

    assert response.status_code == 200
    assert response.json() == {"items": []}


def test_list_lessons_returns_generated_and_saved_with_metadata(client, session) -> None:
    first = _generate_lesson(client, mode="discover_new_topic")
    second = _generate_lesson(client, mode="phrase_seeded", phrase="JVM safepoints")

    save_response = client.post(f"/api/v1/lessons/{second['lessonId']}/save")
    assert save_response.status_code == 200

    list_response = client.get("/api/v1/lessons")
    assert list_response.status_code == 200
    items = list_response.json()["items"]

    assert {item["lessonId"] for item in items} == {first["lessonId"], second["lessonId"]}

    by_id = {item["lessonId"]: item for item in items}
    assert by_id[first["lessonId"]]["status"] == "generated"
    assert by_id[first["lessonId"]]["savedAt"] is None
    assert by_id[second["lessonId"]]["status"] == "saved"
    assert by_id[second["lessonId"]]["savedAt"] is not None
    assert by_id[second["lessonId"]]["seedPhrase"] == "JVM safepoints"


def test_get_lesson_detail_returns_full_payload_with_sources(client, session) -> None:
    generated = _generate_lesson(client)
    lesson_id = generated["lessonId"]

    lesson = session.get(Lesson, lesson_id)
    assert lesson is not None
    session.add(
        LessonSource(
            lesson_id=lesson.id,
            url="https://example.com/grounding",
            title="Grounding Article",
            domain="example.com",
            author="Test Author",
            metadata_json={"kind": "article"},
        )
    )
    session.commit()

    response = client.get(f"/api/v1/lessons/{lesson_id}")
    assert response.status_code == 200
    payload = response.json()

    assert payload["lessonId"] == lesson_id
    assert payload["title"] == generated["lessonTitle"]
    assert payload["contentMarkdown"]
    assert isinstance(payload["toc"], list) and len(payload["toc"]) >= 1
    assert payload["toc"][0]["anchor"]
    assert len(payload["sources"]) == 1
    assert payload["sources"][0]["url"] == "https://example.com/grounding"
    assert payload["sources"][0]["domain"] == "example.com"


def test_get_lesson_detail_returns_404_for_unknown_lesson(client) -> None:
    response = client.get("/api/v1/lessons/unknown-id-xyz")
    assert response.status_code == 404
    assert response.json() == {"detail": "Lesson not found."}


def test_save_lesson_marks_status_and_saved_at(client, session) -> None:
    generated = _generate_lesson(client)
    lesson_id = generated["lessonId"]

    response = client.post(f"/api/v1/lessons/{lesson_id}/save")
    assert response.status_code == 200
    payload = response.json()

    assert payload["status"] == "saved"
    assert payload["savedAt"] is not None

    stored = session.get(Lesson, lesson_id)
    assert stored is not None
    assert stored.status == LessonStatus.SAVED
    assert stored.saved_at is not None


def test_save_lesson_is_idempotent_and_preserves_first_saved_at(client, session) -> None:
    generated = _generate_lesson(client)
    lesson_id = generated["lessonId"]

    assert client.post(f"/api/v1/lessons/{lesson_id}/save").status_code == 200
    session.expire_all()
    first_persisted = session.get(Lesson, lesson_id)
    assert first_persisted is not None
    first_saved_at = first_persisted.saved_at
    assert first_saved_at is not None

    second = client.post(f"/api/v1/lessons/{lesson_id}/save")
    assert second.status_code == 200
    assert second.json()["status"] == "saved"

    session.expire_all()
    second_persisted = session.get(Lesson, lesson_id)
    assert second_persisted is not None
    assert second_persisted.saved_at == first_saved_at
    assert second_persisted.status == LessonStatus.SAVED


def test_save_lesson_returns_404_for_unknown_lesson(client) -> None:
    response = client.post("/api/v1/lessons/unknown-id-xyz/save")
    assert response.status_code == 404
    assert response.json() == {"detail": "Lesson not found."}
