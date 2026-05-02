"""Stage-local data contracts for the retrieval pipeline.

The retrieval layer owns its own intermediate types (`SearchHit`,
`FetchedDocument`, `ExtractedContent`, `RankedExtract`) and converts the
final shortlist into `RankedSource` from the agent layer at its outer
boundary, so persistence and AI providers never see retrieval internals.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class SourceKind(str, Enum):
    """Coarse content category — useful for ranking and source diversity."""

    BLOG = "blog"
    DOCS = "docs"
    POSTMORTEM = "postmortem"
    PAPER = "paper"
    REPO = "repo"
    NEWSLETTER = "newsletter"
    TALK = "talk"
    OTHER = "other"


class FetchStatus(str, Enum):
    """Outcome of a fetch attempt — keeps failures in the trace explicit."""

    OK = "ok"
    NOT_FOUND = "not_found"
    BLOCKED = "blocked"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass(frozen=True)
class SearchQuery:
    """One query the search provider should resolve.

    The `intent` is preserved so downstream stages can score relevance
    against the planner's framing instead of just the literal query.
    """

    text: str
    intent: str | None = None
    max_results: int = 5
    recency_days: int | None = None


@dataclass(frozen=True)
class SearchHit:
    """Single discovered candidate URL from the search provider."""

    url: str
    title: str
    snippet: str | None = None
    domain: str | None = None
    source_kind: SourceKind = SourceKind.OTHER
    discovery_score: float | None = None
    query_text: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FetchedDocument:
    """Raw fetch artifact for a single hit."""

    hit: SearchHit
    status: FetchStatus
    raw_text: str | None = None
    content_type: str | None = None
    retrieved_at: datetime | None = None
    error: str | None = None


@dataclass(frozen=True)
class ExtractedContent:
    """Normalized readable content produced from a fetched document."""

    url: str
    title: str
    normalized_text: str
    domain: str | None = None
    author: str | None = None
    published_at: datetime | None = None
    source_kind: SourceKind = SourceKind.OTHER
    word_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RankedExtract:
    """Scored extract — input to the evidence packager."""

    content: ExtractedContent
    relevance_score: float
    quality_score: float
    novelty_score: float
    combined_score: float
    rationale: str | None = None
