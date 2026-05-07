import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { KeywordTable } from "../components/KeywordTable";
import { PulseKPIs } from "../components/PulseKPIs";
import { ReviewCard, type Review } from "../components/ReviewCard";

const base = () => import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8090";

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
    <main style={{ maxWidth: 980, margin: "0 auto", padding: 16 }}>
      <h1>Weekly Pulse</h1>
      <PulseKPIs
        overallRating={data.overall_rating}
        totalReviews={data.total_reviews}
        positiveCount={data.positive_count}
        negativeCount={data.negative_count}
      />
      <div style={{ display: "flex", gap: 8, marginTop: 12, marginBottom: 12 }}>
        <button onClick={() => setTab("overview")}>Overview</button>
        <button onClick={() => setTab("reviews")}>Reviews</button>
        <button onClick={() => setTab("keywords")}>Keywords</button>
      </div>
      {tab === "overview" && (
        <section>
          <div style={{ fontSize: 12, color: "#666", marginBottom: 8 }}>
            Model path: {data.model_path ?? "unknown"} | LLM model: {data.model_used ?? "n/a"}
          </div>
          <p>{data.summary_text}</p>
          <ol>
            {data.action_items.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ol>
          <h3 style={{ marginTop: 20 }}>LLM vs Deterministic Comparison</h3>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <article style={{ border: "1px solid #ddd", borderRadius: 8, padding: 12 }}>
              <h4 style={{ marginTop: 0 }}>LLM Output (Primary)</h4>
              <p>{data.llm_summary_text ?? data.summary_text}</p>
              <ul>
                {(data.llm_themes ?? []).map((t) => (
                  <li key={`llm-${t.theme}`}>{t.theme} ({t.count})</li>
                ))}
              </ul>
            </article>
            <article style={{ border: "1px solid #ddd", borderRadius: 8, padding: 12 }}>
              <h4 style={{ marginTop: 0 }}>Deterministic Fallback (Dashboard View)</h4>
              <p>{data.deterministic_summary_text ?? "No deterministic summary available."}</p>
              <div style={{ fontSize: 12, color: "#666" }}>
                Algorithm: {data.deterministic_algorithm ?? "rule-based"}
              </div>
              <ul>
                {(data.deterministic_themes ?? []).map((t) => (
                  <li key={`det-${t.theme}`}>{t.theme} ({t.count})</li>
                ))}
              </ul>
            </article>
          </div>
        </section>
      )}
      {tab === "reviews" && (
        <section>
          <div style={{ display: "flex", gap: 6, marginBottom: 10 }}>
            {(["all", "positive", "neutral", "negative"] as const).map((s) => (
              <button key={s} onClick={() => setSentiment(s)}>
                {s}
              </button>
            ))}
          </div>
          {(reviews.data?.reviews ?? []).map((review) => (
            <ReviewCard key={`${review.reviewer_name}-${review.review_date}`} review={review} />
          ))}
        </section>
      )}
      {tab === "keywords" && <KeywordTable rows={keywords.data?.keywords ?? []} />}
    </main>
  );
}
