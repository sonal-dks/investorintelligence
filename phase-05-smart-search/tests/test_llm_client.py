"""Tests for LLMClient — fallback behavior, error handling, usage parsing."""

from unittest.mock import MagicMock, patch

import pytest

from backend.services.llm_client import LLMClient


@pytest.fixture
def client():
    return LLMClient(
        api_key="test-key",
        primary_model="test/primary",
        fallback_model="test/fallback",
        max_tokens=100,
    )


def _ok_response(content: str, usage: dict | None = None) -> MagicMock:
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = {
        "choices": [{"message": {"content": content}}],
        "usage": usage or {},
    }
    return resp


class TestLLMGeneration:
    @patch("backend.services.llm_client.httpx.post")
    def test_primary_model_success(self, mock_post: MagicMock, client: LLMClient):
        mock_post.return_value = _ok_response(
            "Test response",
            {
                "prompt_tokens": 120,
                "completion_tokens": 30,
                "total_tokens": 150,
                "cost": 0.00045,
                "cost_details": {"upstream_inference_cost": 0.00045},
            },
        )

        result = client.generate([{"role": "user", "content": "hi"}])
        assert result.text == "Test response"
        assert result.model == "test/primary"
        assert result.prompt_tokens == 120
        assert result.completion_tokens == 30
        assert result.total_tokens == 150
        assert result.cost_usd == pytest.approx(0.00045)
        assert result.cost_details == {"upstream_inference_cost": 0.00045}

    @patch("backend.services.llm_client.httpx.post")
    def test_fallback_on_primary_failure(self, mock_post: MagicMock, client: LLMClient):
        primary_fail = MagicMock()
        primary_fail.raise_for_status.side_effect = Exception("Primary failed")

        mock_post.side_effect = [primary_fail, _ok_response("Fallback response")]

        result = client.generate([{"role": "user", "content": "hi"}])
        assert result.text == "Fallback response"
        assert result.model == "test/fallback"
        assert result.prompt_tokens == 0
        assert result.cost_usd == 0.0

    @patch("backend.services.llm_client.httpx.post")
    def test_error_response_when_all_fail(self, mock_post: MagicMock, client: LLMClient):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = Exception("Failed")
        mock_post.return_value = mock_resp

        result = client.generate([{"role": "user", "content": "hi"}])
        assert "technical difficulties" in result.text.lower()
        assert result.model == "none"
        assert result.total_tokens == 0
        assert result.cost_usd == 0.0

    @patch("backend.services.llm_client.httpx.post")
    def test_missing_usage_defaults_to_zero(self, mock_post: MagicMock, client: LLMClient):
        mock_post.return_value = _ok_response("ok")

        result = client.generate([{"role": "user", "content": "hi"}])
        assert result.text == "ok"
        assert result.prompt_tokens == 0
        assert result.completion_tokens == 0
        assert result.cost_usd == 0.0
