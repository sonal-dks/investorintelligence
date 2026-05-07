"""JWT dependency edge cases."""

import jwt
import pytest
from backend.config import Settings
from backend.deps import decode_supabase_user_jwt
from fastapi import HTTPException


@pytest.fixture
def settings() -> Settings:
    return Settings(
        supabase_url="https://x.supabase.co",
        supabase_service_role_key="k",
        supabase_jwt_secret="unit-test-jwt-secret-unit-test-jwt-secret",
    )


def test_decode_valid(settings: Settings) -> None:
    tok = jwt.encode(
        {"sub": "user-1", "aud": "authenticated", "exp": 9_999_999_999},
        settings.supabase_jwt_secret,
        algorithm="HS256",
    )
    assert decode_supabase_user_jwt(tok, settings) == "user-1"


def test_decode_invalid(settings: Settings) -> None:
    with pytest.raises(HTTPException) as exc:
        decode_supabase_user_jwt("not-a-jwt", settings)
    assert exc.value.status_code == 401


def test_decode_wrong_audience(settings: Settings) -> None:
    tok = jwt.encode(
        {"sub": "user-1", "aud": "wrong", "exp": 9_999_999_999},
        settings.supabase_jwt_secret,
        algorithm="HS256",
    )
    with pytest.raises(HTTPException):
        decode_supabase_user_jwt(tok, settings)
