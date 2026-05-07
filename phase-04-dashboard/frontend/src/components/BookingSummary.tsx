import type { BookingSummary as BookingSummaryType } from "../types";

type Props = {
  data: BookingSummaryType | undefined;
  isLoading: boolean;
  isError: boolean;
};

export function BookingSummary({ data, isLoading, isError }: Props) {
  if (isLoading) return <div className="h-28 rounded-xl bg-muted animate-pulse" />;
  if (isError) return <div className="rounded-xl border border-border p-4 text-sm text-muted-foreground">Unable to load booking summary.</div>;
  const confirmed = data?.confirmed ?? 0;
  const cancelled = data?.cancelled ?? 0;
  const rescheduled = data?.rescheduled ?? 0;
  return (
    <section className="rounded-xl border border-border bg-card p-4">
      <h2 className="text-sm font-semibold">Booking status</h2>
      <p className="text-xs text-muted-foreground mt-0.5">Confirmed, cancelled, and rescheduled totals</p>
      <div className="mt-4 grid grid-cols-3 gap-4">
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-center">
          <p className="text-xs text-emerald-700">Confirmed</p>
          <p className="text-xl font-bold text-emerald-700">{confirmed}</p>
        </div>
        <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-center">
          <p className="text-xs text-red-700">Cancelled</p>
          <p className="text-xl font-bold text-red-700">{cancelled}</p>
        </div>
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-center">
          <p className="text-xs text-amber-700">Rescheduled</p>
          <p className="text-xl font-bold text-amber-700">{rescheduled}</p>
        </div>
      </div>
    </section>
  );
}
