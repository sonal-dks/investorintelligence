import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
export function PulseKPIs(props) {
    return (_jsxs("section", { style: { display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 12 }, children: [_jsx(Kpi, { label: "Overall Rating", value: props.overallRating.toFixed(2) }), _jsx(Kpi, { label: "New Reviews", value: String(props.totalReviews) }), _jsx(Kpi, { label: "Positive", value: String(props.positiveCount) }), _jsx(Kpi, { label: "Negative", value: String(props.negativeCount) })] }));
}
function Kpi({ label, value }) {
    return (_jsxs("div", { style: { border: "1px solid #ddd", borderRadius: 8, padding: 12 }, children: [_jsx("div", { style: { fontSize: 12, color: "#666" }, children: label }), _jsx("div", { style: { fontSize: 20, fontWeight: 600 }, children: value })] }));
}
