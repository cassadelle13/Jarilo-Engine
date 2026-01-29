"""
Industrial-grade structured logging system for Jarilo.

Assimilated from MemGPT's production-ready logging architecture with enhancements
for task correlation, JSON formatting, and comprehensive observability.

Features:
- JSON structured logging for production monitoring
- Context-aware logging with task_id correlation
- Automatic capture of logs from uvicorn, sqlalchemy, fastapi
- Multiple sinks (console, file) with configurable formatting
- Request tracing and performance metrics
"""

import json
import logging
import sys
import traceback
from contextvars import ContextVar
from datetime import datetime, timezone
from logging.config import dictConfig
from pathlib import Path
from typing import Any, Optional

# Context variable for log correlation
_log_context: ContextVar[dict[str, Any]] = ContextVar("log_context", default={})


class LogContext:
    """Context manager for log correlation."""

    @staticmethod
    def set(key: str, value: Any) -> None:
        """Set a context value for log correlation."""
        ctx = _log_context.get().copy()
        ctx[key] = value
        _log_context.set(ctx)

    @staticmethod
    def get(key: Optional[str] = None) -> Any:
        """Get context value(s)."""
        ctx = _log_context.get()
        if key is None:
            return ctx
        return ctx.get(key)

    @staticmethod
    def clear() -> None:
        """Clear all context values."""
        _log_context.set({})

    @staticmethod
    def update(**kwargs: Any) -> None:
        """Update multiple context values."""
        ctx = _log_context.get().copy()
        ctx.update(kwargs)
        _log_context.set(ctx)

    @staticmethod
    def remove(key: str) -> None:
        """Remove a context value."""
        ctx = _log_context.get().copy()
        ctx.pop(key, None)
        _log_context.set(ctx)


class LogContextFilter(logging.Filter):
    """Filter to inject log context into log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Add context variables to the log record."""
        context = LogContext.get()
        for key, value in context.items():
            setattr(record, key, value)
        return True


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging with task correlation.

    Outputs logs in JSON format compatible with monitoring systems.
    Automatically includes context fields like task_id, user_id, etc.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON with context enrichment."""
        # Base log structure
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
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
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "stacktrace": "".join(traceback.format_exception(*record.exc_info)),
            }

        # Add context variables (task_id, user_id, etc.)
        context = LogContext.get()
        if context:
            log_data.update(context)

        # Add any extra fields from the log record
        for key, value in record.__dict__.items():
            if key not in [
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "exc_info", "exc_text", "stack_info",
                "lineno", "funcName", "created", "msecs", "relativeCreated",
                "thread", "threadName", "processName", "process", "message"
            ] and not key.startswith("_"):
                log_data[key] = value

        return json.dumps(log_data, default=str, ensure_ascii=False)


def setup_logging(
    level: str = "INFO",
    json_format: bool = True,
    log_file: Optional[str] = None,
    capture_libraries: bool = True
) -> logging.Logger:
    """
    Setup comprehensive logging configuration for Jarilo.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        json_format: Use JSON formatting for structured logs
        log_file: Path to log file (optional)
        capture_libraries: Capture logs from uvicorn, sqlalchemy, fastapi

    Returns:
        Configured logger instance
    """
    # Remove existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Determine formatters
    if json_format:
        formatter_config = {
            "format": "%(message)s"  # Raw message, JSONFormatter will handle formatting
        }
    else:
        formatter_config = {
            "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        }

    # Base logging config
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": formatter_config,
            "standard": {
                "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
            }
        },
        "filters": {
            "log_context": {
                "()": LogContextFilter
            }
        },
        "handlers": {
            "console": {
                "level": level,
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "json" if json_format else "standard",
                "filters": ["log_context"]
            }
        },
        "root": {
            "level": level,
            "handlers": ["console"]
        }
    }

    # Add file handler if specified
    if log_file:
        config["handlers"]["file"] = {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": log_file,
            "maxBytes": 10 * 1024 * 1024,  # 10MB
            "backupCount": 5,
            "formatter": "json" if json_format else "standard",
            "filters": ["log_context"]
        }
        config["root"]["handlers"].append("file")

    # Configure library loggers
    if capture_libraries:
        config["loggers"] = {
            # Capture uvicorn logs
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn.error": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False
            },
            # Capture SQLAlchemy logs
            "sqlalchemy": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False
            },
            "sqlalchemy.engine": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "sqlalchemy.pool": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False
            },
            # Capture FastAPI logs
            "fastapi": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            # Reduce noise from other libraries
            "httpx": {
                "level": "WARNING",
                "propagate": False
            },
            "urllib3": {
                "level": "WARNING",
                "propagate": False
            }
        }

    # Apply configuration
    dictConfig(config)

    # If JSON format, replace the formatter with our custom JSONFormatter
    if json_format:
        console_handler = logging.getLogger().handlers[0]  # Get the console handler
        console_handler.setFormatter(JSONFormatter())

    # Create and return logger
    logger = logging.getLogger("jarilo")
    logger.setLevel(getattr(logging, level.upper()))

    return logger


# Global logger instance
jarilo_logger = setup_logging()