import { useMemo, useState } from "react";

type EvalRun = {
  run_id: string;
  run_type: string;
  started_at: string;
  finished_at: string | null;
  total_cases: number;
  passed_cases: number;
  failed_cases: number;
  pass_rate: number;
};

type EvalCase = {
  case_id: string;
  run_id: string;
  category: string;
  input_text: string;
  expected_type: string;
  actual_type: string;
  score: number;
  passed: boolean;
  notes: string | null;
};

type EvalRunWithCases = {
  run: EvalRun;
  cases: EvalCase[];
};

const base = () => import.meta.env.VITE_API_BASE ?? "";

async function jsonOrThrow<T>(res: Response): Promise<T> {
  if (!res.ok) throw new Error(`Request failed (${res.status})`);
  return (await res.json()) as T;
}

export function EvaluationSuitePage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<EvalRunWithCases | null>(null);

  const failures = useMemo(() => data?.cases.filter((c) => !c.passed) ?? [], [data]);

  const loadLatest = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${base()}/api/eval/latest`);
      const body = await jsonOrThrow<EvalRunWithCases>(res);
      setData(body);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load latest evaluation");
    } finally {
      setLoading(false);
    }
  };

  const runFresh = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${base()}/api/eval/run`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-user-role": "admin",
        },
        body: JSON.stringify({ run_type: "full" }),
      });
      const body = await jsonOrThrow<EvalRunWithCases>(res);
      setData(body);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to run evaluation");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-border bg-card p-5">
        <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold">Evaluation Suite</h2>
          <p className="text-sm text-muted-foreground">Admin-only quality and safety checks (Phase 11).</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => void loadLatest()}
            disabled={loading}
            className="rounded-lg border border-border px-3 py-2 text-sm"
          >
            Load latest
          </button>
          <button
            type="button"
            onClick={() => void runFresh()}
            disabled={loading}
            className="rounded-lg bg-primary text-primary-foreground px-3 py-2 text-sm"
          >
            Run full eval
          </button>
        </div>
      </div>
      </div>

      {loading ? <div className="text-sm text-muted-foreground">Working...</div> : null}
      {error ? <div className="text-sm text-red-600">{error}</div> : null}

      {data ? (
        <>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <div className="rounded-lg border border-border p-3">
              <div className="text-xs text-muted-foreground">Run type</div>
              <div className="text-sm font-semibold">{data.run.run_type}</div>
            </div>
            <div className="rounded-lg border border-border p-3">
              <div className="text-xs text-muted-foreground">Total cases</div>
              <div className="text-sm font-semibold">{data.run.total_cases}</div>
            </div>
            <div className="rounded-lg border border-border p-3">
              <div className="text-xs text-muted-foreground">Pass rate</div>
              <div className="text-sm font-semibold">{data.run.pass_rate.toFixed(2)}%</div>
            </div>
            <div className="rounded-lg border border-border p-3">
              <div className="text-xs text-muted-foreground">Failed</div>
              <div className="text-sm font-semibold">{data.run.failed_cases}</div>
            </div>
          </div>

          <div className="rounded-lg border border-border">
            <div className="px-4 py-3 border-b border-border text-sm font-medium">
              Failed cases ({failures.length})
            </div>
            <div className="divide-y divide-border">
              {failures.length === 0 ? (
                <div className="px-4 py-3 text-sm text-muted-foreground">No failed cases.</div>
              ) : (
                failures.map((c) => (
                  <div key={c.case_id} className="px-4 py-3 text-sm">
                    <div className="font-medium">
                      {c.category} · expected {c.expected_type} / actual {c.actual_type}
                    </div>
                    <div className="text-muted-foreground mt-1">{c.input_text}</div>
                    {c.notes ? <div className="text-xs text-muted-foreground mt-1">Notes: {c.notes}</div> : null}
                  </div>
                ))
              )}
            </div>
          </div>
        </>
      ) : (
        <div className="rounded-lg border border-border p-4 text-sm text-muted-foreground">
          No evaluation data loaded yet. Click &quot;Load latest&quot; or &quot;Run full eval&quot;.
        </div>
      )}
    </div>
  );
}
