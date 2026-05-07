from __future__ import annotations

import json
from pathlib import Path

from .. import config


def load_test_cases() -> list[dict]:
    path = config.project_root() / "phase-11-evaluation-suite" / "test_cases" / "hand_crafted.json"
    return json.loads(path.read_text(encoding="utf-8"))
