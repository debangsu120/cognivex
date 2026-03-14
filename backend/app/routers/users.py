from fastapi import APIRouter, Depends, HTTPException
from supabase import AsyncClient
from typing import Optional
from app.deps import get_supabase, get_current_user
from app.models.user import UserResponse, ProfileUpdate, ProfileResponse
from app.models.response import APIResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=APIResponse[ProfileResponse])
async def get_me(
    supabase: AsyncClient = Depends(get_supabase),
    current_user: dict = Depends(get_current_user)
):
    """Get current user's profile."""
    try:
        response = await supabase.table("profiles").select("*").eq("user_id", current_user.id).execute()

        if not response.data:
            # Create profile if doesn't exist
            new_profile = {
                "user_id": current_user.id,
                "email": current_user.email,
                "full_name": current_user.user_metadata.get("full_name") if current_user.user_metadata else None
            }
            response = await supabase.table("profiles").insert(new_profile).execute()

        profile = response.data[0]
        return APIResponse(data=profile)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/me", response_model=APIResponse[ProfileResponse])
async def update_me(
    profile_data: ProfileUpdate,
    supabase: AsyncClient = Depends(get_supabase),
    current_user: dict = Depends(get_current_user)
):
    """Update current user's profile."""
    try:
        # Filter out None values
        update_data = {k: v for k, v in profile_data.model_dump().items() if v is not None}

        response = await supabase.table("profiles").update(update_data).eq("user_id", current_user.id).execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Profile not found")

        return APIResponse(data=response.data[0], message="Profile updated successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}", response_model=APIResponse[ProfileResponse])
async def get_user(
    user_id: str,
    supabase: AsyncClient = Depends(get_supabase),
    current_user: dict = Depends(get_current_user)
):
    """Get a user's public profile."""
    try:
        response = await supabase.table("profiles").select("*").eq("user_id", user_id).execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="User not found")

        return APIResponse(data=response.data[0])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
