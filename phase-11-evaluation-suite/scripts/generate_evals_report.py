from __future__ import annotations

import argparse
import json
from pathlib import Path

from backend.services.report_generator import write_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Evals-Report.md from run/case JSON")
    parser.add_argument("--run-json", required=True, help="Path to latest evaluation run JSON")
    parser.add_argument("--cases-json", required=True, help="Path to evaluation cases JSON list")
    args = parser.parse_args()

    run = json.loads(Path(args.run_json).read_text(encoding="utf-8"))
    cases = json.loads(Path(args.cases_json).read_text(encoding="utf-8"))
    out = write_report(run, cases)
    print(f"wrote report: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
