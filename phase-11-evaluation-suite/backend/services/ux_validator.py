from __future__ import annotations


class UXValidator:
    def evaluate_pulse(
        self,
        summary_text: str,
        action_items: list[str],
        top_theme: str | None = None,
        voice_greeting: str | None = None,
    ) -> tuple[bool, str, int, int]:
        words = len((summary_text or "").split())
        actions = len(action_items or [])
        theme = (top_theme or "").strip()
        greeting = (voice_greeting or "").strip().lower()
        voice_mentions_theme = (not theme) or (theme.lower() in greeting)
        passed = words <= 250 and actions == 3 and voice_mentions_theme
        reason = (
            f"word_count={words}, action_items={actions}, "
            f"voice_mentions_top_theme={voice_mentions_theme}"
        )
        return passed, reason, words, actions
