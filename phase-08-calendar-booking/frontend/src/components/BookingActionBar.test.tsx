import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { BookingActionBar } from "../components/BookingActionBar";

const baseBooking = {
  id: "1",
  booking_code: "BK-20260507-001",
  user_id: "u",
  topic: "ELSS",
  scheduled_at: "2026-05-10T10:00:00Z",
  duration_minutes: 30,
  calendar_event_id: "e1",
  approval_id: "a1",
  created_at: "2026-05-07T00:00:00Z",
  updated_at: "2026-05-07T00:00:00Z",
  previous_scheduled_at: null,
};

describe("BookingActionBar", () => {
  it("disables Send Email until confirmed", () => {
    render(
      <BookingActionBar
        booking={{ ...baseBooking, status: "pending" }}
        pulseAvailable={false}
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
        onSendEmail={async () => {}}
      />,
    );
    expect(screen.getByRole("button", { name: /send email/i })).toBeDisabled();
  });

  it("enables Send Email when confirmed", () => {
    render(
      <BookingActionBar
        booking={{ ...baseBooking, status: "confirmed" }}
        pulseAvailable={true}
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
        onSendEmail={async () => {}}
      />,
    );
    expect(screen.getByRole("button", { name: /send email/i })).toBeEnabled();
  });

  it("opens confirm modal", async () => {
    const user = userEvent.setup();
    render(
      <BookingActionBar
        booking={{ ...baseBooking, status: "confirmed" }}
        pulseAvailable={true}
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
        onSendEmail={async () => {}}
      />,
    );
    await user.click(screen.getByRole("button", { name: /send email/i }));
    expect(screen.getByRole("heading", { name: /send booking email/i })).toBeInTheDocument();
  });
});
