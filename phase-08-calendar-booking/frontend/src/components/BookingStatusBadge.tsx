import type { Booking } from "../lib/api";

const colors: Record<Booking["status"], string> = {
  pending: "#b45309",
  pending_calendar: "#b45309",
  confirmed: "#15803d",
  cancelled: "#b91c1c",
  rescheduled: "#1d4ed8",
};

export function BookingStatusBadge({ status }: { status: Booking["status"] }) {
  return (
    <span
      style={{
        display: "inline-block",
        padding: "2px 8px",
        borderRadius: 999,
        fontSize: "0.75rem",
        fontWeight: 600,
        color: "#fff",
        background: colors[status] ?? "#64748b",
      }}
    >
      {status}
    </span>
  );
}
