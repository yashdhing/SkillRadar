"""Default retrieval stage selection.

Pipeline code should resolve stages through this factory so a swap from
the deterministic mocks to real search/fetch/rank backends is one place.
"""

from __future__ import annotations

from skillradar_api.retrieval.mock import (
    MockContentExtractor,
    MockContentFetcher,
    MockEvidencePackager,
    MockSearchProvider,
    MockSourceRanker,
)
from skillradar_api.retrieval.pipeline import RetrievalPipeline
from skillradar_api.retrieval.protocols import (
    ContentExtractor,
    ContentFetcher,
    EvidencePackager,
    SearchProvider,
    SourceRanker,
)


def get_default_search_provider() -> SearchProvider:
    return MockSearchProvider()


def get_default_content_fetcher() -> ContentFetcher:
    return MockContentFetcher()


def get_default_content_extractor() -> ContentExtractor:
    return MockContentExtractor()


def get_default_source_ranker() -> SourceRanker:
    return MockSourceRanker()


def get_default_evidence_packager() -> EvidencePackager:
    return MockEvidencePackager()


def build_default_retrieval_pipeline(
    *,
    max_sources: int = 5,
    per_query_results: int = 3,
) -> RetrievalPipeline:
    """Return a `RetrievalPipeline` wired to the default mock stages."""
    return RetrievalPipeline(
        search=get_default_search_provider(),
        fetcher=get_default_content_fetcher(),
        extractor=get_default_content_extractor(),
        ranker=get_default_source_ranker(),
        packager=get_default_evidence_packager(),
        max_sources=max_sources,
        per_query_results=per_query_results,
    )
