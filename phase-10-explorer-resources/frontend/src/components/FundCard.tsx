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
};

function metric(value: number | null | undefined, suffix = ""): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "N/A";
  return `${value.toFixed(2)}${suffix}`;
}

export function FundCard({ fund }: { fund: Fund }) {
  return (
    <article style={{ border: "1px solid #e5e7eb", borderRadius: 12, padding: 16 }}>
      <h3 style={{ margin: 0, fontSize: 16 }}>{fund.fund_name}</h3>
      <p style={{ margin: "6px 0 12px", color: "#4b5563" }}>{fund.category || "Uncategorized"}</p>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, fontSize: 13 }}>
        <div>NAV: {metric(fund.nav)}</div>
        <div>NAV Date: {fund.nav_date || "N/A"}</div>
        <div>AUM (Cr): {metric(fund.aum_cr)}</div>
        <div>Expense: {metric(fund.expense_ratio, "%")}</div>
        <div>Min SIP: {fund.min_sip ?? "N/A"}</div>
        <div>Risk: {fund.risk_level || "N/A"}</div>
        <div>1Y: {metric(fund.returns_1y, "%")}</div>
        <div>3Y: {metric(fund.returns_3y, "%")}</div>
        <div>5Y: {metric(fund.returns_5y, "%")}</div>
      </div>
      <a href={fund.source_url || "https://groww.in"} target="_blank" rel="noreferrer" style={{ display: "inline-block", marginTop: 12 }}>
        Source
      </a>
    </article>
  );
}
