from __future__ import annotations

import base64
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from backend import config

# Scopes requested during OAuth (scripts/gmail_oauth_refresh_token.py) must cover all operations here.
_GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.compose",
]


def _gmail_credentials():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    cid = config.gmail_client_id()
    secret = config.gmail_client_secret()
    refresh = config.gmail_refresh_token()
    sender = config.gmail_from_address()
    if not all([cid, secret, refresh, sender]):
        raise RuntimeError(
            "Gmail OAuth env vars incomplete (CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN, FROM_ADDRESS)"
        )
    creds = Credentials(
        token=None,
        refresh_token=refresh,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=cid,
        client_secret=secret,
        scopes=_GMAIL_SCOPES,
    )
    creds.refresh(Request())
    return creds, sender


def send_gmail_impl(
    to_addresses: list[str],
    subject: str,
    body_markdown: str,
    body_html: str,
    idempotency_key: str,
    attachments: list[dict] | None = None,
) -> str:
    """Send email via Gmail API; returns message id."""
    _ = idempotency_key  # idempotency enforced at BookingEmailService / bridge layer

    if config.use_mock_gmail():
        return f"mock-gmail-{hash(subject) & 0xFFFFFFFF:x}"

    from googleapiclient.discovery import build

    creds, sender = _gmail_credentials()
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)

    msg = MIMEMultipart("alternative")
    msg["to"] = ", ".join(to_addresses)
    msg["from"] = sender
    msg["subject"] = subject
    msg.attach(MIMEText(body_markdown, "plain", "utf-8"))
    msg.attach(MIMEText(body_html, "html", "utf-8"))
    for a in attachments or []:
        data_b64 = str(a.get("content_base64") or "")
        if not data_b64:
            continue
        part = MIMEApplication(base64.b64decode(data_b64), _subtype="pdf")
        part.add_header("Content-Disposition", "attachment", filename=str(a.get("filename") or "attachment.pdf"))
        msg.attach(part)

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    sent = service.users().messages().send(userId="me", body={"raw": raw}).execute()
    return str(sent["id"])


def create_draft_impl(
    to_addresses: list[str],
    subject: str,
    body_markdown: str,
    body_html: str,
) -> str:
    """Create a Gmail draft (visible in Drafts). Returns draft id."""
    if config.use_mock_gmail():
        return f"mock-draft-{hash(subject) & 0xFFFFFFFF:x}"

    from googleapiclient.discovery import build

    creds, sender = _gmail_credentials()
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)

    msg = MIMEMultipart("alternative")
    msg["to"] = ", ".join(to_addresses)
    msg["from"] = sender
    msg["subject"] = subject
    msg.attach(MIMEText(body_markdown, "plain", "utf-8"))
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    draft = (
        service.users()
        .drafts()
        .create(userId="me", body={"message": {"raw": raw}})
        .execute()
    )
    return str(draft["id"])
