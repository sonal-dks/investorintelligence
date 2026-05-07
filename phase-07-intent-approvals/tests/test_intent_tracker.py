from backend.models.schemas import Intent
from backend.services.intent_tracker import IntentTracker


def test_tracker_handles_detect_confirm_cancel():
    tracker = IntentTracker()
    session_id = 's1'
    base = Intent(
        type='booking',
        confidence=0.8,
        details={'topic': 'SIP review', 'time_preference': 'next week'},
        status='detected',
    )

    _, first = tracker.track(session_id, [base])
    assert first[0].to_status == 'detected'

    confirmed = base.model_copy(update={'status': 'confirmed', 'confidence': 0.91})
    _, second = tracker.track(session_id, [confirmed])
    assert second[0].from_status == 'detected'
    assert second[0].to_status == 'confirmed'

    cancelled = base.model_copy(update={'status': 'cancelled', 'confidence': 0.95})
    _, third = tracker.track(session_id, [cancelled])
    assert third[0].from_status == 'confirmed'
    assert third[0].to_status == 'cancelled'
