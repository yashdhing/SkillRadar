"""Retrieval quality policy.

Centralizes the knobs that govern how sources are filtered, scored, and
deduplicated as they pass through the ranking and evidence-packaging stages.
Both stages accept a `RetrievalQualityPolicy` so the same configuration
drives credibility boosts in the ranker and threshold/cap enforcement in
the packager — no copy-pasted filters between stages.

The protocol seam in `retrieval/protocols.py` is unchanged; only the mock
implementations consult this policy. Real ranker / packager backends should
do the same.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RetrievalQualityPolicy:
    """Quality controls for the retrieval pipeline.

    All thresholds default to no-op so a default policy preserves the
    original "let everything through" behavior. Use `STANDARD_QUALITY_POLICY`
    for the production-leaning defaults the generation service ships with.

    Attributes:
        min_relevance_score: Drop ranked extracts whose relevance is below
            this floor. Use sparingly — too high a floor will starve the
            composer.
        min_quality_score: Drop ranked extracts whose quality (richness +
            credibility) is below this floor.
        min_word_count: Drop ranked extracts whose normalized text falls
            below this length. Catches thin content-farm pages that pass
            relevance but have no actual depth.
        max_per_domain: After dedup-by-URL, also enforce a per-domain cap so
            one domain cannot dominate the evidence bundle. `None` disables.
        allowed_domains: When set, ONLY domains in this set may pass. Useful
            for source-allowlist mode.
        denied_domains: Domains in this set are dropped regardless of score.
        preferred_domains: Domains that get a `domain_credibility_boost`
            applied to their quality_score in the ranker.
        domain_credibility_boost: Additive boost applied to quality_score
            when the extract's domain is in `preferred_domains`. Clamped to
            keep quality in [0, 1].
    """

    min_relevance_score: float = 0.0
    min_quality_score: float = 0.0
    min_word_count: int = 0
    max_per_domain: int | None = None
    allowed_domains: frozenset[str] | None = None
    denied_domains: frozenset[str] = frozenset()
    preferred_domains: frozenset[str] = frozenset()
    domain_credibility_boost: float = 0.2
    extra_metadata: dict[str, str] = field(default_factory=dict)


# Production-leaning defaults — applied automatically by the generation
# service via `build_default_retrieval_pipeline`. Tests that need raw
# packager behavior pass `RetrievalQualityPolicy()` explicitly.
STANDARD_QUALITY_POLICY = RetrievalQualityPolicy(
    min_word_count=20,
    max_per_domain=2,
    domain_credibility_boost=0.2,
)
