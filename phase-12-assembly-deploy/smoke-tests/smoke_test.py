"""Minimal smoke checks for deployed phase-12 endpoints.

Usage:
  BACKEND_BASE_URL=https://your-render-url.onrender.com python smoke_test.py
"""

from __future__ import annotations

import os
import sys

import httpx


def _check(url: str) -> bool:
    try:
        r = httpx.get(url, timeout=15)
        print(f"{url} -> {r.status_code}")
        return r.status_code < 500
    except Exception as exc:
        print(f"{url} -> error: {exc}")
        return False


def main() -> int:
    base = os.getenv("BACKEND_BASE_URL", "").rstrip("/")
    if not base:
        print("Missing BACKEND_BASE_URL")
        return 2

    checks = [
        f"{base}/health",
        f"{base}/health/details",
    ]
    ok = all(_check(url) for url in checks)
    print("SMOKE RESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
