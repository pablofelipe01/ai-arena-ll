"""
API Routes - FastAPI route modules.
"""

from .trading_routes import router as trading_router
from .market_routes import router as market_router
from .health_routes import router as health_router

__all__ = [
    "trading_router",
    "market_router",
    "health_router",
]
