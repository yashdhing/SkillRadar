from __future__ import annotations

import asyncio

from skillradar_api.agents.types import LessonBrief, LessonShape, NoveltyTarget
from skillradar_api.retrieval import (
    STANDARD_QUALITY_POLICY,
    ContentExtractor,
    ContentFetcher,
    EvidencePackager,
    RetrievalPipeline,
    RetrievalQualityPolicy,
    RetrievalResult,
    SearchProvider,
    SourceRanker,
    build_default_retrieval_pipeline,
    get_default_content_extractor,
    get_default_content_fetcher,
    get_default_evidence_packager,
    get_default_search_provider,
    get_default_source_ranker,
)
from skillradar_api.retrieval.mock import (
    MockEvidencePackager,
    MockSourceRanker,
)
from skillradar_api.retrieval.types import (
    ExtractedContent,
    FetchStatus,
    FetchedDocument,
    RankedExtract,
    SearchHit,
    SearchQuery,
    SourceKind,
)


def _brief(
    *,
    queries: tuple[str, ...] = ("kafka exactly once",),
    target: str = "Kafka exactly-once",
) -> LessonBrief:
    return LessonBrief(
        intent=f"Lesson on {target}.",
        target_topic=target,
        search_queries=queries,
        shape=LessonShape.PRACTICAL_WALKTHROUGH,
        novelty=NoveltyTarget.DEEP_DIVE,
        desired_section_titles=("Why this topic", "Core concepts"),
    )


def test_factory_returns_protocol_compatible_stages() -> None:
    assert isinstance(get_default_search_provider(), SearchProvider)
    assert isinstance(get_default_content_fetcher(), ContentFetcher)
    assert isinstance(get_default_content_extractor(), ContentExtractor)
    assert isinstance(get_default_source_ranker(), SourceRanker)
    assert isinstance(get_default_evidence_packager(), EvidencePackager)


def test_search_provider_emits_deterministic_hits() -> None:
    provider = get_default_search_provider()
    query = SearchQuery(text="kafka exactly once", max_results=2)

    first = asyncio.run(provider.search(query))
    second = asyncio.run(provider.search(query))

    assert first == second
    assert len(first) >= 1
    assert all(hit.url.startswith("https://") for hit in first)
    assert all(hit.query_text == "kafka exactly once" for hit in first)


def test_search_provider_returns_empty_on_blank_query() -> None:
    provider = get_default_search_provider()
    assert asyncio.run(provider.search(SearchQuery(text="   "))) == ()


def test_content_fetcher_handles_blocklisted_urls_without_raising() -> None:
    fetcher = get_default_content_fetcher()
    blocked_hit = SearchHit(
        url="https://blocked.example.com/article",
        title="Blocked",
        domain="blocked.example.com",
    )

    document = asyncio.run(fetcher.fetch(blocked_hit))
    assert document.status == FetchStatus.BLOCKED
    assert document.raw_text is None
    assert document.error is not None


def test_content_extractor_skips_failed_fetches() -> None:
    extractor = get_default_content_extractor()
    failed = FetchedDocument(
        hit=SearchHit(url="https://x", title="x"),
        status=FetchStatus.ERROR,
    )

    assert asyncio.run(extractor.extract(failed)) is None


def test_content_extractor_strips_html_and_counts_words() -> None:
    extractor = get_default_content_extractor()
    hit = SearchHit(
        url="https://example.com/a",
        title="Sample Doc",
        domain="example.com",
        source_kind=SourceKind.DOCS,
        query_text="kafka",
    )
    document = FetchedDocument(
        hit=hit,
        status=FetchStatus.OK,
        raw_text="<html><body><h1>Title</h1><p>Hello world this is a test.</p></body></html>",
        content_type="text/html",
    )

    extracted = asyncio.run(extractor.extract(document))
    assert extracted is not None
    assert "<" not in extracted.normalized_text
    assert extracted.word_count > 0
    assert extracted.domain == "example.com"


def test_source_ranker_orders_extracts_by_overlap() -> None:
    ranker = get_default_source_ranker()
    relevant = SearchHit(
        url="https://example.com/a", title="kafka exactly once guide"
    )
    unrelated = SearchHit(
        url="https://example.com/b", title="ocean cycling routes"
    )

    fetcher = get_default_content_fetcher()
    extractor = get_default_content_extractor()

    relevant_doc = asyncio.run(fetcher.fetch(relevant))
    unrelated_doc = asyncio.run(fetcher.fetch(unrelated))
    extracts = [
        asyncio.run(extractor.extract(unrelated_doc)),
        asyncio.run(extractor.extract(relevant_doc)),
    ]
    extracts = [extract for extract in extracts if extract is not None]

    ranked = asyncio.run(ranker.rank(extracts, _brief()))

    assert ranked[0].content.title == "kafka exactly once guide"
    assert ranked[0].combined_score >= ranked[-1].combined_score


def test_evidence_packager_dedupes_and_caps() -> None:
    packager = get_default_evidence_packager()
    ranker = get_default_source_ranker()
    fetcher = get_default_content_fetcher()
    extractor = get_default_content_extractor()

    hit = SearchHit(url="https://example.com/dup", title="kafka exactly once")
    document = asyncio.run(fetcher.fetch(hit))
    extract = asyncio.run(extractor.extract(document))
    assert extract is not None
    ranked = asyncio.run(ranker.rank([extract, extract, extract], _brief()))

    result = asyncio.run(packager.package(ranked, _brief(), max_sources=5))
    assert len(result.accepted) == 1
    assert len(result.dropped) == 2
    assert all(item.reason == "duplicate_url" for item in result.dropped)

    capped = asyncio.run(packager.package(ranked, _brief(), max_sources=0))
    assert capped.accepted == ()
    # max_sources=0 still triggers dedup before the max-sources check, so the
    # first item is dropped as max_sources_reached and the rest as duplicates.
    drop_reasons = {item.reason for item in capped.dropped}
    assert "max_sources_reached" in drop_reasons


def test_pipeline_runs_end_to_end_and_preserves_intermediate_trace() -> None:
    pipeline = build_default_retrieval_pipeline(
        max_sources=3, per_query_results=2
    )
    brief = _brief(queries=("kafka exactly once", "kafka exactly once case"))

    result = asyncio.run(pipeline.run(brief))

    assert isinstance(result, RetrievalResult)
    assert len(result.hits) >= 1
    assert len(result.fetches) == len(result.hits)
    assert len(result.extracts) <= len(result.fetches)
    assert len(result.ranked) == len(result.extracts)
    assert len(result.sources) <= 3
    assert all(source.url.startswith("https://") for source in result.sources)
    assert all(source.metadata["brief_target_topic"] for source in result.sources)


def test_pipeline_returns_empty_result_when_brief_has_no_queries() -> None:
    pipeline = build_default_retrieval_pipeline()
    brief = _brief(queries=())

    result = asyncio.run(pipeline.run(brief))
    assert result.sources == ()
    assert result.hits == ()
    assert result.fetches == ()
    assert result.extracts == ()
    assert result.ranked == ()


def test_pipeline_records_fetch_failures_without_aborting() -> None:
    """A blocked hit should appear in `fetch_failures` and not poison extracts."""

    class _BlockingSearch:
        async def search(self, query: SearchQuery):  # type: ignore[no-untyped-def]
            return (
                SearchHit(
                    url="https://blocked.example.com/x",
                    title="blocked",
                    domain="blocked.example.com",
                    query_text=query.text,
                ),
                SearchHit(
                    url="https://example.com/ok",
                    title=f"{query.text} reference",
                    domain="example.com",
                    query_text=query.text,
                ),
            )

    pipeline = RetrievalPipeline(
        search=_BlockingSearch(),
        fetcher=get_default_content_fetcher(),
        extractor=get_default_content_extractor(),
        ranker=get_default_source_ranker(),
        packager=get_default_evidence_packager(),
        max_sources=5,
    )

    result = asyncio.run(pipeline.run(_brief(queries=("kafka exactly once",))))

    assert len(result.fetch_failures) == 1
    assert result.fetch_failures[0].hit.url.startswith(
        "https://blocked.example.com"
    )
    assert all(source.url != result.fetch_failures[0].hit.url for source in result.sources)
    assert len(result.sources) >= 1


# --- TASK-013: source quality controls -----------------------------------


def _make_extract(
    *,
    url: str = "https://example.com/x",
    title: str = "kafka exactly once primer",
    domain: str | None = "example.com",
    word_count: int = 200,
    text: str | None = None,
) -> ExtractedContent:
    return ExtractedContent(
        url=url,
        title=title,
        normalized_text=text or " ".join(["word"] * word_count),
        domain=domain,
        source_kind=SourceKind.BLOG,
        word_count=word_count,
        metadata={},
    )


def test_ranker_applies_credibility_boost_for_preferred_domains() -> None:
    policy = RetrievalQualityPolicy(
        preferred_domains=frozenset({"trusted.example.com"}),
        domain_credibility_boost=0.3,
    )
    ranker = MockSourceRanker(policy=policy)
    trusted = _make_extract(
        url="https://trusted.example.com/a",
        domain="trusted.example.com",
        word_count=20,
    )
    untrusted = _make_extract(
        url="https://other.example.com/b",
        domain="other.example.com",
        word_count=20,
    )

    ranked = asyncio.run(ranker.rank([untrusted, trusted], _brief()))

    by_domain = {item.content.domain: item for item in ranked}
    assert (
        by_domain["trusted.example.com"].quality_score
        > by_domain["other.example.com"].quality_score
    )


def test_packager_drops_thin_content_below_min_word_count() -> None:
    policy = RetrievalQualityPolicy(min_word_count=50)
    packager = MockEvidencePackager(policy=policy)

    thin = RankedExtract(
        content=_make_extract(url="https://example.com/thin", word_count=10),
        relevance_score=0.9,
        quality_score=0.9,
        novelty_score=0.6,
        combined_score=0.85,
    )
    rich = RankedExtract(
        content=_make_extract(url="https://example.com/rich", word_count=120),
        relevance_score=0.9,
        quality_score=0.9,
        novelty_score=0.6,
        combined_score=0.85,
    )

    result = asyncio.run(packager.package([thin, rich], _brief(), max_sources=5))
    assert [source.url for source in result.accepted] == ["https://example.com/rich"]
    thin_drops = [item for item in result.dropped if item.reason == "thin_content"]
    assert len(thin_drops) == 1


def test_packager_enforces_per_domain_cap() -> None:
    policy = RetrievalQualityPolicy(max_per_domain=1)
    packager = MockEvidencePackager(policy=policy)

    a = RankedExtract(
        content=_make_extract(url="https://example.com/a", domain="dup.example.com"),
        relevance_score=0.9, quality_score=0.9, novelty_score=0.6, combined_score=0.85,
    )
    b = RankedExtract(
        content=_make_extract(url="https://example.com/b", domain="dup.example.com"),
        relevance_score=0.85, quality_score=0.85, novelty_score=0.6, combined_score=0.8,
    )

    result = asyncio.run(packager.package([a, b], _brief(), max_sources=5))
    assert len(result.accepted) == 1
    assert any(item.reason == "per_domain_cap" for item in result.dropped)


def test_packager_respects_denylist_and_allowlist() -> None:
    deny_policy = RetrievalQualityPolicy(
        denied_domains=frozenset({"bad.example.com"})
    )
    bad = RankedExtract(
        content=_make_extract(url="https://bad.example.com/x", domain="bad.example.com"),
        relevance_score=0.9, quality_score=0.9, novelty_score=0.6, combined_score=0.85,
    )
    good = RankedExtract(
        content=_make_extract(url="https://good.example.com/y", domain="good.example.com"),
        relevance_score=0.8, quality_score=0.8, novelty_score=0.6, combined_score=0.75,
    )

    deny_result = asyncio.run(
        MockEvidencePackager(policy=deny_policy).package(
            [bad, good], _brief(), max_sources=5
        )
    )
    assert [source.domain for source in deny_result.accepted] == ["good.example.com"]
    assert any(item.reason == "denied_domain" for item in deny_result.dropped)

    allow_policy = RetrievalQualityPolicy(
        allowed_domains=frozenset({"good.example.com"})
    )
    allow_result = asyncio.run(
        MockEvidencePackager(policy=allow_policy).package(
            [bad, good], _brief(), max_sources=5
        )
    )
    assert [source.domain for source in allow_result.accepted] == ["good.example.com"]
    assert any(
        item.reason == "not_in_allowlist" for item in allow_result.dropped
    )


def test_packager_records_low_relevance_and_low_quality_drops() -> None:
    policy = RetrievalQualityPolicy(
        min_relevance_score=0.5, min_quality_score=0.5
    )
    packager = MockEvidencePackager(policy=policy)
    low_rel = RankedExtract(
        content=_make_extract(url="https://example.com/lr"),
        relevance_score=0.1, quality_score=0.9, novelty_score=0.6, combined_score=0.5,
    )
    low_qual = RankedExtract(
        content=_make_extract(url="https://example.com/lq"),
        relevance_score=0.9, quality_score=0.1, novelty_score=0.6, combined_score=0.5,
    )
    ok = RankedExtract(
        content=_make_extract(url="https://example.com/ok"),
        relevance_score=0.9, quality_score=0.9, novelty_score=0.6, combined_score=0.85,
    )

    result = asyncio.run(packager.package([low_rel, low_qual, ok], _brief(), max_sources=5))
    accepted_urls = {source.url for source in result.accepted}
    assert accepted_urls == {"https://example.com/ok"}
    reasons = {item.reason for item in result.dropped}
    assert reasons == {"low_relevance", "low_quality"}


def test_pipeline_default_uses_standard_quality_policy() -> None:
    pipeline = build_default_retrieval_pipeline()
    # Ranker and packager must share the same standard policy by default.
    assert pipeline.ranker.policy is STANDARD_QUALITY_POLICY  # type: ignore[attr-defined]
    assert pipeline.packager.policy is STANDARD_QUALITY_POLICY  # type: ignore[attr-defined]


def test_pipeline_surfaces_dropped_extracts_in_result_trace() -> None:
    """A run with a tight per-domain cap should expose drops in `result.dropped`."""
    policy = RetrievalQualityPolicy(max_per_domain=1)
    pipeline = build_default_retrieval_pipeline(
        max_sources=10, per_query_results=2, quality_policy=policy
    )
    # Single query yields 2 hits on the SAME synthetic domain, so the cap drops one.
    brief = _brief(queries=("kafka exactly once",))

    result = asyncio.run(pipeline.run(brief))
    assert len(result.sources) == 1
    assert len(result.dropped) >= 1
    assert any(item.reason == "per_domain_cap" for item in result.dropped)


def test_pipeline_with_explicit_zero_policy_disables_filters() -> None:
    """Passing a bare RetrievalQualityPolicy should restore unfiltered behavior."""
    pipeline = build_default_retrieval_pipeline(
        max_sources=10,
        per_query_results=2,
        quality_policy=RetrievalQualityPolicy(),
    )
    brief = _brief(queries=("kafka exactly once",))

    result = asyncio.run(pipeline.run(brief))
    # No per-domain cap, no thresholds: every healthy extract should survive.
    assert len(result.sources) == len(result.extracts)
    assert all(item.reason == "duplicate_url" for item in result.dropped)


def test_packager_records_preferred_domain_metadata_on_accepted_sources() -> None:
    policy = RetrievalQualityPolicy(
        preferred_domains=frozenset({"trusted.example.com"})
    )
    packager = MockEvidencePackager(policy=policy)
    trusted = RankedExtract(
        content=_make_extract(
            url="https://trusted.example.com/a",
            domain="trusted.example.com",
        ),
        relevance_score=0.9, quality_score=0.9, novelty_score=0.6, combined_score=0.85,
    )
    other = RankedExtract(
        content=_make_extract(url="https://other.example.com/b", domain="other.example.com"),
        relevance_score=0.85, quality_score=0.85, novelty_score=0.6, combined_score=0.8,
    )

    result = asyncio.run(packager.package([trusted, other], _brief(), max_sources=5))
    by_domain = {source.domain: source for source in result.accepted}
    assert by_domain["trusted.example.com"].metadata["preferred_domain"] is True
    assert by_domain["other.example.com"].metadata["preferred_domain"] is False
