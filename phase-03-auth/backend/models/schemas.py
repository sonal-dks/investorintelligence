"""Request/response schemas for user profile API."""

import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

ROLE_LITERAL = Literal["investor", "admin"]
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class UserProfileResponse(BaseModel):
    id: str
    user_id: str
    email: str | None
    display_name: str | None
    role: ROLE_LITERAL
    first_login_complete: bool
    created_at: datetime
    updated_at: datetime


class ProfileUpsertRequest(BaseModel):
    role: Literal["investor", "admin"] | None = None
    email: str | None = None
    display_name: str | None = Field(default=None, max_length=255)
    first_login_complete: bool | None = None

    @field_validator("email")
    @classmethod
    def email_format(cls, v: str | None) -> str | None:
        if v is None or v == "":
            return None
        if not EMAIL_RE.match(v.strip()):
            raise ValueError("Invalid email format")
        return v.strip()
