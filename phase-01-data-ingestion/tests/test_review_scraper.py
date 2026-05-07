"""Unit tests for review scraper logic."""

from unittest.mock import patch
from datetime import datetime

from backend.scrapers.review_scraper import scrape_reviews


class TestReviewScraper:

    @patch("backend.scrapers.review_scraper.reviews")
    def test_returns_mapped_reviews(self, mock_reviews):
        mock_reviews.return_value = (
            [
                {
                    "reviewId": "rev1",
                    "userName": "User A",
                    "score": 5,
                    "content": "Great app!",
                    "at": datetime(2026, 5, 4),
                    "thumbsUpCount": 10,
                    "reviewCreatedVersion": "6.2.1",
                },
                {
                    "reviewId": "rev2",
                    "userName": "User B",
                    "score": 2,
                    "content": "Crashes often.",
                    "at": datetime(2026, 5, 3),
                    "thumbsUpCount": 3,
                    "reviewCreatedVersion": "6.2.0",
                },
            ],
            None,
        )

        result = scrape_reviews(app_id="test.app", count=10)
        assert len(result) == 2
        assert result[0]["review_id"] == "rev1"
        assert result[0]["rating"] == 5
        assert result[0]["review_date"] == "2026-05-04"
        assert result[1]["review_id"] == "rev2"

    @patch("backend.scrapers.review_scraper.reviews")
    def test_deduplicates_by_review_id(self, mock_reviews):
        mock_reviews.return_value = (
            [
                {"reviewId": "dup1", "userName": "A", "score": 4, "content": "ok", "at": None, "thumbsUpCount": 0, "reviewCreatedVersion": None},
                {"reviewId": "dup1", "userName": "A", "score": 4, "content": "ok", "at": None, "thumbsUpCount": 0, "reviewCreatedVersion": None},
            ],
            None,
        )

        result = scrape_reviews(app_id="test.app", count=10)
        assert len(result) == 1

    @patch("backend.scrapers.review_scraper.reviews")
    def test_skips_empty_review_id(self, mock_reviews):
        mock_reviews.return_value = (
            [
                {"reviewId": "", "userName": "A", "score": 3, "content": "meh", "at": None, "thumbsUpCount": 0, "reviewCreatedVersion": None},
                {"reviewId": "real1", "userName": "B", "score": 5, "content": "good", "at": None, "thumbsUpCount": 0, "reviewCreatedVersion": None},
            ],
            None,
        )

        result = scrape_reviews(app_id="test.app", count=10)
        assert len(result) == 1
        assert result[0]["review_id"] == "real1"

    @patch("backend.scrapers.review_scraper.reviews")
    def test_handles_api_failure(self, mock_reviews):
        mock_reviews.side_effect = Exception("API rate limited")
        result = scrape_reviews(app_id="test.app", count=10)
        assert result == []

    @patch("backend.scrapers.review_scraper.reviews")
    def test_empty_response(self, mock_reviews):
        mock_reviews.return_value = ([], None)
        result = scrape_reviews(app_id="test.app", count=10)
        assert result == []
