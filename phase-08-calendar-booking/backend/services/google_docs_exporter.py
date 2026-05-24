from __future__ import annotations

import json
import os

from backend import config


def _service_account_credentials():
    from google.oauth2 import service_account

    raw = config.google_service_account_json()
    if not raw:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON not set")
    scopes = ["https://www.googleapis.com/auth/drive.readonly"]
    if raw.strip().startswith("{"):
        info = json.loads(raw)
        return service_account.Credentials.from_service_account_info(info, scopes=scopes)
    if os.path.exists(raw):
        return service_account.Credentials.from_service_account_file(raw, scopes=scopes)
    raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON must be JSON content or a valid file path")


def export_google_doc_pdf(doc_url: str) -> bytes:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
    import io
    import re

    m = re.search(r"/document/d/([a-zA-Z0-9_-]+)", doc_url or "")
    if not m:
        raise RuntimeError("Invalid Google Doc URL for export")
    doc_id = m.group(1)
    creds = _service_account_credentials()
    drive = build("drive", "v3", credentials=creds, cache_discovery=False)
    req = drive.files().export_media(fileId=doc_id, mimeType="application/pdf")
    buf = io.BytesIO()
    downloader = MediaIoBaseDownload(buf, req)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return buf.getvalue()

