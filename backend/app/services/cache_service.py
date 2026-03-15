"""
Cache Service for AI Response Caching

Reduces AI API costs by caching responses for similar prompts.
"""

from typing import Dict, List, Optional, Any
import hashlib
import json
from datetime import datetime, timedelta
from supabase import AsyncClient


class CacheService:
    """Service for caching AI responses."""

    def __init__(self, supabase_client: AsyncClient):
        self.supabase = supabase_client
        self.default_ttl_hours = 24

    def _hash_prompt(self, prompt: str) -> str:
        """Create a hash for the prompt.

        Args:
            prompt: Prompt text

        Returns:
            Hash string
        """
        return hashlib.sha256(prompt.encode()).hexdigest()[:64]

    async def get_cached_response(
        self,
        prompt: str,
        model: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached response for a prompt.

        Args:
            prompt: Prompt text
            model: Model used

        Returns:
            Cached response or None
        """
        prompt_hash = self._hash_prompt(prompt)

        result = await self.supabase.table("ai_cache").select(
            "response_text, token_count, created_at"
        ).eq("prompt_hash", prompt_hash).eq(
            "model_used", model
        ).gt("expires_at", datetime.utcnow().isoformat()).execute()

        if result.data:
            # Update access time
            await self.supabase.table("ai_cache").update({
                "created_at": datetime.utcnow().isoformat()
            }).eq("id", result.data[0].get("id")).execute()

            return {
                "response": json.loads(result.data[0]["response_text"]),
                "cached": True,
                "token_count": result.data[0].get("token_count"),
                "cached_at": result.data[0].get("created_at")
            }

        return None

    async def cache_response(
        self,
        prompt: str,
        response: Dict[str, Any],
        model: str,
        token_count: Optional[int] = None,
        ttl_hours: Optional[int] = None
    ) -> Dict[str, Any]:
        """Cache an AI response.

        Args:
            prompt: Original prompt
            response: AI response
            model: Model used
            token_count: Number of tokens used
            ttl_hours: Time to live in hours

        Returns:
            Cache record
        """
        prompt_hash = self._hash_prompt(prompt)
        ttl = ttl_hours or self.default_ttl_hours

        data = {
            "prompt_hash": prompt_hash,
            "prompt_text": prompt[:500],  # Store truncated prompt
            "response_text": json.dumps(response),
            "model_used": model,
            "token_count": token_count,
            "expires_at": (datetime.utcnow() + timedelta(hours=ttl)).isoformat()
        }

        # Check if exists
        existing = await self.supabase.table("ai_cache").select(
            "id"
        ).eq("prompt_hash", prompt_hash).execute()

        if existing.data:
            # Update
            result = await self.supabase.table("ai_cache").update(data).eq(
                "id", existing.data[0]["id"]
            ).execute()
        else:
            # Insert
            result = await self.supabase.table("ai_cache").insert(data).execute()

        return result.data[0] if result.data else {"status": "cached"}

    async def invalidate_cache(
        self,
        prompt: str
    ) -> bool:
        """Invalidate a cached response.

        Args:
            prompt: Prompt to invalidate

        Returns:
            True if invalidated
        """
        prompt_hash = self._hash_prompt(prompt)

        await self.supabase.table("ai_cache").delete().eq(
            "prompt_hash", prompt_hash
        ).execute()

        return True

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Cache stats
        """
        # Total entries
        total = await self.supabase.table("ai_cache").select(
            "id", count="exact"
        ).execute()

        # Active (not expired)
        active = await self.supabase.table("ai_cache").select(
            "id", count="exact"
        ).gt("expires_at", datetime.utcnow().isoformat()).execute()

        # Expired
        expired = await self.supabase.table("ai_cache").select(
            "id", count="exact"
        ).lte("expires_at", datetime.utcnow().isoformat()).execute()

        # Total tokens cached
        tokens = await self.supabase.table("ai_cache").select(
            "token_count"
        ).execute()

        total_tokens = sum(
            t.get("token_count", 0) or 0
            for t in tokens.data
        )

        return {
            "total_entries": total.count or 0,
            "active_entries": active.count or 0,
            "expired_entries": expired.count or 0,
            "total_tokens_cached": total_tokens
        }

    async def cleanup_expired(self) -> int:
        """Remove expired cache entries.

        Returns:
            Number of entries removed
        """
        result = await self.supabase.table("ai_cache").delete().lte(
            "expires_at", datetime.utcnow().isoformat()
        ).execute()

        return len(result.data) if result.data else 0


def create_cache_service(supabase_client: AsyncClient) -> CacheService:
    """Create a CacheService instance.

    Args:
        supabase_client: Async Supabase client

    Returns:
        Configured CacheService
    """
    return CacheService(supabase_client)
