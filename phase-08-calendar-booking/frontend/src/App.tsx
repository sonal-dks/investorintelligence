import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { BookingActionBar } from "./components/BookingActionBar";
import { BookingEmailHistory } from "./components/BookingEmailHistory";
import { BookingStatusBadge } from "./components/BookingStatusBadge";
import { CalendarTab } from "./components/CalendarTab";
import {
  cancelBooking,
  confirmBooking,
  fetchBookings,
  fetchPulseAvailable,
  sendBookingEmail,
} from "./lib/api";

export function App() {
  const qc = useQueryClient();
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const bookingsQ = useQuery({ queryKey: ["bookings"], queryFn: fetchBookings });
  const pulseQ = useQuery({ queryKey: ["pulse"], queryFn: fetchPulseAvailable });

  const selected = useMemo(
    () => bookingsQ.data?.find((b) => b.id === selectedId) ?? null,
    [bookingsQ.data, selectedId],
  );

  const mConfirm = useMutation({
    mutationFn: () => {
      if (!selected) throw new Error("none");
      return confirmBooking(selected.id, selected.approval_id);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["bookings"] }),
  });

  const mCancel = useMutation({
    mutationFn: () => {
      if (!selected) throw new Error("none");
      return cancelBooking(selected.id, selected.approval_id);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["bookings"] }),
  });

  const mSend = useMutation({
    mutationFn: async () => {
      if (!selected) throw new Error("none");
      await sendBookingEmail(selected.id);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["bookings"] });
      qc.invalidateQueries({ queryKey: ["booking-emails"] });
    },
  });

  return (
    <div style={{ padding: 24, maxWidth: 1100, margin: "0 auto" }}>
      <h1 style={{ marginTop: 0 }}>Phase 08 — Calendar & bookings</h1>
      <p style={{ color: "#475569", fontSize: "0.95rem" }}>
        Point <code>VITE_API_BASE</code> at the Phase 08 API (e.g. <code>http://127.0.0.1:8090</code>). Admin actions use{" "}
        <code>x-user-role: admin</code> (set in API client).
      </p>

      <div style={{ display: "grid", gap: 24, gridTemplateColumns: "1fr 1fr" }}>
        <section>
          <h2>Calendar</h2>
          <CalendarTab />
        </section>
        <section>
          <h2>Bookings</h2>
          {bookingsQ.isLoading && <p>Loading…</p>}
          {bookingsQ.isError && <p style={{ color: "#b91c1c" }}>Failed to load bookings.</p>}
          <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
            {(bookingsQ.data ?? []).map((b) => (
              <li key={b.id}>
                <button
                  type="button"
                  onClick={() => setSelectedId(b.id)}
                  style={{
                    width: "100%",
                    textAlign: "left",
                    marginBottom: 6,
                    border: selectedId === b.id ? "2px solid #0f766e" : "1px solid #e2e8f0",
                    background: selectedId === b.id ? "#ecfdf5" : "#fff",
                  }}
                >
                  <strong>{b.booking_code}</strong> · {b.topic}
                  <div style={{ marginTop: 4 }}>
                    <BookingStatusBadge status={b.status} />
                  </div>
                </button>
              </li>
            ))}
          </ul>
          {!bookingsQ.data?.length && !bookingsQ.isLoading && (
            <p style={{ color: "#64748b", fontSize: "0.9rem" }}>
              No bookings yet. Create one via <code>POST /api/bookings</code> (admin).
            </p>
          )}
        </section>
      </div>

      <section style={{ marginTop: 24 }}>
        <h2>Booking detail</h2>
        {selected && (
          <div style={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: 8, padding: 16 }}>
            <p>
              <strong>Code:</strong> {selected.booking_code} · <BookingStatusBadge status={selected.status} />
            </p>
            <p>
              <strong>When:</strong> {selected.scheduled_at}
            </p>
            <p>
              <strong>Topic:</strong> {selected.topic}
            </p>
            <p>
              <strong>Approval:</strong> {selected.approval_id}
            </p>
            <BookingActionBar
              booking={selected}
              pulseAvailable={pulseQ.data ?? false}
              onConfirm={() => mConfirm.mutate()}
              onCancel={() => mCancel.mutate()}
              onSendEmail={async () => {
                await mSend.mutateAsync();
              }}
            />
            {(mConfirm.isError || mCancel.isError || mSend.isError) && (
              <p style={{ color: "#b91c1c", fontSize: "0.85rem" }}>Action failed — check API logs.</p>
            )}
            <BookingEmailHistory bookingId={selected.id} />
          </div>
        )}
      </section>
    </div>
  );
}
