from __future__ import annotations

from pathlib import Path

from .. import config


def render_report(run: dict, cases: list[dict]) -> str:
    by_type: dict[str, list[dict]] = {}
    for case in cases:
        by_type.setdefault(case["case_type"], []).append(case)

    faith_by_query = {c["query"]: c for c in by_type.get("rag_faithfulness", [])}
    rel_by_query = {c["query"]: c for c in by_type.get("rag_relevance", [])}
    golden_queries = sorted(set(faith_by_query) | set(rel_by_query))
    safety_cases = by_type.get("safety", [])
    ux_cases = by_type.get("ux", [])

    lines = [
        "# Evals Report: Performance and Safety",
        "",
        "## Scope",
        "- Retrieval Accuracy (Golden Dataset: 5 complex M1 + M2 questions)",
        "- Constraint Adherence (3 adversarial safety prompts)",
        "- Tone & Structure (Weekly Pulse checks + Voice top-theme mention)",
        "",
        "## Latest Run",
        f"- Run ID: `{run['run_id']}`",
        f"- Run type: `{run['run_type']}`",
        f"- Faithfulness: `{run['rag_faithfulness_pct']:.2f}%`",
        f"- Relevance: `{run['rag_relevance_pct']:.2f}%`",
        f"- Safety: `{run['safety_pass_pct']:.2f}%`",
        f"- Total cases: `{run['total_cases']}` | Passed: `{run['passed_cases']}`",
        "",
        "## Category Breakdown",
    ]
    for case_type in ["rag_faithfulness", "rag_relevance", "safety", "ux"]:
        group = by_type.get(case_type, [])
        if not group:
            lines.append(f"- {case_type}: no cases")
            continue
        passed = sum(1 for c in group if c["passed"])
        lines.append(f"- {case_type}: {passed}/{len(group)} passed")

    lines.extend(["", "## Golden Dataset (Retrieval Accuracy)"])
    if not golden_queries:
        lines.append("- No golden dataset cases available.")
    else:
        for idx, query in enumerate(golden_queries, start=1):
            faith = faith_by_query.get(query)
            rel = rel_by_query.get(query)
            faith_status = "PASS" if faith and faith["passed"] else "FAIL"
            rel_status = "PASS" if rel and rel["passed"] else "FAIL"
            lines.append(f"- G{idx}: {query} | Faithfulness: {faith_status} | Relevance: {rel_status}")

    lines.extend(["", "## Adversarial Safety Eval"])
    if not safety_cases:
        lines.append("- No safety/adversarial cases available.")
    else:
        for idx, case in enumerate(safety_cases, start=1):
            status = "PASS" if case["passed"] else "FAIL"
            lines.append(f"- S{idx}: {case['query']} | Result: {status}")

    lines.extend(["", "## Tone & Structure (UX Eval)"])
    if not ux_cases:
        lines.append("- No UX cases available.")
    else:
        for idx, case in enumerate(ux_cases, start=1):
            status = "PASS" if case["passed"] else "FAIL"
            lines.append(f"- U{idx}: {case['query']} | Result: {status} | {case['judge_reasoning']}")

    lines.extend(["", "## Notable Failing Cases"])
    failures = [c for c in cases if not c["passed"]][:10]
    if not failures:
        lines.append("- No failing cases in latest run.")
    else:
        for case in failures:
            lines.append(f"- `{case['case_type']}`: {case['query']} -> {case['judge_reasoning']}")
    lines.extend(["", "## Notes", "- Generated from `evaluation_runs` and `evaluation_cases` (derived artifact)."])
    return "\n".join(lines) + "\n"


def write_report(run: dict, cases: list[dict]) -> Path:
    out = config.project_root() / "Docs" / "Architecture" / "Evals-Report.md"
    out.write_text(render_report(run, cases), encoding="utf-8")
    return out
