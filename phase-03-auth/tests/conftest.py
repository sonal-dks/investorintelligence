"""Pytest fixtures."""

from datetime import UTC
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

_TEST_JWT_SECRET = "test-secret-test-secret-test-secret-32b"
_TEST_UID = "00000000-0000-0000-0000-0000000000aa"


def pytest_configure(config: pytest.Config) -> None:
    """Ensure env vars exist before any test module imports backend.main."""
    import os

    os.environ["SUPABASE_URL"] = "https://example.supabase.co"
    os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "test-service-role"
    os.environ["SUPABASE_JWT_SECRET"] = _TEST_JWT_SECRET
    os.environ["CORS_ORIGINS"] = "http://localhost:5173"
    from backend.config import get_settings

    get_settings.cache_clear()


@pytest.fixture
def test_bearer() -> str:
    import jwt

    token = jwt.encode(
        {"sub": _TEST_UID, "aud": "authenticated", "exp": 9_999_999_999},
        _TEST_JWT_SECRET,
        algorithm="HS256",
    )
    return f"Bearer {token}"


@pytest.fixture
def mock_service() -> MagicMock:
    from datetime import datetime

    from backend.models.schemas import UserProfileResponse

    svc = MagicMock()
    svc.get_by_user_id.return_value = UserProfileResponse(
        id="550e8400-e29b-41d4-a716-446655440000",
        user_id=_TEST_UID,
        email="user@example.com",
        display_name="Test User",
        role="investor",
        first_login_complete=True,
        created_at=datetime(2026, 5, 6, 10, 0, 0, tzinfo=UTC),
        updated_at=datetime(2026, 5, 6, 10, 1, 0, tzinfo=UTC),
    )
    return svc


@pytest.fixture
def client(mock_service: MagicMock) -> TestClient:
    from backend.main import app
    from backend.routers import user_router

    def fake_profile_service() -> MagicMock:
        return mock_service

    app.dependency_overrides[user_router.get_profile_service] = fake_profile_service
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
