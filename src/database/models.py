"""
Pydantic models para datos de base de datos.

Estos modelos proporcionan validación y type hints para todos los
objetos que se guardan y recuperan de Supabase.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field, validator, UUID4


# ============================================
# ENUMS
# ============================================

class PositionSide(str, Enum):
    """Lado de la posición."""
    LONG = "LONG"
    SHORT = "SHORT"


class PositionStatus(str, Enum):
    """Estado de la posición."""
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    LIQUIDATED = "LIQUIDATED"


class TradeSide(str, Enum):
    """Lado del trade."""
    BUY = "BUY"
    SELL = "SELL"


class TradeType(str, Enum):
    """Tipo de trade."""
    OPEN = "OPEN"
    CLOSE = "CLOSE"
    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT = "TAKE_PROFIT"
    LIQUIDATION = "LIQUIDATION"


class TradeStatus(str, Enum):
    """Estado del trade."""
    PENDING = "PENDING"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class OrderType(str, Enum):
    """Tipo de orden."""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT = "TAKE_PROFIT"
    STOP_MARKET = "STOP_MARKET"


class OrderStatus(str, Enum):
    """Estado de la orden."""
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class APICallStatus(str, Enum):
    """Estado de llamada API."""
    SUCCESS = "SUCCESS"
    TIMEOUT = "TIMEOUT"
    ERROR = "ERROR"
    RATE_LIMITED = "RATE_LIMITED"


# ============================================
# DATABASE MODELS
# ============================================

class LLMAccountDB(BaseModel):
    """Modelo para llm_accounts table."""

    id: Optional[UUID4] = None
    llm_id: str = Field(..., regex=r"^LLM-[A-C]$")

    # LLM Configuration
    provider: str  # 'claude', 'deepseek', 'openai'
    model: str
    temperature: Decimal = Field(..., ge=0, le=2)
    max_tokens: int = 1000

    # Virtual Balance
    balance: Decimal = Field(default=Decimal("100.00"), ge=0)
    initial_balance: Decimal = Field(default=Decimal("100.00"), ge=0)

    # Position Tracking
    margin_used: Decimal = Field(default=Decimal("0.00"), ge=0)
    available_balance: Optional[Decimal] = None  # Generated column
    open_positions: int = Field(default=0, ge=0)

    # Performance Metrics
    total_pnl: Decimal = Field(default=Decimal("0.00"))
    realized_pnl: Decimal = Field(default=Decimal("0.00"))
    unrealized_pnl: Decimal = Field(default=Decimal("0.00"))

    total_trades: int = Field(default=0, ge=0)
    winning_trades: int = Field(default=0, ge=0)
    losing_trades: int = Field(default=0, ge=0)
    win_rate: Optional[Decimal] = None  # Generated column

    # Risk Metrics
    max_drawdown: Decimal = Field(default=Decimal("0.00"))
    sharpe_ratio: Decimal = Field(default=Decimal("0.00"))

    # Rate Limiting
    api_calls_today: int = Field(default=0, ge=0)
    api_calls_this_hour: int = Field(default=0, ge=0)
    last_decision_at: Optional[datetime] = None

    # Status
    is_active: bool = True
    is_trading_enabled: bool = True
    last_error: Optional[str] = None
    error_count: int = Field(default=0, ge=0)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


class PositionDB(BaseModel):
    """Modelo para positions table."""

    id: Optional[UUID4] = None
    llm_id: str = Field(..., regex=r"^LLM-[A-C]$")

    # Position Details
    symbol: str
    side: PositionSide

    # Entry Info
    entry_price: Decimal = Field(..., gt=0)
    quantity: Decimal = Field(..., gt=0)
    leverage: int = Field(..., ge=1, le=125)

    # Margin & Value
    margin_used: Decimal = Field(..., gt=0)
    notional_value: Optional[Decimal] = None  # Generated column

    # Current Status
    current_price: Optional[Decimal] = None
    unrealized_pnl: Decimal = Field(default=Decimal("0.00"))
    pnl_percentage: Decimal = Field(default=Decimal("0.00"))

    # Risk Management
    liquidation_price: Decimal = Field(..., gt=0)
    stop_loss: Optional[Decimal] = None
    take_profit: Optional[Decimal] = None

    # LLM Decision Info
    reasoning: Optional[str] = None
    confidence: Optional[Decimal] = Field(None, ge=0, le=1)
    strategy: Optional[str] = None

    # Binance Order IDs
    entry_order_id: Optional[str] = None
    binance_position_id: Optional[str] = None

    # Status
    status: PositionStatus = PositionStatus.OPEN

    # Timestamps
    opened_at: datetime = Field(default_factory=datetime.utcnow)
    closed_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


class TradeDB(BaseModel):
    """Modelo para trades table."""

    id: Optional[UUID4] = None
    llm_id: str = Field(..., regex=r"^LLM-[A-C]$")
    position_id: Optional[UUID4] = None

    # Trade Details
    symbol: str
    side: TradeSide
    trade_type: TradeType

    # Execution Details
    price: Decimal = Field(..., gt=0)
    quantity: Decimal = Field(..., gt=0)
    notional_value: Optional[Decimal] = None  # Generated column

    # P&L (solo para trades de cierre)
    pnl: Optional[Decimal] = None
    pnl_percentage: Optional[Decimal] = None
    fees: Decimal = Field(..., ge=0)
    net_pnl: Optional[Decimal] = None

    # LLM Decision Info
    reasoning: str
    confidence: Optional[Decimal] = Field(None, ge=0, le=1)
    strategy: Optional[str] = None
    llm_response_time_ms: Optional[int] = None

    # Binance Order Info
    binance_order_id: Optional[str] = None
    commission: Optional[Decimal] = None
    commission_asset: Optional[str] = None

    # Status
    status: TradeStatus = TradeStatus.EXECUTED
    error_message: Optional[str] = None

    # Timestamps
    executed_at: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


class OrderDB(BaseModel):
    """Modelo para orders table."""

    id: Optional[UUID4] = None
    llm_id: str = Field(..., regex=r"^LLM-[A-C]$")
    position_id: Optional[UUID4] = None

    # Order Details
    symbol: str
    side: TradeSide
    order_type: OrderType

    # Quantity & Price
    quantity: Decimal = Field(..., gt=0)
    price: Optional[Decimal] = Field(None, gt=0)
    stop_price: Optional[Decimal] = Field(None, gt=0)

    # Binance Response
    binance_order_id: Optional[str] = None
    client_order_id: Optional[str] = None
    binance_status: Optional[str] = None

    # Execution
    executed_quantity: Decimal = Field(default=Decimal("0.00"), ge=0)
    executed_price: Optional[Decimal] = None

    # Status
    status: OrderStatus = OrderStatus.PENDING
    error_message: Optional[str] = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    submitted_at: Optional[datetime] = None
    filled_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


class MarketDataDB(BaseModel):
    """Modelo para market_data table."""

    id: Optional[UUID4] = None
    symbol: str

    # Current Price Data
    price: Decimal = Field(..., gt=0)
    bid: Optional[Decimal] = None
    ask: Optional[Decimal] = None
    volume_24h: Optional[Decimal] = None

    # Price Changes
    price_change_24h: Optional[Decimal] = None
    price_change_pct_24h: Optional[Decimal] = None

    # Technical Indicators
    rsi_14: Optional[Decimal] = None
    macd: Optional[Decimal] = None
    macd_signal: Optional[Decimal] = None
    bb_upper: Optional[Decimal] = None
    bb_middle: Optional[Decimal] = None
    bb_lower: Optional[Decimal] = None

    # Additional Market Info
    funding_rate: Optional[Decimal] = None
    open_interest: Optional[Decimal] = None

    # Timestamps
    data_timestamp: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


class RejectedDecisionDB(BaseModel):
    """Modelo para rejected_decisions table."""

    id: Optional[UUID4] = None
    llm_id: str = Field(..., regex=r"^LLM-[A-C]$")

    # Decision Details
    symbol: str
    action: str

    # LLM Response
    llm_reasoning: str
    llm_confidence: Optional[Decimal] = Field(None, ge=0, le=1)
    llm_strategy: Optional[str] = None
    llm_response_time_ms: Optional[int] = None
    raw_llm_response: Optional[Dict[str, Any]] = None

    # Rejection Details
    rejection_reason: str
    rejection_details: Optional[Dict[str, Any]] = None
    validator: Optional[str] = None

    # Market Context
    market_price: Optional[Decimal] = None
    account_balance: Optional[Decimal] = None
    open_positions_count: Optional[int] = None

    # Timestamps
    rejected_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


class LLMAPICallDB(BaseModel):
    """Modelo para llm_api_calls table."""

    id: Optional[UUID4] = None
    llm_id: str = Field(..., regex=r"^LLM-[A-C]$")

    # API Call Details
    provider: str
    model: str

    # Request
    prompt_tokens: Optional[int] = None
    request_payload: Optional[Dict[str, Any]] = None

    # Response
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    response_time_ms: int
    response_payload: Optional[Dict[str, Any]] = None

    # Cost Estimation
    estimated_cost_usd: Optional[Decimal] = None

    # Status
    status: APICallStatus
    error_message: Optional[str] = None
    http_status_code: Optional[int] = None

    # Timestamps
    called_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


# ============================================
# VIEW MODELS (READ-ONLY)
# ============================================

class LLMLeaderboardView(BaseModel):
    """Modelo para llm_leaderboard view."""

    llm_id: str
    provider: str
    model: str
    temperature: Decimal
    balance: Decimal
    total_pnl: Decimal
    roi_percentage: Decimal
    total_trades: int
    win_rate: Optional[Decimal]
    open_positions: int
    sharpe_ratio: Decimal
    max_drawdown: Decimal
    is_active: bool
    is_trading_enabled: bool

    class Config:
        json_encoders = {Decimal: str}


class ActivePositionSummary(BaseModel):
    """Modelo para active_positions_summary view."""

    llm_id: str
    symbol: str
    side: str
    entry_price: Decimal
    current_price: Optional[Decimal]
    quantity: Decimal
    leverage: int
    unrealized_pnl: Decimal
    pnl_percentage: Decimal
    liquidation_price: Decimal
    opened_at: datetime
    hours_open: Optional[float]

    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


class LLMTradingStats(BaseModel):
    """Modelo para llm_trading_stats view."""

    llm_id: str
    provider: str
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: Optional[Decimal]
    total_pnl: Decimal
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    current_open_positions: int
    total_open_pnl: Optional[Decimal]

    class Config:
        json_encoders = {Decimal: str}
