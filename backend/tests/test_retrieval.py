from __future__ import annotations

import asyncio

from skillradar_api.agents.types import LessonBrief, LessonShape, NoveltyTarget
from skillradar_api.retrieval import (
    ContentExtractor,
    ContentFetcher,
    EvidencePackager,
    RetrievalPipeline,
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
from skillradar_api.retrieval.types import (
    FetchStatus,
    FetchedDocument,
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

    sources = asyncio.run(packager.package(ranked, _brief(), max_sources=5))
    assert len(sources) == 1

    sources_capped = asyncio.run(packager.package(ranked, _brief(), max_sources=0))
    assert sources_capped == ()


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
