"""Unit tests for the BM25 LexicalIndex."""

from __future__ import annotations

from backend.services.lexical_index import LexicalIndex, tokenize


def _docs() -> list[dict]:
    return [
        {
            "id": "a::fact::exit_load",
            "text": "Exit load for Mirae Asset Large Cap: 1% if redeemed within 1 year",
            "metadata": {"fund_slug": "mirae", "chunk_type": "fact", "source_field": "exit_load"},
        },
        {
            "id": "a::fact::nav",
            "text": "NAV of Mirae Asset Large Cap: ₹105.43 as of 2026-05-06",
            "metadata": {"fund_slug": "mirae", "chunk_type": "fact", "source_field": "nav"},
        },
        {
            "id": "b::fact::expense",
            "text": "Expense ratio of Parag Parikh Flexi Cap: 0.65% Direct Plan",
            "metadata": {"fund_slug": "parag", "chunk_type": "fact", "source_field": "expense_ratio"},
        },
    ]


def test_tokenize_lowercases_and_strips_punctuation():
    assert tokenize("Hello, World! 123") == ["hello", "world", "123"]


def test_search_returns_empty_for_empty_index():
    idx = LexicalIndex([])
    assert idx.search("anything", top_k=5) == []


def test_search_returns_empty_for_zero_top_k():
    idx = LexicalIndex(_docs())
    assert idx.search("Mirae", top_k=0) == []


def test_search_finds_exact_phrase():
    idx = LexicalIndex(_docs())
    results = idx.search("exit load 1% if redeemed within 1 year", top_k=3)
    assert results
    assert results[0]["metadata"]["source_field"] == "exit_load"


def test_search_filters_zero_score_hits():
    idx = LexicalIndex(_docs())
    results = idx.search("Tesla Apple Microsoft", top_k=3)
    assert results == []
