"""user_profiles access via Supabase service role (server-side only)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from supabase import Client, create_client

from backend.config import Settings
from backend.models.schemas import UserProfileResponse


def _parse_ts(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        cleaned = value.replace("Z", "+00:00")
        return datetime.fromisoformat(cleaned)
    raise ValueError("Invalid timestamp")


def _row_to_response(row: dict[str, Any]) -> UserProfileResponse:
    return UserProfileResponse(
        id=str(row["id"]),
        user_id=str(row["user_id"]),
        email=row.get("email"),
        display_name=row.get("display_name"),
        role=row["role"],
        first_login_complete=bool(row.get("first_login_complete", False)),
        created_at=_parse_ts(row["created_at"]),
        updated_at=_parse_ts(row["updated_at"]),
    )


class UserProfileService:
    def __init__(self, settings: Settings) -> None:
        self._client: Client = create_client(
            settings.supabase_url,
            settings.supabase_service_role_key,
        )

    def get_by_user_id(self, user_id: str) -> UserProfileResponse | None:
        result = (
            self._client.table("user_profiles")
            .select("*")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        rows = result.data or []
        if not rows:
            return None
        return _row_to_response(rows[0])

    def upsert_profile(self, user_id: str, patch: dict[str, Any]) -> UserProfileResponse:
        """Create or update profile. Idempotent UPSERT on user_id.

        ``patch`` contains only fields present in the request body (validated upstream).
        """
        existing = self.get_by_user_id(user_id)
        if existing is None and patch.get("role") is None:
            raise ValueError("role is required when creating a profile")

        row: dict[str, Any] = {"user_id": user_id}
        if existing is None:
            row["role"] = patch["role"]
            row["first_login_complete"] = bool(patch.get("first_login_complete", False))
            row["email"] = patch.get("email")
            row["display_name"] = patch.get("display_name")
        else:
            row["role"] = patch["role"] if "role" in patch else existing.role
            if "first_login_complete" in patch:
                row["first_login_complete"] = patch["first_login_complete"]
            else:
                row["first_login_complete"] = existing.first_login_complete
            if "email" in patch:
                row["email"] = patch["email"]
            else:
                row["email"] = existing.email
            if "display_name" in patch:
                row["display_name"] = patch["display_name"]
            else:
                row["display_name"] = existing.display_name

        result = self._client.table("user_profiles").upsert(row, on_conflict="user_id").execute()
        rows = result.data or []
        if not rows:
            got = self.get_by_user_id(user_id)
            if got is None:
                raise RuntimeError("Profile upsert returned no row")
            return got
        return _row_to_response(rows[0])
