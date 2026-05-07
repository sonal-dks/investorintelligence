from __future__ import annotations

import uuid
from datetime import UTC, datetime

from backend.models.schemas import Approval, Intent
from backend.services.intent_tracker import IntentTracker


class ApprovalGeneratorService:
    TYPE_MAP = {
        'booking': 'booking',
        'email': 'email',
        'calendar_hold': 'calendar',
        'note': 'note',
        'follow_up': 'follow_up',
        'reschedule': 'booking',
    }

    def create(self, session_id: str, investor_id: str, investor_name: str, intent: Intent, source_type: str = 'chat') -> Approval:
        action_type = self.TYPE_MAP.get(intent.type, 'note')
        topic = str(intent.details.get('topic') or 'General request')
        intent_hash = IntentTracker.compute_hash(session_id, intent.type, intent.details)
        return Approval(
            id=str(uuid.uuid4()),
            action_type=action_type,
            title=f"{intent.type.replace('_', ' ').title()} - {topic[:50]}",
            description='Auto-generated from confirmed intent',
            investor_id=investor_id,
            investor_name=investor_name,
            status='pending',
            priority='medium',
            payload={
                'topic': topic,
                'time_preference': intent.details.get('time_preference', 'unspecified'),
                'source_message': intent.details.get('source_message', ''),
                'required_fields_ok': True,
            },
            source_session_id=session_id,
            source_type=source_type,
            created_at=datetime.now(UTC).isoformat(),
            intent_hash=intent_hash,
        )
