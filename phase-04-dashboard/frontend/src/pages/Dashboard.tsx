import { useDashboardOverview } from "../hooks/useDashboard";

export function DashboardPage() {
  const overview = useDashboardOverview();
  const data = overview.data;

  if (overview.isLoading) return <div className="p-4 text-sm text-muted-foreground">Loading dashboard...</div>;

  const fallback = {
    kpis: [
      { key: "total_active_users", label: "TOTAL ACTIVE USERS", value: 0, subtitle: "—" },
      { key: "total_login_sessions", label: "TOTAL LOGIN SESSIONS", value: 0, subtitle: "—" },
      { key: "chatbot_sessions", label: "CHATBOT SESSIONS", value: 0, subtitle: "—" },
      { key: "voice_sessions", label: "VOICE SESSIONS", value: 0, subtitle: "—" },
      { key: "total_bookings", label: "TOTAL BOOKINGS", value: 0, subtitle: "—" },
      { key: "email_triggers", label: "EMAIL TRIGGERS", value: 0, subtitle: "—" },
      { key: "pending_approvals", label: "PENDING APPROVALS", value: 0, subtitle: "—" },
      { key: "fund_resources", label: "FUND RESOURCES", value: 0, subtitle: "—" },
    ],
    stocks: [],
    booking_summary: { confirmed: 0, cancelled: 0, rescheduled: 0, total: 0 },
    pulse: {
      overall_rating: 0,
      new_reviews_this_week: 0,
      top_keyword: "—",
      top_keyword_mentions: 0,
      last_pulse_label: "Last Pulse: —",
    },
  };
  const view = data ?? fallback;

  return (
    <div className="space-y-6">
      {overview.isError ? (
        <div className="rounded-lg border border-border bg-card px-4 py-2 text-xs text-muted-foreground">
          Live dashboard metrics are temporarily unavailable.
        </div>
      ) : null}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {view.kpis.map((kpi) => (
          <section key={kpi.key} className="rounded-xl border bg-card p-4">
            <p className="text-[11px] font-semibold tracking-wide text-muted-foreground">{kpi.label}</p>
            <p className="mt-2 text-3xl font-semibold leading-none">{kpi.value}</p>
            <p className="mt-2 text-xs text-muted-foreground">{kpi.subtitle}</p>
          </section>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <section className="rounded-xl border bg-card p-4 xl:col-span-2">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold">STOCKS PRICE TRACKER</h2>
            <span className="text-xs text-muted-foreground">Live mutual fund NAV</span>
          </div>
          <div className="space-y-2">
            {view.stocks.length === 0 ? (
              <p className="rounded-md border border-border px-3 py-2 text-sm text-muted-foreground">—</p>
            ) : null}
            {view.stocks.map((stock) => (
              <div key={stock.symbol + stock.name} className="flex items-center justify-between rounded-md border px-3 py-2">
                <div>
                  <p className="text-sm font-medium">{stock.symbol}</p>
                  <p className="text-xs text-muted-foreground">{stock.name}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium">Rs {stock.price.toFixed(2)}</p>
                  <p className={`text-xs ${stock.change_pct >= 0 ? "text-emerald-600" : "text-rose-600"}`}>
                    {stock.change_pct >= 0 ? "+" : ""}
                    {stock.change_pct.toFixed(2)}%
                  </p>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="space-y-4">
          <article className="rounded-xl border bg-card p-4">
            <h3 className="text-sm font-semibold">BOOKING STATUS</h3>
            <div className="mt-3 grid grid-cols-3 gap-2 text-center">
              <div className="rounded-md border p-2">
                <p className="text-xs text-muted-foreground">Confirmed</p>
                <p className="text-lg font-semibold">{view.booking_summary.confirmed}</p>
              </div>
              <div className="rounded-md border p-2">
                <p className="text-xs text-muted-foreground">Cancelled</p>
                <p className="text-lg font-semibold">{view.booking_summary.cancelled}</p>
              </div>
              <div className="rounded-md border p-2">
                <p className="text-xs text-muted-foreground">Rescheduled</p>
                <p className="text-lg font-semibold">{view.booking_summary.rescheduled}</p>
              </div>
            </div>
          </article>

          <article className="rounded-xl border bg-card p-4">
            <h3 className="text-sm font-semibold">WEEKLY PULSE SNAPSHOT</h3>
            <p className="mt-2 text-xs text-muted-foreground">{view.pulse.last_pulse_label}</p>
            <p className="mt-2 text-2xl font-semibold">{view.pulse.overall_rating.toFixed(1)} / 5</p>
            <p className="text-sm text-muted-foreground">{view.pulse.new_reviews_this_week} new reviews this week</p>
            <p className="mt-3 text-sm">
              <span className="text-muted-foreground">Top keyword: </span>
              <span className="font-medium">{view.pulse.top_keyword}</span>
              <span className="text-muted-foreground"> ({view.pulse.top_keyword_mentions})</span>
            </p>
          </article>
        </section>
      </div>
    </div>
  );
}
