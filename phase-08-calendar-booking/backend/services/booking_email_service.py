from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from backend import config
from backend.mcp_action_server.bridge import McpBridge
from backend.models.schemas import (
    BookingEmailHistoryItem,
    BookingEmailHistoryResponse,
    SendEmailResponse,
    SendEmailResponseSend,
)
from backend.repositories.memory import MemoryBookingEmailRepository, MemoryBookingRepository
from backend.services.email_template_renderer import EmailTemplateRenderer, format_scheduled_local, format_themes
from backend.services.google_docs_exporter import export_google_doc_pdf
from backend.services.pulse_fetcher import fetch_latest_pulse
from backend.services.user_resolver import resolve_user


class BookingEmailService:
    def __init__(
        self,
        bookings: MemoryBookingRepository,
        emails: MemoryBookingEmailRepository,
        mcp: McpBridge,
        renderer: EmailTemplateRenderer,
    ) -> None:
        self._bookings = bookings
        self._emails = emails
        self._mcp = mcp
        self._renderer = renderer

    def send_booking_email(
        self,
        booking_id: str,
        *,
        actor_id: str,
        allow_notice: bool = False,
    ) -> SendEmailResponse:
        row = self._bookings.get(booking_id)
        if row is None:
            raise ValueError("Booking not found")

        st = row["status"]
        if st == "confirmed":
            pass
        elif allow_notice and st in ("cancelled", "rescheduled"):
            pass
        else:
            raise ValueError(
                "Send email allowed only for confirmed bookings "
                "(or use notice=1 for cancelled/rescheduled)"
            )

        advisor = config.advisor_email()
        if not advisor:
            raise RuntimeError("ADVISOR_EMAIL is not configured")

        pulse = fetch_latest_pulse()
        include_pulse = pulse is not None

        user_email, user_name = resolve_user(row["user_id"])
        advisor_name = "Advisor"

        ctx_base: dict[str, str] = {
            "user_name": user_name,
            "user_email": user_email,
            "advisor_name": advisor_name,
            "advisor_email": advisor,
            "status": st,
            "booking_code": row["booking_code"],
            "topic": row["topic"],
            "scheduled_at_local": format_scheduled_local(row["scheduled_at"]),
            "duration_minutes": str(row["duration_minutes"]),
            "calendar_event_link": row.get("calendar_event_id") or "",
            "newsletter_subject": f"Weekly Pulse + Fee Explainer — {datetime.now(UTC).date().isoformat()}",
            "previous_scheduled_at_local": format_scheduled_local(row["previous_scheduled_at"])
            if row.get("previous_scheduled_at")
            else "",
        }

        if pulse:
            ctx_base["pulse_week_start"] = str(pulse.week_start or "")
            ctx_base["pulse_summary"] = pulse.summary_text
            ctx_base["top_themes"] = format_themes(pulse.themes)
            ctx_base["pulse_judge_score"] = f"{float(pulse.judge_overall_score or 0.0):.1f}"
            ctx_base["pulse_judge_metrics"] = ", ".join(
                f"{k}: {v}" for k, v in (pulse.judge_metrics or {}).items()
            )
            ctx_base["pulse_doc_url"] = pulse.doc_url or ""
            ctx_base["fee_scenario"] = pulse.fee_scenario or "Fee explanation currently unavailable."
            ctx_base["fee_explanation_bullets"] = (
                "\n".join(f"- {x}" for x in (pulse.explanation_bullets or [])[:5]) or "- (none)"
            )
            ctx_base["newsletter_subject"] = f"Weekly Pulse + Fee Explainer — {ctx_base['pulse_week_start']}"
            for i in range(3):
                key = f"pulse_action_item_{i + 1}"
                items = pulse.action_items
                ctx_base[key] = items[i] if i < len(items) else ""
            ctx_base["pulse_generated_at"] = pulse.generated_at

        pulse_raw = self._renderer.pulse_block_template()
        approval_id = row["approval_id"]
        sends: list[SendEmailResponseSend] = []
        now = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        newsletter_attachments: list[dict] = []
        if pulse and pulse.doc_url:
            try:
                pdf = export_google_doc_pdf(pulse.doc_url)
                if pdf:
                    import base64

                    newsletter_attachments = [
                        {
                            "filename": f"weekly-pulse-{ctx_base.get('pulse_week_start','latest')}.pdf",
                            "content_base64": base64.b64encode(pdf).decode("utf-8"),
                        }
                    ]
            except Exception:
                newsletter_attachments = []

        for role, to_addr in (("user", user_email), ("advisor", advisor)):
            idem = f"booking:{booking_id}:status:{st}:role:{role}"
            existing = self._emails.find(booking_id, st, role)
            if existing and existing.get("send_status") == "sent":
                sends.append(
                    SendEmailResponseSend(
                        recipient_role=role,
                        recipient_email=self._mask(to_addr),
                        gmail_message_id=existing.get("gmail_message_id"),
                        deduped=True,
                    )
                )
                continue

            rendered = self._renderer.render(
                role=role,
                ctx=ctx_base,
                include_pulse=include_pulse,
                pulse_block_raw=pulse_raw,
            )

            pending_row = {
                "id": str(uuid4()),
                "booking_id": booking_id,
                "status_at_send": st,
                "recipient_role": role,
                "recipient_email": to_addr,
                "subject": rendered.subject,
                "body_markdown": rendered.body_markdown,
                "body_html": rendered.body_html,
                "idempotency_key": idem,
                "gmail_message_id": None,
                "send_status": "pending",
                "error_message": None,
                "sent_at": now,
                "sent_by": actor_id,
            }
            if not existing:
                self._emails.append(pending_row)
            else:
                self._emails.update_by_idempotency(
                    idem,
                    {
                        "subject": rendered.subject,
                        "body_markdown": rendered.body_markdown,
                        "body_html": rendered.body_html,
                        "send_status": "pending",
                        "error_message": None,
                        "sent_at": now,
                        "sent_by": actor_id,
                    },
                )

            try:
                mid = self._mcp.gmail_send(
                    approval_id=approval_id,
                    actor_id=actor_id,
                    idempotency_key=f"gmail:{idem}",
                    to=[to_addr],
                    subject=rendered.subject,
                    body_markdown=rendered.body_markdown,
                    body_html=rendered.body_html,
                    attachments=newsletter_attachments,
                )
            except Exception as e:
                self._emails.update_by_idempotency(
                    idem,
                    {"send_status": "failed", "error_message": str(e)},
                )
                raise

            self._emails.update_by_idempotency(
                idem,
                {"send_status": "sent", "gmail_message_id": mid},
            )

            sends.append(
                SendEmailResponseSend(
                    recipient_role=role,
                    recipient_email=self._mask(to_addr),
                    gmail_message_id=mid,
                    deduped=False,
                )
            )

        return SendEmailResponse(
            booking_id=booking_id,
            status_at_send=st,
            sends=sends,
            pulse_included=include_pulse,
        )

    @staticmethod
    def _mask(email: str) -> str:
        if "@" not in email:
            return email
        u, d = email.split("@", 1)
        return f"{u[0]}***@{d}" if u else email

    def history(self, booking_id: str) -> BookingEmailHistoryResponse:
        rows = self._emails.list_for_booking(booking_id)
        hist = [
            BookingEmailHistoryItem(
                status_at_send=r["status_at_send"],
                recipient_role=r["recipient_role"],
                recipient_email=self._mask(r["recipient_email"]),
                subject=r.get("subject") or "",
                sent_at=r.get("sent_at") or "",
                gmail_message_id=r.get("gmail_message_id"),
                sent_by=r.get("sent_by") or "",
                idempotency_key=r.get("idempotency_key") or "",
            )
            for r in rows
        ]
        return BookingEmailHistoryResponse(booking_id=booking_id, history=hist)
