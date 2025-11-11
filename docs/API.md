# Crypto LLM Trading System - API Reference

Complete API reference documentation for all **23 REST endpoints** and **WebSocket** protocol.

---

## Table of Contents

1. [API Overview](#api-overview)
2. [Authentication](#authentication)
3. [Base URL](#base-url)
4. [Health Endpoints](#health-endpoints)
5. [Trading Endpoints](#trading-endpoints)
6. [Market Data Endpoints](#market-data-endpoints)
7. [Scheduler Endpoints](#scheduler-endpoints)
8. [WebSocket API](#websocket-api)
9. [Response Models](#response-models)
10. [Error Handling](#error-handling)

---

## API Overview

### Characteristics

- **Protocol**: REST (HTTP/HTTPS)
- **Data Format**: JSON
- **Methods**: GET, POST, WebSocket
- **Authentication**: None (public API for development)
- **CORS**: Enabled for all origins
- **Rate Limiting**: None (currently)

### API Versioning

Current version: **v1.0.0**

No version prefix in URLs (may be added in future releases)

---

## Authentication

**Currently**: No authentication required (development/demo mode)

**Production Recommendations**:
- API Key authentication
- JWT tokens
- Rate limiting per API key
- IP whitelisting

---

## Base URL

**Local Development**:
```
http://localhost:8000
```

**Production** (customize):
```
https://your-domain.com
```

---

## Health Endpoints

### GET /

**Description**: API root endpoint with basic information

**Response**:
```json
{
  "message": "Crypto LLM Trading API",
  "version": "1.0.0",
  "status": "running",
  "timestamp": "2025-11-11T10:30:00Z"
}
```

**Status Codes**:
- `200 OK`: API is running

---

### GET /health

**Description**: Health check endpoint

**Response**:
```json
{
  "status": "healthy",
  "uptime_seconds": 3600,
  "timestamp": "2025-11-11T10:30:00Z",
  "services": {
    "database": "connected",
    "binance_api": "connected",
    "scheduler": "running"
  }
}
```

**Status Codes**:
- `200 OK`: All systems healthy
- `503 Service Unavailable`: System unhealthy

---

## Trading Endpoints

### GET /trading/status

**Description**: Get overall trading system status

**Response**:
```json
{
  "active_llms": 3,
  "total_equity_usdt": 315.50,
  "total_pnl": 15.50,
  "total_pnl_pct": 5.17,
  "total_trades": 45,
  "average_win_rate": 62.5,
  "accounts": [
    {
      "llm_id": "LLM-A",
      "provider": "anthropic",
      "model_name": "claude-sonnet-4-20250514",
      "balance_usdt": 105.20,
      "margin_used": 15.00,
      "equity_usdt": 108.50,
      "total_pnl": 8.50,
      "total_pnl_pct": 8.5,
      "total_trades": 15,
      "win_rate": 66.67,
      "open_positions_count": 2,
      "is_trading_enabled": true
    }
    // ... LLM-B, LLM-C
  ],
  "summary": {
    "total_equity_usdt": 315.50,
    "total_pnl": 15.50,
    "total_pnl_pct": 5.17,
    "total_trades": 45,
    "average_win_rate": 62.5
  }
}
```

**Status Codes**:
- `200 OK`: Success

---

### GET /trading/accounts

**Description**: Get all LLM trading accounts

**Response**:
```json
[
  {
    "llm_id": "LLM-A",
    "provider": "anthropic",
    "model_name": "claude-sonnet-4-20250514",
    "balance_usdt": 105.20,
    "margin_used": 15.00,
    "unrealized_pnl": 3.30,
    "equity_usdt": 108.50,
    "total_trades": 15,
    "winning_trades": 10,
    "losing_trades": 5,
    "win_rate": 66.67,
    "total_realized_pnl": 5.20,
    "total_pnl": 8.50,
    "total_pnl_pct": 8.5,
    "open_positions_count": 2,
    "open_positions": [
      {
        "id": "uuid-123",
        "symbol": "ETHUSDT",
        "side": "LONG",
        "entry_price": 2000.00,
        "current_price": 2050.00,
        "quantity": 0.01,
        "leverage": 5,
        "unrealized_pnl": 2.50,
        "unrealized_pnl_pct": 62.5,
        "opened_at": "2025-11-11T10:00:00Z",
        "duration_seconds": 1800
      }
    ]
  }
  // ... LLM-B, LLM-C
]
```

**Status Codes**:
- `200 OK`: Success

---

### GET /trading/accounts/{llm_id}

**Description**: Get specific LLM account details

**Path Parameters**:
- `llm_id` (string, required): LLM identifier (LLM-A, LLM-B, or LLM-C)

**Example**:
```
GET /trading/accounts/LLM-A
```

**Response**:
```json
{
  "llm_id": "LLM-A",
  "provider": "anthropic",
  "model_name": "claude-sonnet-4-20250514",
  "balance_usdt": 105.20,
  "margin_used": 15.00,
  "unrealized_pnl": 3.30,
  "equity_usdt": 108.50,
  "total_trades": 15,
  "winning_trades": 10,
  "losing_trades": 5,
  "win_rate": 66.67,
  "total_realized_pnl": 5.20,
  "total_pnl": 8.50,
  "total_pnl_pct": 8.5,
  "open_positions_count": 2,
  "open_positions": [...]
}
```

**Status Codes**:
- `200 OK`: Success
- `404 Not Found`: LLM ID not found

---

### GET /trading/positions

**Description**: Get all open positions across all LLMs

**Response**:
```json
[
  {
    "id": "uuid-123",
    "llm_id": "LLM-A",
    "provider": "anthropic",
    "symbol": "ETHUSDT",
    "side": "LONG",
    "entry_price": 2000.00,
    "current_price": 2050.00,
    "quantity": 0.01,
    "leverage": 5,
    "margin": 4.00,
    "unrealized_pnl": 2.50,
    "unrealized_pnl_pct": 62.5,
    "liquidation_price": 1920.00,
    "stop_loss": 1960.00,
    "take_profit": 2100.00,
    "opened_at": "2025-11-11T10:00:00Z",
    "duration_seconds": 1800
  }
  // ... more positions
]
```

**Status Codes**:
- `200 OK`: Success (empty array if no positions)

---

### GET /trading/positions/{llm_id}

**Description**: Get open positions for specific LLM

**Path Parameters**:
- `llm_id` (string, required): LLM identifier

**Example**:
```
GET /trading/positions/LLM-A
```

**Response**: Same format as `/trading/positions` but filtered by LLM

**Status Codes**:
- `200 OK`: Success
- `404 Not Found`: LLM ID not found

---

### GET /trading/trades

**Description**: Get trade history for all LLMs

**Query Parameters**:
- `limit` (integer, optional, default=100): Maximum trades to return

**Example**:
```
GET /trading/trades?limit=50
```

**Response**:
```json
[
  {
    "id": "uuid-456",
    "llm_id": "LLM-A",
    "symbol": "ETHUSDT",
    "action": "BUY",
    "side": "LONG",
    "entry_price": 2000.00,
    "exit_price": 2050.00,
    "quantity": 0.01,
    "leverage": 5,
    "realized_pnl": 2.50,
    "pnl_percentage": 62.5,
    "fees": 0.05,
    "exit_reason": "TAKE_PROFIT",
    "executed_at": "2025-11-11T10:00:00Z",
    "closed_at": "2025-11-11T10:30:00Z",
    "duration_seconds": 1800
  }
  // ... more trades
]
```

**Status Codes**:
- `200 OK`: Success

---

### GET /trading/trades/{llm_id}

**Description**: Get trade history for specific LLM

**Path Parameters**:
- `llm_id` (string, required): LLM identifier

**Query Parameters**:
- `limit` (integer, optional, default=100): Maximum trades to return

**Example**:
```
GET /trading/trades/LLM-A?limit=20
```

**Response**: Same format as `/trading/trades` but filtered by LLM

**Status Codes**:
- `200 OK`: Success
- `404 Not Found`: LLM ID not found

---

### GET /trading/leaderboard

**Description**: Get LLM performance leaderboard

**Response**:
```json
[
  {
    "rank": 1,
    "llm_id": "LLM-A",
    "provider": "anthropic",
    "model_name": "claude-sonnet-4-20250514",
    "balance_usdt": 108.50,
    "total_pnl": 8.50,
    "roi_percentage": 8.5,
    "total_trades": 15,
    "win_rate": 66.67,
    "sharpe_ratio": 1.25,
    "max_drawdown": -5.2
  },
  {
    "rank": 2,
    "llm_id": "LLM-C",
    "provider": "openai",
    "model_name": "gpt-4o",
    "balance_usdt": 105.00,
    "total_pnl": 5.00,
    "roi_percentage": 5.0,
    "total_trades": 18,
    "win_rate": 61.11,
    "sharpe_ratio": 0.95,
    "max_drawdown": -3.8
  },
  {
    "rank": 3,
    "llm_id": "LLM-B",
    "provider": "deepseek",
    "model_name": "deepseek-reasoner",
    "balance_usdt": 102.00,
    "total_pnl": 2.00,
    "roi_percentage": 2.0,
    "total_trades": 12,
    "win_rate": 58.33,
    "sharpe_ratio": 0.75,
    "max_drawdown": -6.5
  }
]
```

**Status Codes**:
- `200 OK`: Success

---

## Market Data Endpoints

### GET /market/snapshot

**Description**: Get complete market snapshot for all symbols

**Response**:
```json
{
  "symbols": {
    "ETHUSDT": {
      "price": 2050.00,
      "price_change_pct_24h": 2.5,
      "volume_24h": 1500000.00,
      "high_24h": 2080.00,
      "low_24h": 1980.00
    },
    "BNBUSDT": {
      "price": 305.50,
      "price_change_pct_24h": 1.8,
      "volume_24h": 850000.00,
      "high_24h": 310.00,
      "low_24h": 298.00
    }
    // ... XRPUSDT, DOGEUSDT, ADAUSDT, AVAXUSDT
  },
  "summary": {
    "total_symbols": 6,
    "average_change_24h": 1.95,
    "total_volume_24h": 5500000.00,
    "last_updated": "2025-11-11T10:30:00Z"
  }
}
```

**Status Codes**:
- `200 OK`: Success

---

### GET /market/prices

**Description**: Get current prices for all symbols

**Response**:
```json
{
  "ETHUSDT": 2050.00,
  "BNBUSDT": 305.50,
  "XRPUSDT": 0.65,
  "DOGEUSDT": 0.085,
  "ADAUSDT": 0.58,
  "AVAXUSDT": 42.30,
  "timestamp": "2025-11-11T10:30:00Z"
}
```

**Status Codes**:
- `200 OK`: Success

---

### GET /market/price/{symbol}

**Description**: Get current price for specific symbol

**Path Parameters**:
- `symbol` (string, required): Trading pair (e.g., ETHUSDT)

**Example**:
```
GET /market/price/ETHUSDT
```

**Response**:
```json
{
  "symbol": "ETHUSDT",
  "price": 2050.00,
  "timestamp": "2025-11-11T10:30:00Z"
}
```

**Status Codes**:
- `200 OK`: Success
- `400 Bad Request`: Invalid symbol

---

### GET /market/ticker/{symbol}

**Description**: Get ticker data for specific symbol

**Path Parameters**:
- `symbol` (string, required): Trading pair

**Example**:
```
GET /market/ticker/ETHUSDT
```

**Response**:
```json
{
  "symbol": "ETHUSDT",
  "price": 2050.00,
  "bid": 2049.50,
  "ask": 2050.50,
  "volume_24h": 1500000.00,
  "price_change_24h": 50.00,
  "price_change_pct_24h": 2.5,
  "high_24h": 2080.00,
  "low_24h": 1980.00,
  "timestamp": "2025-11-11T10:30:00Z"
}
```

**Status Codes**:
- `200 OK`: Success
- `400 Bad Request`: Invalid symbol

---

### GET /market/indicators/{symbol}

**Description**: Get technical indicators for specific symbol

**Path Parameters**:
- `symbol` (string, required): Trading pair

**Query Parameters**:
- `interval` (string, optional, default="1h"): Candlestick interval

**Example**:
```
GET /market/indicators/ETHUSDT?interval=1h
```

**Response**:
```json
{
  "symbol": "ETHUSDT",
  "interval": "1h",
  "indicators": {
    "sma_20": 2035.50,
    "sma_50": 2020.00,
    "ema_12": 2045.00,
    "ema_26": 2030.00,
    "rsi_14": 62.5,
    "macd": 5.5,
    "macd_signal": 4.2,
    "bollinger_upper": 2080.00,
    "bollinger_middle": 2035.00,
    "bollinger_lower": 1990.00
  },
  "timestamp": "2025-11-11T10:30:00Z"
}
```

**Status Codes**:
- `200 OK`: Success
- `400 Bad Request`: Invalid symbol or interval

---

## Scheduler Endpoints

### GET /scheduler/status

**Description**: Get background scheduler status

**Response**:
```json
{
  "is_running": true,
  "is_paused": false,
  "total_executions": 142,
  "total_errors": 3,
  "last_execution_at": "2025-11-11T10:25:00Z",
  "last_execution_duration_seconds": 2.5,
  "last_execution_status": "SUCCESS",
  "next_run_at": "2025-11-11T10:30:00Z",
  "interval_minutes": 5
}
```

**Status Codes**:
- `200 OK`: Success

---

### POST /scheduler/trigger

**Description**: Manually trigger a trading cycle

**Response**:
```json
{
  "status": "triggered",
  "message": "Trading cycle triggered manually",
  "cycle_id": "uuid-789",
  "triggered_at": "2025-11-11T10:30:00Z"
}
```

**Status Codes**:
- `200 OK`: Cycle triggered successfully
- `409 Conflict`: Cycle already running

---

### POST /scheduler/pause

**Description**: Pause the background scheduler

**Response**:
```json
{
  "status": "paused",
  "message": "Scheduler paused successfully",
  "paused_at": "2025-11-11T10:30:00Z"
}
```

**Status Codes**:
- `200 OK`: Scheduler paused
- `400 Bad Request`: Already paused

---

### POST /scheduler/resume

**Description**: Resume the background scheduler

**Response**:
```json
{
  "status": "resumed",
  "message": "Scheduler resumed successfully",
  "resumed_at": "2025-11-11T10:30:00Z",
  "next_run_at": "2025-11-11T10:35:00Z"
}
```

**Status Codes**:
- `200 OK`: Scheduler resumed
- `400 Bad Request`: Not paused

---

### GET /scheduler/stats

**Description**: Get detailed scheduler statistics

**Response**:
```json
{
  "total_executions": 142,
  "successful_executions": 139,
  "failed_executions": 3,
  "success_rate": 97.89,
  "total_errors": 3,
  "average_duration_seconds": 2.3,
  "min_duration_seconds": 1.8,
  "max_duration_seconds": 4.2,
  "last_10_executions": [
    {
      "cycle_id": "uuid-789",
      "status": "SUCCESS",
      "duration_seconds": 2.1,
      "executed_at": "2025-11-11T10:25:00Z",
      "llms_processed": 3
    }
    // ... 9 more
  ]
}
```

**Status Codes**:
- `200 OK`: Success

---

### GET /scheduler/next-run

**Description**: Get next scheduled execution time

**Response**:
```json
{
  "next_run_at": "2025-11-11T10:35:00Z",
  "seconds_until_next_run": 300,
  "interval_minutes": 5
}
```

**Status Codes**:
- `200 OK`: Success

---

## WebSocket API

### WS /ws

**Description**: WebSocket connection for real-time updates

**Connection**:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  console.log('Connected');
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message);
};

ws.onclose = () => {
  console.log('Disconnected');
};
```

**Message Format**:
```json
{
  "type": "event_type",
  "data": {...},
  "timestamp": "2025-11-11T10:30:00Z"
}
```

**Event Types**:

**connection**:
```json
{
  "type": "connection",
  "data": {
    "client_id": "uuid-123",
    "connected_at": "2025-11-11T10:30:00Z"
  },
  "timestamp": "2025-11-11T10:30:00Z"
}
```

**cycle_start**:
```json
{
  "type": "cycle_start",
  "data": {
    "cycle_id": "uuid-456",
    "started_at": "2025-11-11T10:30:00Z"
  },
  "timestamp": "2025-11-11T10:30:00Z"
}
```

**cycle_complete**:
```json
{
  "type": "cycle_complete",
  "data": {
    "cycle_id": "uuid-456",
    "status": "SUCCESS",
    "duration_seconds": 2.5,
    "llms_processed": 3,
    "positions_opened": 2,
    "positions_closed": 1,
    "completed_at": "2025-11-11T10:30:02Z"
  },
  "timestamp": "2025-11-11T10:30:02Z"
}
```

**llm_decision**:
```json
{
  "type": "llm_decision",
  "data": {
    "llm_id": "LLM-A",
    "decision": {
      "action": "BUY",
      "symbol": "ETHUSDT",
      "side": "LONG",
      "size_usd": 20.00,
      "leverage": 5,
      "confidence": 0.75,
      "reasoning": "Bullish trend identified..."
    },
    "approved": true,
    "executed": true
  },
  "timestamp": "2025-11-11T10:30:01Z"
}
```

**position_update**:
```json
{
  "type": "position_update",
  "data": {
    "action": "OPENED",
    "position": {
      "id": "uuid-789",
      "llm_id": "LLM-A",
      "symbol": "ETHUSDT",
      "side": "LONG",
      "entry_price": 2050.00,
      "quantity": 0.01,
      "leverage": 5,
      "margin": 4.00
    }
  },
  "timestamp": "2025-11-11T10:30:01Z"
}
```

**Client Messages** (send to server):

**ping**:
```json
{
  "type": "ping"
}
```

Response:
```json
{
  "type": "pong",
  "timestamp": "2025-11-11T10:30:00Z"
}
```

---

### GET /ws/stats

**Description**: Get WebSocket connection statistics

**Response**:
```json
{
  "active_connections": 3,
  "total_connections_made": 15,
  "messages_sent": 1250,
  "messages_received": 45,
  "uptime_seconds": 3600
}
```

**Status Codes**:
- `200 OK`: Success

---

## Response Models

### Common Fields

All successful responses include:
- Relevant data fields
- `timestamp` (ISO 8601 format)

All error responses include:
- `error` (error type)
- `message` (human-readable message)
- `timestamp`

---

## Error Handling

### HTTP Status Codes

- `200 OK`: Request successful
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource conflict (e.g., scheduler already running)
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service temporarily unavailable

### Error Response Format

```json
{
  "error": "ErrorType",
  "message": "Human-readable error message",
  "details": {
    "field": "Additional error details"
  },
  "timestamp": "2025-11-11T10:30:00Z"
}
```

### Common Errors

**Invalid LLM ID**:
```json
{
  "error": "NotFound",
  "message": "LLM ID 'LLM-X' not found",
  "timestamp": "2025-11-11T10:30:00Z"
}
```

**Invalid Symbol**:
```json
{
  "error": "BadRequest",
  "message": "Invalid trading symbol 'INVALID'",
  "timestamp": "2025-11-11T10:30:00Z"
}
```

**Scheduler Already Running**:
```json
{
  "error": "Conflict",
  "message": "Trading cycle already in progress",
  "timestamp": "2025-11-11T10:30:00Z"
}
```

---

## Rate Limiting

**Current**: No rate limiting (development mode)

**Production Recommendations**:
- 100 requests per minute per IP
- 1000 requests per hour per API key
- WebSocket: 5 connections per IP

---

## Interactive API Documentation

Access interactive API docs:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

---

**Complete API with 23 endpoints + WebSocket for real-time trading data.** 📡
