"""Unit/integration tests: in-memory pulse store unless E2E overrides (see tests/e2e/)."""

from __future__ import annotations

import os

# Always isolate unit/API tests from live Supabase (override user shell env).
os.environ["PHASE09_DISABLE_SUPABASE"] = "1"
# Block OpenRouter for unit tests even if phase .env would load a key (dotenv does not override set vars).
os.environ["OPENROUTER_API_KEY"] = ""
