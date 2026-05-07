export type Review = {
  reviewer_name: string;
  rating: number;
  review_text: string;
  review_date: string;
  sentiment: "positive" | "neutral" | "negative";
};

export function ReviewCard({ review }: { review: Review }) {
  return (
    <article style={{ border: "1px solid #ddd", borderRadius: 8, padding: 12, marginBottom: 10 }}>
      <header style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
        <strong>{review.reviewer_name}</strong>
        <span>{review.review_date}</span>
      </header>
      <div style={{ marginBottom: 8 }}>{"★".repeat(review.rating)}{"☆".repeat(5 - review.rating)}</div>
      <p style={{ margin: 0 }}>{review.review_text}</p>
    </article>
  );
}
