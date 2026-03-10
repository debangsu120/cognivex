from typing import AsyncGenerator, Optional
from fastapi import Depends, Header
from supabase import create_client, AsyncClient
from app.config import settings
from app.exceptions import UnauthorizedException


_supabase_async_client: Optional[AsyncClient] = None


def get_supabase() -> AsyncClient:
    """Get async Supabase client."""
    global _supabase_async_client
    if _supabase_async_client is None:
        _supabase_async_client = create_client(
            settings.supabase_url,
            settings.supabase_key
        )
    return _supabase_async_client


async def get_current_user(
    authorization: Optional[str] = Header(None),
    supabase: AsyncClient = Depends(get_supabase)
) -> dict:
    """Get current authenticated user from JWT token."""
    if not authorization:
        raise UnauthorizedException("Authorization header missing")

    try:
        token = authorization.replace("Bearer ", "")
        user = await supabase.auth.get_user(token)
        if not user.user:
            raise UnauthorizedException("Invalid token")
        return user.user
    except Exception as e:
        raise UnauthorizedException(f"Authentication failed: {str(e)}")


async def get_current_user_optional(
    authorization: Optional[str] = Header(None),
    supabase: AsyncClient = Depends(get_supabase)
) -> Optional[dict]:
    """Get current user if authenticated, otherwise return None."""
    if not authorization:
        return None

    try:
        token = authorization.replace("Bearer ", "")
        user = await supabase.auth.get_user(token)
        return user.user if user.user else None
    except Exception:
        return None
