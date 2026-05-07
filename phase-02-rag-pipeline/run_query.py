"""CLI: run a single query against the persisted Chroma collection.

Usage:
    python run_query.py "What is the exit load of Mirae Asset Large Cap?"
    python run_query.py "exit load mirae" --top-k 5 --json
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.services.rag_pipeline import RAGPipeline  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s :: %(message)s",
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Query the RAG vector store.")
    parser.add_argument("query", help="natural-language question")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--fund", default=None, help="explicit fund_slug filter")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    pipeline = RAGPipeline()
    retrieval = pipeline.get_retrieval()
    result = retrieval.query(args.query, top_k=args.top_k, fund_filter=args.fund)
    payload = result.model_dump()
    if args.json:
        json.dump(payload, sys.stdout, indent=2, default=str)
        sys.stdout.write("\n")
    else:
        print(json.dumps(payload, indent=2, default=str))
    return 0 if result.results else 1


if __name__ == "__main__":
    raise SystemExit(main())
