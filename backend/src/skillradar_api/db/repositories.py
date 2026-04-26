from sqlalchemy import select
from sqlalchemy.orm import Session

from skillradar_api.db.models import GenerationRequest, Lesson, LessonSource, UserProfile


class UserProfileRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, profile: UserProfile) -> UserProfile:
        self.session.add(profile)
        return profile

    def get_by_id(self, profile_id: str) -> UserProfile | None:
        return self.session.get(UserProfile, profile_id)

    def get_first(self) -> UserProfile | None:
        return self.session.scalar(select(UserProfile).order_by(UserProfile.created_at.asc()))


class LessonRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, lesson: Lesson) -> Lesson:
        self.session.add(lesson)
        return lesson

    def get_by_slug(self, slug: str) -> Lesson | None:
        return self.session.scalar(select(Lesson).where(Lesson.slug == slug))

    def get_active(self) -> Lesson | None:
        return self.session.scalar(select(Lesson).where(Lesson.is_active.is_(True)))


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

    def get_by_id(self, request_id: str) -> GenerationRequest | None:
        return self.session.get(GenerationRequest, request_id)
