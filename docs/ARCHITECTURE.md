# Crypto LLM Trading System - Architecture Documentation

Complete architectural documentation for the **Crypto LLM Trading System** - a multi-LLM automated cryptocurrency trading platform.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Diagrams](#architecture-diagrams)
3. [Component Architecture](#component-architecture)
4. [Data Flow](#data-flow)
5. [Database Schema](#database-schema)
6. [API Architecture](#api-architecture)
7. [Background Jobs](#background-jobs)
8. [Design Patterns](#design-patterns)
9. [Technology Stack](#technology-stack)

---

## System Overview

### High-Level Description

The Crypto LLM Trading System is an **autonomous trading platform** where three Large Language Models compete in cryptocurrency futures trading on Binance. Each LLM starts with a virtual $100 balance and makes independent trading decisions every 5 minutes.

### Key Features

- **3 Competing LLMs**: Claude Sonnet 4, DeepSeek Reasoner, GPT-4o
- **Automated Trading**: 5-minute cycles with autonomous decision-making
- **Real-time Monitoring**: WebSocket dashboard with live updates
- **Complete Audit Trail**: All decisions, trades, and positions logged
- **Risk Management**: Built-in limits and validation
- **RESTful API**: 23 endpoints for data access
- **Performance Tracking**: Leaderboard, PnL, win rates

### Design Goals

1. **Autonomous**: Fully automated trading without human intervention
2. **Fair Competition**: Equal starting capital and access to data
3. **Transparent**: Complete audit trail of all decisions
4. **Reliable**: Error handling and recovery mechanisms
5. **Scalable**: Modular architecture for easy extension
6. **Observable**: Real-time monitoring and reporting

---

## Architecture Diagrams

### System Architecture (High-Level)

```
┌─────────────────────────────────────────────────────────────────────┐
│                     CRYPTO LLM TRADING SYSTEM                        │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────┐         ┌─────────────────┐         ┌─────────────┐
│   FRONTEND      │         │    BACKEND      │         │  EXTERNAL   │
│   LAYER         │         │    LAYER        │         │  SERVICES   │
└─────────────────┘         └─────────────────┘         └─────────────┘

┌─────────────────┐         ┌─────────────────┐         ┌─────────────┐
│  Dashboard      │◄────────│  FastAPI        │         │  Binance    │
│  (HTML/JS)      │  WebSocket│  Application   │◄────────│  Futures    │
│                 │         │                 │  REST   │  API        │
│  - Live Updates │         │  - 23 Endpoints │         │             │
│  - Leaderboard  │         │  - WebSocket    │         │  - Market   │
│  - Positions    │         │  - Background   │         │    Data     │
│  - Trades       │         │    Jobs         │         │  - Account  │
└─────────────────┘         └─────────────────┘         │    Info     │
                                    │                    └─────────────┘
                                    │
                                    ▼                    ┌─────────────┐
                            ┌───────────────┐            │  Supabase   │
                            │  SERVICES     │◄───────────│  PostgreSQL │
                            │  LAYER        │   SQL      │             │
                            └───────────────┘            │  - Accounts │
                                    │                    │  - Positions│
                                    │                    │  - Trades   │
                                    ▼                    └─────────────┘
                            ┌───────────────┐
                            │  CORE         │            ┌─────────────┐
                            │  LOGIC        │            │  LLM APIs   │
                            └───────────────┘            │             │
                                    │                    │  - Claude   │
                                    │                    │  - DeepSeek │
                                    └────────────────────│  - GPT-4o   │
                                                         └─────────────┘
```

### Layer Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          LAYER ARCHITECTURE                          │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  PRESENTATION LAYER                                                  │
│  - FastAPI Routes (REST + WebSocket)                                │
│  - Request/Response Models (Pydantic)                               │
│  - Static File Serving (Dashboard)                                  │
└─────────────────────────────────────────────────────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  SERVICE LAYER                                                       │
│  - TradingService (orchestration)                                   │
│  - AccountService (account management)                              │
│  - MarketDataService (data aggregation)                            │
└─────────────────────────────────────────────────────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  CORE BUSINESS LOGIC                                                │
│  - LLMDecisionService (decision making)                             │
│  - PositionManager (position lifecycle)                             │
│  - RiskManager (validation & limits)                                │
└─────────────────────────────────────────────────────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  DATA ACCESS LAYER                                                   │
│  - SupabaseClient (database operations)                             │
│  - BinanceClient (market data & trading)                            │
│  - LLMClients (AI decision making)                                  │
└─────────────────────────────────────────────────────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  EXTERNAL SERVICES                                                   │
│  - Supabase (PostgreSQL database)                                   │
│  - Binance Futures API (market & trading)                           │
│  - Anthropic API (Claude Sonnet 4)                                  │
│  - DeepSeek API (DeepSeek Reasoner)                                 │
│  - OpenAI API (GPT-4o)                                              │
└─────────────────────────────────────────────────────────────────────┘
```

### Trading Cycle Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                      TRADING CYCLE WORKFLOW                          │
│                      (Executes every 5 minutes)                      │
└─────────────────────────────────────────────────────────────────────┘

     START
       │
       ▼
┌──────────────┐
│  Scheduler   │  APScheduler triggers cycle
│  Trigger     │
└──────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────┐
│  STEP 1: Fetch Market Data                                       │
│  - Get current prices for 6 symbols                              │
│  - Fetch 100 candlesticks for technical analysis                 │
│  - Update market snapshot in memory                              │
└──────────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────┐
│  STEP 2: Process Each LLM (Parallel)                            │
│                                                                   │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                │
│  │  LLM-A     │  │  LLM-B     │  │  LLM-C     │                │
│  │  (Claude)  │  │  (DeepSeek)│  │  (GPT-4o)  │                │
│  └────────────┘  └────────────┘  └────────────┘                │
│       │               │               │                          │
│       ▼               ▼               ▼                          │
│  ┌─────────────────────────────────────────┐                    │
│  │  2.1: Get LLM Decision                  │                    │
│  │  - Send market data + account state     │                    │
│  │  - LLM analyzes and returns decision    │                    │
│  │  - Parse decision (BUY/SELL/HOLD)       │                    │
│  └─────────────────────────────────────────┘                    │
│       │                                                          │
│       ▼                                                          │
│  ┌─────────────────────────────────────────┐                    │
│  │  2.2: Risk Validation                   │                    │
│  │  - Check balance sufficient             │                    │
│  │  - Validate leverage within limits      │                    │
│  │  - Verify position limit not exceeded   │                    │
│  │  - Check exposure limits                │                    │
│  └─────────────────────────────────────────┘                    │
│       │                                                          │
│       ▼                                                          │
│  ┌─────────────────────────────────────────┐                    │
│  │  2.3: Execute Decision                  │                    │
│  │  - If BUY/SELL: Open position           │                    │
│  │  - If HOLD: Skip                        │                    │
│  │  - Update account balance               │                    │
│  │  - Record trade in database             │                    │
│  └─────────────────────────────────────────┘                    │
└──────────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────┐
│  STEP 3: Update Open Positions                                   │
│  - Check all open positions                                      │
│  - Update current prices                                         │
│  - Calculate unrealized PnL                                      │
│  - Check stop loss / take profit triggers                        │
│  - Close positions if triggered                                  │
└──────────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────┐
│  STEP 4: Broadcast Updates                                       │
│  - Send cycle complete event to WebSocket clients                │
│  - Update dashboard with new data                                │
│  - Log cycle execution stats                                     │
└──────────────────────────────────────────────────────────────────┘
       │
       ▼
     END
```

---

## Component Architecture

### Service Layer Components

```
TradingService (Orchestrator)
├── execute_trading_cycle()
│   ├── Update market data
│   ├── Process all LLMs
│   ├── Update positions
│   └── Broadcast events
├── get_trading_status()
├── get_llm_account()
├── get_all_positions()
└── get_leaderboard()

AccountService (Account Management)
├── get_all_accounts()
├── get_account(llm_id)
├── update_balance()
├── update_stats()
└── get_summary()

MarketDataService (Market Data)
├── update_market_data()
├── get_current_price(symbol)
├── get_market_snapshot()
├── get_technical_indicators()
└── get_ticker_data()
```

### Core Logic Components

```
LLMDecisionService (Decision Making)
├── get_trading_decision(llm_id)
│   ├── Prepare market context
│   ├── Call LLM API
│   ├── Parse response
│   └── Return decision
└── process_all_llms()

PositionManager (Position Lifecycle)
├── open_position()
│   ├── Validate decision
│   ├── Calculate margin
│   ├── Create position record
│   └── Update account
├── close_position()
│   ├── Calculate PnL
│   ├── Update account balance
│   └── Record trade
└── update_positions()

RiskManager (Risk Validation)
├── validate_decision()
│   ├── Check balance
│   ├── Validate leverage
│   ├── Check position limits
│   └── Verify exposure
└── check_liquidation()
```

### Data Access Components

```
SupabaseClient (Database)
├── Account Operations
│   ├── get_llm_account()
│   ├── get_all_llm_accounts()
│   ├── update_llm_balance()
│   └── update_llm_stats()
├── Position Operations
│   ├── create_position()
│   ├── get_open_positions()
│   ├── update_position()
│   └── close_position()
├── Trade Operations
│   ├── create_trade()
│   └── get_trades()
└── Views & Analytics
    ├── get_llm_leaderboard()
    ├── get_active_positions_summary()
    └── get_llm_trading_stats()

BinanceClient (Market Data & Trading)
├── get_ticker()
├── get_klines()
├── get_account_balance()
└── Connection management

LLMClients (AI Decisions)
├── ClaudeClient (Anthropic)
├── DeepSeekClient
└── OpenAIClient
    └── get_trading_decision()
```

---

## Data Flow

### Complete Trading Cycle Data Flow

```
1. TRIGGER
   APScheduler → TradingService.execute_trading_cycle()

2. MARKET DATA FETCH
   TradingService → MarketDataService → BinanceClient
   │
   └─► Get prices for 6 symbols
       Get candlestick data (100 candles)
       Calculate technical indicators
       Store in memory cache

3. LLM DECISION (for each LLM)
   TradingService → LLMDecisionService → LLMClient (API)
   │
   ├─► Prepare context:
   │   - Current account state (balance, positions, PnL)
   │   - Market data (prices, trends, indicators)
   │   - Trading constraints (limits, rules)
   │
   ├─► Call LLM API:
   │   - Send prompt with context
   │   - Receive decision (BUY/SELL/HOLD + reasoning)
   │
   └─► Parse & validate response

4. RISK VALIDATION
   TradingService → RiskManager
   │
   └─► Check:
       - Balance ≥ margin required
       - Leverage ≤ max_leverage (10x)
       - Open positions < max_positions (3)
       - Size within limits ($10-$30)

       Result: APPROVED / REJECTED (with reason)

5. POSITION EXECUTION (if approved)
   TradingService → PositionManager → SupabaseClient
   │
   ├─► Create position record
   ├─► Calculate margin & liquidation price
   ├─► Update account balance (deduct margin)
   ├─► Create trade record
   └─► Log to database

6. POSITION UPDATES
   TradingService → PositionManager → BinanceClient + SupabaseClient
   │
   ├─► For each open position:
   │   - Fetch current price
   │   - Calculate unrealized PnL
   │   - Check SL/TP triggers
   │   - Close if triggered
   │
   └─► Update database with new prices

7. WEBSOCKET BROADCAST
   TradingService → WebSocketManager → Connected Clients
   │
   └─► Broadcast events:
       - cycle_start
       - llm_decision (for each LLM)
       - position_update
       - cycle_complete

8. LOGGING
   TradingService → Logger
   │
   └─► Log to files:
       - logs/app.log (general logs)
       - logs/llm_decisions.log (decision audit trail)
```

---

## Database Schema

### Entity Relationship Diagram

```
┌─────────────────────┐
│   llm_accounts      │  (Master table for LLM accounts)
│   PK: llm_id        │
├─────────────────────┤
│ llm_id (VARCHAR)    │
│ provider            │
│ model_name          │
│ balance (DECIMAL)   │
│ margin_used         │
│ total_pnl           │
│ realized_pnl        │
│ unrealized_pnl      │
│ total_trades (INT)  │
│ winning_trades      │
│ losing_trades       │
│ open_positions      │
│ is_active (BOOL)    │
│ ...                 │
└─────────────────────┘
         │
         │ 1:N
         ▼
┌─────────────────────┐
│    positions        │  (Trading positions)
│    PK: id (UUID)    │
├─────────────────────┤
│ id                  │
│ llm_id (FK) ────────┼─► llm_accounts
│ symbol              │
│ side (LONG/SHORT)   │
│ entry_price         │
│ current_price       │
│ quantity            │
│ leverage            │
│ margin              │
│ unrealized_pnl      │
│ liquidation_price   │
│ stop_loss           │
│ take_profit         │
│ status (ENUM)       │
│ opened_at           │
│ closed_at           │
└─────────────────────┘
         │
         │ 1:N
         ▼
┌─────────────────────┐
│      trades         │  (Trade history)
│    PK: id (UUID)    │
├─────────────────────┤
│ id                  │
│ llm_id (FK) ────────┼─► llm_accounts
│ position_id (FK) ───┼─► positions
│ symbol              │
│ action (BUY/SELL)   │
│ side                │
│ entry_price         │
│ exit_price          │
│ quantity            │
│ realized_pnl        │
│ pnl_percentage      │
│ fees                │
│ exit_reason         │
│ executed_at         │
│ closed_at           │
└─────────────────────┘

┌─────────────────────┐
│   market_data       │  (Market snapshots)
│   PK: id (UUID)     │
├─────────────────────┤
│ symbol              │
│ price               │
│ volume_24h          │
│ price_change_24h    │
│ high_24h            │
│ low_24h             │
│ data_timestamp      │
└─────────────────────┘

┌─────────────────────┐
│rejected_decisions   │  (Audit trail)
│   PK: id (UUID)     │
├─────────────────────┤
│ llm_id (FK) ────────┼─► llm_accounts
│ symbol              │
│ decision            │
│ reasoning           │
│ rejection_reason    │
│ confidence          │
│ created_at          │
└─────────────────────┘

┌─────────────────────┐
│  llm_api_calls      │  (API usage tracking)
│   PK: id (UUID)     │
├─────────────────────┤
│ llm_id (FK) ────────┼─► llm_accounts
│ provider            │
│ model               │
│ response_time_ms    │
│ prompt_tokens       │
│ completion_tokens   │
│ estimated_cost      │
│ success (BOOL)      │
│ called_at           │
└─────────────────────┘
```

### Database Views

**llm_leaderboard**:
- Aggregated performance metrics per LLM
- Sorted by balance DESC, total_pnl DESC
- Calculated fields: ROI %, win rate

**active_positions_summary**:
- All open positions with current PnL
- Joined with account info
- Calculated duration and PnL %

**llm_trading_stats**:
- Comprehensive trading statistics per LLM
- Aggregated position and trade data
- Current market exposure

---

## API Architecture

### REST API Endpoints (23 total)

```
Health Endpoints (2)
├── GET  /                    # API root
└── GET  /health              # Health check

Trading Endpoints (8)
├── GET  /trading/status      # Overall trading status
├── GET  /trading/accounts    # All LLM accounts
├── GET  /trading/accounts/{llm_id}  # Specific account
├── GET  /trading/positions   # All positions
├── GET  /trading/positions/{llm_id}  # LLM positions
├── GET  /trading/trades      # All trades
├── GET  /trading/trades/{llm_id}     # LLM trades
└── GET  /trading/leaderboard # LLM rankings

Market Endpoints (5)
├── GET  /market/snapshot     # All market data
├── GET  /market/prices       # Current prices
├── GET  /market/price/{symbol}       # Symbol price
├── GET  /market/ticker/{symbol}      # Ticker data
└── GET  /market/indicators/{symbol}  # Technical indicators

Scheduler Endpoints (6)
├── GET  /scheduler/status    # Scheduler state
├── POST /scheduler/trigger   # Manual cycle
├── POST /scheduler/pause     # Pause scheduler
├── POST /scheduler/resume    # Resume scheduler
├── GET  /scheduler/stats     # Job statistics
└── GET  /scheduler/next-run  # Next execution

WebSocket Endpoints (2)
├── WS   /ws                  # WebSocket connection
└── GET  /ws/stats            # Connection stats
```

### WebSocket Protocol

**Message Format**:
```json
{
  "type": "event_type",
  "data": {...},
  "timestamp": "2025-11-11T10:30:00Z"
}
```

**Event Types**:
- `connection` - Client connected
- `initial_data` - Initial state sent
- `market_snapshot` - Market data update
- `scheduler_status` - Scheduler state
- `cycle_start` - Trading cycle starting
- `cycle_complete` - Trading cycle completed
- `llm_decision` - LLM made decision
- `position_update` - Position opened/closed
- `account_update` - Account balance changed
- `error` - Error occurred

---

## Background Jobs

### APScheduler Configuration

```python
BackgroundScheduler(
    timezone="UTC",
    job_defaults={
        "coalesce": True,        # Combine missed runs
        "max_instances": 1,      # One job at a time
        "misfire_grace_time": 30 # 30s grace for delayed starts
    }
)
```

### Scheduled Jobs

**1. Trading Cycle Job**
- Interval: 5 minutes
- Function: `execute_trading_cycle()`
- Concurrency: Protected (skip if previous running)

**2. Health Check Job**
- Interval: 15 minutes
- Function: `health_check_job()`
- Purpose: Monitor system health

**3. Account Sync Job**
- Interval: 10 minutes
- Function: `sync_accounts_job()`
- Purpose: Sync account data with database

---

## Design Patterns

### Patterns Used

**1. Singleton Pattern**
- Used for: Service instances, database connections
- Example: `get_supabase_client()`, `get_trading_service()`

**2. Dependency Injection**
- Used for: FastAPI route dependencies
- Example: `Depends(get_trading_service_dependency)`

**3. Factory Pattern**
- Used for: LLM client creation
- Example: `get_llm_client(llm_id)`

**4. Strategy Pattern**
- Used for: Different LLM providers
- Example: `ClaudeClient`, `DeepSeekClient`, `OpenAIClient`

**5. Observer Pattern**
- Used for: WebSocket event broadcasting
- Example: `WebSocketManager.broadcast()`

**6. Repository Pattern**
- Used for: Database access abstraction
- Example: `SupabaseClient` wraps all DB operations

---

## Technology Stack

### Backend

- **Framework**: FastAPI 0.104+
- **Python**: 3.9+
- **ASGI Server**: Uvicorn
- **Scheduler**: APScheduler 3.10+
- **Database Client**: Supabase Python SDK
- **HTTP Client**: HTTPX (async)
- **Validation**: Pydantic v2

### External Services

- **Database**: Supabase (PostgreSQL 15)
- **Market Data**: Binance Futures API
- **LLM Providers**:
  - Anthropic (Claude API)
  - DeepSeek (API)
  - OpenAI (API)

### Frontend

- **UI**: HTML5 + CSS3 + JavaScript (Vanilla)
- **WebSocket**: Native WebSocket API
- **Styling**: Custom CSS (dark theme)

### Development Tools

- **Testing**: pytest + pytest-cov
- **Code Quality**: Type hints (Python 3.9+)
- **Logging**: Python logging module
- **Environment**: python-dotenv

---

## Performance Considerations

### Optimization Strategies

**1. Market Data Caching**
- Cache duration: 60 seconds
- Reduces Binance API calls

**2. Database Connection Pooling**
- Supabase client reuses connections
- Singleton pattern for clients

**3. Async Operations**
- FastAPI runs on asyncio
- Non-blocking I/O for all external calls

**4. Risk Validation Performance**
- In-memory calculations
- < 1ms per validation

**5. WebSocket Broadcasting**
- Efficient message serialization
- Handles multiple concurrent connections

---

**Architecture designed for reliability, scalability, and maintainability.** 🏗️
