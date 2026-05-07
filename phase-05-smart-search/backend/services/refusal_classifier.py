"""Refusal classifier — identifies advice/unsafe requests.

Rule-based patterns detect investment advice, recommendations, and
prediction queries. These are refused with a standard safe response.
"""

from __future__ import annotations

import re

ADVICE_PATTERNS = [
    re.compile(r"\bshould\s+i\s+invest\b", re.IGNORECASE),
    re.compile(r"\brecommend\b", re.IGNORECASE),
    re.compile(r"\bwhich\s+fund\s+is\s+better\b", re.IGNORECASE),
    re.compile(r"\bbuy\s+or\s+sell\b", re.IGNORECASE),
    re.compile(r"\bwill\s+it\s+go\s+up\b", re.IGNORECASE),
    re.compile(r"\bwill\s+(?:the\s+)?(?:nav|price|market)\s+(?:go|rise|fall|drop|increase|decrease)\b", re.IGNORECASE),
    re.compile(r"\bis\s+(?:it|this)\s+a\s+good\s+(?:time|investment)\b", re.IGNORECASE),
    re.compile(r"\bpredict(?:ion)?\b", re.IGNORECASE),
    re.compile(r"\bguarantee\b", re.IGNORECASE),
    re.compile(r"\bbest\s+fund\s+(?:to|for)\b", re.IGNORECASE),
    re.compile(r"\badvice\b", re.IGNORECASE),
]

REFUSAL_RESPONSE = (
    "I can provide factual information about mutual funds, but I'm not able to "
    "give investment advice or recommendations. I cannot tell you whether you "
    "should invest in a specific fund.\n\n"
    "I can help you with:\n"
    "- Fund details (NAV, returns, expense ratio)\n"
    "- Exit load and tax rules\n"
    "- Fund comparisons on factual metrics\n\n"
    "Would you like to know about any specific fund's details?"
)


class RefusalClassifier:
    def check(self, text: str) -> tuple[bool, str | None]:
        for pattern in ADVICE_PATTERNS:
            if pattern.search(text):
                return True, REFUSAL_RESPONSE
        return False, None
