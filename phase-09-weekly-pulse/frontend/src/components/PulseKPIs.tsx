type Props = {
  overallRating: number;
  totalReviews: number;
  positiveCount: number;
  negativeCount: number;
};

export function PulseKPIs(props: Props) {
  return (
    <section style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 12 }}>
      <Kpi label="Overall Rating" value={props.overallRating.toFixed(2)} />
      <Kpi label="New Reviews" value={String(props.totalReviews)} />
      <Kpi label="Positive" value={String(props.positiveCount)} />
      <Kpi label="Negative" value={String(props.negativeCount)} />
    </section>
  );
}

function Kpi({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ border: "1px solid #ddd", borderRadius: 8, padding: 12 }}>
      <div style={{ fontSize: 12, color: "#666" }}>{label}</div>
      <div style={{ fontSize: 20, fontWeight: 600 }}>{value}</div>
    </div>
  );
}
