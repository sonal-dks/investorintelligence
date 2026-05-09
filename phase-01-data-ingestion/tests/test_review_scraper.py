"""Unit tests for review scraper logic."""

from unittest.mock import patch
from datetime import datetime, timezone, timedelta

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
                    "content": "Great app for investing and tracking portfolio performance.",
                    "at": datetime(2026, 5, 4),
                    "thumbsUpCount": 10,
                    "reviewCreatedVersion": "6.2.1",
                },
                {
                    "reviewId": "rev2",
                    "userName": "User B",
                    "score": 2,
                    "content": "App crashes often after update and needs urgent fixes.",
                    "at": datetime(2026, 5, 3),
                    "thumbsUpCount": 3,
                    "reviewCreatedVersion": "6.2.0",
                },
            ],
            None,
        )

        result = scrape_reviews(app_id="test.app", count=10, lookback_days=365)
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

        result = scrape_reviews(app_id="test.app", count=10, lookback_days=365)
        assert len(result) == 0

    @patch("backend.scrapers.review_scraper.reviews")
    def test_skips_empty_review_id(self, mock_reviews):
        mock_reviews.return_value = (
            [
                {"reviewId": "", "userName": "A", "score": 3, "content": "meh", "at": None, "thumbsUpCount": 0, "reviewCreatedVersion": None},
                {"reviewId": "real1", "userName": "B", "score": 5, "content": "This app is good and useful for long term investing.", "at": None, "thumbsUpCount": 0, "reviewCreatedVersion": None},
            ],
            None,
        )

        result = scrape_reviews(app_id="test.app", count=10, lookback_days=365)
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

    @patch("backend.scrapers.review_scraper.reviews")
    def test_filters_old_non_english_profanity_and_short(self, mock_reviews):
        now = datetime.now(timezone.utc)
        mock_reviews.return_value = (
            [
                {
                    "reviewId": "ok1",
                    "userName": "U1",
                    "score": 5,
                    "content": "Very good app for investing and tracking portfolios.",
                    "at": now - timedelta(days=5),
                    "thumbsUpCount": 0,
                    "reviewCreatedVersion": "1.0.0",
                },
                {
                    "reviewId": "old1",
                    "userName": "U2",
                    "score": 5,
                    "content": "Very good app for investing and tracking portfolios.",
                    "at": now - timedelta(days=120),
                    "thumbsUpCount": 0,
                    "reviewCreatedVersion": "1.0.0",
                },
                {
                    "reviewId": "short1",
                    "userName": "U3",
                    "score": 4,
                    "content": "Nice app",
                    "at": now - timedelta(days=3),
                    "thumbsUpCount": 0,
                    "reviewCreatedVersion": "1.0.0",
                },
                {
                    "reviewId": "bad1",
                    "userName": "U4",
                    "score": 1,
                    "content": "This app is fucking useless and always broken.",
                    "at": now - timedelta(days=2),
                    "thumbsUpCount": 0,
                    "reviewCreatedVersion": "1.0.0",
                },
                {
                    "reviewId": "noneng1",
                    "userName": "U5",
                    "score": 4,
                    "content": "bahut accha hai ye app mujhe pasand aaya",
                    "at": now - timedelta(days=1),
                    "thumbsUpCount": 0,
                    "reviewCreatedVersion": "1.0.0",
                },
            ],
            None,
        )
        result = scrape_reviews(app_id="test.app", count=50, lookback_days=60)
        assert [r["review_id"] for r in result] == ["ok1"]

    @patch("backend.scrapers.review_scraper.reviews")
    def test_paginates_beyond_initial_count(self, mock_reviews):
        now = datetime.now(timezone.utc)
        mock_reviews.side_effect = [
            (
                [
                    {
                        "reviewId": "p1",
                        "userName": "U1",
                        "score": 5,
                        "content": "Excellent app for long term investing and goal planning.",
                        "at": now - timedelta(days=1),
                        "thumbsUpCount": 0,
                        "reviewCreatedVersion": "1.0.0",
                    }
                ],
                "token1",
            ),
            (
                [
                    {
                        "reviewId": "p2",
                        "userName": "U2",
                        "score": 4,
                        "content": "Useful app with smooth navigation and clear portfolio data.",
                        "at": now - timedelta(days=2),
                        "thumbsUpCount": 0,
                        "reviewCreatedVersion": "1.0.0",
                    }
                ],
                None,
            ),
        ]
        result = scrape_reviews(app_id="test.app", count=1, lookback_days=60)
        assert [r["review_id"] for r in result] == ["p1", "p2"]
