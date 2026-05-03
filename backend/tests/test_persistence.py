from sqlalchemy.exc import IntegrityError

from skillradar_api.db.enums import GenerationRequestStatus, LessonMode, LessonStatus
from skillradar_api.db.models import GenerationRequest, Lesson, LessonSource, UserProfile
from skillradar_api.db.repositories import (
    GenerationRequestRepository,
    LessonRepository,
    LessonSourceRepository,
    UserProfileRepository,
)


def test_repositories_can_persist_core_entities(session) -> None:
    profile_repo = UserProfileRepository(session)
    lesson_repo = LessonRepository(session)
    source_repo = LessonSourceRepository(session)
    request_repo = GenerationRequestRepository(session)

    profile = profile_repo.add(
        UserProfile(
            name="Yash Dhing",
            role_title="SDE3",
            bio="Backend and distributed systems engineer.",
            skills_json=["Java", "Python", "Kafka"],
            experience_json=[{"theme": "reliability"}],
            topic_preferences_json=[{"topic": "distributed systems", "weight": 1.0}],
        )
    )
    lesson = lesson_repo.add(
        Lesson(
            title="Kafka Reliability Patterns",
            slug="kafka-reliability-patterns",
            status=LessonStatus.GENERATED,
            mode=LessonMode.DISCOVER_NEW_TOPIC,
            summary="A grounded lesson on resilient event processing.",
            estimated_study_minutes=60,
            why_this_matters="Matches current backend and reliability work.",
            content_markdown="# Kafka Reliability Patterns",
            toc_json=[{"title": "Intro", "anchor": "intro", "depth": 1}],
            metadata_json={"source_count": 1},
            is_active=True,
        )
    )
    source_repo.add(
        LessonSource(
            lesson=lesson,
            url="https://example.com/kafka",
            title="Kafka Reliability",
            domain="example.com",
            metadata_json={"kind": "article"},
        )
    )
    request_repo.add(
        GenerationRequest(
            mode=LessonMode.DISCOVER_NEW_TOPIC,
            input_context_json={"reason": "explore"},
            status=GenerationRequestStatus.COMPLETED,
        )
    )

    session.commit()

    assert profile.id is not None
    assert lesson_repo.get_by_slug("kafka-reliability-patterns") is not None


def test_only_one_active_lesson_can_exist(session) -> None:
    first_lesson = Lesson(
        title="First Lesson",
        slug="first-lesson",
        status=LessonStatus.GENERATED,
        mode=LessonMode.DISCOVER_NEW_TOPIC,
        summary="First lesson summary",
        estimated_study_minutes=60,
        why_this_matters="Important",
        content_markdown="# First",
        toc_json=[{"title": "First", "anchor": "first", "depth": 1}],
        metadata_json={"source_count": 0},
        is_active=True,
    )
    second_lesson = Lesson(
        title="Second Lesson",
        slug="second-lesson",
        status=LessonStatus.GENERATED,
        mode=LessonMode.PHRASE_SEEDED,
        summary="Second lesson summary",
        estimated_study_minutes=60,
        why_this_matters="Also important",
        content_markdown="# Second",
        toc_json=[{"title": "Second", "anchor": "second", "depth": 1}],
        metadata_json={"source_count": 0},
        is_active=True,
    )

    session.add(first_lesson)
    session.commit()

    session.add(second_lesson)

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
    else:
        raise AssertionError("Expected unique active lesson constraint to be enforced")



def test_list_all_uses_id_tiebreaker_when_created_at_ties(session) -> None:
    """Back-to-back inserts share a created_at on SQLite; id desc tiebreaks."""
    from datetime import datetime, timezone

    shared_ts = datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc)
    lessons = []
    for slug, lesson_id in [
        ("alpha", "11111111-1111-1111-1111-111111111111"),
        ("beta", "33333333-3333-3333-3333-333333333333"),
        ("gamma", "22222222-2222-2222-2222-222222222222"),
    ]:
        lesson = Lesson(
            id=lesson_id,
            title=slug,
            slug=slug,
            status=LessonStatus.GENERATED,
            mode=LessonMode.DISCOVER_NEW_TOPIC,
            summary=f"{slug} summary",
            estimated_study_minutes=60,
            why_this_matters="x",
            content_markdown=f"# {slug}",
            toc_json=[{"title": "x", "anchor": "x", "depth": 1}],
            metadata_json={},
            created_at=shared_ts,
            updated_at=shared_ts,
        )
        lessons.append(lesson)
        session.add(lesson)
    session.commit()

    listed = LessonRepository(session).list_all()
    # All three share the same created_at; id desc decides the order.
    assert [item.id for item in listed] == sorted(
        [item.id for item in listed], reverse=True
    )
    # Specifically: beta(3...) > gamma(2...) > alpha(1...).
    assert [item.slug for item in listed] == ["beta", "gamma", "alpha"]
