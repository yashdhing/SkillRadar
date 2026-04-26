from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from skillradar_api.api.schemas import GenerateLessonRequest, GenerateLessonResponse
from skillradar_api.db.session import get_db_session
from skillradar_api.generation.service import create_generation_request

router = APIRouter(prefix="/lessons", tags=["lessons"])


@router.post("/generate", response_model=GenerateLessonResponse, status_code=status.HTTP_201_CREATED)
def generate_lesson(
    request: GenerateLessonRequest,
    session: Session = Depends(get_db_session),
) -> GenerateLessonResponse:
    response = create_generation_request(session, request)
    session.commit()
    return response

