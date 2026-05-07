"""User profile endpoints."""

from fastapi import APIRouter, Depends, HTTPException

from backend.config import Settings, get_settings
from backend.deps import get_current_user_id
from backend.models.schemas import ProfileUpsertRequest, UserProfileResponse
from backend.services.user_profile_service import UserProfileService

router = APIRouter(prefix="/api/users", tags=["users"])


def get_profile_service(settings: Settings = Depends(get_settings)) -> UserProfileService:
    return UserProfileService(settings)


@router.get("/me", response_model=UserProfileResponse)
def get_me(
    user_id: str = Depends(get_current_user_id),
    svc: UserProfileService = Depends(get_profile_service),
) -> UserProfileResponse:
    profile = svc.get_by_user_id(user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.post("/profile", response_model=UserProfileResponse)
def upsert_profile(
    body: ProfileUpsertRequest,
    user_id: str = Depends(get_current_user_id),
    svc: UserProfileService = Depends(get_profile_service),
) -> UserProfileResponse:
    patch = body.model_dump(exclude_unset=True)
    try:
        return svc.upsert_profile(user_id, patch)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
