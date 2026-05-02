from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session, selectinload

from skillradar_api.db.enums import LessonStatus
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

    def get_by_id(self, lesson_id: str) -> Lesson | None:
        return self.session.get(Lesson, lesson_id)

    def get_active(self) -> Lesson | None:
        return self.session.scalar(select(Lesson).where(Lesson.is_active.is_(True)))

    def clear_active_flags(self) -> None:
        self.session.execute(update(Lesson).values(is_active=False))

    def get_with_sources(self, lesson_id: str) -> Lesson | None:
        return self.session.scalar(
            select(Lesson)
            .options(selectinload(Lesson.sources))
            .where(Lesson.id == lesson_id)
        )

    def list_all(self, *, statuses: list[LessonStatus] | None = None) -> list[Lesson]:
        statement = select(Lesson).order_by(Lesson.created_at.desc())
        if statuses:
            statement = statement.where(Lesson.status.in_(statuses))
        return list(self.session.scalars(statement).all())

    def mark_saved(self, lesson: Lesson) -> Lesson:
        if lesson.status != LessonStatus.SAVED:
            lesson.status = LessonStatus.SAVED
        if lesson.saved_at is None:
            lesson.saved_at = datetime.now(tz=timezone.utc)
        return lesson


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
