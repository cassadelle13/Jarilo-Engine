"""
Middleware for Jarilo FastAPI application.

Assimilated from MemGPT's middleware for exception handling and request logging.
Enhanced with structured JSON logging and task correlation.
"""

import time
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from core.logging import jarilo_logger, LogContext


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """
    Middleware to catch and handle all unhandled exceptions.

    Provides structured error responses and logging for debugging.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            jarilo_logger.error(
                f"Unhandled exception in request {request.method} {request.url}: {e}",
                exc_info=True
            )

            # Return structured error response
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "type": "server_error",
                    "request_id": getattr(request.state, "request_id", None)
                }
            )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all incoming requests with timing information and task correlation.

    Enhanced with structured JSON logging and automatic task_id injection.
    Helps with observability and performance monitoring.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        print(f"=== MIDDLEWARE: {request.method} {request.url} ===")
        start_time = time.time()

        # Extract task_id from headers or query params if present
        task_id = request.headers.get("X-Task-ID") or request.query_params.get("task_id")

        # Set context for this request
        LogContext.set("request_id", f"req_{int(start_time * 1000000)}")
        if task_id:
            LogContext.set("task_id", task_id)

        # Log incoming request
        jarilo_logger.info(
            f"Request: {request.method} {request.url}",
            extra={
                "method": request.method,
                "url": str(request.url),
                "client_ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown")
            }
        )

        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            # Log response
            jarilo_logger.info(
                f"Response: {request.method} {request.url}",
                extra={
                    "status_code": response.status_code,
                    "process_time": round(process_time * 1000, 2),  # ms
                    "response_size": getattr(response, "content_length", 0)
                }
            )

            return response

        except Exception as e:
            process_time = time.time() - start_time
            jarilo_logger.error(
                f"Request failed: {request.method} {request.url}",
                extra={
                    "error": str(e),
                    "process_time": round(process_time * 1000, 2)
                },
                exc_info=True
            )
            raise
        finally:
            # Clear context after request
            LogContext.clear()