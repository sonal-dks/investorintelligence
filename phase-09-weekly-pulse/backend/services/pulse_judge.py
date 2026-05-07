from __future__ import annotations


class PulseJudge:
    def validate(self, summary_text: str, action_items: list[str]) -> dict:
        issues: list[str] = []
        words = [w for w in summary_text.split() if w.strip()]
        if len(words) > 250:
            issues.append("summary_word_count_exceeds_250")
        if len(action_items) != 3:
            issues.append("action_items_must_be_exactly_3")
        if not summary_text.strip():
            issues.append("summary_empty")
        # Basic PII-style check to avoid leaking emails in generated summary text.
        if "@" in summary_text:
            issues.append("summary_contains_pii_like_email")
        return {"pass": len(issues) == 0, "issues": issues, "word_count": len(words)}
