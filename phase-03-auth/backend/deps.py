"""FastAPI dependencies: JWT verification."""

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.config import Settings, get_settings

security = HTTPBearer(auto_error=False)

ALLOWED_ALGS = ("HS256",)


def decode_supabase_user_jwt(token: str, settings: Settings) -> str:
    """Verify Supabase access token and return auth user id (sub)."""
    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=list(ALLOWED_ALGS),
            audience="authenticated",
            options={"require": ["exp", "sub"]},
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc
    sub = payload.get("sub")
    if not sub or not isinstance(sub, str):
        raise HTTPException(status_code=401, detail="Token missing subject")
    return sub


def get_current_user_id(
    creds: HTTPAuthorizationCredentials | None = Depends(security),
    settings: Settings = Depends(get_settings),
) -> str:
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Not authenticated")
    return decode_supabase_user_jwt(creds.credentials, settings)
