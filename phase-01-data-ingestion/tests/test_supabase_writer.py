"""Unit tests for SupabaseWriter with mocked Supabase client."""

import pytest
from unittest.mock import patch, MagicMock

from backend.models.schemas import FundData, ReviewData
from backend.db.supabase_writer import write_to_supabase, _serialize


class TestSerialize:

    def test_serializes_fund_data(self):
        fund = FundData(
            fund_slug="test-fund",
            fund_name="Test Fund",
            category="Large Cap",
            nav=100.0,
            source_url="https://example.com",
        )
        result = _serialize([fund])
        assert len(result) == 1
        assert result[0]["fund_slug"] == "test-fund"
        assert isinstance(result[0]["scraped_at"], str)

    def test_serializes_review_data(self):
        review = ReviewData(
            review_id="rev1",
            rating=4,
        )
        result = _serialize([review])
        assert len(result) == 1
        assert result[0]["review_id"] == "rev1"

    def test_empty_list(self):
        assert _serialize([]) == []


class TestWriteToSupabase:

    @pytest.mark.asyncio
    @patch("backend.db.supabase_writer._get_client")
    async def test_successful_insert(self, mock_get_client):
        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_insert = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [{"id": "1"}, {"id": "2"}]

        mock_client.table.return_value = mock_table
        mock_table.insert.return_value = mock_insert
        mock_insert.execute.return_value = mock_response
        mock_get_client.return_value = mock_client

        funds = [
            FundData(fund_slug="f1", fund_name="Fund 1", category="Large Cap", nav=100, source_url="https://example.com"),
            FundData(fund_slug="f2", fund_name="Fund 2", category="Mid Cap", nav=200, source_url="https://example.com"),
        ]
        result = await write_to_supabase(funds, "mutual_fund_data")
        assert result.inserted == 2
        assert result.failed == 0

    @pytest.mark.asyncio
    @patch("backend.db.supabase_writer._get_client")
    async def test_batch_failure_continues(self, mock_get_client):
        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_insert = MagicMock()
        mock_insert.execute.side_effect = Exception("Supabase error")

        mock_client.table.return_value = mock_table
        mock_table.insert.return_value = mock_insert
        mock_get_client.return_value = mock_client

        funds = [
            FundData(fund_slug="f1", fund_name="Fund 1", category="Large Cap", nav=100, source_url="https://example.com"),
        ]
        result = await write_to_supabase(funds, "mutual_fund_data")
        assert result.inserted == 0
        assert result.failed == 1
        assert len(result.errors) == 1

    @pytest.mark.asyncio
    @patch("backend.db.supabase_writer._get_client")
    async def test_empty_data_skips(self, mock_get_client):
        result = await write_to_supabase([], "mutual_fund_data")
        assert result.inserted == 0
        assert result.failed == 0
        mock_get_client.assert_not_called()
