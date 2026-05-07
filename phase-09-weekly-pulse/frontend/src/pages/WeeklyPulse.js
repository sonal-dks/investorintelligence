import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { KeywordTable } from "../components/KeywordTable";
import { PulseKPIs } from "../components/PulseKPIs";
import { ReviewCard } from "../components/ReviewCard";
const base = () => import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8090";
export function WeeklyPulsePage() {
    const [tab, setTab] = useState("overview");
    const [sentiment, setSentiment] = useState("all");
    const latest = useQuery({
        queryKey: ["pulse-latest"],
        queryFn: async () => {
            const r = await fetch(`${base()}/api/pulse/latest`);
            if (!r.ok)
                throw new Error("pulse-latest");
            return r.json();
        },
    });
    const reviews = useQuery({
        queryKey: ["pulse-reviews", sentiment],
        queryFn: async () => {
            const r = await fetch(`${base()}/api/pulse/reviews?sentiment=${sentiment}&page=1&limit=20`);
            if (!r.ok)
                throw new Error("pulse-reviews");
            return r.json();
        },
    });
    const keywords = useQuery({
        queryKey: ["pulse-keywords"],
        queryFn: async () => {
            const r = await fetch(`${base()}/api/pulse/keywords`);
            if (!r.ok)
                throw new Error("pulse-keywords");
            return r.json();
        },
    });
    if (latest.isLoading)
        return _jsx("main", { children: "Loading weekly pulse..." });
    if (latest.isError)
        return _jsx("main", { children: "First analysis will run on Monday." });
    const data = latest.data;
    if (!data)
        return _jsx("main", { children: "No pulse data." });
    return (_jsxs("main", { style: { maxWidth: 980, margin: "0 auto", padding: 16 }, children: [_jsx("h1", { children: "Weekly Pulse" }), _jsx(PulseKPIs, { overallRating: data.overall_rating, totalReviews: data.total_reviews, positiveCount: data.positive_count, negativeCount: data.negative_count }), _jsxs("div", { style: { display: "flex", gap: 8, marginTop: 12, marginBottom: 12 }, children: [_jsx("button", { onClick: () => setTab("overview"), children: "Overview" }), _jsx("button", { onClick: () => setTab("reviews"), children: "Reviews" }), _jsx("button", { onClick: () => setTab("keywords"), children: "Keywords" })] }), tab === "overview" && (_jsxs("section", { children: [_jsxs("div", { style: { fontSize: 12, color: "#666", marginBottom: 8 }, children: ["Model path: ", data.model_path ?? "unknown", " | LLM model: ", data.model_used ?? "n/a"] }), _jsx("p", { children: data.summary_text }), _jsx("ol", { children: data.action_items.map((item) => (_jsx("li", { children: item }, item))) }), _jsx("h3", { style: { marginTop: 20 }, children: "LLM vs Deterministic Comparison" }), _jsxs("div", { style: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }, children: [_jsxs("article", { style: { border: "1px solid #ddd", borderRadius: 8, padding: 12 }, children: [_jsx("h4", { style: { marginTop: 0 }, children: "LLM Output (Primary)" }), _jsx("p", { children: data.llm_summary_text ?? data.summary_text }), _jsx("ul", { children: (data.llm_themes ?? []).map((t) => (_jsxs("li", { children: [t.theme, " (", t.count, ")"] }, `llm-${t.theme}`))) })] }), _jsxs("article", { style: { border: "1px solid #ddd", borderRadius: 8, padding: 12 }, children: [_jsx("h4", { style: { marginTop: 0 }, children: "Deterministic Fallback (Dashboard View)" }), _jsx("p", { children: data.deterministic_summary_text ?? "No deterministic summary available." }), _jsxs("div", { style: { fontSize: 12, color: "#666" }, children: ["Algorithm: ", data.deterministic_algorithm ?? "rule-based"] }), _jsx("ul", { children: (data.deterministic_themes ?? []).map((t) => (_jsxs("li", { children: [t.theme, " (", t.count, ")"] }, `det-${t.theme}`))) })] })] })] })), tab === "reviews" && (_jsxs("section", { children: [_jsx("div", { style: { display: "flex", gap: 6, marginBottom: 10 }, children: ["all", "positive", "neutral", "negative"].map((s) => (_jsx("button", { onClick: () => setSentiment(s), children: s }, s))) }), (reviews.data?.reviews ?? []).map((review) => (_jsx(ReviewCard, { review: review }, `${review.reviewer_name}-${review.review_date}`)))] })), tab === "keywords" && _jsx(KeywordTable, { rows: keywords.data?.keywords ?? [] })] }));
}
