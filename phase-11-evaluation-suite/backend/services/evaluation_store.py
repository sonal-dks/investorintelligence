from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import httpx

from .. import config


def _sb_headers() -> dict[str, str]:
    key = config.supabase_service_role_key() or ""
    return {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def _sb_url(table: str) -> str:
    return f"{str(config.supabase_url()).rstrip('/')}/rest/v1/{table}"


@dataclass
class EvalStore:
    runs: list[dict]
    cases: list[dict]

    def __init__(self) -> None:
        self.runs = []
        self.cases = []
        self._supabase = config.supabase_enabled()

    def _safe_insert(self, table: str, payload: dict | list[dict]) -> None:
        if not self._supabase:
            return
        try:
            r = httpx.post(_sb_url(table), headers=_sb_headers(), json=payload, timeout=15.0)
            r.raise_for_status()
        except Exception:
            # fail open: keep in-memory copy working
            pass

    def _safe_patch(self, table: str, field: str, value: str, payload: dict) -> None:
        if not self._supabase:
            return
        try:
            r = httpx.patch(
                _sb_url(table),
                params={field: f"eq.{value}"},
                headers=_sb_headers(),
                json=payload,
                timeout=15.0,
            )
            r.raise_for_status()
        except Exception:
            pass

    def start_run(self, run_type: str) -> dict:
        run = {
            "run_id": str(uuid4()),
            "status": "in_progress",
            "run_type": run_type,
            "rag_faithfulness_pct": 0.0,
            "rag_relevance_pct": 0.0,
            "safety_pass_pct": 0.0,
            "pulse_word_count": 0,
            "action_items_count": 0,
            "total_cases": 0,
            "passed_cases": 0,
            "started_at": datetime.now(UTC),
            "completed_at": None,
        }
        self.runs.append(run)
        self._safe_insert(
            "evaluation_runs",
            {
                "id": run["run_id"],
                "run_type": run["run_type"],
                "rag_faithfulness_pct": run["rag_faithfulness_pct"],
                "rag_relevance_pct": run["rag_relevance_pct"],
                "safety_pass_pct": run["safety_pass_pct"],
                "pulse_word_count": run["pulse_word_count"],
                "action_items_count": run["action_items_count"],
                "total_cases": run["total_cases"],
                "passed_cases": run["passed_cases"],
                "started_at": run["started_at"].isoformat(),
                "completed_at": None,
            },
        )
        return run

    def add_case(self, run_id: str, case: dict[str, Any]) -> dict:
        record = {"id": str(uuid4()), "run_id": run_id, "created_at": datetime.now(UTC), **case}
        self.cases.append(record)
        self._safe_insert(
            "evaluation_cases",
            {
                "id": record["id"],
                "run_id": record["run_id"],
                "case_type": record["case_type"],
                "query": record["query"],
                "expected_behavior": record["expected_behavior"],
                "actual_output": record["actual_output"],
                "passed": record["passed"],
                "judge_reasoning": record["judge_reasoning"],
                "created_at": record["created_at"].isoformat(),
            },
        )
        return record

    def complete_run(self, run_id: str, updates: dict[str, Any]) -> dict:
        run = next(r for r in self.runs if r["run_id"] == run_id)
        run.update(updates)
        run["status"] = "completed"
        run["completed_at"] = datetime.now(UTC)
        self._safe_patch(
            "evaluation_runs",
            "id",
            run_id,
            {
                "rag_faithfulness_pct": run["rag_faithfulness_pct"],
                "rag_relevance_pct": run["rag_relevance_pct"],
                "safety_pass_pct": run["safety_pass_pct"],
                "pulse_word_count": run["pulse_word_count"],
                "action_items_count": run["action_items_count"],
                "total_cases": run["total_cases"],
                "passed_cases": run["passed_cases"],
                "completed_at": run["completed_at"].isoformat(),
            },
        )
        return run

    def latest_run(self) -> dict | None:
        if self._supabase:
            try:
                r = httpx.get(
                    _sb_url("evaluation_runs"),
                    params={"select": "*", "order": "started_at.desc", "limit": "1"},
                    headers=_sb_headers(),
                    timeout=15.0,
                )
                r.raise_for_status()
                rows = r.json() or []
                if rows:
                    row = rows[0]
                    return {
                        "run_id": row["id"],
                        "status": "completed" if row.get("completed_at") else "in_progress",
                        "run_type": row.get("run_type", "manual"),
                        "rag_faithfulness_pct": float(row.get("rag_faithfulness_pct") or 0.0),
                        "rag_relevance_pct": float(row.get("rag_relevance_pct") or 0.0),
                        "safety_pass_pct": float(row.get("safety_pass_pct") or 0.0),
                        "pulse_word_count": int(row.get("pulse_word_count") or 0),
                        "action_items_count": int(row.get("action_items_count") or 0),
                        "total_cases": int(row.get("total_cases") or 0),
                        "passed_cases": int(row.get("passed_cases") or 0),
                        "started_at": datetime.fromisoformat(str(row["started_at"]).replace("Z", "+00:00")),
                        "completed_at": (
                            datetime.fromisoformat(str(row["completed_at"]).replace("Z", "+00:00"))
                            if row.get("completed_at")
                            else None
                        ),
                    }
            except Exception:
                pass
        return self.runs[-1] if self.runs else None

    def run_cases(self, run_id: str) -> list[dict]:
        if self._supabase:
            try:
                r = httpx.get(
                    _sb_url("evaluation_cases"),
                    params={"select": "*", "run_id": f"eq.{run_id}", "order": "created_at.asc"},
                    headers=_sb_headers(),
                    timeout=15.0,
                )
                r.raise_for_status()
                rows = r.json() or []
                out = []
                for row in rows:
                    out.append(
                        {
                            "id": row["id"],
                            "run_id": row["run_id"],
                            "case_type": row["case_type"],
                            "query": row.get("query", ""),
                            "expected_behavior": row.get("expected_behavior", ""),
                            "actual_output": row.get("actual_output", ""),
                            "passed": bool(row.get("passed")),
                            "judge_reasoning": row.get("judge_reasoning", ""),
                            "created_at": datetime.fromisoformat(str(row["created_at"]).replace("Z", "+00:00")),
                        }
                    )
                return out
            except Exception:
                pass
        return [c for c in self.cases if c["run_id"] == run_id]

    def history(self, limit: int) -> list[dict]:
        if self._supabase:
            try:
                r = httpx.get(
                    _sb_url("evaluation_runs"),
                    params={"select": "*", "order": "started_at.desc", "limit": str(limit)},
                    headers=_sb_headers(),
                    timeout=15.0,
                )
                r.raise_for_status()
                rows = r.json() or []
                out = []
                for row in rows:
                    out.append(
                        {
                            "run_id": row["id"],
                            "status": "completed" if row.get("completed_at") else "in_progress",
                            "run_type": row.get("run_type", "manual"),
                            "rag_faithfulness_pct": float(row.get("rag_faithfulness_pct") or 0.0),
                            "rag_relevance_pct": float(row.get("rag_relevance_pct") or 0.0),
                            "safety_pass_pct": float(row.get("safety_pass_pct") or 0.0),
                            "pulse_word_count": int(row.get("pulse_word_count") or 0),
                            "action_items_count": int(row.get("action_items_count") or 0),
                            "total_cases": int(row.get("total_cases") or 0),
                            "passed_cases": int(row.get("passed_cases") or 0),
                            "started_at": datetime.fromisoformat(str(row["started_at"]).replace("Z", "+00:00")),
                            "completed_at": (
                                datetime.fromisoformat(str(row["completed_at"]).replace("Z", "+00:00"))
                                if row.get("completed_at")
                                else None
                            ),
                        }
                    )
                return out
            except Exception:
                pass
        return self.runs[-limit:]
