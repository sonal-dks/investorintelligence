import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { KeywordTable } from "../components/KeywordTable";
import { PulseKPIs } from "../components/PulseKPIs";
import { ReviewCard, type Review } from "../components/ReviewCard";

const base = () => import.meta.env.VITE_API_BASE ?? "";

type Latest = {
  overall_rating: number;
  total_reviews: number;
  positive_count: number;
  negative_count: number;
  summary_text: string;
  llm_summary_text?: string;
  deterministic_summary_text?: string;
  action_items: string[];
  llm_themes?: Array<{ theme: string; count: number; sentiment: string }>;
  deterministic_themes?: Array<{ theme: string; count: number; sentiment: string }>;
  model_path?: string;
  model_used?: string;
  deterministic_algorithm?: string;
};

export function WeeklyPulsePage() {
  const [tab, setTab] = useState<"overview" | "reviews" | "keywords">("overview");
  const [themeView, setThemeView] = useState<"llm" | "deterministic">("llm");
  const [sentiment, setSentiment] = useState<"all" | "positive" | "neutral" | "negative">("all");
  const latest = useQuery({
    queryKey: ["pulse-latest"],
    queryFn: async (): Promise<Latest> => {
      const r = await fetch(`${base()}/api/pulse/latest`);
      if (!r.ok) throw new Error("pulse-latest");
      return r.json();
    },
  });
  const reviews = useQuery({
    queryKey: ["pulse-reviews", sentiment],
    queryFn: async (): Promise<{ reviews: Review[] }> => {
      const r = await fetch(`${base()}/api/pulse/reviews?sentiment=${sentiment}&page=1&limit=20`);
      if (!r.ok) throw new Error("pulse-reviews");
      return r.json();
    },
  });
  const keywords = useQuery({
    queryKey: ["pulse-keywords"],
    queryFn: async (): Promise<{ keywords: any[] }> => {
      const r = await fetch(`${base()}/api/pulse/keywords`);
      if (!r.ok) throw new Error("pulse-keywords");
      return r.json();
    },
  });

  if (latest.isLoading) return <main>Loading weekly pulse...</main>;
  if (latest.isError) return <main>First analysis will run on Monday.</main>;
  const data = latest.data;
  if (!data) return <main>No pulse data.</main>;

  return (
    <main className="mx-auto max-w-6xl space-y-4">
      <div className="rounded-xl border border-border bg-card p-5">
        <h1 className="text-xl font-semibold">Weekly Pulse</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          App review sentiment, themes, and model-backed weekly insights.
        </p>
      </div>
      <PulseKPIs
        overallRating={data.overall_rating}
        totalReviews={data.total_reviews}
        positiveCount={data.positive_count}
        negativeCount={data.negative_count}
      />
      <div className="flex flex-wrap gap-2 rounded-xl border border-border bg-card p-2">
        <button className="rounded-md border border-border px-3 py-1.5 text-sm" onClick={() => setTab("overview")}>
          Overview
        </button>
        <button className="rounded-md border border-border px-3 py-1.5 text-sm" onClick={() => setTab("reviews")}>
          Reviews
        </button>
        <button className="rounded-md border border-border px-3 py-1.5 text-sm" onClick={() => setTab("keywords")}>
          Keywords
        </button>
      </div>
      {tab === "overview" && (
        <section className="space-y-3 rounded-xl border border-border bg-card p-5">
          <div className="text-xs text-muted-foreground">
            Model path: {data.model_path ?? "unknown"} | LLM model: {data.model_used ?? "n/a"} | Deterministic:{" "}
            {data.deterministic_algorithm ?? "rule-based-v1"}
          </div>
          <p className="text-sm">{data.summary_text}</p>
          <ol className="list-inside list-decimal space-y-1 text-sm text-muted-foreground">
            {data.action_items.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ol>
          <h3 className="pt-2 text-sm font-semibold">Themes Comparison</h3>
          <div className="flex gap-2">
            <button className="rounded-md border border-border px-3 py-1.5 text-sm" onClick={() => setThemeView("llm")}>
              LLM Themes
            </button>
            <button
              className="rounded-md border border-border px-3 py-1.5 text-sm"
              onClick={() => setThemeView("deterministic")}
            >
              Deterministic Themes
            </button>
          </div>
          {themeView === "llm" ? (
            <article className="rounded-lg border border-border p-3">
              <h4 className="text-sm font-semibold">LLM Output (Primary)</h4>
              <p className="mt-2 text-sm">{data.llm_summary_text ?? data.summary_text}</p>
              <ul className="mt-2 space-y-1 text-sm text-muted-foreground">
                {(data.llm_themes ?? []).map((t) => (
                  <li key={`llm-${t.theme}`}>
                    {t.theme} ({t.count}) - {t.sentiment}
                  </li>
                ))}
              </ul>
            </article>
          ) : (
            <article className="rounded-lg border border-border p-3">
              <h4 className="text-sm font-semibold">Deterministic Fallback</h4>
              <p className="mt-2 text-sm">{data.deterministic_summary_text ?? "No deterministic summary available."}</p>
              <div className="mt-2 text-xs text-muted-foreground">
                Algorithm: {data.deterministic_algorithm ?? "rule-based-v1"}
              </div>
              <ul className="mt-2 space-y-1 text-sm text-muted-foreground">
                {(data.deterministic_themes ?? []).map((t) => (
                  <li key={`det-${t.theme}`}>
                    {t.theme} ({t.count}) - {t.sentiment}
                  </li>
                ))}
              </ul>
            </article>
          )}
        </section>
      )}
      {tab === "reviews" && (
        <section className="rounded-xl border border-border bg-card p-4">
          <div className="mb-3 flex flex-wrap gap-2">
            {(["all", "positive", "neutral", "negative"] as const).map((s) => (
              <button key={s} className="rounded-md border border-border px-3 py-1 text-sm" onClick={() => setSentiment(s)}>
                {s}
              </button>
            ))}
          </div>
          {(reviews.data?.reviews ?? []).map((review) => (
            <ReviewCard key={`${review.reviewer_name}-${review.review_date}`} review={review} />
          ))}
        </section>
      )}
      {tab === "keywords" && (
        <section className="rounded-xl border border-border bg-card p-4">
          <KeywordTable rows={keywords.data?.keywords ?? []} />
        </section>
      )}
    </main>
  );
}
