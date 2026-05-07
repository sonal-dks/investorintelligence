import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { FeeSection } from "../components/FeeSection";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function fetchFunds() {
  const res = await fetch(`${API_BASE}/api/funds`);
  if (!res.ok) throw new Error("fund_api_failed");
  return res.json();
}

async function fetchFees() {
  const res = await fetch(`${API_BASE}/api/resources/fees`);
  if (!res.ok) throw new Error("fee_api_failed");
  return res.json();
}

export function ResourceHubPage() {
  const [tab, setTab] = useState<"funds" | "fees">("funds");
  const funds = useQuery({ queryKey: ["resource-funds"], queryFn: fetchFunds });
  const fees = useQuery({ queryKey: ["resource-fees"], queryFn: fetchFees });

  return (
    <main style={{ padding: 20 }}>
      <h1>Resource Hub</h1>
      <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
        <button onClick={() => setTab("funds")} style={{ padding: "8px 12px" }}>Mutual Funds</button>
        <button onClick={() => setTab("fees")} style={{ padding: "8px 12px" }}>Fee Explainer</button>
      </div>
      {tab === "funds" ? (
        <section>
          {funds.isLoading ? <div>Loading funds...</div> : null}
          {funds.isError ? <div>Unable to load funds.</div> : null}
          {(funds.data?.funds || []).slice(0, 30).map((f: any) => (
            <div key={f.fund_slug} style={{ borderBottom: "1px solid #f3f4f6", padding: "8px 0" }}>
              <strong>{f.fund_name}</strong> | {f.category || "N/A"} | NAV {f.nav ?? "N/A"} | 1Y {f.returns_1y ?? "N/A"}%
            </div>
          ))}
        </section>
      ) : (
        <section>
          {fees.isLoading ? <div>Loading fee explainer...</div> : null}
          {fees.isError ? <div>Unable to load fee explainer.</div> : null}
          {(fees.data?.sections || []).map((section: any) => (
            <FeeSection key={section.fee_type} title={section.title} items={section.items} />
          ))}
          <div style={{ color: "#4b5563", fontSize: 13 }}>
            Source: {fees.data?.source_url || "https://groww.in"} | Last updated: {fees.data?.last_updated || "N/A"}
          </div>
        </section>
      )}
    </main>
  );
}
