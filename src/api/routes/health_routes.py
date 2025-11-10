"""
Health Routes - Health check and system information endpoints.
"""

import time
from datetime import datetime
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from src.api.models.responses import HealthResponse
from src.utils.logger import app_logger


router = APIRouter(tags=["Health"])


# Track server start time for uptime calculation
_server_start_time = time.time()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Returns service health status and uptime."
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns:
    - Service status (healthy/unhealthy)
    - Current server timestamp
    - API version
    - Server uptime in seconds
    """
    try:
        uptime = time.time() - _server_start_time

        return HealthResponse(
            status="healthy",
            timestamp=datetime.utcnow(),
            version="1.0.0",
            uptime_seconds=uptime
        )

    except Exception as e:
        app_logger.error(f"Health check failed: {e}", exc_info=True)
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.utcnow(),
            version="1.0.0",
            uptime_seconds=0.0
        )


@router.get(
    "/",
    summary="API root",
    description="Returns API information and available endpoints."
)
async def root() -> JSONResponse:
    """
    API root endpoint.

    Returns:
    - API name and version
    - Available endpoints
    - Documentation link
    """
    return JSONResponse({
        "name": "Crypto LLM Trading API",
        "version": "1.0.0",
        "description": "REST API for LLM-based cryptocurrency trading system",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "trading": {
                "status": "/trading/status",
                "accounts": "/trading/accounts",
                "account": "/trading/accounts/{llm_id}",
                "positions": "/trading/positions",
                "positions_by_llm": "/trading/positions/{llm_id}",
                "trades": "/trading/trades",
                "trades_by_llm": "/trading/trades/{llm_id}",
                "leaderboard": "/trading/leaderboard"
            },
            "market": {
                "snapshot": "/market/snapshot",
                "prices": "/market/prices",
                "price": "/market/price/{symbol}",
                "ticker": "/market/ticker/{symbol}",
                "indicators": "/market/indicators/{symbol}"
            }
        },
        "timestamp": datetime.utcnow().isoformat()
    })
