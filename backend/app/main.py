"""
CogniVex AI Interview Platform - Main Application

This is the FastAPI application entry point.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.production import prod_settings, get_cors_config, is_production
from app.logging_config import logger, setup_logging
from app.middleware.rate_limit import RateLimitMiddleware
from app.routers import auth, users, companies, jobs, interviews, resume, dashboard, rankings, recruiter, analytics


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown."""
    # Startup
    logger.info(
        "Starting CogniVex AI Interview Platform",
        extra={
            "environment": prod_settings.environment,
            "debug": settings.debug
        }
    )

    yield

    # Shutdown
    logger.info("Shutting down CogniVex AI Interview Platform")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="AI Interview Platform Backend API - CogniVex",
    version="1.0.0",
    debug=settings.debug,
    docs_url="/docs" if not is_production() else None,
    redoc_url="/redoc" if not is_production() else None,
    openapi_url="/openapi.json" if not is_production() else None,
    lifespan=lifespan
)

# Add rate limiting middleware (only in production or if enabled)
if prod_settings.rate_limit_enabled:
    rate_limit_config = {
        "requests": prod_settings.rate_limit_requests,
        "window": prod_settings.rate_limit_window
    }
    app.add_middleware(
        RateLimitMiddleware,
        **rate_limit_config
    )

# CORS middleware - use production config if in production
if is_production():
    cors_config = get_cors_config()
else:
    # Development CORS - allow all
    cors_config = {
        "allow_origins": ["*"],
        "allow_credentials": True,
        "allow_methods": ["*"],
        "allow_headers": ["*"],
    }

app.add_middleware(
    CORSMiddleware,
    **cors_config
)

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(companies.router, prefix="/api/v1")
app.include_router(jobs.router, prefix="/api/v1")
app.include_router(interviews.router, prefix="/api/v1")
app.include_router(resume.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(rankings.router, prefix="/api/v1")
app.include_router(recruiter.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "CogniVex AI Interview Platform API",
        "version": "1.0.0",
        "docs": "/docs",
        "environment": prod_settings.environment
    }


@app.get("/health")
async def health_check(request: Request):
    """
    Health check endpoint for monitoring.

    Returns:
        JSON response with health status
    """
    # Basic health check
    health_status = {
        "status": "healthy",
        "service": "convexiv-api",
        "version": "1.0.0"
    }

    # Add database check in production
    if is_production():
        try:
            # Try to connect to Supabase
            from app.services.supabase import get_supabase_client
            client = get_supabase_client()
            # Simple query to check connection
            # Note: We don't actually execute to avoid unnecessary DB calls
            health_status["database"] = "connected"
        except Exception as e:
            logger.warning(f"Database health check failed: {str(e)}")
            health_status["database"] = "disconnected"
            health_status["status"] = "degraded"

    logger.debug("Health check performed", extra={"status": health_status["status"]})
    return health_status


@app.get("/ready")
async def readiness_check(request: Request):
    """
    Readiness probe for container orchestration (Kubernetes, etc.).

    Returns:
        JSON response indicating if the service is ready to accept traffic
    """
    ready = True
    checks = {
        "service": True,
        "database": False,
        "config": True
    }

    # Check database connection
    try:
        from app.services.supabase import get_supabase_client
        client = get_supabase_client()
        checks["database"] = True
    except Exception as e:
        logger.warning(f"Database readiness check failed: {str(e)}")
        checks["database"] = False
        ready = False

    # Check configuration
    if not settings.supabase_url or not settings.supabase_key:
        checks["config"] = False
        ready = False

    return JSONResponse(
        status_code=200 if ready else 503,
        content={
            "ready": ready,
            "checks": checks,
            "service": "convexiv-api"
        }
    )


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "exception": str(exc)
        },
        exc_info=True
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred" if not is_production() else "Please try again later",
            "request_id": request.headers.get("X-Request-ID", "unknown")
        }
    )


if __name__ == "__main__":
    import uvicorn

    # Run with production settings if in production mode
    if is_production():
        logger.info("Running in production mode")
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            workers=prod_settings.workers,
            timeout_keep_alive=prod_settings.timeout_keep_alive,
            log_level="info"
        )
    else:
        uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)