from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Query

from ..models.schemas import EvalCaseResult, EvalRunRequest, EvalRunResult, EvalRunWithCases
from ..services.evaluation_runner import EvaluationRunner
from ..services.evaluation_store import EvalStore

router = APIRouter(prefix="/api/eval", tags=["evaluation"])
_store = EvalStore()
_runner = EvaluationRunner(_store)


def _require_admin(user_role: str | None) -> None:
    if user_role != "admin":
        raise HTTPException(status_code=403, detail="admin_only")


@router.post("/run", response_model=EvalRunWithCases)
def run_eval(request: EvalRunRequest, x_user_role: str | None = Header(default=None)) -> EvalRunWithCases:
    _require_admin(x_user_role)
    run, cases = _runner.run(run_type=request.run_type)
    return EvalRunWithCases(run=EvalRunResult(**run), cases=[EvalCaseResult(**c) for c in cases])


@router.get("/latest", response_model=EvalRunWithCases)
def latest_eval() -> EvalRunWithCases:
    run = _store.latest_run()
    if run is None:
        raise HTTPException(status_code=404, detail="no_evaluation_run")
    cases = _store.run_cases(run["run_id"])
    return EvalRunWithCases(run=EvalRunResult(**run), cases=[EvalCaseResult(**c) for c in cases])


@router.get("/history", response_model=list[EvalRunResult])
def eval_history(limit: int = Query(default=20, ge=1, le=100)) -> list[EvalRunResult]:
    runs = _store.history(limit)
    return [EvalRunResult(**r) for r in runs]


@router.get("/cases", response_model=list[EvalCaseResult])
def eval_cases(run_id: str) -> list[EvalCaseResult]:
    return [EvalCaseResult(**c) for c in _store.run_cases(run_id)]
