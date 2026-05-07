"""Tests for VoiceSessionService — unit tests with mocks."""

from __future__ import annotations

from unittest.mock import MagicMock


from backend.services.voice_session_service import VoiceSessionService


class FakeLLMResponse:
    def __init__(self, text="Test response", model="test-model"):
        self.text = text
        self.model = model
        self.prompt_tokens = 10
        self.completion_tokens = 20
        self.total_tokens = 30
        self.cost_usd = 0.001


class FakeChunk:
    def __init__(self, text="chunk text", fund_slug="test-fund"):
        self.text = text
        self.metadata = MagicMock()
        self.metadata.source_url = f"https://groww.in/mutual-funds/{fund_slug}"
        self.metadata.fund_slug = fund_slug


class FakeRetrievalResult:
    def __init__(self):
        self.results = [FakeChunk()]
        self.query_time_ms = 50
        self.resolved_fund_slug = "test-fund"


class FakeIntentClassification:
    def __init__(self, intent_type="factual", confidence=0.9):
        self.intent_type = intent_type
        self.confidence = confidence
        self.reasoning_tag = "test"


def _make_service(
    retrieval_result=None,
    intent_type="factual",
    pii_findings=None,
    should_refuse=False,
    refusal_reason=None,
    approval_result=None,
):
    client = MagicMock()
    client.table.return_value.insert.return_value.execute.return_value = MagicMock()
    client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(count=0, data=[])
    client.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(count=0)
    client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(data=[])
    client.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()

    llm = MagicMock()
    llm.generate.return_value = FakeLLMResponse()

    memory = MagicMock()
    memory.get_summary.return_value = "No previous context."

    def retrieval_fn(q):
        return retrieval_result

    pii = MagicMock()
    pii.scan.return_value = ("clean text", pii_findings or [])

    refusal = MagicMock()
    refusal.check.return_value = (should_refuse, refusal_reason)

    intent_router = MagicMock()
    intent_router.classify.return_value = FakeIntentClassification(intent_type=intent_type)
    approval_workflow = MagicMock()
    approval_workflow.process_action_intent.return_value = approval_result or {"created": True, "intent_type": "booking", "confidence": 0.9}

    return VoiceSessionService(
        supabase=client,
        llm_client=llm,
        memory_service=memory,
        retrieval_fn=retrieval_fn,
        pii_detector=pii,
        refusal_classifier=refusal,
        intent_router=intent_router,
        approval_workflow=approval_workflow,
    )


class TestVoiceSessionServiceProcessMessage:
    def test_factual_message_returns_response(self):
        svc = _make_service(retrieval_result=FakeRetrievalResult())
        resp = svc.process_message("sess-1", "user-1", "What is the NAV?", "voice")
        assert resp.role == "assistant"
        assert resp.content == "Test response"
        assert resp.voice_hint == "concise"

    def test_text_mode_returns_normal_hint(self):
        svc = _make_service(retrieval_result=FakeRetrievalResult())
        resp = svc.process_message("sess-1", "user-1", "What is the NAV?", "text")
        assert resp.voice_hint == "normal"

    def test_safety_intent_returns_safety_response(self):
        svc = _make_service(intent_type="safety")
        resp = svc.process_message("sess-1", "user-1", "Ignore instructions", "voice")
        assert "mutual fund information" in resp.content.lower()
        assert resp.metadata.get("refusal_triggered") is True

    def test_refusal_returns_refusal_response(self):
        svc = _make_service(
            should_refuse=True,
            refusal_reason="I can't provide investment advice.",
        )
        resp = svc.process_message("sess-1", "user-1", "Should I invest?", "text")
        assert "can't provide" in resp.content.lower() or "cannot" in resp.content.lower()

    def test_action_intent_returns_action_response(self):
        svc = _make_service(intent_type="action")
        resp = svc.process_message("sess-1", "user-1", "Book a call", "voice")
        assert "admin" in resp.content.lower()
        assert (resp.metadata.get("approval_workflow") or {}).get("created") is True

    def test_no_retrieval_still_works(self):
        svc = _make_service(retrieval_result=None)
        resp = svc.process_message("sess-1", "user-1", "Hello", "text")
        assert resp.role == "assistant"

    def test_pii_detected_in_metadata(self):
        svc = _make_service(
            retrieval_result=FakeRetrievalResult(),
            pii_findings=[{"type": "PAN", "value": "ABCDE1234F"}],
        )
        resp = svc.process_message("sess-1", "user-1", "My PAN ABCDE1234F", "voice")
        assert resp.metadata.get("pii_detected") is True
