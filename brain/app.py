#!/usr/bin/env python3
"""
FastAPI application for Jarilo Brain.

This module contains the FastAPI application instance and all route registrations.
"""

import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Initialize logging first
from core.logging import setup_logging
setup_logging()

import logging
from orm import db_manager

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Приложение запускается...")
    try:
        # Инициализация StateManager
        from workspace.state_manager import StateManager
        app.state.state_manager = StateManager()
        logger.info("StateManager initialized successfully")
        
        # Инициализация базы данных
        await db_manager.init_db()
        logger.info("Database initialized successfully")
        yield
        logger.info("Приложение завершается нормально")
    except Exception as e:
        logger.error(f"Приложение завершается с ошибкой: {e}", exc_info=True)
        raise
    finally:
        # Закрытие базы данных
        await db_manager.close_db()
        logger.info("Database connection closed")

# Create FastAPI application
app = FastAPI(title="Jarilo Brain", lifespan=lifespan)

# Add security middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3002", "http://localhost:3000", "http://127.0.0.1:3002"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "0.0.0.0"]
)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response

# Health endpoint (вне try-except для гарантии регистрации)
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "jarilo-brain", "version": "1.0.0"}

@app.get("/")
async def root():
    return {"message": "Hello World"}

try:
    # Import and register routers
    # from api.v1.health_router import router as health_router
    from api.v1.secrets_router import router as secrets_router
    from api.v1.endpoints import router as main_router
    # from api.middleware import ExceptionHandlerMiddleware, RequestLoggingMiddleware

    # Add middleware
    # app.add_middleware(ExceptionHandlerMiddleware)
    # app.add_middleware(RequestLoggingMiddleware)

    # Register routers
    # app.include_router(health_router, prefix="/api/v1", tags=["health"])
    app.include_router(secrets_router, prefix="/api/v1", tags=["secrets"])
    app.include_router(main_router, prefix="/api/v1", tags=["main"])

    logger.info("Роутеры зарегистрированы успешно")

    # Simple test endpoints
    @app.get("/api/v1/test-secrets")
    async def test_secrets():
        return {"message": "Secrets endpoint works", "status": "ok"}

    @app.post("/test")
    async def test_endpoint(data: dict):
        return {"received": data}

except Exception as e:
    import traceback
    logger.error(f"ОШИБКА при создании FastAPI приложения: {e}", exc_info=True)
    traceback.print_exc()
    raise

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Необработанное исключение: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Внутренняя ошибка сервера: {str(exc)}"}
    )