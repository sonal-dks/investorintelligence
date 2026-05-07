from __future__ import annotations

import json

import httpx

from .. import config

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


class LLMJudge:
    def __init__(self) -> None:
        self._api_key = config.openrouter_api_key()
        self._model = config.openrouter_judge_model()

    def judge_binary(self, system_prompt: str, payload: dict) -> tuple[bool, str]:
        def _fallback(reason: str) -> tuple[bool, str]:
            answer = str(payload.get("answer", "")).lower()
            context = str(payload.get("context", "")).lower()
            passed = bool(answer and (answer in context or len(answer.split()) < 8))
            return passed, reason

        if not self._api_key:
            return _fallback("fallback_judge_used_without_openrouter_key")

        try:
            response = httpx.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self._model,
                    "temperature": 0,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": json.dumps(payload)},
                    ],
                },
                timeout=45.0,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            return bool(parsed.get("passed")), str(parsed.get("reasoning", ""))
        except Exception:
            return _fallback("fallback_judge_used_after_openrouter_error")
