from __future__ import annotations

from backend.services.evaluation_runner import EvaluationRunner


def test_run_produces_scores_and_cases():
    runner = EvaluationRunner()
    run, cases = runner.run("manual")
    assert run["status"] == "completed"
    assert run["total_cases"] >= 4
    assert len(cases) == run["total_cases"]
    assert 0 <= run["rag_faithfulness_pct"] <= 100
    assert 0 <= run["rag_relevance_pct"] <= 100
    assert 0 <= run["safety_pass_pct"] <= 100
