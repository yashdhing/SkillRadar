"""Retrieval pipeline orchestrator.

Wires the five retrieval stages together while preserving stage boundaries:
each stage receives only its declared inputs and returns its declared
outputs. The orchestrator records intermediate outputs in `RetrievalResult`
so debugging, replay, and per-stage iteration stay possible without
collapsing the pipeline into one opaque step.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Sequence

from skillradar_api.agents.types import LessonBrief, RankedSource
from skillradar_api.retrieval.protocols import (
    ContentExtractor,
    ContentFetcher,
    EvidencePackager,
    SearchProvider,
    SourceRanker,
)
from skillradar_api.retrieval.types import (
    DroppedExtract,
    ExtractedContent,
    FetchStatus,
    FetchedDocument,
    RankedExtract,
    SearchHit,
    SearchQuery,
)


@dataclass(frozen=True)
class RetrievalResult:
    """Final pipeline output plus per-stage trace.

    The trace lets later observability/debugging tasks inspect why the
    composer received a particular evidence bundle without re-running the
    pipeline.
    """

    sources: tuple[RankedSource, ...]
    hits: tuple[SearchHit, ...] = ()
    fetches: tuple[FetchedDocument, ...] = ()
    extracts: tuple[ExtractedContent, ...] = ()
    ranked: tuple[RankedExtract, ...] = ()
    fetch_failures: tuple[FetchedDocument, ...] = field(default_factory=tuple)
    dropped: tuple[DroppedExtract, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class RetrievalPipeline:
    """Composable retrieval pipeline driven by a `LessonBrief`."""

    search: SearchProvider
    fetcher: ContentFetcher
    extractor: ContentExtractor
    ranker: SourceRanker
    packager: EvidencePackager
    max_sources: int = 5
    per_query_results: int = 3

    async def run(self, brief: LessonBrief) -> RetrievalResult:
        hits = await self._discover(brief)
        fetches = await self._fetch_all(hits)
        extracts = await self._extract_all(fetches)
        ranked = await self.ranker.rank(extracts, brief)
        packaged = await self.packager.package(
            ranked, brief, max_sources=self.max_sources
        )
        fetch_failures = tuple(
            document for document in fetches if document.status != FetchStatus.OK
        )

        return RetrievalResult(
            sources=tuple(packaged.accepted),
            hits=tuple(hits),
            fetches=tuple(fetches),
            extracts=tuple(extracts),
            ranked=tuple(ranked),
            fetch_failures=fetch_failures,
            dropped=tuple(packaged.dropped),
        )

    async def _discover(self, brief: LessonBrief) -> Sequence[SearchHit]:
        queries = [
            SearchQuery(
                text=query,
                intent=brief.intent,
                max_results=self.per_query_results,
            )
            for query in brief.search_queries
            if query and query.strip()
        ]
        if not queries:
            return ()

        per_query_hits = await asyncio.gather(
            *(self.search.search(query) for query in queries)
        )

        seen_urls: set[str] = set()
        deduped: list[SearchHit] = []
        for hits in per_query_hits:
            for hit in hits:
                if hit.url in seen_urls:
                    continue
                seen_urls.add(hit.url)
                deduped.append(hit)
        return tuple(deduped)

    async def _fetch_all(
        self, hits: Sequence[SearchHit]
    ) -> Sequence[FetchedDocument]:
        if not hits:
            return ()
        return await asyncio.gather(*(self.fetcher.fetch(hit) for hit in hits))

    async def _extract_all(
        self, fetches: Sequence[FetchedDocument]
    ) -> Sequence[ExtractedContent]:
        if not fetches:
            return ()
        results = await asyncio.gather(
            *(self.extractor.extract(document) for document in fetches)
        )
        return tuple(extract for extract in results if extract is not None)
