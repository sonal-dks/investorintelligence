const base = () => import.meta.env.VITE_API_BASE ?? "";

export type Booking = {
  id: string;
  booking_code: string;
  user_id: string;
  topic: string;
  scheduled_at: string;
  duration_minutes: number;
  status: "pending" | "confirmed" | "cancelled" | "rescheduled" | "pending_calendar";
  calendar_event_id: string | null;
  approval_id: string;
  created_at: string;
  updated_at: string;
  previous_scheduled_at: string | null;
};

const adminHeaders = { "x-user-role": "admin" };

export async function fetchPulseAvailable(): Promise<boolean> {
  const r = await fetch(`${base()}/api/bookings/meta/pulse-available`);
  if (!r.ok) return false;
  const j = await r.json();
  return Boolean(j.available);
}

export async function fetchCalendarIframe(): Promise<string | null> {
  const r = await fetch(`${base()}/api/calendar/iframe-url`);
  if (!r.ok) return null;
  const j = await r.json();
  return j.url ?? null;
}

export async function fetchBookings(): Promise<Booking[]> {
  const r = await fetch(`${base()}/api/bookings`);
  if (!r.ok) throw new Error("bookings");
  return r.json();
}

export async function confirmBooking(id: string, approvalId: string): Promise<Booking> {
  const r = await fetch(`${base()}/api/bookings/${id}/confirm?approval_id=${encodeURIComponent(approvalId)}`, {
    method: "PATCH",
    headers: adminHeaders,
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function cancelBooking(id: string, approvalId: string): Promise<Booking> {
  const r = await fetch(`${base()}/api/bookings/${id}/cancel?approval_id=${encodeURIComponent(approvalId)}`, {
    method: "PATCH",
    headers: adminHeaders,
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function sendBookingEmail(id: string): Promise<unknown> {
  const r = await fetch(`${base()}/api/bookings/${id}/send-email`, {
    method: "POST",
    headers: adminHeaders,
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function fetchBookingEmails(id: string): Promise<{
  booking_id: string;
  history: Array<{
    status_at_send: string;
    recipient_role: string;
    recipient_email: string;
    subject: string;
    sent_at: string;
    gmail_message_id: string | null;
    sent_by: string;
    idempotency_key: string;
  }>;
}> {
  const r = await fetch(`${base()}/api/bookings/${id}/emails`, { headers: adminHeaders });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}
