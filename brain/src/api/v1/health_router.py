"""
Health check endpoints for Jarilo.

Provides monitoring capabilities for system health and database connectivity.
"""

from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from orm.db import get_db_session
from core.logging import jarilo_logger

router = APIRouter()


@router.get("/health", response_model=Dict[str, Any])
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint.

    Returns system status and basic information.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "jarilo-brain",
        "version": "1.0.0"
    }


@router.get("/health/db", response_model=Dict[str, Any])
async def database_health_check(
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Database connectivity health check.

    Tests database connection and basic query execution.
    """
    try:
        # Execute a simple query to test connectivity
        result = await db.execute(text("SELECT 1 as test"))
        row = result.fetchone()

        if row and row[0] == 1:
            jarilo_logger.info("Database health check passed")
            return {
                "status": "healthy",
                "database": "connected",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise Exception("Unexpected query result")

    except Exception as e:
        jarilo_logger.error(f"Database health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Database unhealthy: {str(e)}"
        )


@router.get("/health/full", response_model=Dict[str, Any])
async def full_health_check(
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Comprehensive health check including all system components.
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }

    # Database check
    try:
        await db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {e}"
        health_status["status"] = "unhealthy"

    # Add more checks here as needed (e.g., external services, memory usage)

    jarilo_logger.info(f"Full health check: {health_status['status']}")

    return health_status