"""
FastAPI Main Application - REST API server.

Provides GET-only endpoints for:
- Trading status and accounts
- Open positions and trade history
- Market data and technical indicators
- LLM performance leaderboard

Run with: uvicorn src.api.main:app --reload --port 8000
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from src.api.routes import trading_router, market_router, health_router
from src.api.dependencies import initialize_all_services, cleanup_all_services
from src.utils.logger import app_logger
from config.settings import settings


# ============================================================================
# Lifespan Context Manager
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events:
    - Startup: Initialize all services
    - Shutdown: Cleanup resources
    """
    # Startup
    app_logger.info("=" * 60)
    app_logger.info("Starting FastAPI application...")
    app_logger.info("=" * 60)

    try:
        # Initialize all services
        initialize_all_services()
        app_logger.info("API server ready")
    except Exception as e:
        app_logger.error(f"Failed to initialize services: {e}", exc_info=True)
        raise

    yield

    # Shutdown
    app_logger.info("Shutting down FastAPI application...")
    cleanup_all_services()
    app_logger.info("API server stopped")


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Crypto LLM Trading API",
    description=(
        "REST API for LLM-based cryptocurrency trading system.\n\n"
        "Features:\n"
        "- 3 LLMs (Claude Sonnet 4, DeepSeek, GPT-4o) competing in trading\n"
        "- Real-time market data and technical indicators\n"
        "- Account management and position tracking\n"
        "- Trade history and performance leaderboard\n\n"
        "All endpoints are GET-only (read-only)."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


# ============================================================================
# CORS Middleware
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["GET"],  # Only GET methods allowed
    allow_headers=["*"],
)


# ============================================================================
# Exception Handlers
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler.

    Catches all unhandled exceptions and returns a JSON error response.
    """
    app_logger.error(
        f"Unhandled exception on {request.method} {request.url}: {exc}",
        exc_info=True
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "An internal server error occurred",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# ============================================================================
# Request Logging Middleware
# ============================================================================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Log all incoming requests.
    """
    start_time = datetime.utcnow()

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration = (datetime.utcnow() - start_time).total_seconds()

    # Log request
    app_logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Duration: {duration:.3f}s"
    )

    return response


# ============================================================================
# Route Registration
# ============================================================================

# Health routes (no prefix)
app.include_router(health_router)

# Trading routes
app.include_router(trading_router)

# Market data routes
app.include_router(market_router)


# ============================================================================
# Run Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    app_logger.info("Starting uvicorn server...")

    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload for development
        log_level="info"
    )
