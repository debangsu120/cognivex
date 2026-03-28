from fastapi import APIRouter, Depends, HTTPException, Body
from supabase import AsyncClient
from app.deps import get_supabase
from app.models.user import UserCreate, UserResponse
from app.models.response import AuthResponse, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=AuthResponse)
async def signup(
    user_data: UserCreate,
    supabase: AsyncClient = Depends(get_supabase)
):
    """Register a new user."""
    try:
        response = await supabase.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password,
            "options": {
                "data": {
                    "full_name": user_data.full_name
                }
            }
        })

        if response.user:
            # Create profile record
            await supabase.table("profiles").insert({
                "user_id": response.user.id,
                "email": response.user.email,
                "full_name": user_data.full_name
            }).execute()

        return AuthResponse(
            session=response.session.model_dump() if response.session else None,
            user=response.user.model_dump() if response.user else None
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=AuthResponse)
async def login(
    credentials: dict = Body(..., examples=[{"email": "user@example.com", "password": "password123"}]),
    supabase: AsyncClient = Depends(get_supabase)
):
    """Login with email and password."""
    try:
        email = credentials.get("email")
        password = credentials.get("password")

        if not email or not password:
            raise HTTPException(status_code=422, detail="Email and password required")

        response = await supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        return AuthResponse(
            session=response.session.model_dump() if response.session else None,
            user=response.user.model_dump() if response.user else None
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid credentials")


@router.post("/logout")
async def logout(supabase: AsyncClient = Depends(get_supabase)):
    """Logout the current user."""
    try:
        await supabase.auth.sign_out()
        return {"message": "Logged out successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/me")
async def get_current_user(supabase: AsyncClient = Depends(get_supabase)):
    """Get current authenticated user."""
    try:
        response = await supabase.auth.get_user()
        return response.user
    except Exception as e:
        raise HTTPException(status_code=401, detail="Not authenticated")
