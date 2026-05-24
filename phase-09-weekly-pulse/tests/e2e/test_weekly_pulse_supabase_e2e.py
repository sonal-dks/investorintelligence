"""Full-stack Weekly Pulse against live Supabase; isolated subprocess (fresh config cache)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

PHASE09_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = PHASE09_ROOT / "scripts" / "e2e_weekly_pulse_supabase.py"


@pytest.mark.e2e
def test_weekly_pulse_supabase_subprocess_e2e():
    if os.getenv("RUN_PULSE_E2E", "").lower() not in ("1", "true", "yes"):
        pytest.skip("Set RUN_PULSE_E2E=1 to run live Supabase E2E (needs credentials + >=10 reviews this week).")

    env = os.environ.copy()
    env.pop("PHASE09_DISABLE_SUPABASE", None)

    r = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=str(PHASE09_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert r.returncode == 0, f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}"
