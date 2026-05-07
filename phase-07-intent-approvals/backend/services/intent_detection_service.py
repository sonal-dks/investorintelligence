from __future__ import annotations

from backend.models.schemas import ConversationMessage, Intent


class IntentDetectionService:
    """Deterministic fallback detector for Phase 07 testability."""

    KEYWORDS = {
        'booking': ('book', 'schedule', 'call', 'appointment'),
        'email': ('email', 'mail', 'send details'),
        'note': ('note', 'remember', 'write this down'),
        'follow_up': ('follow up', 'remind me', 'reminder'),
        'reschedule': ('reschedule', 'move to next week', 'postpone'),
        'cancel_booking': ('cancel', 'never mind', "don't book"),
    }

    def detect(self, messages: list[ConversationMessage]) -> list[Intent]:
        if not messages:
            return []
        latest = messages[-1].content.lower().strip()
        intents: list[Intent] = []

        for intent_type, keywords in self.KEYWORDS.items():
            if any(k in latest for k in keywords):
                status = 'detected'
                confidence = 0.84
                if 'yes' in latest or 'please' in latest:
                    status = 'confirmed'
                    confidence = 0.92
                if intent_type == 'cancel_booking':
                    status = 'cancelled'
                    confidence = 0.93
                if intent_type == 'reschedule':
                    status = 'modified'
                    confidence = 0.88
                intents.append(
                    Intent(
                        type=intent_type,
                        confidence=confidence,
                        details={
                            'source_message': messages[-1].content,
                            'topic': self._extract_topic(messages[-1].content),
                            'time_preference': self._extract_time_pref(messages[-1].content),
                        },
                        status=status,
                    )
                )

        if 'maybe' in latest and intents:
            for idx, item in enumerate(intents):
                intents[idx] = item.model_copy(update={'confidence': 0.55, 'status': 'detected'})

        return intents

    @staticmethod
    def _extract_topic(text: str) -> str:
        parts = text.split('about', 1)
        return parts[1].strip() if len(parts) > 1 else text[:80]

    @staticmethod
    def _extract_time_pref(text: str) -> str:
        lowered = text.lower()
        if 'next week' in lowered:
            return 'next week'
        if 'tomorrow' in lowered:
            return 'tomorrow'
        return 'unspecified'
