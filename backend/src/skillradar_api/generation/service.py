from __future__ import annotations

import re
from uuid import uuid4

from sqlalchemy.orm import Session

from skillradar_api.api.schemas import GenerateLessonRequest, GenerateLessonResponse
from skillradar_api.db.enums import GenerationRequestStatus, LessonMode, LessonStatus
from skillradar_api.db.models import GenerationRequest, Lesson
from skillradar_api.db.repositories import (
    GenerationRequestRepository,
    LessonRepository,
    UserProfileRepository,
)


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or f"lesson-{uuid4().hex[:8]}"


def _build_title(
    mode: LessonMode,
    seed_phrase: str | None,
    active_lesson_title: str | None,
) -> str:
    if mode == LessonMode.CONTINUE_ACTIVE_LESSON:
        if active_lesson_title:
            return f"Next step after {active_lesson_title}"
        return "Next step in your current backend study track"
    if mode == LessonMode.PHRASE_SEEDED and seed_phrase:
        return f"{seed_phrase.strip()} in practice"
    return "A fresh lesson for backend and distributed-systems growth"


def _build_summary(mode: LessonMode, seed_phrase: str | None) -> str:
    if mode == LessonMode.CONTINUE_ACTIVE_LESSON:
        return (
            "A generated draft that continues the current study direction while "
            "full active-lesson orchestration is still being wired."
        )
    if mode == LessonMode.PHRASE_SEEDED and seed_phrase:
        return (
            f"A generated draft lesson seeded from '{seed_phrase.strip()}' with "
            "placeholder structure until the retrieval and composition pipeline lands."
        )
    return (
        "A generated draft lesson that explores a new topic aligned to the "
        "seeded SkillRadar profile."
    )


def _build_why_this_matters(role_title: str, mode: LessonMode) -> str:
    if mode == LessonMode.PHRASE_SEEDED:
        return (
            f"This phrase-seeded draft is framed for {role_title}-level practical "
            "backend growth and can later be enriched with grounded sources."
        )
    if mode == LessonMode.CONTINUE_ACTIVE_LESSON:
        return (
            f"This draft keeps momentum for an {role_title} study track until "
            "active-lesson state and retrieval orchestration are connected."
        )
    return (
        f"This draft explores a career-useful direction for an {role_title}, "
        "using the seeded profile as a lightweight relevance anchor."
    )


def _build_toc(mode: LessonMode) -> list[dict[str, str | int]]:
    base_entries = [
        {"title": "Why this topic", "anchor": "why-this-topic", "depth": 1},
        {"title": "Core concepts", "anchor": "core-concepts", "depth": 1},
        {"title": "Applied walkthrough", "anchor": "applied-walkthrough", "depth": 1},
    ]
    if mode == LessonMode.CONTINUE_ACTIVE_LESSON:
        base_entries.append(
            {"title": "Next continuation questions", "anchor": "next-questions", "depth": 1},
        )
    elif mode == LessonMode.PHRASE_SEEDED:
        base_entries.append(
            {"title": "Phrase-specific angles", "anchor": "phrase-angles", "depth": 1},
        )
    else:
        base_entries.append(
            {"title": "Adjacent follow-ups", "anchor": "adjacent-follow-ups", "depth": 1},
        )
    return base_entries


def _build_content_markdown(title: str, summary: str, toc: list[dict[str, str | int]]) -> str:
    sections = [
        f"# {title}",
        "",
        summary,
        "",
    ]
    for entry in toc:
        sections.extend(
            [
                f"## {entry['title']}",
                "",
                "This is a generated draft section placeholder. A later task will replace this content with grounded lesson material produced from modular retrieval and composition stages.",
                "",
            ]
        )
    return "\n".join(sections)


def create_generation_request(
    session: Session,
    request: GenerateLessonRequest,
) -> GenerateLessonResponse:
    generation_request_repo = GenerationRequestRepository(session)
    lesson_repo = LessonRepository(session)
    profile_repo = UserProfileRepository(session)

    profile = profile_repo.get_first()
    active_lesson = lesson_repo.get_active()

    title = _build_title(request.mode, request.seed_phrase, active_lesson.title if active_lesson else None)
    summary = _build_summary(request.mode, request.seed_phrase)
    toc = _build_toc(request.mode)

    generation_request = generation_request_repo.add(
        GenerationRequest(
            mode=request.mode,
            seed_phrase=request.seed_phrase,
            input_context_json={
                "profileId": profile.id if profile else None,
                "activeLessonId": active_lesson.id if active_lesson else None,
                "activeLessonAvailable": active_lesson is not None,
            },
            status=GenerationRequestStatus.RUNNING,
        )
    )
    session.flush()

    slug = f"{_slugify(title)}-{generation_request.id[:8]}"
    lesson = lesson_repo.add(
        Lesson(
            title=title,
            slug=slug,
            status=LessonStatus.GENERATED,
            mode=request.mode,
            seed_phrase=request.seed_phrase,
            summary=summary,
            estimated_study_minutes=60,
            why_this_matters=_build_why_this_matters(
                profile.role_title if profile else "senior engineer",
                request.mode,
            ),
            content_markdown=_build_content_markdown(title, summary, toc),
            toc_json=toc,
            metadata_json={
                "generationRequestId": generation_request.id,
                "placeholder": True,
                "activeLessonAvailable": active_lesson is not None,
            },
            is_active=False,
            parent_lesson_id=active_lesson.id if request.mode == LessonMode.CONTINUE_ACTIVE_LESSON and active_lesson else None,
        )
    )
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
    )

