"""Unit tests for EntityResolver.

Edge cases (Addendum A2 #2 + phase-02-edge-cases-success.md):
  - exact match → resolves
  - typo / phonetic ("mirae larg cap") → resolves
  - shorthand alias ("ELSS Mirae") → resolves to ELSS fund
  - empty / stopword-only query → returns None
  - unknown fund → returns None below threshold
  - mixed Hindi-English → resolves on the English part
"""

from __future__ import annotations

from backend.services.entity_resolver import EntityResolver, FundEntity


def _build_resolver(fuzz_threshold: int = 70) -> EntityResolver:
    funds = [
        FundEntity(
            fund_slug="mirae-asset-large-cap-fund-direct-growth",
            fund_name="Mirae Asset Large Cap Fund Direct Growth",
        ),
        FundEntity(
            fund_slug="mirae-asset-elss-tax-saver-fund-direct-growth",
            fund_name="Mirae Asset ELSS Tax Saver Fund Direct Growth",
        ),
        FundEntity(
            fund_slug="parag-parikh-flexi-cap-fund-direct-growth",
            fund_name="Parag Parikh Flexi Cap Fund Direct Growth",
        ),
    ]
    return EntityResolver(funds, fuzz_threshold=fuzz_threshold)


def test_exact_match_resolves():
    r = _build_resolver()
    match = r.resolve("Mirae Asset Large Cap Fund")
    assert match is not None
    entity, score = match
    assert entity.fund_slug == "mirae-asset-large-cap-fund-direct-growth"
    assert score >= 80


def test_typo_query_resolves():
    r = _build_resolver()
    match = r.resolve("tell query about mirae larg cap")
    assert match is not None
    entity, _ = match
    assert "large-cap" in entity.fund_slug


def test_shorthand_resolves_to_elss():
    r = _build_resolver()
    match = r.resolve("ELSS Mirae")
    assert match is not None
    entity, _ = match
    assert entity.fund_slug == "mirae-asset-elss-tax-saver-fund-direct-growth"


def test_empty_query_returns_none():
    r = _build_resolver()
    assert r.resolve("") is None
    assert r.resolve("   ") is None


def test_stopwords_only_returns_none_or_low_score():
    r = _build_resolver(fuzz_threshold=80)
    assert r.resolve("what is the of fund") is None


def test_completely_unknown_fund_returns_none():
    r = _build_resolver(fuzz_threshold=85)
    assert r.resolve("Tesla Stock Performance") is None


def test_mixed_language_query_still_resolves():
    r = _build_resolver()
    match = r.resolve("kya hai mirae large cap ka exit load?")
    assert match is not None
    entity, _ = match
    assert "large-cap" in entity.fund_slug
