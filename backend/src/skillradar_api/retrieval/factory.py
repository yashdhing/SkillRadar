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
from skillradar_api.retrieval.quality import (
    STANDARD_QUALITY_POLICY,
    RetrievalQualityPolicy,
)


def get_default_search_provider() -> SearchProvider:
    return MockSearchProvider()


def get_default_content_fetcher() -> ContentFetcher:
    return MockContentFetcher()


def get_default_content_extractor() -> ContentExtractor:
    return MockContentExtractor()


def get_default_source_ranker(
    policy: RetrievalQualityPolicy | None = None,
) -> SourceRanker:
    return MockSourceRanker(policy=policy)


def get_default_evidence_packager(
    policy: RetrievalQualityPolicy | None = None,
) -> EvidencePackager:
    return MockEvidencePackager(policy=policy)


def build_default_retrieval_pipeline(
    *,
    max_sources: int = 5,
    per_query_results: int = 3,
    quality_policy: RetrievalQualityPolicy | None = None,
) -> RetrievalPipeline:
    """Return a `RetrievalPipeline` wired to the default mock stages.

    Defaults to `STANDARD_QUALITY_POLICY` so the pipeline ships with the
    quality controls turned on. Pass an explicit policy (including a bare
    `RetrievalQualityPolicy()`) to opt into different behavior — useful for
    tests that need raw packager behavior or future per-request overrides.
    """
    policy = quality_policy if quality_policy is not None else STANDARD_QUALITY_POLICY
    return RetrievalPipeline(
        search=get_default_search_provider(),
        fetcher=get_default_content_fetcher(),
        extractor=get_default_content_extractor(),
        ranker=get_default_source_ranker(policy),
        packager=get_default_evidence_packager(policy),
        max_sources=max_sources,
        per_query_results=per_query_results,
    )
