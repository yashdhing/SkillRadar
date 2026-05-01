from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from skillradar_api.api.schemas import LessonSummaryResponse
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
