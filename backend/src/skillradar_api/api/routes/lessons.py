from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from skillradar_api.api.schemas import (
    GenerateLessonRequest,
    GenerateLessonResponse,
    LessonSummaryResponse,
)
from skillradar_api.db.session import get_db_session
from skillradar_api.generation.service import create_generation_request
from skillradar_api.lessons.service import activate_lesson, get_active_lesson_summary

router = APIRouter(prefix="/lessons", tags=["lessons"])


@router.post("/generate", response_model=GenerateLessonResponse, status_code=status.HTTP_201_CREATED)
def generate_lesson(
    request: GenerateLessonRequest,
    session: Session = Depends(get_db_session),
) -> GenerateLessonResponse:
    response = create_generation_request(session, request)
    session.commit()
    return response


@router.get("/active", response_model=LessonSummaryResponse)
def get_active_lesson(
    session: Session = Depends(get_db_session),
) -> LessonSummaryResponse:
    return get_active_lesson_summary(session)


@router.post("/{lesson_id}/activate", response_model=LessonSummaryResponse)
def mark_lesson_active(
    lesson_id: str,
    session: Session = Depends(get_db_session),
) -> LessonSummaryResponse:
    response = activate_lesson(session, lesson_id)
    session.commit()
    return response
