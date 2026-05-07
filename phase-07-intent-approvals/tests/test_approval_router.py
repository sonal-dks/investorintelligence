from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_health():
    resp = client.get('/health')
    assert resp.status_code == 200
    assert resp.json()['phase'] == '07-intent-approvals'


def test_approval_flow_with_multiturn_and_cancellation():
    session = 'session-edge-1'

    detect_1 = client.post('/api/intents/detect', json={
        'session_id': session,
        'messages': [
            {'role': 'user', 'content': 'I want to book a call about ELSS next week'},
            {'role': 'assistant', 'content': 'Would you like me to set it up?'},
            {'role': 'user', 'content': 'Yes please book it next week'},
        ],
    })
    assert detect_1.status_code == 200

    approvals = client.get('/api/approvals?status=pending')
    assert approvals.status_code == 200
    assert approvals.json()['pending_count'] >= 1
    approval_id = approvals.json()['items'][0]['id']

    reject_as_investor = client.patch(f'/api/approvals/{approval_id}', json={'status': 'approved', 'reviewed_by': 'ops-1'})
    assert reject_as_investor.status_code == 403

    approve_as_admin = client.patch(
        f'/api/approvals/{approval_id}',
        json={'status': 'approved', 'reviewed_by': 'ops-1'},
        headers={'x-user-role': 'admin'},
    )
    assert approve_as_admin.status_code == 200
    assert approve_as_admin.json()['status'] == 'approved'

    # user changes mind -> cancellation should be tracked
    detect_2 = client.post('/api/intents/detect', json={
        'session_id': session,
        'messages': [
            {'role': 'user', 'content': 'Actually never mind, cancel that booking'},
        ],
    })
    assert detect_2.status_code == 200


def test_ambiguous_intent_does_not_create_approval():
    session = 'session-ambiguous'
    resp = client.post('/api/intents/detect', json={
        'session_id': session,
        'messages': [
            {'role': 'user', 'content': 'maybe schedule something sometime'},
        ],
    })
    assert resp.status_code == 200

    pending = client.get('/api/approvals?status=pending').json()
    matching = [i for i in pending['items'] if i['source_session_id'] == session]
    assert matching == []
