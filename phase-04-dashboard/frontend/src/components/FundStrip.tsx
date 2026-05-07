import type { FundStrip as FundStripType } from "../types";

type Props = {
  data: FundStripType | undefined;
  isLoading: boolean;
  isError: boolean;
};

export function FundStrip({ data, isLoading, isError }: Props) {
  if (isLoading) return <div className="h-24 rounded-xl bg-muted animate-pulse" />;
  if (isError) return <div className="rounded-xl border border-border p-4 text-sm text-muted-foreground">Unable to load funds.</div>;
  if (!data?.funds.length) {
    return <div className="rounded-xl border border-border p-4 text-sm text-muted-foreground">Awaiting first data refresh.</div>;
  }
  return (
    <section className="rounded-xl border border-border bg-card p-4">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold">Mutual fund NAV strip</h2>
        <p className="text-xs text-muted-foreground">Last scraped: {data.last_scraped_at ?? "n/a"}</p>
      </div>
      <div className="max-h-52 overflow-auto">
        {data.funds.map((fund) => (
          <div key={fund.fund_name} className="flex items-center justify-between py-2.5 border-b border-border last:border-0">
            <div>
              <p className="text-sm font-semibold text-foreground">{fund.fund_name}</p>
              <p className="text-xs text-muted-foreground">{fund.category}</p>
            </div>
            <div className="text-right">
              <p className="text-sm font-semibold text-foreground">{fund.nav.toFixed(2)}</p>
              <p className="text-xs text-muted-foreground">{fund.nav_date ?? "n/a"}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
