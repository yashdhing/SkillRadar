from sqlalchemy import select
from sqlalchemy.orm import Session

from skillradar_api.db.models import GenerationRequest, Lesson, LessonSource, UserProfile


class UserProfileRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, profile: UserProfile) -> UserProfile:
        self.session.add(profile)
        return profile


class LessonRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, lesson: Lesson) -> Lesson:
        self.session.add(lesson)
        return lesson

    def get_by_slug(self, slug: str) -> Lesson | None:
        return self.session.scalar(select(Lesson).where(Lesson.slug == slug))


class LessonSourceRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, source: LessonSource) -> LessonSource:
        self.session.add(source)
        return source


class GenerationRequestRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, request: GenerationRequest) -> GenerationRequest:
        self.session.add(request)
        return request

