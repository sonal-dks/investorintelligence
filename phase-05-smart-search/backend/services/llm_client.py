"""OpenRouter LLM client with primary + fallback model chain.

Follows the ai-ml-fallback-implementation skill:
  1. Retry with bounded attempts
  2. Switch to fallback model
  3. Return controlled degraded response on total failure
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import httpx

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

ERROR_RESPONSE = (
    "I'm sorry, I'm experiencing technical difficulties right now. "
    "Please try again in a moment."
)


@dataclass
class LLMResponse:
    """Result of an LLM call. Tokens/cost are 0 when the call fully fails."""

    text: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    cost_details: dict = field(default_factory=dict)


class LLMClient:
    def __init__(
        self,
        api_key: str,
        primary_model: str,
        fallback_model: str,
        max_tokens: int = 1024,
    ) -> None:
        self._api_key = api_key
        self._primary = primary_model
        self._fallback = fallback_model
        self._max_tokens = max_tokens

    def generate(
        self,
        messages: list[dict[str, str]],
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """Tries primary then fallback model. Always returns an LLMResponse."""
        effective_max = max_tokens or self._max_tokens
        for model in [self._primary, self._fallback]:
            try:
                return self._call_openrouter(model, messages, effective_max)
            except Exception:
                logger.exception("llm_call_failed", extra={"model": model})
                continue

        logger.error("all_llm_models_failed")
        return LLMResponse(text=ERROR_RESPONSE, model="none")

    def _call_openrouter(
        self,
        model: str,
        messages: list[dict[str, str]],
        max_tokens: int,
    ) -> LLMResponse:
        resp = httpx.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0.3,
            },
            timeout=60.0,
        )
        resp.raise_for_status()
        data = resp.json()
        text = data["choices"][0]["message"]["content"].strip()
        usage = data.get("usage") or {}
        return LLMResponse(
            text=text,
            model=model,
            prompt_tokens=int(usage.get("prompt_tokens", 0) or 0),
            completion_tokens=int(usage.get("completion_tokens", 0) or 0),
            total_tokens=int(usage.get("total_tokens", 0) or 0),
            cost_usd=float(usage.get("cost", 0.0) or 0.0),
            cost_details=usage.get("cost_details") or {},
        )
