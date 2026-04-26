from skillradar_api.db.enums import GenerationRequestStatus, LessonMode
from skillradar_api.db.models import GenerationRequest, Lesson
from skillradar_api.db.repositories import GenerationRequestRepository


def test_generate_lesson_creates_request_and_lesson_for_discover_mode(
    client,
    session,
) -> None:
    response = client.post(
        "/api/v1/lessons/generate",
        json={"mode": "discover_new_topic", "seedPhrase": None},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["mode"] == "discover_new_topic"
    assert payload["lessonTitle"]
    assert payload["lessonSummary"]

    stored_request = GenerationRequestRepository(session).get_by_id(
        payload["generationRequestId"],
    )
    stored_lesson = session.get(Lesson, payload["lessonId"])

    assert stored_request is not None
    assert stored_request.status == GenerationRequestStatus.COMPLETED
    assert stored_request.mode == LessonMode.DISCOVER_NEW_TOPIC
    assert stored_lesson is not None
    assert stored_lesson.metadata_json["generationRequestId"] == stored_request.id


def test_generate_lesson_requires_phrase_for_phrase_seeded_mode(client) -> None:
    response = client.post(
        "/api/v1/lessons/generate",
        json={"mode": "phrase_seeded", "seedPhrase": "   "},
    )

    assert response.status_code == 422


def test_generate_lesson_clears_phrase_for_non_phrase_modes(client, session) -> None:
    response = client.post(
        "/api/v1/lessons/generate",
        json={
            "mode": "continue_active_lesson",
            "seedPhrase": "should be ignored",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    stored_request = session.get(GenerationRequest, payload["generationRequestId"])

    assert payload["seedPhrase"] is None
    assert stored_request is not None
    assert stored_request.seed_phrase is None

