"""API tests with mocked UserProfileService."""

from datetime import UTC
from unittest.mock import MagicMock

from fastapi.testclient import TestClient


def test_get_me_ok(client: TestClient, test_bearer: str) -> None:
    r = client.get("/api/users/me", headers={"Authorization": test_bearer})
    assert r.status_code == 200
    data = r.json()
    assert data["user_id"] == "00000000-0000-0000-0000-0000000000aa"
    assert data["role"] == "investor"


def test_get_me_404(client: TestClient, test_bearer: str, mock_service: MagicMock) -> None:
    mock_service.get_by_user_id.return_value = None
    r = client.get("/api/users/me", headers={"Authorization": test_bearer})
    assert r.status_code == 404


def test_get_me_unauthorized(client: TestClient) -> None:
    r = client.get("/api/users/me")
    assert r.status_code == 401


def test_get_me_bad_token(client: TestClient) -> None:
    r = client.get("/api/users/me", headers={"Authorization": "Bearer invalid"})
    assert r.status_code == 401


def test_post_profile_create(client: TestClient, test_bearer: str, mock_service: MagicMock) -> None:
    mock_service.get_by_user_id.return_value = None

    from datetime import datetime

    from backend.models.schemas import UserProfileResponse

    mock_service.upsert_profile.return_value = UserProfileResponse(
        id="550e8400-e29b-41d4-a716-446655440000",
        user_id="00000000-0000-0000-0000-0000000000aa",
        email="a@b.com",
        display_name="A",
        role="admin",
        first_login_complete=False,
        created_at=datetime(2026, 5, 6, 10, 0, 0, tzinfo=UTC),
        updated_at=datetime(2026, 5, 6, 10, 0, 0, tzinfo=UTC),
    )

    r = client.post(
        "/api/users/profile",
        headers={"Authorization": test_bearer},
        json={"role": "admin", "email": "a@b.com", "display_name": "A"},
    )
    assert r.status_code == 200
    assert r.json()["role"] == "admin"
    mock_service.upsert_profile.assert_called_once()
    call_kw = mock_service.upsert_profile.call_args[0]
    assert call_kw[1]["role"] == "admin"


def test_post_profile_missing_role_on_create(
    client: TestClient, test_bearer: str, mock_service: MagicMock
) -> None:
    mock_service.get_by_user_id.return_value = None
    mock_service.upsert_profile.side_effect = ValueError("role is required when creating a profile")
    r = client.post(
        "/api/users/profile",
        headers={"Authorization": test_bearer},
        json={"email": "a@b.com"},
    )
    assert r.status_code == 400
