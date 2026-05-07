from __future__ import annotations

import hashlib
from dataclasses import dataclass

from backend.models.schemas import Intent


@dataclass
class Transition:
    intent_hash: str
    from_status: str
    to_status: str
    intent_type: str


class IntentTracker:
    def __init__(self) -> None:
        self._session_state: dict[str, dict[str, Intent]] = {}

    def track(self, session_id: str, intents: list[Intent]) -> tuple[list[Intent], list[Transition]]:
        state = self._session_state.setdefault(session_id, {})
        transitions: list[Transition] = []
        tracked: list[Intent] = []

        for intent in intents:
            intent_hash = self.compute_hash(session_id, intent.type, intent.details)
            prev = state.get(intent_hash)
            if prev is None:
                state[intent_hash] = intent
                transitions.append(Transition(intent_hash, 'none', intent.status, intent.type))
            elif prev.status != intent.status:
                transitions.append(Transition(intent_hash, prev.status, intent.status, intent.type))
                state[intent_hash] = intent
            tracked.append(intent)

        return tracked, transitions

    @staticmethod
    def compute_hash(session_id: str, intent_type: str, details: dict) -> str:
        key = f"{session_id}:{intent_type}:{details.get('topic','')}:{details.get('time_preference','')}"
        return hashlib.sha256(key.encode('utf-8')).hexdigest()[:16]
