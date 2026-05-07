from __future__ import annotations

from .llm_judge import LLMJudge

_PROMPT = (
    "You are a strict RAG faithfulness evaluator. Return JSON "
    '{"passed": true|false, "reasoning": "..."} only. Pass only if answer is fully grounded in context.'
)


class FaithfulnessEvaluator:
    def __init__(self, judge: LLMJudge) -> None:
        self._judge = judge

    def evaluate(self, query: str, context: str, answer: str) -> tuple[bool, str]:
        return self._judge.judge_binary(
            _PROMPT,
            {"query": query, "context": context, "answer": answer},
        )
