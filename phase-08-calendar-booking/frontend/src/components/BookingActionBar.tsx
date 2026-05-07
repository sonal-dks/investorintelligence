import type { Booking } from "../lib/api";

import { SendBookingEmailButton } from "./SendBookingEmailButton";

type Props = {
  booking: Booking | null;
  pulseAvailable: boolean;
  onConfirm: () => void;
  onCancel: () => void;
  onSendEmail: () => Promise<void>;
};

export function BookingActionBar({ booking, pulseAvailable, onConfirm, onCancel, onSendEmail }: Props) {
  if (!booking) {
    return <p style={{ color: "#64748b" }}>Select a booking.</p>;
  }

  const canConfirm = booking.status === "pending" || booking.status === "pending_calendar";
  const canCancel = booking.status !== "cancelled";
  const sendDisabled = booking.status !== "confirmed";
  const sendReason = sendDisabled
    ? "Confirm the booking before sending email."
    : !pulseAvailable
      ? "Weekly Pulse not yet available — email will omit the pulse section (footnote added)."
      : "Send confirmation to user and advisor.";

  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 8, alignItems: "center" }}>
      {canConfirm && (
        <button type="button" className="primary" onClick={onConfirm}>
          Approve / Confirm
        </button>
      )}
      {canCancel && (
        <button type="button" className="danger" onClick={onCancel}>
          Cancel
        </button>
      )}
      <SendBookingEmailButton
        disabled={sendDisabled}
        disabledReason={sendReason}
        onSend={onSendEmail}
      />
      {!pulseAvailable && booking.status === "confirmed" && (
        <span style={{ fontSize: "0.75rem", color: "#b45309" }}>Pulse section omitted until Phase 09 data exists.</span>
      )}
    </div>
  );
}
