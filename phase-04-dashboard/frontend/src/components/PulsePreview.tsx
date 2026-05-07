import type { PulsePreview as PulsePreviewType } from "../types";

type Props = {
  data: PulsePreviewType | undefined;
  isLoading: boolean;
  isError: boolean;
};

export function PulsePreview({ data, isLoading, isError }: Props) {
  if (isLoading) return <div className="h-28 rounded-xl bg-muted animate-pulse" />;
  if (isError) return <div className="rounded-xl border border-border p-4 text-sm text-muted-foreground">Unable to load weekly pulse.</div>;
  return (
    <section className="rounded-xl border border-border bg-card p-4">
      <h2 className="text-sm font-semibold">Weekly pulse preview</h2>
      <div className="mt-4 space-y-1">
        <p className="text-sm">Rating: <span className="font-semibold">{data?.overall_rating ?? 0}</span></p>
        <p className="text-sm">New reviews: <span className="font-semibold">{data?.new_reviews_this_week ?? 0}</span></p>
        <p className="text-xs text-muted-foreground">{data?.sentiment_summary ?? "No weekly pulse data yet"}</p>
      </div>
    </section>
  );
}
