"""Tests for PIIDetector — covers all PII patterns and edge cases."""

import pytest

from backend.services.pii_detector import PIIDetector


@pytest.fixture
def detector():
    return PIIDetector()


class TestPANDetection:
    def test_valid_pan(self, detector: PIIDetector):
        text = "My PAN is ABCDE1234F"
        cleaned, findings = detector.scan(text)
        assert "[REDACTED_PAN]" in cleaned
        assert len(findings) == 1
        assert findings[0].pii_type == "PAN"
        assert findings[0].value == "ABCDE1234F"

    def test_pan_in_sentence(self, detector: PIIDetector):
        text = "PAN number XYZAB9876Q for tax filing"
        cleaned, findings = detector.scan(text)
        assert "[REDACTED_PAN]" in cleaned
        assert "XYZAB9876Q" not in cleaned

    def test_invalid_pan_not_detected(self, detector: PIIDetector):
        text = "This is ABCDE12345 which is not a PAN"
        cleaned, findings = detector.scan(text)
        assert len(findings) == 0
        assert cleaned == text


class TestAadhaarDetection:
    def test_aadhaar_with_spaces(self, detector: PIIDetector):
        text = "Aadhaar: 1234 5678 9012"
        cleaned, findings = detector.scan(text)
        assert "[REDACTED_AADHAAR]" in cleaned
        assert any(f.pii_type == "AADHAAR" for f in findings)

    def test_aadhaar_without_spaces(self, detector: PIIDetector):
        text = "My aadhaar 123456789012"
        cleaned, findings = detector.scan(text)
        assert "[REDACTED_AADHAAR]" in cleaned


class TestPhoneDetection:
    def test_phone_with_country_code(self, detector: PIIDetector):
        text = "Call me at +919876543210"
        cleaned, findings = detector.scan(text)
        assert "[REDACTED_PHONE]" in cleaned
        assert any(f.pii_type == "PHONE" for f in findings)

    def test_phone_without_code(self, detector: PIIDetector):
        text = "Phone: 9876543210"
        cleaned, findings = detector.scan(text)
        assert "[REDACTED_PHONE]" in cleaned

    def test_short_number_not_detected(self, detector: PIIDetector):
        text = "The NAV is 12345"
        cleaned, findings = detector.scan(text)
        phone_findings = [f for f in findings if f.pii_type == "PHONE"]
        assert len(phone_findings) == 0


class TestEmailDetection:
    def test_email(self, detector: PIIDetector):
        text = "Email me at arjun@example.com"
        cleaned, findings = detector.scan(text)
        assert "[REDACTED_EMAIL]" in cleaned
        assert any(f.pii_type == "EMAIL" for f in findings)


class TestMultiplePII:
    def test_multiple_types(self, detector: PIIDetector):
        text = "My PAN is ABCDE1234F and phone 9876543210"
        cleaned, findings = detector.scan(text)
        assert "[REDACTED_PAN]" in cleaned
        assert "[REDACTED_PHONE]" in cleaned
        assert len(findings) == 2

    def test_no_pii(self, detector: PIIDetector):
        text = "What is the exit load of Mirae Asset Large Cap Fund?"
        cleaned, findings = detector.scan(text)
        assert cleaned == text
        assert len(findings) == 0

    def test_empty_string(self, detector: PIIDetector):
        cleaned, findings = detector.scan("")
        assert cleaned == ""
        assert len(findings) == 0
