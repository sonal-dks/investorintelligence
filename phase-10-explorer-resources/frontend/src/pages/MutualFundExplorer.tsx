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

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

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

  if (q.isLoading) return <main style={{ padding: 20 }}>Loading funds...</main>;
  if (q.isError) return <main style={{ padding: 20 }}>Data loading, please check back.</main>;

  const summary = q.data!.summary;
  const stale = summary.last_scraped_at ? Date.now() - new Date(summary.last_scraped_at).getTime() > 14 * 24 * 60 * 60 * 1000 : false;

  return (
    <main style={{ padding: 20 }}>
      <h1 style={{ marginBottom: 4 }}>Mutual Fund Explorer</h1>
      <div style={{ marginBottom: 14, color: "#4b5563" }}>
        Last scraped: {summary.last_scraped_at || "N/A"} {stale ? " | Data may be outdated" : ""}
      </div>
      <div style={{ display: "flex", gap: 12, marginBottom: 12, flexWrap: "wrap" }}>
        <div style={{ padding: 10, border: "1px solid #e5e7eb", borderRadius: 10 }}>Tracked: {summary.tracked_funds}</div>
        <div style={{ padding: 10, border: "1px solid #e5e7eb", borderRadius: 10 }}>Avg Expense: {summary.avg_expense_ratio}%</div>
        <div style={{ padding: 10, border: "1px solid #e5e7eb", borderRadius: 10 }}>High Risk: {summary.high_risk_funds}</div>
      </div>

      <input
        aria-label="Search funds"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder="Search fund by name"
        style={{ width: "100%", maxWidth: 420, marginBottom: 12, padding: 10 }}
      />

      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 16 }}>
        {categories.map((c) => (
          <button key={c} onClick={() => setCategory(c)} style={{ padding: "6px 10px", borderRadius: 16, border: "1px solid #d1d5db", background: c === category ? "#111827" : "#fff", color: c === category ? "#fff" : "#111827" }}>
            {c}
          </button>
        ))}
      </div>

      {filtered.length === 0 ? (
        <div style={{ border: "1px dashed #d1d5db", borderRadius: 10, padding: 14 }}>No funds match your search.</div>
      ) : (
        <section style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: 12 }}>
          {filtered.map((fund) => (
            <FundCard key={fund.fund_slug} fund={fund} />
          ))}
        </section>
      )}
    </main>
  );
}
