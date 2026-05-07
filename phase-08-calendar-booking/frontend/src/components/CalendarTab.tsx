import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { fetchCalendarIframe } from "../lib/api";

export function CalendarTab() {
  const q = useQuery({ queryKey: ["calendar-iframe"], queryFn: fetchCalendarIframe });
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (q.isError) setErr("Failed to load embed URL");
  }, [q.isError]);

  if (q.isLoading) return <p style={{ color: "#64748b" }}>Loading calendar…</p>;

  const url = q.data;
  if (!url) {
    return (
      <div style={{ border: "1px dashed #94a3b8", borderRadius: 8, padding: 16 }}>
        <p>No embed URL. Set GOOGLE_CALENDAR_ID on the API.</p>
        {err && <p style={{ color: "#b91c1c" }}>{err}</p>}
      </div>
    );
  }

  return (
    <iframe
      title="Advisor calendar"
      src={url}
      style={{ width: "100%", height: 420, border: "1px solid #e2e8f0", borderRadius: 8 }}
    />
  );
}
