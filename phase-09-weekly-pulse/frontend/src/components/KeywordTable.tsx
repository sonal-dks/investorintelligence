type Row = {
  keyword: string;
  mention_count: number;
  wow_change_pct: number;
  trend: "up" | "down" | "flat";
};

export function KeywordTable({ rows }: { rows: Row[] }) {
  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th align="left">Keyword</th>
            <th align="left">Mentions</th>
            <th align="left">WoW %</th>
            <th align="left">Trend</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.keyword}>
              <td>{row.keyword}</td>
              <td>{row.mention_count}</td>
              <td style={{ color: row.wow_change_pct >= 0 ? "green" : "crimson" }}>
                {row.wow_change_pct}%
              </td>
              <td>{row.trend === "up" ? "↑" : row.trend === "down" ? "↓" : "→"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
