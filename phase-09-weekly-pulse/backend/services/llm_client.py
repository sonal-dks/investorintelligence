from __future__ import annotations

import json
import os
from dataclasses import dataclass

import httpx

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


@dataclass
class LLMGenResult:
    summary_text: str
    action_items: list[str]
    themes: list[dict]
    model_used: str
    model_path: str


class PulseLLMClient:
    def __init__(
        self,
        api_key: str | None = None,
        primary_model: str | None = None,
        fallback_model: str | None = None,
    ) -> None:
        self._api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self._primary = primary_model or os.getenv("PHASE09_LLM_PRIMARY_MODEL", "anthropic/claude-3.5-sonnet")
        self._fallback = fallback_model or os.getenv("PHASE09_LLM_FALLBACK_MODEL", "openai/gpt-4o-mini")

    def is_enabled(self) -> bool:
        return bool(self._api_key)

    def generate(self, review_snippets: list[str], stats: dict) -> LLMGenResult:
        if not self.is_enabled():
            raise RuntimeError("llm_not_configured")
        for model in (self._primary, self._fallback):
            for strict in (False, True):
                try:
                    return self._call_model(
                        model=model,
                        review_snippets=review_snippets,
                        stats=stats,
                        strict=strict,
                        model_path="primary_llm" if model == self._primary else "fallback_llm",
                    )
                except Exception:
                    continue
        raise RuntimeError("all_llm_models_failed")

    def _call_model(
        self,
        model: str,
        review_snippets: list[str],
        stats: dict,
        strict: bool,
        model_path: str,
    ) -> LLMGenResult:
        strict_line = "Do not exceed 220 words." if strict else "Do not exceed 250 words."
        prompt = (
            "You are generating a weekly product pulse. Return ONLY valid JSON with keys: "
            "summary_text (string), action_items (array of exactly 3 strings), "
            "themes (array of up to 5 objects with keys theme,count,sentiment). "
            f"{strict_line} Keep neutral operational tone.\n\n"
            f"Stats: {json.dumps(stats)}\n"
            f"Review snippets: {json.dumps(review_snippets[:50])}"
        )
        resp = httpx.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "max_tokens": 700,
            },
            timeout=45.0,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        return LLMGenResult(
            summary_text=str(parsed["summary_text"]).strip(),
            action_items=[str(x).strip() for x in parsed["action_items"]],
            themes=list(parsed.get("themes") or []),
            model_used=model,
            model_path=model_path,
        )
