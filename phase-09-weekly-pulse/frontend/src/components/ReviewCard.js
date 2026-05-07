import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
export function ReviewCard({ review }) {
    return (_jsxs("article", { style: { border: "1px solid #ddd", borderRadius: 8, padding: 12, marginBottom: 10 }, children: [_jsxs("header", { style: { display: "flex", justifyContent: "space-between", marginBottom: 8 }, children: [_jsx("strong", { children: review.reviewer_name }), _jsx("span", { children: review.review_date })] }), _jsxs("div", { style: { marginBottom: 8 }, children: ["★".repeat(review.rating), "☆".repeat(5 - review.rating)] }), _jsx("p", { style: { margin: 0 }, children: review.review_text })] }));
}
