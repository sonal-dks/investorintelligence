"""Unit tests for ChunkingService.

Edge cases covered (per phase-02-edge-cases-success.md and LLD §Edge-Case Validation):
  - missing required fields → fund skipped, slug recorded
  - sparse data → only fact chunks for present fields
  - very long exit_load_text → truncated to <=1500 chars
  - exit_load extraction picks the active rule line out of glossary copy
  - chunk min length enforced (no chunks <10 chars)
  - special-character fund names preserved
"""

from __future__ import annotations

from backend.services.chunking_service import (
    MAX_CHUNK_LEN,
    chunk_fee_explainer_rows,
    chunk_fund,
    chunk_funds,
)


def test_mutual_fund_chunks_have_corpus_metadata(sample_fund):
    chunks = chunk_fund(sample_fund)
    assert all(c.metadata.corpus == "mutual_fund" for c in chunks)
    nav_chunk = next(c for c in chunks if c.metadata.source_field == "nav")
    assert nav_chunk.metadata.source_url and "groww.in" in nav_chunk.metadata.source_url


def test_full_fund_produces_expected_chunk_set(sample_fund):
    chunks = chunk_fund(sample_fund)

    fields = {c.metadata.source_field for c in chunks}
    expected_fields = {
        "category",
        "nav",
        "aum_cr",
        "expense_ratio",
        "min_sip",
        "risk_level",
        "returns",
        "exit_load",
        "tax",
        "combined",
    }
    assert expected_fields.issubset(fields), f"missing: {expected_fields - fields}"

    types = {c.metadata.chunk_type for c in chunks}
    assert "fact" in types and "description" in types


def test_chunks_satisfy_min_length(sample_fund):
    chunks = chunk_fund(sample_fund)
    assert all(len(c.text) >= 10 for c in chunks)


def test_chunks_are_unique_by_id(sample_fund):
    chunks = chunk_fund(sample_fund)
    ids = [c.id for c in chunks]
    assert len(ids) == len(set(ids))


def test_exit_load_extracts_active_rule(sample_fund):
    chunks = chunk_fund(sample_fund)
    exit_chunks = [c for c in chunks if c.metadata.source_field == "exit_load"]
    assert exit_chunks, "exit_load chunk missing"
    assert "1%" in exit_chunks[0].text
    assert "1 year" in exit_chunks[0].text


def test_chunk_text_max_length():
    fund = {
        "fund_slug": "huge-text-fund-direct-growth",
        "fund_name": "Huge Text Fund",
        "category": "ELSS",
        "nav": 12.0,
        "exit_load_text": "Exit load of 1% if redeemed within 1 year. " + ("padding " * 1000),
        "source_url": "https://example",
        "scraped_at": "2026-05-07T00:00:00Z",
    }
    chunks = chunk_fund(fund)
    for c in chunks:
        assert len(c.text) <= MAX_CHUNK_LEN + 3  # +3 for the "..." suffix


def test_sparse_fund_only_emits_chunks_for_present_fields(sparse_fund):
    chunks = chunk_fund(sparse_fund)
    fields = {c.metadata.source_field for c in chunks}
    assert "nav" in fields
    assert "category" in fields
    assert "exit_load" not in fields  # no exit_load_text in sparse fund
    assert "returns" not in fields


def test_malformed_fund_is_skipped(malformed_fund):
    assert chunk_fund(malformed_fund) == []


def test_chunk_funds_aggregates_and_records_skipped(sample_fund, malformed_fund):
    chunks, skipped = chunk_funds([sample_fund, malformed_fund])
    assert len(chunks) > 5
    assert skipped == ["<unknown>"]


def test_fee_explainer_narrative_chunks():
    rows = [
        {
            "fee_type": "exit_load",
            "category": "What it means",
            "description": "Exit load is charged on early redemption.",
            "typical_range": "0-1%",
            "source_url": "https://groww.in",
            "last_updated": "2026-05-07T00:00:00Z",
        },
        {
            "fee_type": "stt",
            "category": "What it means",
            "description": "STT applies to certain equity-oriented fund transactions.",
            "source_url": "https://groww.in",
            "last_updated": "2026-05-07T00:00:00Z",
        },
    ]
    chunks, skipped = chunk_fee_explainer_rows(rows)
    assert not skipped
    assert len(chunks) == 2
    assert {c.metadata.fee_type for c in chunks} == {"exit_load", "stt"}
    assert all(c.metadata.corpus == "fee_explainer" for c in chunks)


def test_special_character_fund_name_preserved():
    fund = {
        "fund_slug": "fund-with-amp",
        "fund_name": "Mirae Asset Large & Midcap Fund (Direct)",
        "category": "Large & MidCap",
        "nav": 100.0,
        "source_url": "https://example",
        "scraped_at": "2026-05-07T00:00:00Z",
    }
    chunks = chunk_fund(fund)
    assert any("Large & Midcap" in c.text for c in chunks)
