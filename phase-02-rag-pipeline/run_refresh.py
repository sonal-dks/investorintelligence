"""CLI: rebuild the ChromaDB collection from latest Supabase rows.

Usage:
    python run_refresh.py          # human-friendly output
    python run_refresh.py --json   # machine-readable
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

# Make `backend.*` importable when this script is run directly.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.services.rag_pipeline import RAGPipeline  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s :: %(message)s",
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh the RAG vector store.")
    parser.add_argument("--json", action="store_true", help="emit JSON result")
    args = parser.parse_args()

    pipeline = RAGPipeline()
    result = pipeline.refresh()
    payload = result.model_dump()
    if args.json:
        json.dump(payload, sys.stdout, indent=2, default=str)
        sys.stdout.write("\n")
    else:
        print(json.dumps(payload, indent=2, default=str))
    return 0 if result.status == "success" else 2


if __name__ == "__main__":
    raise SystemExit(main())
