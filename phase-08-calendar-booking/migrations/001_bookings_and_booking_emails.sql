-- Phase 08: bookings + booking_emails audit (apply in Supabase SQL editor)

create table if not exists public.bookings (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  booking_code text not null unique,
  topic text not null,
  scheduled_at timestamptz not null,
  duration_minutes int not null check (duration_minutes >= 1 and duration_minutes <= 480),
  status text not null check (status in ('pending', 'confirmed', 'cancelled', 'rescheduled', 'pending_calendar')),
  calendar_event_id text,
  approval_id text not null,
  previous_scheduled_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_bookings_user_status on public.bookings (user_id, status);
create index if not exists idx_bookings_approval on public.bookings (approval_id);

create table if not exists public.booking_emails (
  id uuid primary key default gen_random_uuid(),
  booking_id uuid not null references public.bookings (id) on delete cascade,
  status_at_send text not null,
  recipient_role text not null check (recipient_role in ('user', 'advisor')),
  recipient_email text not null,
  subject text not null,
  body_markdown text not null,
  body_html text not null,
  idempotency_key text not null,
  gmail_message_id text,
  send_status text not null check (send_status in ('sent', 'failed', 'pending')),
  error_message text,
  sent_at timestamptz not null default now(),
  sent_by uuid references auth.users (id),
  unique (booking_id, status_at_send, recipient_role)
);

create index if not exists idx_booking_emails_booking on public.booking_emails (booking_id);
