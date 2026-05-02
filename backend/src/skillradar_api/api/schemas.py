from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from skillradar_api.db.enums import GenerationRequestStatus, LessonMode, LessonStatus


class GenerateLessonRequest(BaseModel):
    mode: LessonMode
    seed_phrase: str | None = Field(default=None, alias="seedPhrase")

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="after")
    def validate_phrase_rules(self) -> "GenerateLessonRequest":
        normalized_phrase = self.seed_phrase.strip() if self.seed_phrase else None

        if self.mode == LessonMode.PHRASE_SEEDED and not normalized_phrase:
            raise ValueError("seedPhrase is required when mode is phrase_seeded")

        if self.mode != LessonMode.PHRASE_SEEDED:
            self.seed_phrase = None
        else:
            self.seed_phrase = normalized_phrase

        return self


class GenerateLessonResponse(BaseModel):
    generation_request_id: str = Field(alias="generationRequestId")
    lesson_id: str = Field(alias="lessonId")
    lesson_title: str = Field(alias="lessonTitle")
    lesson_summary: str = Field(alias="lessonSummary")
    status: GenerationRequestStatus
    mode: LessonMode
    seed_phrase: str | None = Field(alias="seedPhrase")
    fallback_reason: str | None = Field(default=None, alias="fallbackReason")

    model_config = ConfigDict(populate_by_name=True, use_enum_values=True)


class LessonSummaryResponse(BaseModel):
    lesson_id: str = Field(alias="lessonId")
    title: str
    summary: str
    mode: LessonMode
    estimated_study_minutes: int = Field(alias="estimatedStudyMinutes")
    is_active: bool = Field(alias="isActive")

    model_config = ConfigDict(populate_by_name=True, use_enum_values=True)


class LessonListItem(BaseModel):
    lesson_id: str = Field(alias="lessonId")
    title: str
    summary: str
    mode: LessonMode
    status: LessonStatus
    seed_phrase: str | None = Field(alias="seedPhrase")
    estimated_study_minutes: int = Field(alias="estimatedStudyMinutes")
    is_active: bool = Field(alias="isActive")
    saved_at: datetime | None = Field(alias="savedAt")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    model_config = ConfigDict(populate_by_name=True, use_enum_values=True)


class LessonListResponse(BaseModel):
    items: list[LessonListItem]


class TocEntryResponse(BaseModel):
    title: str
    anchor: str
    depth: int


class LessonSourceItem(BaseModel):
    source_id: str = Field(alias="sourceId")
    url: str
    title: str
    domain: str | None
    author: str | None

    model_config = ConfigDict(populate_by_name=True)


class LessonDetailResponse(BaseModel):
    lesson_id: str = Field(alias="lessonId")
    title: str
    slug: str
    summary: str
    why_this_matters: str = Field(alias="whyThisMatters")
    mode: LessonMode
    status: LessonStatus
    seed_phrase: str | None = Field(alias="seedPhrase")
    estimated_study_minutes: int = Field(alias="estimatedStudyMinutes")
    is_active: bool = Field(alias="isActive")
    saved_at: datetime | None = Field(alias="savedAt")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    content_markdown: str = Field(alias="contentMarkdown")
    toc: list[TocEntryResponse]
    sources: list[LessonSourceItem]

    model_config = ConfigDict(populate_by_name=True, use_enum_values=True)
