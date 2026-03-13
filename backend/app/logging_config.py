"""
Logging configuration for CogniVex AI Interview Platform.

This module provides:
- Structured logging with JSON format
- Multiple log handlers (console, file, syslog)
- Log formatting with contextual information
- Debug/Release mode logging levels
"""

import logging
import sys
import os
from typing import Any, Dict
from datetime import datetime
import json
import traceback

from app.config import settings
from app.production import prod_settings, is_production


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }

        # Add extra fields
        if hasattr(record, "extra"):
            log_data.update(record.extra)

        # Add request context if available
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id

        return json.dumps(log_data)


class StandardFormatter(logging.Formatter):
    """Standard formatter for development."""

    def __init__(self):
        super().__init__(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )


def setup_logging() -> logging.Logger:
    """Configure and return the application logger."""
    # Get log level from settings
    log_level = getattr(logging, prod_settings.log_level.upper(), logging.INFO)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    # Choose formatter based on configuration
    if prod_settings.log_format == "json" and is_production():
        formatter = JSONFormatter()
    else:
        formatter = StandardFormatter()

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (only in production)
    if is_production() and prod_settings.log_file_path:
        log_file = prod_settings.log_file_path
        log_dir = os.path.dirname(log_file)

        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)

        # Always use JSON in production files
        file_formatter = JSONFormatter()
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    # Configure third-party loggers
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)

    return root_logger


# Create application logger
logger = setup_logging()


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """Custom logger adapter with context."""

    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """Add context to log messages."""
        if "extra" not in kwargs:
            kwargs["extra"] = {}

        # Add context from adapter
        if self.extra:
            kwargs["extra"].update(self.extra)

        return msg, kwargs


def get_logger_with_context(**context) -> LoggerAdapter:
    """Get a logger with additional context."""
    return LoggerAdapter(logger, context)


# Log application startup
logger.info(
    "CogniVex AI Interview Platform logging initialized",
    extra={
        "environment": prod_settings.environment,
        "log_level": prod_settings.log_level,
        "log_format": prod_settings.log_format
    }
)