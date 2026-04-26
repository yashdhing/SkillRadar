from enum import Enum


class LessonStatus(str, Enum):
    GENERATED = "generated"
    SAVED = "saved"
    ARCHIVED = "archived"


class LessonMode(str, Enum):
    CONTINUE_ACTIVE_LESSON = "continue_active_lesson"
    DISCOVER_NEW_TOPIC = "discover_new_topic"
    PHRASE_SEEDED = "phrase_seeded"


class GenerationRequestStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

