#!/usr/bin/env python3
"""
One-time OAuth to mint GMAIL_REFRESH_TOKEN (sign in as kumarsonal100@gmail.com).

Google Cloud Console → APIs & Services → Credentials → OAuth 2.0 Client (Web):
  - Add Authorized redirect URI: http://localhost:8765/

Enable Gmail API for project radiant-tide-495605-d1.

Usage (from phase-08-calendar-booking):
  PYTHONPATH=. ./venv/bin/python scripts/gmail_oauth_refresh_token.py

Paste the printed line into .env.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = ROOT.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402
from google_auth_oauthlib.flow import InstalledAppFlow  # noqa: E402

load_dotenv(ROOT / ".env", override=False)

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.compose",
]

REDIRECT_PORT = 8765

# Default Web client JSON at repo root (Final project/)
_DEFAULT_SECRET = (
    REPO_ROOT / "client_secret_641330500970-nb8k5i1jctpaotl66o54ea4slmchg56o.apps.googleusercontent.com.json"
)


def main() -> None:
    cid = os.getenv("GMAIL_CLIENT_ID")
    secret = os.getenv("GMAIL_CLIENT_SECRET")
    if not cid or not secret:
        if _DEFAULT_SECRET.is_file():
            data = json.loads(_DEFAULT_SECRET.read_text())
            web = data.get("web") or {}
            cid = web.get("client_id")
            secret = web.get("client_secret")
    if not cid or not secret:
        print("Set GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET in .env", file=sys.stderr)
        sys.exit(1)

    client_config = {
        "installed": {
            "client_id": cid,
            "client_secret": secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [f"http://localhost:{REDIRECT_PORT}/"],
        }
    }

    flow = InstalledAppFlow.from_client_config(client_config, scopes=SCOPES)
    print(
        f"\n1) Confirm this redirect URI is added to your OAuth Web client:\n"
        f"     http://localhost:{REDIRECT_PORT}/\n"
        f"2) Browser will open — sign in as {os.getenv('GMAIL_FROM_ADDRESS', 'your Gmail')}\n"
    )
    creds = flow.run_local_server(port=REDIRECT_PORT, prompt="consent", access_type="offline")
    if not creds.refresh_token:
        print(
            "No refresh_token. In Google Account → Security → Third-party access, remove this app and re-run.",
            file=sys.stderr,
        )
        sys.exit(1)
    print("\n--- Add to phase-08-calendar-booking/.env ---\n")
    print(f'GMAIL_REFRESH_TOKEN={creds.refresh_token}')
    print("\n--- End ---\n")


if __name__ == "__main__":
    main()
