"""
Rate limiting middleware for CogniVex AI Interview Platform.

This module provides API rate limiting using a token bucket algorithm.
Supports configurable limits per endpoint and per user.
"""

import time
from typing import Dict, Tuple, Optional
from collections import defaultdict
from dataclasses import dataclass, field
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.production import prod_settings, get_rate_limit_config
from app.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class RateLimitBucket:
    """Token bucket for rate limiting."""
    tokens: float
    last_update: float
    requests: int = 0


class RateLimiter:
    """Token bucket rate limiter implementation."""

    def __init__(
        self,
        requests: int = 100,
        window: int = 60,
        burst: int = 10
    ):
        """
        Initialize rate limiter.

        Args:
            requests: Maximum requests allowed in the time window
            window: Time window in seconds
            burst: Additional burst capacity
        """
        self.requests = requests
        self.window = window
        self.burst = burst
        self._buckets: Dict[str, RateLimitBucket] = defaultdict(
            lambda: RateLimitBucket(
                tokens=float(requests + burst),
                last_update=time.time()
            )
        )

    def _refill_bucket(self, bucket: RateLimitBucket) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - bucket.last_update

        # Add tokens based on rate
        refill_rate = self.requests / self.window
        bucket.tokens = min(
            self.burst + self.requests,
            bucket.tokens + (elapsed * refill_rate)
        )
        bucket.last_update = now

    def check(self, key: str) -> Tuple[bool, int, int]:
        """
        Check if request is allowed.

        Args:
            key: Unique identifier (IP, user ID, etc.)

        Returns:
            Tuple of (allowed, remaining_requests, reset_seconds)
        """
        bucket = self._buckets[key]
        self._refill_bucket(bucket)

        if bucket.tokens >= 1:
            bucket.tokens -= 1
            bucket.requests += 1

            remaining = int(bucket.tokens)
            reset_time = bucket.last_update + self.window
            reset_seconds = max(0, int(reset_time - time.time()))

            return True, remaining, reset_seconds

        reset_time = bucket.last_update + self.window
        reset_seconds = max(0, int(reset_time - time.time()))

        return False, 0, reset_seconds

    def reset(self, key: str) -> None:
        """Reset rate limit for a key."""
        if key in self._buckets:
            del self._buckets[key]


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get or create the global rate limiter."""
    global _rate_limiter
    if _rate_limiter is None:
        config = get_rate_limit_config()
        _rate_limiter = RateLimiter(
            requests=config.get("requests", 100),
            window=config.get("window", 60),
            burst=config.get("burst", 10)
        )
    return _rate_limiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for API rate limiting."""

    # Endpoints to skip rate limiting
    EXEMPT_PATHS = [
        "/",
        "/health",
        "/ready",
        "/docs",
        "/openapi.json",
        "/redoc",
    ]

    def __init__(self, app, requests: int = 100, window: int = 60):
        """Initialize rate limit middleware."""
        super().__init__(app)
        self.rate_limiter = RateLimiter(
            requests=requests,
            window=window,
            burst=10
        )
        logger.info(
            f"Rate limiting enabled: {requests} requests per {window} seconds"
        )

    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        # Skip rate limiting for exempt paths
        if any(request.url.path.startswith(path) for path in self.EXEMPT_PATHS):
            return await call_next(request)

        # Skip if rate limiting is disabled
        if not prod_settings.rate_limit_enabled:
            return await call_next(request)

        # Get client identifier
        client_id = self._get_client_id(request)

        # Check rate limit
        allowed, remaining, reset_seconds = self.rate_limiter.check(client_id)

        # Log rate limit attempts
        logger.debug(
            f"Rate limit check: {client_id} - allowed={allowed}, remaining={remaining}"
        )

        if not allowed:
            logger.warning(
                f"Rate limit exceeded for client: {client_id}",
                extra={"client_id": client_id, "path": request.url.path}
            )

            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "message": "Rate limit exceeded. Please try again later.",
                    "retry_after": reset_seconds
                },
                headers={
                    "X-RateLimit-Limit": str(self.rate_limiter.requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_seconds),
                    "Retry-After": str(reset_seconds)
                }
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(self.rate_limiter.requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_seconds)

        return response

    def _get_client_id(self, request: Request) -> str:
        """Get unique identifier for client."""
        # Try to get user ID if authenticated
        if hasattr(request.state, "user_id") and request.state.user_id:
            return f"user:{request.state.user_id}"

        # Fall back to IP address
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        return f"ip:{client_ip}"


# Utility function to reset rate limit (for testing or admin)
def reset_rate_limit(key: str) -> None:
    """Reset rate limit for a specific key."""
    get_rate_limiter().reset(key)
    logger.info(f"Rate limit reset for: {key}")