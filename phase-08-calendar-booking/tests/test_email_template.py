from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from backend.services.email_template_renderer import EmailTemplateRenderer, parse_blocks


MINIMAL_TEMPLATE = """
<!-- block:subject_user -->
Subj {booking_code}
<!-- endblock -->
<!-- block:subject_advisor -->
Adv {booking_code}
<!-- endblock -->
<!-- block:intro_user -->
Hi {user_name}
<!-- endblock -->
<!-- block:intro_advisor -->
Hi {advisor_name}
<!-- endblock -->
<!-- block:booking_details -->
Code {booking_code} {status}
<!-- endblock -->
<!-- block:pulse_block -->
Pulse {pulse_summary}
<!-- endblock -->
<!-- block:footer -->
End
<!-- endblock -->
"""


def test_parse_blocks_roundtrip():
    blocks = parse_blocks(MINIMAL_TEMPLATE)
    assert "subject_user" in blocks
    assert "pulse_block" in blocks


def test_render_without_pulse():
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
        f.write(MINIMAL_TEMPLATE)
        path = f.name
    try:
        r = EmailTemplateRenderer(path)
        ctx = {
            "user_name": "U",
            "advisor_name": "A",
            "user_email": "u@e.com",
            "advisor_email": "a@e.com",
            "status": "confirmed",
            "booking_code": "BK-20260507-001",
            "topic": "t",
            "scheduled_at_local": "2026-05-10 10:00 IST",
            "duration_minutes": "30",
            "calendar_event_link": "",
            "previous_scheduled_at_local": "",
        }
        out = r.render(
            role="user",
            ctx=ctx,
            include_pulse=False,
            pulse_block_raw=r.pulse_block_template(),
        )
        assert "BK-20260507-001" in out.subject
        assert "Weekly Pulse not available" in out.body_markdown
    finally:
        Path(path).unlink(missing_ok=True)


def test_malformed_template_raises():
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
        f.write("no blocks here")
        path = f.name
    try:
        with pytest.raises(ValueError):
            EmailTemplateRenderer(path).pulse_block_template()
    finally:
        Path(path).unlink(missing_ok=True)
