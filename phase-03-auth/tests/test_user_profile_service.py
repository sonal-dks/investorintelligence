"""UserProfileService logic with Supabase client mocked."""

from unittest.mock import MagicMock, patch

import pytest
from backend.config import Settings
from backend.services.user_profile_service import UserProfileService


@pytest.fixture
def settings() -> Settings:
    return Settings(
        supabase_url="https://x.supabase.co",
        supabase_service_role_key="srk",
        supabase_jwt_secret="secret",
    )


def test_upsert_requires_role_on_create(settings: Settings) -> None:
    with patch("backend.services.user_profile_service.create_client") as cc:
        mock_table = MagicMock()
        mock_client = MagicMock()
        mock_client.table.return_value = mock_table
        cc.return_value = mock_client

        chain = MagicMock()
        mock_table.select.return_value = chain
        chain.eq.return_value = chain
        chain.limit.return_value = chain
        chain.execute.return_value = MagicMock(data=[])

        svc = UserProfileService(settings)
        with pytest.raises(ValueError, match="role is required"):
            svc.upsert_profile("u1", {})
