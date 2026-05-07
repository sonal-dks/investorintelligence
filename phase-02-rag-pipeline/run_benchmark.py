"""Run the 20-query precision benchmark against the persisted Chroma collection.

Usage:
    python run_benchmark.py
    python run_benchmark.py --json

Pass criterion (architecture.md Phase 02 §Success Criteria):
    top-3 precision > 80%
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.services.rag_pipeline import RAGPipeline  # noqa: E402
from tests.benchmark_queries import BENCHMARK  # noqa: E402

logging.basicConfig(level=logging.WARNING)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    pipeline = RAGPipeline()
    retrieval = pipeline.get_retrieval()

    per_query: list[dict] = []
    correct = 0
    total_latency = 0
    started = time.time()
    for query, expected_substring in BENCHMARK:
        response = retrieval.query(query, top_k=5)
        top3 = response.results[:3]
        match_idx = next(
            (i for i, r in enumerate(top3) if expected_substring in r.metadata.fund_slug),
            -1,
        )
        passed = match_idx >= 0
        if passed:
            correct += 1
        total_latency += response.query_time_ms
        per_query.append(
            {
                "query": query,
                "expected_substring": expected_substring,
                "passed": passed,
                "match_rank": match_idx if passed else None,
                "top1_slug": top3[0].metadata.fund_slug if top3 else None,
                "query_time_ms": response.query_time_ms,
                "resolved_fund_slug": response.resolved_fund_slug,
            }
        )

    precision = correct / len(BENCHMARK)
    summary = {
        "queries_total": len(BENCHMARK),
        "queries_passed": correct,
        "top3_precision": round(precision, 4),
        "passes_threshold_80pct": precision >= 0.80,
        "avg_query_time_ms": int(total_latency / max(1, len(BENCHMARK))),
        "elapsed_total_ms": int((time.time() - started) * 1000),
        "embedding_model_used": retrieval._embedder.model_name,
        "per_query": per_query,
    }
    if args.json:
        json.dump(summary, sys.stdout, indent=2, default=str)
        sys.stdout.write("\n")
    else:
        for entry in per_query:
            mark = "PASS" if entry["passed"] else "FAIL"
            print(f"  [{mark}] {entry['query']}  →  top1={entry['top1_slug']}")
        print(
            f"\n{summary['queries_passed']}/{summary['queries_total']} passed  "
            f"(top-3 precision = {summary['top3_precision']:.0%})  "
            f"avg {summary['avg_query_time_ms']}ms / query"
        )
    return 0 if summary["passes_threshold_80pct"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
