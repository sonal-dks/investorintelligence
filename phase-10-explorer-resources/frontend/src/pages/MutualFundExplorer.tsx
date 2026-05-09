import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { FundCard } from "../components/FundCard";

type Fund = {
  fund_slug: string;
  fund_name: string;
  category: string | null;
  nav: number | null;
  nav_date: string | null;
  aum_cr: number | null;
  expense_ratio: number | null;
  min_sip: number | null;
  risk_level: string | null;
  returns_1y: number | null;
  returns_3y: number | null;
  returns_5y: number | null;
  source_url: string | null;
  scraped_at: string | null;
};

type FundsResponse = {
  funds: Fund[];
  summary: {
    tracked_funds: number;
    avg_expense_ratio: number;
    high_risk_funds: number;
    last_scraped_at: string | null;
  };
};

const API_BASE = import.meta.env.VITE_API_BASE ?? import.meta.env.VITE_API_BASE_URL ?? "";

async function fetchFunds(): Promise<FundsResponse> {
  const res = await fetch(`${API_BASE}/api/funds`);
  if (!res.ok) throw new Error("fund_api_failed");
  return res.json();
}

export function MutualFundExplorerPage() {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("All");
  const q = useQuery({ queryKey: ["funds"], queryFn: fetchFunds });

  const categories = useMemo(() => {
    const set = new Set<string>();
    (q.data?.funds || []).forEach((f) => {
      if (f.category) set.add(f.category);
    });
    return ["All", ...Array.from(set).sort()];
  }, [q.data]);

  const filtered = useMemo(() => {
    const term = search.trim().toLowerCase();
    return (q.data?.funds || []).filter((fund) => {
      const matchesName = term === "" || fund.fund_name.toLowerCase().includes(term);
      const matchesCategory = category === "All" || fund.category === category;
      return matchesName && matchesCategory;
    });
  }, [q.data, search, category]);

  if (q.isLoading) return <main className="p-4 text-sm text-muted-foreground">Loading funds...</main>;
  if (q.isError) return <main className="p-4 text-sm text-destructive">Data loading, please check back.</main>;

  const summary = q.data!.summary;
  const stale = summary.last_scraped_at ? Date.now() - new Date(summary.last_scraped_at).getTime() > 14 * 24 * 60 * 60 * 1000 : false;

  return (
    <main className="mx-auto max-w-6xl space-y-4 px-4 py-4">
      <div className="rounded-xl border border-border bg-card p-5">
        <h1 className="text-xl font-semibold">Mutual Fund Explorer</h1>
        <div className="mt-1 text-sm text-muted-foreground">
        Last scraped: {summary.last_scraped_at || "N/A"} {stale ? " | Data may be outdated" : ""}
        </div>
      </div>
      <div className="grid gap-3 sm:grid-cols-3">
        <div className="rounded-lg border border-border bg-card p-3 text-sm">Tracked: {summary.tracked_funds}</div>
        <div className="rounded-lg border border-border bg-card p-3 text-sm">Avg Expense: {summary.avg_expense_ratio}%</div>
        <div className="rounded-lg border border-border bg-card p-3 text-sm">High Risk: {summary.high_risk_funds}</div>
      </div>

      <div className="rounded-xl border border-border bg-card p-4">
        <input
          aria-label="Search funds"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search fund by name"
          className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm"
        />

        <div className="mt-3 flex flex-wrap gap-2">
          {categories.map((c) => (
            <button
              key={c}
              onClick={() => setCategory(c)}
              className={`rounded-full border px-3 py-1 text-xs ${
                c === category ? "border-primary bg-primary text-primary-foreground" : "border-border bg-background"
              }`}
            >
              {c}
            </button>
          ))}
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border bg-card p-4 text-sm text-muted-foreground">
          No funds match your search.
        </div>
      ) : (
        <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {filtered.map((fund) => (
            <FundCard key={fund.fund_slug} fund={fund} />
          ))}
        </section>
      )}
    </main>
  );
}
