from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from skillradar_api.api.schemas import (
    LessonDetailResponse,
    LessonListItem,
    LessonListResponse,
    LessonSourceItem,
    LessonSummaryResponse,
    TocEntryResponse,
)
from skillradar_api.db.models import Lesson
from skillradar_api.db.repositories import LessonRepository


def _to_lesson_summary(lesson: Lesson) -> LessonSummaryResponse:
    return LessonSummaryResponse(
        lessonId=lesson.id,
        title=lesson.title,
        summary=lesson.summary,
        mode=lesson.mode,
        estimatedStudyMinutes=lesson.estimated_study_minutes,
        isActive=lesson.is_active,
    )


def _to_lesson_list_item(lesson: Lesson) -> LessonListItem:
    return LessonListItem(
        lessonId=lesson.id,
        title=lesson.title,
        summary=lesson.summary,
        mode=lesson.mode,
        status=lesson.status,
        seedPhrase=lesson.seed_phrase,
        estimatedStudyMinutes=lesson.estimated_study_minutes,
        isActive=lesson.is_active,
        savedAt=lesson.saved_at,
        createdAt=lesson.created_at,
        updatedAt=lesson.updated_at,
    )


def _to_toc_entries(toc_json: list[dict]) -> list[TocEntryResponse]:
    return [
        TocEntryResponse(
            title=str(entry.get("title", "")),
            anchor=str(entry.get("anchor", "")),
            depth=int(entry.get("depth", 1)),
        )
        for entry in toc_json
    ]


def _to_source_items(lesson: Lesson) -> list[LessonSourceItem]:
    return [
        LessonSourceItem(
            sourceId=source.id,
            url=source.url,
            title=source.title,
            domain=source.domain,
            author=source.author,
        )
        for source in lesson.sources
    ]


def _to_lesson_detail(lesson: Lesson) -> LessonDetailResponse:
    return LessonDetailResponse(
        lessonId=lesson.id,
        title=lesson.title,
        slug=lesson.slug,
        summary=lesson.summary,
        whyThisMatters=lesson.why_this_matters,
        mode=lesson.mode,
        status=lesson.status,
        seedPhrase=lesson.seed_phrase,
        estimatedStudyMinutes=lesson.estimated_study_minutes,
        isActive=lesson.is_active,
        savedAt=lesson.saved_at,
        createdAt=lesson.created_at,
        updatedAt=lesson.updated_at,
        contentMarkdown=lesson.content_markdown,
        toc=_to_toc_entries(lesson.toc_json),
        sources=_to_source_items(lesson),
    )


def get_active_lesson_summary(session: Session) -> LessonSummaryResponse:
    lesson = LessonRepository(session).get_active()
    if lesson is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active lesson is set.",
        )
    return _to_lesson_summary(lesson)


def activate_lesson(session: Session, lesson_id: str) -> LessonSummaryResponse:
    repository = LessonRepository(session)
    lesson = repository.get_by_id(lesson_id)

    if lesson is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found.",
        )

    repository.clear_active_flags()
    lesson.is_active = True
    session.flush()

    return _to_lesson_summary(lesson)


def list_lessons(session: Session) -> LessonListResponse:
    lessons = LessonRepository(session).list_all()
    return LessonListResponse(items=[_to_lesson_list_item(lesson) for lesson in lessons])


def get_lesson_detail(session: Session, lesson_id: str) -> LessonDetailResponse:
    lesson = LessonRepository(session).get_with_sources(lesson_id)
    if lesson is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found.",
        )
    return _to_lesson_detail(lesson)


def save_lesson(session: Session, lesson_id: str) -> LessonDetailResponse:
    repository = LessonRepository(session)
    lesson = repository.get_with_sources(lesson_id)
    if lesson is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found.",
        )
    repository.mark_saved(lesson)
    session.flush()
    return _to_lesson_detail(lesson)
