import { useQuery } from "@tanstack/react-query";

import { fetchBookingEmails } from "../lib/api";

export function BookingEmailHistory({ bookingId }: { bookingId: string | null }) {
  const q = useQuery({
    queryKey: ["booking-emails", bookingId],
    queryFn: () => fetchBookingEmails(bookingId!),
    enabled: Boolean(bookingId),
  });

  if (!bookingId) return null;
  if (q.isLoading) return <p style={{ fontSize: "0.85rem", color: "#64748b" }}>Loading email history…</p>;
  if (q.isError) return <p style={{ color: "#b91c1c" }}>Could not load email history.</p>;

  const rows = q.data?.history ?? [];
  if (!rows.length) {
    return <p style={{ fontSize: "0.85rem", color: "#64748b" }}>No confirmation emails sent yet.</p>;
  }

  return (
    <div style={{ marginTop: 12 }}>
      <h4 style={{ margin: "0 0 8px", fontSize: "0.9rem" }}>Email audit</h4>
      <ul style={{ margin: 0, paddingLeft: 18, fontSize: "0.8rem" }}>
        {rows.map((r) => (
          <li key={`${r.idempotency_key}-${r.sent_at}`}>
            <strong>{r.recipient_role}</strong> · {r.status_at_send} · {r.sent_at} · {r.recipient_email}
          </li>
        ))}
      </ul>
    </div>
  );
}
