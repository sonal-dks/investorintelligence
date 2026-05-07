"""Pydantic validation — edge cases from phase-03 criteria."""

import pytest
from backend.models.schemas import ProfileUpsertRequest
from pydantic import ValidationError


def test_email_valid() -> None:
    m = ProfileUpsertRequest(email="user@example.com")
    assert m.email == "user@example.com"


def test_email_invalid() -> None:
    with pytest.raises(ValidationError):
        ProfileUpsertRequest(email="not-an-email")


def test_display_name_max_length() -> None:
    with pytest.raises(ValidationError):
        ProfileUpsertRequest(display_name="x" * 300)


def test_empty_email_becomes_none() -> None:
    m = ProfileUpsertRequest(email="")
    assert m.email is None
