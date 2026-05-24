# Booking Confirmation Email Template

This is the single source of truth for the booking-confirmation email sent by the Phase 08 email extension. It is loaded at runtime by `EmailTemplateRenderer` and rendered twice per send — once for the user, once for the advisor. Edit freely; the renderer only cares about the named blocks (`<!-- block:NAME -->` ... `<!-- endblock -->`) and the `{placeholder}` tokens listed at the bottom.

> **Edit guidance:**
> - Keep block names exactly as shown.
> - You can reorder placeholders inside a block, add prose, or reword anything.
> - Two intro blocks exist (`intro_user`, `intro_advisor`); the renderer picks the one matching the recipient role.
> - The `pulse_block` is dropped at render time when no recent Weekly Pulse exists. A one-line footnote is appended automatically — you do not need to add a fallback yourself.
> - Status-specific copy (booked / cancelled / rescheduled) is selected by `{status}` substitution; tweak the wording in `booking_details` to fit.

---

<!-- block:subject_user -->
{newsletter_subject}
<!-- endblock -->

<!-- block:subject_advisor -->
{newsletter_subject}
<!-- endblock -->

---

<!-- block:intro_user -->
Hi {user_name},

Quick update on your appointment with our advisor.

- **Status:** {status}
- **Booking code:** `{booking_code}`
- **Topic:** {topic}
- **When:** {scheduled_at_local} ({duration_minutes} min)

If anything looks off, reply to this email and we will sort it out.
<!-- endblock -->

<!-- block:intro_advisor -->
Hi {advisor_name},

A booking on your calendar just changed state — full details below, including the latest Weekly Pulse so you can walk into the conversation with current product context.
<!-- endblock -->

---

<!-- block:booking_details -->
## Booking details

| Field | Value |
|------|------|
| Status | **{status}** |
| Booking code | `{booking_code}` |
| User | {user_name} ({user_email}) |
| Advisor | {advisor_name} ({advisor_email}) |
| Topic | {topic} |
| Scheduled at | {scheduled_at_local} |
| Duration | {duration_minutes} min |
| Calendar event | {calendar_event_link} |

> If the booking was **rescheduled**, the value above is the new time. The previous time was {previous_scheduled_at_local}.
> If the booking was **cancelled**, the calendar event has been removed.
<!-- endblock -->

---

<!-- block:pulse_block -->
## Weekly pulse ({pulse_week_start})

{pulse_summary}

**Top themes this week**
{top_themes}

**Judge score**
- Overall: {pulse_judge_score}/100
- Breakdown: {pulse_judge_metrics}

**Three things we are acting on**
1. {pulse_action_item_1}
2. {pulse_action_item_2}
3. {pulse_action_item_3}

## Fee explanation
{fee_scenario}

{fee_explanation_bullets}

**Attached:** Weekly Pulse PDF  
Doc link: {pulse_doc_url}

_Pulse generated at {pulse_generated_at}._
<!-- endblock -->

---

<!-- block:footer -->
You are receiving this because you are involved in this booking. The Next Leap team will use the booking code above for any follow-ups.

— Next Leap
<!-- endblock -->

---

## Available placeholders

The renderer substitutes the following tokens. Tokens that have no value at send time are replaced with an empty string (or the block they sit in is dropped, for `pulse_block`).

| Placeholder | Source | Notes |
|------------|--------|-------|
| `{user_name}` | Supabase auth `user_metadata.full_name`, fallback `user_metadata.name`, fallback the part of email before `@` | |
| `{user_email}` | Supabase auth `auth.users.email` of the booking owner | |
| `{advisor_name}` | Static config (defaults to "Advisor") | |
| `{advisor_email}` | Env var `ADVISOR_EMAIL` | |
| `{status}` | One of `confirmed`, `cancelled`, `rescheduled` | Lower-cased verbatim from `bookings.status` |
| `{booking_code}` | `bookings.booking_code` | |
| `{topic}` | `bookings.topic` | |
| `{scheduled_at_local}` | `bookings.scheduled_at` rendered in IST (Asia/Kolkata) | |
| `{previous_scheduled_at_local}` | Previous `scheduled_at` if the booking was rescheduled, else empty | |
| `{duration_minutes}` | `bookings.duration_minutes` | |
| `{calendar_event_link}` | Google Calendar event html link, if available | |
| `{pulse_week_start}` | `weekly_pulse.week_start` | Whole `pulse_block` is dropped if no recent pulse |
| `{pulse_summary}` | `weekly_pulse.summary_text` (≤250 words) | |
| `{pulse_action_item_1..3}` | `weekly_pulse.action_items[0..2]` | |
| `{top_themes}` | Bulleted list rendered from `weekly_pulse.themes` | |
| `{pulse_generated_at}` | `weekly_pulse.generated_at` | |
