"""Unit tests for DataValidator — covers valid, missing fields, wrong types, extreme values."""


from backend.validators.data_validator import validate_funds, validate_reviews


# --- Fund validation fixtures ---

def _valid_fund(overrides=None):
    base = {
        "fund_slug": "mirae-asset-large-cap-fund-direct-growth",
        "fund_name": "Mirae Asset Large Cap Fund Direct Growth",
        "category": "Large Cap",
        "nav": 105.4321,
        "nav_date": "2026-05-05",
        "aum_cr": 43215.67,
        "expense_ratio": 0.53,
        "min_sip": 500,
        "risk_level": "Moderately High",
        "returns_1y": 15.67,
        "returns_3y": 12.34,
        "returns_5y": 14.89,
        "exit_load_text": "1% if redeemed within 1 year",
        "tax_text": "LTCG: 10% above ₹1L after 1 year",
        "source_url": "https://groww.in/mutual-funds/mirae-asset-large-cap-fund-direct-growth",
    }
    if overrides:
        base.update(overrides)
    return base


def _valid_review(overrides=None):
    base = {
        "review_id": "gp_review_abc123",
        "reviewer_name": "Rahul S",
        "rating": 4,
        "review_text": "Good app for mutual fund investments.",
        "review_date": "2026-05-04",
        "thumbs_up": 12,
        "app_version": "6.2.1",
    }
    if overrides:
        base.update(overrides)
    return base


class TestFundValidation:

    def test_valid_fund_passes(self):
        valid, errors = validate_funds([_valid_fund()])
        assert len(valid) == 1
        assert len(errors) == 0
        assert valid[0].fund_slug == "mirae-asset-large-cap-fund-direct-growth"

    def test_multiple_valid_funds(self):
        funds = [
            _valid_fund(),
            _valid_fund({"fund_slug": "another-fund", "fund_name": "Another Fund"}),
        ]
        valid, errors = validate_funds(funds)
        assert len(valid) == 2
        assert len(errors) == 0

    def test_missing_fund_slug(self):
        fund = _valid_fund()
        del fund["fund_slug"]
        valid, errors = validate_funds([fund])
        assert len(valid) == 0
        assert len(errors) >= 1

    def test_empty_fund_slug(self):
        valid, errors = validate_funds([_valid_fund({"fund_slug": "  "})])
        assert len(valid) == 0
        assert len(errors) >= 1

    def test_missing_fund_name(self):
        fund = _valid_fund()
        del fund["fund_name"]
        valid, errors = validate_funds([fund])
        assert len(valid) == 0
        assert len(errors) >= 1

    def test_nav_zero(self):
        """NAV must be > 0."""
        valid, errors = validate_funds([_valid_fund({"nav": 0})])
        assert len(valid) == 0
        assert len(errors) >= 1

    def test_nav_negative(self):
        valid, errors = validate_funds([_valid_fund({"nav": -10.5})])
        assert len(valid) == 0
        assert len(errors) >= 1

    def test_aum_negative(self):
        valid, errors = validate_funds([_valid_fund({"aum_cr": -1})])
        assert len(valid) == 0
        assert len(errors) >= 1

    def test_expense_ratio_too_high(self):
        valid, errors = validate_funds([_valid_fund({"expense_ratio": 15.0})])
        assert len(valid) == 0
        assert len(errors) >= 1

    def test_expense_ratio_zero(self):
        valid, errors = validate_funds([_valid_fund({"expense_ratio": 0})])
        assert len(valid) == 0
        assert len(errors) >= 1

    def test_invalid_risk_level(self):
        valid, errors = validate_funds([_valid_fund({"risk_level": "Super Duper High"})])
        assert len(valid) == 0
        assert len(errors) >= 1

    def test_all_valid_risk_levels(self):
        for level in ["Low", "Moderate", "Moderately High", "High", "Very High"]:
            valid, errors = validate_funds([_valid_fund({"risk_level": level})])
            assert len(valid) == 1, f"risk_level={level} should be valid"

    def test_nullable_fields_accepted(self):
        """Optional fields can be None."""
        fund = _valid_fund({
            "nav_date": None,
            "aum_cr": None,
            "expense_ratio": None,
            "min_sip": None,
            "risk_level": None,
            "returns_1y": None,
            "returns_5y": None,
            "exit_load_text": None,
            "tax_text": None,
        })
        valid, errors = validate_funds([fund])
        assert len(valid) == 1
        assert len(errors) == 0

    def test_wrong_type_nav_string(self):
        valid, errors = validate_funds([_valid_fund({"nav": "not-a-number"})])
        assert len(valid) == 0
        assert len(errors) >= 1

    def test_mixed_valid_and_invalid(self):
        funds = [
            _valid_fund(),
            _valid_fund({"nav": 0}),
            _valid_fund({"fund_slug": "good-fund-2", "fund_name": "Good Fund 2"}),
        ]
        valid, errors = validate_funds(funds)
        assert len(valid) == 2
        assert len(errors) >= 1

    def test_empty_list(self):
        valid, errors = validate_funds([])
        assert len(valid) == 0
        assert len(errors) == 0

    def test_large_valid_values(self):
        """Extreme but valid values."""
        fund = _valid_fund({"nav": 99999.9999, "aum_cr": 999999.99, "returns_1y": 500.0})
        valid, errors = validate_funds([fund])
        assert len(valid) == 1


class TestReviewValidation:

    def test_valid_review_passes(self):
        valid, errors = validate_reviews([_valid_review()])
        assert len(valid) == 1
        assert len(errors) == 0

    def test_missing_review_id(self):
        review = _valid_review()
        del review["review_id"]
        valid, errors = validate_reviews([review])
        assert len(valid) == 0
        assert len(errors) >= 1

    def test_empty_review_id(self):
        valid, errors = validate_reviews([_valid_review({"review_id": "  "})])
        assert len(valid) == 0
        assert len(errors) >= 1

    def test_rating_zero(self):
        valid, errors = validate_reviews([_valid_review({"rating": 0})])
        assert len(valid) == 0
        assert len(errors) >= 1

    def test_rating_six(self):
        valid, errors = validate_reviews([_valid_review({"rating": 6})])
        assert len(valid) == 0
        assert len(errors) >= 1

    def test_rating_negative(self):
        valid, errors = validate_reviews([_valid_review({"rating": -1})])
        assert len(valid) == 0
        assert len(errors) >= 1

    def test_all_valid_ratings(self):
        for r in range(1, 6):
            valid, errors = validate_reviews([_valid_review({"rating": r})])
            assert len(valid) == 1, f"rating={r} should be valid"

    def test_nullable_fields(self):
        review = _valid_review({
            "reviewer_name": None,
            "review_text": None,
            "review_date": None,
            "app_version": None,
        })
        valid, errors = validate_reviews([review])
        assert len(valid) == 1

    def test_negative_thumbs_up(self):
        valid, errors = validate_reviews([_valid_review({"thumbs_up": -1})])
        assert len(valid) == 0
        assert len(errors) >= 1

    def test_empty_list(self):
        valid, errors = validate_reviews([])
        assert len(valid) == 0
        assert len(errors) == 0

    def test_dedup_by_review_id_not_validator_job(self):
        """Validator validates each record independently; dedup is scraper's job."""
        reviews = [
            _valid_review({"review_id": "dup1"}),
            _valid_review({"review_id": "dup1"}),
        ]
        valid, errors = validate_reviews(reviews)
        assert len(valid) == 2  # validator doesn't dedup
