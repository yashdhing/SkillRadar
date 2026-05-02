"""Structural interfaces for each retrieval pipeline stage.

Pipeline code, orchestrators, and tests should depend on these protocols
only; concrete providers (mock today, real search/fetch backends later)
plug in through the factory.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence, runtime_checkable

from skillradar_api.agents.types import LessonBrief, RankedSource
from skillradar_api.retrieval.types import (
    DroppedExtract,
    ExtractedContent,
    FetchedDocument,
    RankedExtract,
    SearchHit,
    SearchQuery,
)


@dataclass(frozen=True)
class PackagedEvidence:
    """Packager output: accepted shortlist plus per-extract drop reasons.

    The split keeps stage boundaries explicit — the orchestrator can record
    drop reasons in `RetrievalResult` without re-deriving them, and downstream
    quality auditing has a single typed surface to read.
    """

    accepted: tuple[RankedSource, ...]
    dropped: tuple[DroppedExtract, ...] = ()


@runtime_checkable
class SearchProvider(Protocol):
    """Discovers candidate URLs for a query."""

    async def search(self, query: SearchQuery) -> Sequence[SearchHit]:
        ...


@runtime_checkable
class ContentFetcher(Protocol):
    """Retrieves raw page content for a `SearchHit`.

    Implementations should NEVER raise on transport errors — they should
    return a `FetchedDocument` with an explicit `FetchStatus` so the rest of
    the pipeline can continue while the orchestrator records the failure.
    """

    async def fetch(self, hit: SearchHit) -> FetchedDocument:
        ...


@runtime_checkable
class ContentExtractor(Protocol):
    """Converts raw page content into normalized readable text."""

    async def extract(self, document: FetchedDocument) -> ExtractedContent | None:
        ...


@runtime_checkable
class SourceRanker(Protocol):
    """Scores extracts against the planner brief."""

    async def rank(
        self,
        extracts: Sequence[ExtractedContent],
        brief: LessonBrief,
    ) -> Sequence[RankedExtract]:
        ...


@runtime_checkable
class EvidencePackager(Protocol):
    """Picks the final shortlist and converts to the agent layer's `RankedSource`."""

    async def package(
        self,
        ranked: Sequence[RankedExtract],
        brief: LessonBrief,
        *,
        max_sources: int,
    ) -> PackagedEvidence:
        ...
