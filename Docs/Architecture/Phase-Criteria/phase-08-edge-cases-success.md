# Phase 08: Calendar and Booking - Edge Cases and Success Criteria

> Phase 08 implements decision A5 (FastMCP action layer) and includes the booking-confirmation email sub-feature. All Calendar and Gmail side-effects flow through the in-house FastMCP `MCPActionServer`.

## Detailed Edge Cases

### Calendar (MCP-mediated)
- Calendar edge: slot conflict between availability check and event creation.
- Timing edge: timezone mismatch (stored UTC, displayed IST) causes wrong meeting time.
- Workflow edge: approval arrives without finalized booking details.
- Retry edge: API outage creates pending booking but event confirmation retries fail.
- Integrity edge: duplicate booking code under concurrent approvals.
- MCP edge: `MCPActionServer` unreachable mid-flow → BookingService surfaces "Action server unavailable" and does not partially write Supabase.
- MCP edge: tool call missing `approval_id` / `actor_id` / `idempotency_key` → MCPActionServer rejects with 400 (uniform contract per A5).

### Booking-confirmation email (Phase 08 extension)
- Pre-condition edge: admin clicks Send Email while `bookings.status != 'confirmed'` → server returns 409 even if the UI button was somehow enabled.
- Idempotency edge: admin double-clicks Send Email within the same status → second call is deduped via `UNIQUE (booking_id, status_at_send, recipient_role)`; both responses include `"deduped": true` and the original `gmail_message_id`.
- Re-send edge: status transitions confirmed → cancelled → admin sends a cancel-notice email; this is a new `status_at_send` so it is not blocked by idempotency.
- Recipient edge: user has no email recorded in Supabase auth (should not happen post-Phase-03) → server returns 422 for the user send and still attempts the advisor send.
- Recipient edge: `ADVISOR_EMAIL` env var unset or invalid → server returns 500 with "ADVISOR_EMAIL not configured" and writes nothing to `booking_emails`.
- Pulse-data edge: no Weekly Pulse generated yet, or latest pulse > 14 days old → email is rendered without the `pulse_block` and a one-line footnote is appended; `pulse_included = false` in the response.
- Template edge: template file missing or malformed (block markers not paired) → server returns 500 with template error; admin retry surfaces the same error until the file is fixed; no MCP `gmail.send` call is made.
- Transport edge: Gmail OAuth refresh token revoked → MCP `gmail.send` returns a typed auth error; `booking_emails.send_status = 'failed'`, `error_message` recorded, admin sees "Re-authorize email transport" CTA. Booking truth is unaffected.
- Transport edge: Gmail rate-limit / 429 → MCP returns retryable error; backend records failure, admin can retry; no auto-retry without admin click.
- Privacy edge: rendered HTML must not include the raw Gmail refresh token, OAuth client secret, or service account JSON in any header or body — verified by template-rendering unit test.

### UI buttons
- Cancel button is always visible for non-terminal bookings (`pending`, `confirmed`, `rescheduled`); hidden once `status = cancelled`.
- Send Email button is always rendered (so admins know the capability exists) but disabled with explanatory tooltip when `status != 'confirmed'`.
- Reschedule button opens a slot picker that re-uses MCP `calendar.check_availability` so admin sees live calendar context.

## Success Criteria

### Calendar via FastMCP
- Approved booking intents create/confirm calendar events with unique booking codes through MCP `calendar.*` tools (no direct Google Calendar REST in API code).
- Conflict handling suggests alternate slots and prevents double booking.
- Calendar hold lifecycle (pending / confirmed / cancelled / rescheduled) remains consistent across MCP tool calls and Supabase rows.
- Booking records and calendar events stay synchronized under retries.
- All executions remain approval-gated and auditable.

### Booking-confirmation email
- Send Email button is **disabled** unless `bookings.status = 'confirmed'`; disabled state is also enforced server-side (UI is not the only check).
- Send delivers exactly one email to the user (Supabase auth email) and one to `ADVISOR_EMAIL` per status snapshot, via MCP `gmail.send`.
- Each send writes one `booking_emails` row with the idempotency key `(booking_id, status_at_send, recipient_role)`.
- Same-status re-send is deduped (no second Gmail message).
- Status-change re-send (e.g. cancel-notice after a confirmed-notice) is allowed and produces a new `booking_emails` row.
- When Phase 09 has produced a Weekly Pulse within the last 14 days, the email body includes the pulse summary, three action items, and top themes; otherwise the pulse block is omitted with a single-line footnote and the rest of the email renders correctly.
- Email template is loaded from `Docs/Architecture/Email-Templates/booking_confirmation_email.md` and is editable without code changes; renderer recovers gracefully if a placeholder has no value (replaces with empty string) but fails loudly if a required block is malformed.
