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
    <div className="mx-auto max-w-6xl space-y-4 px-4 py-4">
      <div className="rounded-xl border border-border bg-card p-5">
        <h1 className="text-xl font-semibold">Calendar & Bookings</h1>
        <p className="mt-1 text-sm text-muted-foreground">
        Point <code>VITE_API_BASE</code> at the Phase 08 API (e.g. <code>http://127.0.0.1:8090</code>). Admin actions use{" "}
        <code>x-user-role: admin</code> (set in API client).
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <section className="rounded-xl border border-border bg-card p-4">
          <h2 className="mb-3 text-sm font-semibold">Calendar</h2>
          <CalendarTab />
        </section>
        <section className="rounded-xl border border-border bg-card p-4">
          <h2 className="mb-3 text-sm font-semibold">Bookings</h2>
          {bookingsQ.isLoading && <p>Loading…</p>}
          {bookingsQ.isError && <p className="text-sm text-rose-600">Failed to load bookings.</p>}
          <ul className="m-0 list-none space-y-2 p-0">
            {(bookingsQ.data ?? []).map((b) => (
              <li key={b.id}>
                <button
                  type="button"
                  onClick={() => setSelectedId(b.id)}
                  className={`w-full rounded-lg border p-3 text-left ${
                    selectedId === b.id ? "border-primary bg-muted" : "border-border bg-background"
                  }`}
                >
                  <strong>{b.booking_code}</strong> · {b.topic}
                  <div className="mt-1">
                    <BookingStatusBadge status={b.status} />
                  </div>
                </button>
              </li>
            ))}
          </ul>
          {!bookingsQ.data?.length && !bookingsQ.isLoading && (
            <p className="text-sm text-muted-foreground">
              No bookings yet. Create one via <code>POST /api/bookings</code> (admin).
            </p>
          )}
        </section>
      </div>

      <section className="rounded-xl border border-border bg-card p-4">
        <h2 className="mb-3 text-sm font-semibold">Booking detail</h2>
        {selected && (
          <div className="rounded-lg border border-border bg-background p-4">
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
              <p className="text-xs text-rose-600">Action failed — check API logs.</p>
            )}
            <BookingEmailHistory bookingId={selected.id} />
          </div>
        )}
      </section>
    </div>
  );
}
