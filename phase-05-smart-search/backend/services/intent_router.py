"""Intent router — classifies each user turn into intent type.

Mandatory from Phase 05 onward per PRD Addendum A2.
Routes: factual, action, safety, clarification.
"""

from __future__ import annotations

import re

from ..models.schemas import FactualCorpusClassification, IntentClassification

ACTION_PATTERNS = [
    re.compile(r"\b(?:book|schedule|set\s+up)\s+(?:a\s+)?(?:call|meeting|appointment)\b", re.IGNORECASE),
    re.compile(r"\bsend\s+(?:an?\s+)?email\b", re.IGNORECASE),
    re.compile(r"\bcreate\s+(?:a\s+)?(?:note|reminder)\b", re.IGNORECASE),
    re.compile(r"\bfollow\s*-?\s*up\b", re.IGNORECASE),
    re.compile(r"\bcancel\s+(?:my\s+)?(?:booking|appointment|call)\b", re.IGNORECASE),
    re.compile(r"\breschedule\b", re.IGNORECASE),
]

SAFETY_PATTERNS = [
    re.compile(r"\bignore\s+(?:all\s+)?(?:previous\s+)?instructions?\b", re.IGNORECASE),
    re.compile(r"\bsystem\s+prompt\b", re.IGNORECASE),
    re.compile(r"\bjailbreak\b", re.IGNORECASE),
    re.compile(r"\bpretend\s+you\s+are\b", re.IGNORECASE),
    re.compile(r"\bact\s+as\b", re.IGNORECASE),
]

CLARIFICATION_SIGNALS = [
    re.compile(r"\bwhat\s+do\s+you\s+mean\b", re.IGNORECASE),
    re.compile(r"\bcan\s+you\s+explain\b", re.IGNORECASE),
    re.compile(r"\bmore\s+details?\b", re.IGNORECASE),
    re.compile(r"\bwhich\s+(?:one|fund)\b", re.IGNORECASE),
]

# Factual sub-intent: fee explainer vs mutual fund corpus (intent-first + low-confidence fallback).
_FEE_CORPUS_PATTERNS = [
    re.compile(r"\bwhat\s+is\s+(?:an?\s+)?(?:exit\s+load|stt|stamp\s+duty|expense\s+ratio)\b", re.IGNORECASE),
    re.compile(r"\bexplain(?:er)?\s+(?:exit\s+load|fees?|stt|stamp\s+duty|expense\s+ratio)\b", re.IGNORECASE),
    re.compile(r"\bfee\s+explainer\b", re.IGNORECASE),
    re.compile(r"\bsecurities\s+transaction\s+tax\b", re.IGNORECASE),
    re.compile(r"\bstt\b", re.IGNORECASE),
    re.compile(r"\bstamp\s+duty\b", re.IGNORECASE),
    re.compile(r"\bcapital\s+gains(?:\s+tax)?\b", re.IGNORECASE),
    re.compile(r"\bltcg\b|\bstcg\b", re.IGNORECASE),
    re.compile(r"\bexit\s+load\b", re.IGNORECASE),
]

_MF_CORPUS_PATTERNS = [
    re.compile(r"\bnav\b", re.IGNORECASE),
    re.compile(r"\baum\b", re.IGNORECASE),
    re.compile(r"\bmin(?:imum)?\s+sip\b", re.IGNORECASE),
    re.compile(r"\breturns?\b", re.IGNORECASE),
    re.compile(r"\b1y\b|\b3y\b|\b5y\b", re.IGNORECASE),
    re.compile(r"\brisk\s+level\b|\brisk\b", re.IGNORECASE),
    re.compile(r"\bmutual\s+fund\s+(?:name|performance|details?)\b", re.IGNORECASE),
    re.compile(r"\bmirae\b|\baxis\b|\bhdfc\b|\bicici\b", re.IGNORECASE),
]


class IntentRouter:
    def classify(self, text: str) -> IntentClassification:
        for pattern in SAFETY_PATTERNS:
            if pattern.search(text):
                return IntentClassification(
                    intent_type="safety",
                    confidence=0.95,
                    reasoning_tag="safety_pattern_matched",
                )

        for pattern in ACTION_PATTERNS:
            if pattern.search(text):
                return IntentClassification(
                    intent_type="action",
                    confidence=0.85,
                    reasoning_tag="action_pattern_matched",
                )

        for pattern in CLARIFICATION_SIGNALS:
            if pattern.search(text):
                return IntentClassification(
                    intent_type="clarification",
                    confidence=0.75,
                    reasoning_tag="clarification_signal_detected",
                )

        return IntentClassification(
            intent_type="factual",
            confidence=0.80,
            reasoning_tag="default_factual",
        )

    def classify_factual_corpus(self, text: str) -> FactualCorpusClassification:
        """Route factual questions to MF vs fee-explainer Chroma corpus.

        High confidence → intent-first retrieval; low confidence → unified (caller passes ``None``).
        """

        fee_hits = sum(1 for p in _FEE_CORPUS_PATTERNS if p.search(text))
        mf_hits = sum(1 for p in _MF_CORPUS_PATTERNS if p.search(text))

        if fee_hits >= 2 and fee_hits > mf_hits:
            return FactualCorpusClassification(
                retrieval_corpus="fee_explainer",
                confidence=0.82,
                reasoning_tag="fee_corpus_strong",
            )
        if mf_hits >= 2 and mf_hits > fee_hits:
            return FactualCorpusClassification(
                retrieval_corpus="mutual_fund",
                confidence=0.82,
                reasoning_tag="mf_corpus_strong",
            )
        if fee_hits >= 1 and mf_hits == 0:
            return FactualCorpusClassification(
                retrieval_corpus="fee_explainer",
                confidence=0.72,
                reasoning_tag="fee_corpus_weak",
            )
        if mf_hits >= 1 and fee_hits == 0:
            return FactualCorpusClassification(
                retrieval_corpus="mutual_fund",
                confidence=0.72,
                reasoning_tag="mf_corpus_weak",
            )
        return FactualCorpusClassification(
            retrieval_corpus=None,
            confidence=0.55,
            reasoning_tag="corpus_ambiguous_unified",
        )
