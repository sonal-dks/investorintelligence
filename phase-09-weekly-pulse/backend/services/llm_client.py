from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass

import httpx

from backend.services.sentiment_analyzer import SentimentAnalyzer

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

logger = logging.getLogger(__name__)


@dataclass
class LLMGenResult:
    summary_text: str
    action_items: list[str]
    themes: list[dict]
    model_used: str
    model_path: str


@dataclass
class LLMJudgeResult:
    overall_score: float
    metrics: dict
    rationale: str


def _strip_code_fence(content: str) -> str:
    text = content.strip()
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if m:
        return m.group(1).strip()
    return text


def _parse_json_object(content: str) -> dict:
    return json.loads(_strip_code_fence(content))


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

    def classify_review_sentiments(self, reviews: list[dict], batch_size: int = 24) -> list[dict]:
        """Assign positive | neutral | negative per review from text (batched). Falls back per row to star-based on parse errors."""
        if not self.is_enabled():
            raise RuntimeError("llm_not_configured")
        if not reviews:
            return []
        star = SentimentAnalyzer()
        out: list[dict] = []
        for start in range(0, len(reviews), batch_size):
            batch = reviews[start : start + batch_size]
            payload = [
                {"i": start + j, "rating": int(b.get("rating", 0)), "text": (b.get("review_text") or "")[:450]}
                for j, b in enumerate(batch)
            ]
            results_map: dict[int, str] = {}
            for model in (self._primary, self._fallback):
                batch_ok = False
                for json_mode in (True, False):
                    try:
                        prompt = (
                            "For each item, classify sentiment of the review TEXT only (ignore star rating if it disagrees). "
                            'Use exactly one label per item: "positive", "neutral", or "negative".\n'
                            "Return ONLY valid JSON: {\"results\":[{\"i\":0,\"sentiment\":\"negative\"}, ...]}\n"
                            f"Items: {json.dumps(payload)}"
                        )
                        content = self._chat_completion(
                            model=model,
                            messages=[{"role": "user", "content": prompt}],
                            max_tokens=800,
                            temperature=0.0,
                            json_mode=json_mode,
                        )
                        parsed = _parse_json_object(content)
                        for row in parsed.get("results") or []:
                            idx = int(row["i"])
                            s = str(row.get("sentiment", "")).lower().strip()
                            if s not in ("positive", "neutral", "negative"):
                                continue
                            results_map[idx] = s
                        batch_ok = True
                        break
                    except Exception as e:
                        logger.warning("sentiment batch LLM failed model=%s json_mode=%s: %s", model, json_mode, e)
                        continue
                if batch_ok:
                    break
            for j, b in enumerate(batch):
                global_i = start + j
                copied = dict(b)
                if global_i in results_map:
                    copied["sentiment"] = results_map[global_i]
                else:
                    copied["sentiment"] = star.classify_rating(int(copied.get("rating", 0)))
                out.append(copied)
        return out

    def generate(self, review_snippets: list[str], stats: dict) -> LLMGenResult:
        if not self.is_enabled():
            raise RuntimeError("llm_not_configured")
        last_err: Exception | None = None
        for model in (self._primary, self._fallback):
            for strict in (False, True):
                for json_mode in (True, False):
                    try:
                        return self._call_model(
                            model=model,
                            review_snippets=review_snippets,
                            stats=stats,
                            strict=strict,
                            json_mode=json_mode,
                            model_path="primary_llm" if model == self._primary else "fallback_llm",
                        )
                    except Exception as e:
                        last_err = e
                        continue
        logger.warning("pulse LLM exhausted models: %s", last_err)
        raise RuntimeError("all_llm_models_failed") from last_err

    def group_themes(self, themes: list[dict], review_snippets: list[str], max_groups: int = 5) -> list[dict]:
        if not self.is_enabled():
            raise RuntimeError("llm_not_configured")
        prompt = (
            "You are a product insights analyst. Group granular review themes into broader dashboard-friendly clusters.\n"
            "Return ONLY JSON: {\"themes\":[{\"theme\":\"UI/UX\",\"count\":10,\"sentiment\":\"negative\"}]}\n"
            "Rules:\n"
            f"- Return 3 to {max_groups} grouped themes.\n"
            "- Theme names should be broad but useful, e.g. UI/UX, Customer Support, App Performance, Fees & Charges, Trading Reliability.\n"
            "- Avoid very specific issue text in the final grouped theme label.\n"
            "- Count = sum/approx aggregate count in grouped bucket.\n"
            "- sentiment = one of positive, neutral, negative, mixed.\n"
            f"Input granular themes: {json.dumps(themes[:12])}\n"
            f"Sample snippets: {json.dumps(review_snippets[:20])}"
        )
        last_err: Exception | None = None
        for model in (self._primary, self._fallback):
            for json_mode in (True, False):
                try:
                    content = self._chat_completion(
                        model=model,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=900,
                        temperature=0.1,
                        json_mode=json_mode,
                    )
                    parsed = _parse_json_object(content)
                    rows = parsed.get("themes") or []
                    if isinstance(rows, list) and rows:
                        return list(rows)[:max_groups]
                except Exception as e:
                    last_err = e
                    continue
        raise RuntimeError("theme_grouping_failed") from last_err

    def judge_weekly_pulse(
        self,
        summary_text: str,
        action_items: list[str],
        grouped_themes: list[dict],
    ) -> LLMJudgeResult:
        if not self.is_enabled():
            raise RuntimeError("llm_not_configured")
        prompt = (
            "Score this weekly pulse output for dashboard quality.\n"
            "Return ONLY JSON with keys: overall_score (0-100 number), "
            "metrics (object with keys theme_quality,specificity,actionability,safety each 0-100), rationale (short string).\n"
            "Evaluation focus:\n"
            "- grouped themes are broad and useful (not too narrow, not too vague)\n"
            "- action items are concrete\n"
            "- summary is clear and non-PII\n"
            f"summary_text: {json.dumps(summary_text)}\n"
            f"action_items: {json.dumps(action_items)}\n"
            f"grouped_themes: {json.dumps(grouped_themes)}"
        )
        last_err: Exception | None = None
        for model in (self._primary, self._fallback):
            for json_mode in (True, False):
                try:
                    content = self._chat_completion(
                        model=model,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=700,
                        temperature=0.0,
                        json_mode=json_mode,
                    )
                    parsed = _parse_json_object(content)
                    metrics = parsed.get("metrics") or {}
                    return LLMJudgeResult(
                        overall_score=float(parsed.get("overall_score", 0.0)),
                        metrics=metrics if isinstance(metrics, dict) else {},
                        rationale=str(parsed.get("rationale", "")).strip(),
                    )
                except Exception as e:
                    last_err = e
                    continue
        raise RuntimeError("judge_scoring_failed") from last_err

    def _chat_completion(
        self,
        model: str,
        messages: list[dict],
        max_tokens: int,
        temperature: float,
        json_mode: bool,
    ) -> str:
        body: dict = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        resp = httpx.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            json=body,
            timeout=90.0,
        )
        resp.raise_for_status()
        data = resp.json()
        return str(data["choices"][0]["message"]["content"] or "")

    def _call_model(
        self,
        model: str,
        review_snippets: list[str],
        stats: dict,
        strict: bool,
        json_mode: bool,
        model_path: str,
    ) -> LLMGenResult:
        strict_line = "Do not exceed 220 words." if strict else "Do not exceed 250 words."
        banned = (
            '"General Product Feedback", "User Experience", "App Quality", "Customer Satisfaction", '
            '"Overall Experience", "Misc feedback"'
        )
        prompt = (
            "You are generating a weekly product pulse from app store reviews. Return ONLY JSON with keys:\n"
            "- summary_text (string)\n"
            "- action_items (array of exactly 3 short strings)\n"
            "- themes: array of 3 to 5 objects, each with keys theme (string), count (integer), sentiment (string).\n\n"
            "THEME RULES:\n"
            "- Each theme must be a SPECIFIC issue or praise users mention (e.g. "
            '"SIP installment edit flow", "Portfolio dashboard load time on Android", '
            '"Mutual fund discovery search", "Gold/SGB purchase errors").\n'
            f"- Do NOT use vague bucket labels including: {banned}.\n"
            "- Count = approximate number of review snippets that belong to that theme (integer >= 1).\n"
            "- sentiment per theme = dominant tone for that cluster: one of positive, neutral, negative, mixed.\n\n"
            f"{strict_line} Operational tone, no PII, no email addresses.\n\n"
            f"Stats: {json.dumps(stats)}\n"
            f"Review snippets: {json.dumps(review_snippets[:50])}"
        )
        try:
            content = self._chat_completion(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2048,
                temperature=0.15,
                json_mode=json_mode,
            )
        except httpx.HTTPStatusError as e:
            # Some models reject response_format; caller will retry with json_mode False.
            raise e
        parsed = _parse_json_object(content)
        return LLMGenResult(
            summary_text=str(parsed["summary_text"]).strip(),
            action_items=[str(x).strip() for x in parsed["action_items"]],
            themes=list(parsed.get("themes") or []),
            model_used=model,
            model_path=model_path,
        )
