"""PII detection and redaction for user input.

Detects: PAN, Aadhaar, phone numbers, email addresses.
Returns cleaned text with redacted patterns.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

PAN_PATTERN = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b")
AADHAAR_PATTERN = re.compile(r"\b[0-9]{4}\s?[0-9]{4}\s?[0-9]{4}\b")
PHONE_PATTERN = re.compile(r"(?:\+91|0)?[6-9][0-9]{9}\b")
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")


@dataclass
class PIIFinding:
    pii_type: str
    value: str
    start: int
    end: int


class PIIDetector:
    _PATTERNS = [
        ("PAN", PAN_PATTERN),
        ("AADHAAR", AADHAAR_PATTERN),
        ("PHONE", PHONE_PATTERN),
        ("EMAIL", EMAIL_PATTERN),
    ]

    def scan(self, text: str) -> tuple[str, list[PIIFinding]]:
        findings: list[PIIFinding] = []
        for pii_type, pattern in self._PATTERNS:
            for match in pattern.finditer(text):
                findings.append(
                    PIIFinding(
                        pii_type=pii_type,
                        value=match.group(),
                        start=match.start(),
                        end=match.end(),
                    )
                )

        if not findings:
            return text, []

        findings.sort(key=lambda f: f.start, reverse=True)
        cleaned = text
        for finding in findings:
            replacement = f"[REDACTED_{finding.pii_type}]"
            cleaned = cleaned[: finding.start] + replacement + cleaned[finding.end :]

        return cleaned, findings
