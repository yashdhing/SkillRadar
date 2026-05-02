"""Modular retrieval pipeline for SkillRadar lesson grounding.

The pipeline is intentionally split into independently replaceable stages:

1. `SearchProvider` discovers candidate URLs for a `LessonBrief`'s queries.
2. `ContentFetcher` retrieves raw page content for each `SearchHit`.
3. `ContentExtractor` converts raw content into normalized `ExtractedContent`.
4. `SourceRanker` scores extracts for relevance, quality, and novelty.
5. `EvidencePackager` selects, dedupes, and converts the top results into the
   `RankedSource` tuple consumed by `LessonComposerAgent`.

Each stage has a typed input, typed output, and `Protocol` so providers can be
swapped without touching adjacent stages or the orchestrator. The `pipeline`
module wires them together and preserves intermediate outputs for debugging.
"""

from skillradar_api.retrieval.factory import (
    build_default_retrieval_pipeline,
    get_default_content_extractor,
    get_default_content_fetcher,
    get_default_evidence_packager,
    get_default_search_provider,
    get_default_source_ranker,
)
from skillradar_api.retrieval.pipeline import RetrievalPipeline, RetrievalResult
from skillradar_api.retrieval.protocols import (
    ContentExtractor,
    ContentFetcher,
    EvidencePackager,
    PackagedEvidence,
    SearchProvider,
    SourceRanker,
)
from skillradar_api.retrieval.quality import (
    STANDARD_QUALITY_POLICY,
    RetrievalQualityPolicy,
)
from skillradar_api.retrieval.types import (
    DroppedExtract,
    ExtractedContent,
    FetchedDocument,
    RankedExtract,
    SearchHit,
    SearchQuery,
)

__all__ = [
    "STANDARD_QUALITY_POLICY",
    "ContentExtractor",
    "ContentFetcher",
    "DroppedExtract",
    "EvidencePackager",
    "ExtractedContent",
    "FetchedDocument",
    "PackagedEvidence",
    "RankedExtract",
    "RetrievalPipeline",
    "RetrievalQualityPolicy",
    "RetrievalResult",
    "SearchHit",
    "SearchProvider",
    "SearchQuery",
    "SourceRanker",
    "build_default_retrieval_pipeline",
    "get_default_content_extractor",
    "get_default_content_fetcher",
    "get_default_evidence_packager",
    "get_default_search_provider",
    "get_default_source_ranker",
]
