"""Deterministic in-process retrieval stage implementations.

These let the orchestrator, persistence, API layer, and tests depend on the
retrieval protocols today, before any real search/fetch backend is wired in.
Behavior is intentionally simple and predictable so unit tests can assert on
its outputs without flakiness or network access.

Replace each stage independently as real backends arrive (TASK-013+).
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Sequence
from urllib.parse import quote, urlparse

from skillradar_api.agents.types import LessonBrief, RankedSource
from skillradar_api.retrieval.types import (
    ExtractedContent,
    FetchStatus,
    FetchedDocument,
    RankedExtract,
    SearchHit,
    SearchQuery,
    SourceKind,
)

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokens(value: str) -> list[str]:
    return _TOKEN_RE.findall(value.lower())


def _domain_for_query(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "topic"
    return f"{slug[:48]}.example.com"


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "result"


class MockSearchProvider:
    """Returns a small deterministic set of hits per query.

    Two hits are produced per query so the ranker and dedup logic have
    something realistic to operate on. URLs are deterministic functions of
    the query so the rest of the pipeline is reproducible.
    """

    async def search(self, query: SearchQuery) -> Sequence[SearchHit]:
        text = query.text.strip()
        if not text:
            return ()

        domain = _domain_for_query(text)
        slug = _slug(text)
        kinds = (SourceKind.BLOG, SourceKind.DOCS)
        hits: list[SearchHit] = []
        for index in range(min(2, max(1, query.max_results))):
            kind = kinds[index % len(kinds)]
            url = f"https://{domain}/{slug}-{index + 1}"
            hits.append(
                SearchHit(
                    url=url,
                    title=f"{text} — reference {index + 1}",
                    snippet=(
                        f"A grounded reference for '{text}' covering core "
                        "concepts and tradeoffs."
                    ),
                    domain=domain,
                    source_kind=kind,
                    discovery_score=1.0 - (index * 0.1),
                    query_text=text,
                    metadata={"mock": True, "rank": index + 1},
                )
            )
        return tuple(hits)


class MockContentFetcher:
    """Returns synthetic raw text for any non-blocklisted URL.

    URLs that contain `blocked.example.com` simulate a fetch failure so the
    pipeline's failure-tolerance can be exercised by tests.
    """

    async def fetch(self, hit: SearchHit) -> FetchedDocument:
        if "blocked.example.com" in hit.url:
            return FetchedDocument(
                hit=hit,
                status=FetchStatus.BLOCKED,
                error="mock blocklist",
            )

        retrieved_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
        raw_text = (
            f"<html><head><title>{hit.title}</title></head><body>"
            f"<article><h1>{hit.title}</h1>"
            f"<p>{hit.snippet or ''}</p>"
            f"<p>Tradeoffs and failure modes for {hit.query_text}.</p>"
            f"<p>Applied walkthrough for {hit.query_text}.</p>"
            "</article></body></html>"
        )
        return FetchedDocument(
            hit=hit,
            status=FetchStatus.OK,
            raw_text=raw_text,
            content_type="text/html",
            retrieved_at=retrieved_at,
        )


class MockContentExtractor:
    """Strips HTML tags and produces a normalized text block.

    Returns `None` for fetched documents that did not succeed so the
    orchestrator can surface those failures cleanly without polluting the
    extracted-content list.
    """

    _TAG_RE = re.compile(r"<[^>]+>")

    async def extract(self, document: FetchedDocument) -> ExtractedContent | None:
        if document.status != FetchStatus.OK or not document.raw_text:
            return None

        text = self._TAG_RE.sub(" ", document.raw_text)
        normalized = re.sub(r"\s+", " ", text).strip()
        word_count = len(normalized.split())
        domain = document.hit.domain or urlparse(document.hit.url).hostname
        return ExtractedContent(
            url=document.hit.url,
            title=document.hit.title,
            normalized_text=normalized,
            domain=domain,
            source_kind=document.hit.source_kind,
            word_count=word_count,
            metadata={
                "fetched_at": document.retrieved_at.isoformat()
                if document.retrieved_at
                else None,
                "query_text": document.hit.query_text,
            },
        )


class MockSourceRanker:
    """Scores extracts via simple lexical overlap with the brief.

    Real rankers will combine credibility, recency, and novelty; this mock
    keeps the contract honest while remaining deterministic.
    """

    async def rank(
        self,
        extracts: Sequence[ExtractedContent],
        brief: LessonBrief,
    ) -> Sequence[RankedExtract]:
        brief_tokens = set(
            _tokens(brief.target_topic)
            + _tokens(brief.intent)
            + [token for query in brief.search_queries for token in _tokens(query)]
        )

        ranked: list[RankedExtract] = []
        for extract in extracts:
            extract_tokens = set(
                _tokens(extract.title) + _tokens(extract.normalized_text)
            )
            if brief_tokens:
                overlap = len(brief_tokens & extract_tokens)
                relevance = min(1.0, overlap / max(1, len(brief_tokens)))
            else:
                relevance = 0.0

            quality = min(1.0, extract.word_count / 200.0)
            novelty = 1.0 if "case" in extract.title.lower() else 0.6
            combined = (relevance * 0.6) + (quality * 0.25) + (novelty * 0.15)

            ranked.append(
                RankedExtract(
                    content=extract,
                    relevance_score=relevance,
                    quality_score=quality,
                    novelty_score=novelty,
                    combined_score=combined,
                    rationale=f"overlap={relevance:.2f} quality={quality:.2f}",
                )
            )

        ranked.sort(key=lambda item: item.combined_score, reverse=True)
        return tuple(ranked)


class MockEvidencePackager:
    """Dedupes by URL, caps at `max_sources`, and emits `RankedSource`."""

    async def package(
        self,
        ranked: Sequence[RankedExtract],
        brief: LessonBrief,
        *,
        max_sources: int,
    ) -> tuple[RankedSource, ...]:
        seen_urls: set[str] = set()
        sources: list[RankedSource] = []

        for item in ranked:
            if len(sources) >= max_sources:
                break
            url = item.content.url
            if url in seen_urls:
                continue
            seen_urls.add(url)

            source_id = f"mock-{quote(_slug(item.content.title), safe='-')}"
            snippet = item.content.normalized_text[:240]
            sources.append(
                RankedSource(
                    source_id=source_id,
                    url=url,
                    title=item.content.title,
                    domain=item.content.domain,
                    author=item.content.author,
                    published_at=item.content.published_at,
                    snippet=snippet,
                    relevance_score=item.relevance_score,
                    quality_score=item.quality_score,
                    novelty_score=item.novelty_score,
                    metadata={
                        "combined_score": item.combined_score,
                        "rationale": item.rationale,
                        "source_kind": item.content.source_kind.value,
                        "brief_target_topic": brief.target_topic,
                    },
                )
            )

        return tuple(sources)
