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


def test_get_active_lesson_returns_404_when_none_is_set(client) -> None:
    response = client.get("/api/v1/lessons/active")

    assert response.status_code == 404
    assert response.json() == {"detail": "No active lesson is set."}


def test_activate_lesson_marks_it_as_active_and_returns_summary(client, session) -> None:
    generation_response = client.post(
        "/api/v1/lessons/generate",
        json={"mode": "discover_new_topic", "seedPhrase": None},
    )
    lesson_id = generation_response.json()["lessonId"]

    activation_response = client.post(f"/api/v1/lessons/{lesson_id}/activate")

    assert activation_response.status_code == 200
    payload = activation_response.json()
    stored_lesson = session.get(Lesson, lesson_id)

    assert payload["lessonId"] == lesson_id
    assert payload["isActive"] is True
    assert stored_lesson is not None
    assert stored_lesson.is_active is True

    active_response = client.get("/api/v1/lessons/active")
    assert active_response.status_code == 200
    assert active_response.json()["lessonId"] == lesson_id


def test_activate_lesson_clears_previous_active_flag(client, session) -> None:
    first_response = client.post(
        "/api/v1/lessons/generate",
        json={"mode": "discover_new_topic", "seedPhrase": None},
    )
    second_response = client.post(
        "/api/v1/lessons/generate",
        json={"mode": "phrase_seeded", "seedPhrase": "JVM safepoints"},
    )

    first_lesson_id = first_response.json()["lessonId"]
    second_lesson_id = second_response.json()["lessonId"]

    assert client.post(f"/api/v1/lessons/{first_lesson_id}/activate").status_code == 200
    assert client.post(f"/api/v1/lessons/{second_lesson_id}/activate").status_code == 200

    first_lesson = session.get(Lesson, first_lesson_id)
    second_lesson = session.get(Lesson, second_lesson_id)

    assert first_lesson is not None
    assert second_lesson is not None
    assert first_lesson.is_active is False
    assert second_lesson.is_active is True


def test_continue_generation_reports_no_active_fallback_when_none_exists(client, session) -> None:
    response = client.post(
        "/api/v1/lessons/generate",
        json={"mode": "continue_active_lesson", "seedPhrase": None},
    )

    assert response.status_code == 201
    payload = response.json()
    stored_lesson = session.get(Lesson, payload["lessonId"])

    assert payload["fallbackReason"] == "no_active_lesson"
    assert stored_lesson is not None
    assert stored_lesson.parent_lesson_id is None
    assert stored_lesson.metadata_json["fallbackReason"] == "no_active_lesson"


def test_continue_generation_uses_active_lesson_when_available(client, session) -> None:
    first_response = client.post(
        "/api/v1/lessons/generate",
        json={"mode": "discover_new_topic", "seedPhrase": None},
    )
    first_lesson_id = first_response.json()["lessonId"]
    assert client.post(f"/api/v1/lessons/{first_lesson_id}/activate").status_code == 200

    continue_response = client.post(
        "/api/v1/lessons/generate",
        json={"mode": "continue_active_lesson", "seedPhrase": None},
    )

    assert continue_response.status_code == 201
    payload = continue_response.json()
    stored_lesson = session.get(Lesson, payload["lessonId"])

    assert payload["fallbackReason"] is None
    assert stored_lesson is not None
    assert stored_lesson.parent_lesson_id == first_lesson_id
