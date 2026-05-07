"""FastAPI dependencies for auth verification."""

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import create_client

from backend.config.settings import Settings, get_settings

security = HTTPBearer(auto_error=False)
ALLOWED_ALGS = ("HS256",)


def decode_supabase_user_jwt(token: str, settings: Settings) -> str:
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
    token = creds.credentials
    try:
        return decode_supabase_user_jwt(token, settings)
    except HTTPException:
        # Fallback: validate with Supabase Auth directly in case local JWT
        # verification config drifts from project token signing settings.
        try:
            client = create_client(settings.supabase_url, settings.supabase_service_role_key)
            user_response = client.auth.get_user(token)
            user = getattr(user_response, "user", None)
            user_id = getattr(user, "id", None)
            if isinstance(user_id, str) and user_id:
                return user_id
        except Exception as exc:  # noqa: BLE001 - return consistent 401 below
            raise HTTPException(status_code=401, detail="Invalid or expired token") from exc
        raise HTTPException(status_code=401, detail="Invalid or expired token")
