"""
Production-specific settings for CogniVex AI Interview Platform.

This module provides production configurations including:
- Security settings
- CORS configuration
- Logging setup
- Rate limiting
- Performance optimizations
"""

import os
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class ProductionSettings(BaseSettings):
    """Production-specific application settings."""

    # Environment
    environment: str = Field(default="production", alias="ENVIRONMENT")

    # Security
    secret_key: str = Field(default="", alias="SECRET_KEY")
    allowed_hosts: List[str] = Field(
        default=["localhost", "127.0.0.1"],
        alias="ALLOWED_HOSTS"
    )
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")

    # CORS
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000"],
        alias="ALLOWED_ORIGINS"
    )
    allowed_methods: List[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        alias="ALLOWED_METHODS"
    )
    allowed_headers: List[str] = Field(
        default=["Authorization", "Content-Type"],
        alias="ALLOWED_HEADERS"
    )
    allow_credentials: bool = True

    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, alias="RATE_LIMIT_ENABLED")
    rate_limit_requests: int = Field(default=100, alias="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=60, alias="RATE_LIMIT_WINDOW")

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="json", alias="LOG_FORMAT")
    log_file_path: Optional[str] = Field(default=None, alias="LOG_FILE_PATH")

    # Performance
    workers: int = Field(default=4, alias="WORKERS")
    timeout_keep_alive: int = 5

    # Database
    db_pool_size: int = 10
    db_max_overflow: int = 20

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


# Production settings instance
prod_settings = ProductionSettings()


def get_cors_config() -> dict:
    """Get CORS configuration for production."""
    return {
        "allow_origins": prod_settings.allowed_origins,
        "allow_credentials": prod_settings.allow_credentials,
        "allow_methods": prod_settings.allowed_methods,
        "allow_headers": prod_settings.allowed_headers,
    }


def get_rate_limit_config() -> dict:
    """Get rate limiting configuration."""
    return {
        "enabled": prod_settings.rate_limit_enabled,
        "requests": prod_settings.rate_limit_requests,
        "window": prod_settings.rate_limit_window,
    }


def is_production() -> bool:
    """Check if running in production environment."""
    return prod_settings.environment.lower() == "production"


# Production optimizations
if is_production():
    # Disable debug mode
    import sys
    if hasattr(sys, 'settrace'):
        sys.settrace(None)

    # Set environment variables for better performance
    os.environ['PYTHONOPTIMIZE'] = '2'
    os.environ['UVICORN_ACCESS_LOG'] = 'false'