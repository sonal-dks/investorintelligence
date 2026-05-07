from __future__ import annotations

import os
from pathlib import Path

# Load local .env first (optional), then force mocks BEFORE importing backend — config reads env on import.
try:
    from dotenv import load_dotenv

    _root = Path(__file__).resolve().parent.parent
    load_dotenv(_root / ".env", override=False)
except ImportError:
    pass

os.environ["PHASE08_USE_MOCK_CALENDAR"] = "1"
os.environ["PHASE08_USE_MOCK_GMAIL"] = "1"
os.environ.setdefault("ADVISOR_EMAIL", "advisor@example.com")
os.environ.setdefault("PHASE08_TEST_USER_EMAIL", "user@example.com")
os.environ.setdefault("PHASE08_TEST_USER_NAME", "Demo User")

import pytest  # noqa: E402

from backend import deps  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_phase08_state():
    deps.reset_stores_for_tests()
    yield
