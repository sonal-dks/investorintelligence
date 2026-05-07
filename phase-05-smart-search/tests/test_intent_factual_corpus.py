"""Tests for factual corpus routing (mutual fund vs fee explainer)."""

from __future__ import annotations

from backend.services.intent_router import IntentRouter


def test_fee_explainer_strong_query():
    r = IntentRouter().classify_factual_corpus("What is STT and how does stamp duty work for mutual funds?")
    assert r.retrieval_corpus == "fee_explainer"
    assert r.confidence >= 0.7


def test_mutual_fund_strong_query():
    r = IntentRouter().classify_factual_corpus("What is the NAV and AUM of Mirae Asset Large Cap?")
    assert r.retrieval_corpus == "mutual_fund"
    assert r.confidence >= 0.7


def test_ambiguous_falls_back_to_unified():
    r = IntentRouter().classify_factual_corpus("Tell me about mutual funds")
    assert r.retrieval_corpus is None
    assert r.confidence < 0.7
