from __future__ import annotations

from dataclasses import dataclass

from .case_loader import load_test_cases
from .evaluation_store import EvalStore
from .faithfulness_evaluator import FaithfulnessEvaluator
from .llm_judge import LLMJudge
from .relevance_evaluator import RelevanceEvaluator
from .report_generator import write_report
from .safety_evaluator import SafetyEvaluator
from .ux_validator import UXValidator


@dataclass
class EvaluationRunner:
    store: EvalStore

    def __init__(self, store: EvalStore | None = None) -> None:
        self.store = store or EvalStore()
        judge = LLMJudge()
        self._faith = FaithfulnessEvaluator(judge)
        self._rel = RelevanceEvaluator(judge)
        self._safety = SafetyEvaluator()
        self._ux = UXValidator()

    def _score(self, cases: list[dict], case_type: str) -> float:
        subset = [c for c in cases if c["case_type"] == case_type]
        if not subset:
            return 0.0
        passed = sum(1 for c in subset if c["passed"])
        return round((passed / len(subset)) * 100, 2)

    def run(self, run_type: str = "manual") -> tuple[dict, list[dict]]:
        run = self.store.start_run(run_type)
        cases_cfg = load_test_cases()
        pulse_word_count = 0
        action_items_count = 0

        for case in cases_cfg:
            ctype = case["case_type"]
            query = case["query"]
            expected = case.get("expected_behavior", "")
            actual_output = ""
            passed = False
            reasoning = ""

            if ctype == "rag_faithfulness":
                context = case.get("context", "")
                answer = case.get("mock_answer", case.get("expected_answer_snippet", ""))
                passed, reasoning = self._faith.evaluate(query, context, answer)
                actual_output = answer
            elif ctype == "rag_relevance":
                answer = case.get("mock_answer", case.get("expected_answer_snippet", ""))
                passed, reasoning = self._rel.evaluate(query, answer)
                actual_output = answer
            elif ctype == "safety":
                passed, text = self._safety.evaluate(query, expected)
                actual_output = text
                reasoning = "safe_refusal" if passed else "unsafe_or_non_refusal"
            else:  # ux
                summary = case.get("summary_text", "")
                actions = case.get("action_items", [])
                top_theme = case.get("top_theme")
                voice_greeting = case.get("voice_greeting")
                passed, reasoning, pulse_word_count, action_items_count = self._ux.evaluate_pulse(
                    summary,
                    actions,
                    top_theme=top_theme,
                    voice_greeting=voice_greeting,
                )
                actual_output = summary

            self.store.add_case(
                run["run_id"],
                {
                    "case_type": ctype,
                    "query": query,
                    "expected_behavior": expected,
                    "actual_output": actual_output,
                    "passed": passed,
                    "judge_reasoning": reasoning,
                },
            )

        cases = self.store.run_cases(run["run_id"])
        total = len(cases)
        passed_cases = sum(1 for c in cases if c["passed"])
        updates = {
            "rag_faithfulness_pct": self._score(cases, "rag_faithfulness"),
            "rag_relevance_pct": self._score(cases, "rag_relevance"),
            "safety_pass_pct": self._score(cases, "safety"),
            "pulse_word_count": pulse_word_count,
            "action_items_count": action_items_count,
            "total_cases": total,
            "passed_cases": passed_cases,
        }
        final_run = self.store.complete_run(run["run_id"], updates)
        write_report(final_run, cases)
        return final_run, cases
