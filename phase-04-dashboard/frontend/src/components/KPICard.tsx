import { TrendingDown, TrendingUp } from "lucide-react";
import type { ReactNode } from "react";

import type { KPIItem } from "../types";

type Props = {
  label: string;
  icon: ReactNode;
  iconClass: string;
  data: KPIItem;
};

export function KPICard({ label, icon, iconClass, data }: Props) {
  const trendText =
    data.trend_direction === "new"
      ? "New"
      : `${data.trend_pct > 0 ? "+" : ""}${data.trend_pct.toFixed(1)}%`;
  const trendClass =
    data.trend_direction === "up" || data.trend_direction === "new"
      ? "text-emerald-600"
      : data.trend_direction === "down"
        ? "text-red-600"
        : "text-muted-foreground";

  return (
    <article className="border border-border bg-card text-card-foreground rounded-xl shadow-sm hover:shadow-md transition-shadow p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider truncate">{label}</p>
          <p className="mt-1.5 text-2xl font-bold text-foreground leading-none">{data.value}</p>
          <div className={`mt-2 flex items-center gap-1 text-xs font-medium ${trendClass}`}>
            {data.trend_direction === "down" ? (
              <TrendingDown className="w-3 h-3" />
            ) : (
              <TrendingUp className="w-3 h-3" />
            )}
            {trendText}
          </div>
        </div>
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${iconClass}`}>{icon}</div>
      </div>
    </article>
  );
}
