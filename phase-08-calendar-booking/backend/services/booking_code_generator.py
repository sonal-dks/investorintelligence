from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")


def next_booking_code(repo_count_fn) -> str:
    """repo_count_fn(yyyymmdd: str) -> int count of existing BK-YYYYMMDD-* codes for that local day."""
    now = datetime.now(IST)
    ymd = now.strftime("%Y%m%d")
    n = repo_count_fn(ymd) + 1
    if n > 999:
        raise ValueError("Daily booking code limit exceeded")
    return f"BK-{ymd}-{n:03d}"
