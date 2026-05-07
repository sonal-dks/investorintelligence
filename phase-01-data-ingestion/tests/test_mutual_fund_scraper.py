"""Unit tests for mutual fund scraper utility functions."""


from backend.scrapers.mutual_fund_scraper import (
    _slug_from_url,
    _parse_numeric,
    _parse_int,
    _parse_date,
    _classify_category,
    _normalize_risk,
)


class TestSlugFromUrl:

    def test_standard_url(self):
        url = "https://groww.in/mutual-funds/mirae-asset-large-cap-fund-direct-growth"
        assert _slug_from_url(url) == "mirae-asset-large-cap-fund-direct-growth"

    def test_trailing_slash(self):
        url = "https://groww.in/mutual-funds/some-fund/"
        assert _slug_from_url(url) == "some-fund"

    def test_url_with_query(self):
        url = "https://groww.in/mutual-funds/some-fund?ref=home"
        assert _slug_from_url(url) == "some-fund"


class TestParseNumeric:

    def test_simple_float(self):
        assert _parse_numeric("105.43") == 105.43

    def test_with_rupee_symbol(self):
        assert _parse_numeric("₹1,234.56") == 1234.56

    def test_with_commas(self):
        assert _parse_numeric("43,215.67") == 43215.67

    def test_percentage(self):
        assert _parse_numeric("0.53%") == 0.53

    def test_negative(self):
        assert _parse_numeric("-2.45%") == -2.45

    def test_none(self):
        assert _parse_numeric(None) is None

    def test_empty(self):
        assert _parse_numeric("") is None

    def test_no_number(self):
        assert _parse_numeric("N/A") is None

    def test_embedded_number(self):
        assert _parse_numeric("NAV: 105.43 as of today") == 105.43


class TestParseInt:

    def test_simple(self):
        assert _parse_int("500") == 500

    def test_with_rupee(self):
        assert _parse_int("₹1,000") == 1000

    def test_none(self):
        assert _parse_int(None) is None


class TestParseDate:

    def test_standard_format(self):
        assert _parse_date("05 May 2026") == "2026-05-05"

    def test_comma_format(self):
        assert _parse_date("05 May, 2026") == "2026-05-05"

    def test_iso_format(self):
        assert _parse_date("2026-05-05") == "2026-05-05"

    def test_none(self):
        assert _parse_date(None) is None

    def test_empty(self):
        assert _parse_date("") is None

    def test_garbage(self):
        assert _parse_date("not a date") is None


class TestClassifyCategory:

    def test_large_cap(self):
        assert _classify_category("Large Cap") == "Large Cap"

    def test_elss(self):
        assert _classify_category("ELSS Tax Saver") == "ELSS"

    def test_etf(self):
        assert _classify_category("ETF Fund of Funds") == "ETF/FOF"

    def test_sectoral(self):
        assert _classify_category("Sectoral Healthcare Fund") == "Sectoral/Thematic"

    def test_unknown(self):
        assert _classify_category("") == "Unknown"

    def test_none(self):
        assert _classify_category(None) == "Unknown"

    def test_hybrid(self):
        assert _classify_category("Aggressive Hybrid") == "Hybrid"

    def test_debt(self):
        assert _classify_category("Dynamic Bond Fund") == "Debt"


class TestNormalizeRisk:

    def test_very_high(self):
        assert _normalize_risk("Very High") == "Very High"

    def test_moderately_high(self):
        assert _normalize_risk("Moderately High") == "Moderately High"

    def test_case_insensitive(self):
        assert _normalize_risk("moderate") == "Moderate"

    def test_none(self):
        assert _normalize_risk(None) is None

    def test_empty(self):
        assert _normalize_risk("") is None

    def test_unrecognized(self):
        assert _normalize_risk("extreme") is None
