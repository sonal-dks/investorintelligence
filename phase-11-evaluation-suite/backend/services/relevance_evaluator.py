from __future__ import annotations

from .llm_judge import LLMJudge

_PROMPT = (
    "You are a strict answer relevance evaluator. Return JSON "
    '{"passed": true|false, "reasoning": "..."} only. Pass only if answer directly addresses the query.'
)


class RelevanceEvaluator:
    def __init__(self, judge: LLMJudge) -> None:
        self._judge = judge

    def evaluate(self, query: str, answer: str) -> tuple[bool, str]:
        return self._judge.judge_binary(
            _PROMPT,
            {"query": query, "answer": answer},
        )
