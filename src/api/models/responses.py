"""
API Response Models - Pydantic schemas for FastAPI endpoints.

All endpoints return read-only data (GET only).
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# Base Response Models
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status (healthy/unhealthy)")
    timestamp: datetime = Field(..., description="Current server timestamp")
    version: str = Field(default="1.0.0", description="API version")
    uptime_seconds: Optional[float] = Field(None, description="Server uptime in seconds")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "status": "healthy",
            "timestamp": "2025-01-10T12:00:00Z",
            "version": "1.0.0",
            "uptime_seconds": 3600.0
        }
    })


class ErrorResponse(BaseModel):
    """Error response."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    timestamp: datetime = Field(..., description="Error timestamp")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "error": "ValidationError",
            "message": "Invalid LLM ID provided",
            "timestamp": "2025-01-10T12:00:00Z"
        }
    })


# ============================================================================
# Account Models
# ============================================================================

class PositionResponse(BaseModel):
    """Open position response."""
    position_id: str
    symbol: str
    side: str
    entry_price: float
    quantity: float
    leverage: int
    margin_used: float
    unrealized_pnl_usd: float
    unrealized_pnl_pct: float
    roi_pct: float
    stop_loss_price: Optional[float]
    take_profit_price: Optional[float]
    liquidation_price: float
    opened_at: datetime

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "position_id": "LLM-A-ETHUSDT-1704902400",
            "symbol": "ETHUSDT",
            "side": "LONG",
            "entry_price": 3000.0,
            "quantity": 0.01,
            "leverage": 5,
            "margin_used": 6.0,
            "unrealized_pnl_usd": 15.0,
            "unrealized_pnl_pct": 250.0,
            "roi_pct": 5.0,
            "stop_loss_price": 2850.0,
            "take_profit_price": 3300.0,
            "liquidation_price": 2400.0,
            "opened_at": "2025-01-10T10:00:00Z"
        }
    })


class TradeResponse(BaseModel):
    """Closed trade response."""
    trade_id: str
    symbol: str
    side: str
    entry_price: float
    exit_price: float
    quantity: float
    leverage: int
    pnl_usd: float
    pnl_pct: float
    exit_reason: str
    opened_at: datetime
    closed_at: datetime
    duration_minutes: int

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "trade_id": "LLM-A-ETHUSDT-1704902400",
            "symbol": "ETHUSDT",
            "side": "LONG",
            "entry_price": 3000.0,
            "exit_price": 3150.0,
            "quantity": 0.01,
            "leverage": 5,
            "pnl_usd": 7.5,
            "pnl_pct": 125.0,
            "exit_reason": "TAKE_PROFIT",
            "opened_at": "2025-01-10T10:00:00Z",
            "closed_at": "2025-01-10T11:30:00Z",
            "duration_minutes": 90
        }
    })


class AccountResponse(BaseModel):
    """LLM account response."""
    llm_id: str
    balance_usdt: float
    margin_used: float
    unrealized_pnl: float
    equity_usdt: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_realized_pnl: float
    total_pnl: float
    total_pnl_pct: float
    open_positions_count: int
    open_positions: List[PositionResponse]

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "llm_id": "LLM-A",
            "balance_usdt": 107.5,
            "margin_used": 6.0,
            "unrealized_pnl": 15.0,
            "equity_usdt": 122.5,
            "total_trades": 10,
            "winning_trades": 7,
            "losing_trades": 3,
            "win_rate": 70.0,
            "total_realized_pnl": 7.5,
            "total_pnl": 22.5,
            "total_pnl_pct": 22.5,
            "open_positions_count": 1,
            "open_positions": []
        }
    })


class AccountsResponse(BaseModel):
    """All accounts response."""
    accounts: List[AccountResponse]
    total_equity: float
    total_pnl: float
    total_trades: int
    timestamp: datetime

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "accounts": [],
            "total_equity": 315.0,
            "total_pnl": 15.0,
            "total_trades": 25,
            "timestamp": "2025-01-10T12:00:00Z"
        }
    })


# ============================================================================
# Leaderboard Models
# ============================================================================

class LeaderboardEntry(BaseModel):
    """Leaderboard entry."""
    rank: int
    llm_id: str
    equity_usdt: float
    total_pnl: float
    total_pnl_pct: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    open_positions: int

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "rank": 1,
            "llm_id": "LLM-A",
            "equity_usdt": 122.5,
            "total_pnl": 22.5,
            "total_pnl_pct": 22.5,
            "total_trades": 10,
            "winning_trades": 7,
            "losing_trades": 3,
            "win_rate": 70.0,
            "open_positions": 1
        }
    })


class LeaderboardResponse(BaseModel):
    """Leaderboard response."""
    leaderboard: List[LeaderboardEntry]
    summary: Dict[str, Any]
    timestamp: datetime

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "leaderboard": [],
            "summary": {
                "total_equity_usdt": 315.0,
                "total_pnl": 15.0,
                "total_trades": 25,
                "average_win_rate": 65.0
            },
            "timestamp": "2025-01-10T12:00:00Z"
        }
    })


# ============================================================================
# Market Data Models
# ============================================================================

class MarketTickerResponse(BaseModel):
    """Market ticker for a symbol."""
    symbol: str
    price: float
    price_change_pct_24h: float
    volume_24h: float
    high_24h: float
    low_24h: float
    timestamp: datetime

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "symbol": "ETHUSDT",
            "price": 3000.0,
            "price_change_pct_24h": 5.2,
            "volume_24h": 1000000.0,
            "high_24h": 3100.0,
            "low_24h": 2900.0,
            "timestamp": "2025-01-10T12:00:00Z"
        }
    })


class MarketIndicatorsResponse(BaseModel):
    """Technical indicators for a symbol."""
    symbol: str
    rsi: float
    macd: float
    macd_signal: float
    macd_histogram: float
    sma_20: float
    sma_50: float
    trading_signal: str
    timestamp: datetime

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "symbol": "ETHUSDT",
            "rsi": 65.5,
            "macd": 12.5,
            "macd_signal": 10.0,
            "macd_histogram": 2.5,
            "sma_20": 2950.0,
            "sma_50": 2900.0,
            "trading_signal": "BUY",
            "timestamp": "2025-01-10T12:00:00Z"
        }
    })


class MarketSnapshotResponse(BaseModel):
    """Complete market snapshot."""
    symbols: Dict[str, MarketTickerResponse]
    indicators: Dict[str, MarketIndicatorsResponse]
    summary: Dict[str, Any]
    timestamp: datetime

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "symbols": {},
            "indicators": {},
            "summary": {
                "gainers": ["ETHUSDT", "BNBUSDT"],
                "losers": ["XRPUSDT"],
                "symbols_tracked": 6
            },
            "timestamp": "2025-01-10T12:00:00Z"
        }
    })


# ============================================================================
# Trading Status Models
# ============================================================================

class TradingStatusResponse(BaseModel):
    """Trading system status."""
    timestamp: datetime
    llm_count: int
    symbols_tracked: int
    total_open_positions: int
    total_equity: float
    total_pnl: float
    cycle_status: str
    last_cycle_duration: Optional[float]
    accounts_summary: List[Dict[str, Any]]

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "timestamp": "2025-01-10T12:00:00Z",
            "llm_count": 3,
            "symbols_tracked": 6,
            "total_open_positions": 2,
            "total_equity": 315.0,
            "total_pnl": 15.0,
            "cycle_status": "idle",
            "last_cycle_duration": 2.5,
            "accounts_summary": []
        }
    })


# ============================================================================
# Trade History Models
# ============================================================================

class TradesResponse(BaseModel):
    """Trades history response."""
    trades: List[TradeResponse]
    total_count: int
    llm_id: Optional[str]
    timestamp: datetime

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "trades": [],
            "total_count": 25,
            "llm_id": None,
            "timestamp": "2025-01-10T12:00:00Z"
        }
    })


class PositionsResponse(BaseModel):
    """Open positions response."""
    positions: Dict[str, List[PositionResponse]]
    total_count: int
    total_margin_used: float
    total_unrealized_pnl: float
    timestamp: datetime

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "positions": {
                "LLM-A": [],
                "LLM-B": [],
                "LLM-C": []
            },
            "total_count": 2,
            "total_margin_used": 12.0,
            "total_unrealized_pnl": 25.0,
            "timestamp": "2025-01-10T12:00:00Z"
        }
    })
