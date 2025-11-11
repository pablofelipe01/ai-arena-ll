# Crypto LLM Trading System - Setup Guide

Complete setup guide for the **Crypto LLM Trading System** - an automated cryptocurrency trading platform where 3 AI models (Claude Sonnet 4, DeepSeek Reasoner, GPT-4o) compete in live trading.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Database Setup](#database-setup)
4. [Configuration](#configuration)
5. [Running the System](#running-the-system)
6. [Accessing the Dashboard](#accessing-the-dashboard)
7. [Troubleshooting](#troubleshooting)
8. [Architecture Overview](#architecture-overview)

---

## Prerequisites

### Required Software

- **Python 3.9+** ([Download](https://www.python.org/downloads/))
- **Git** ([Download](https://git-scm.com/downloads))
- **Supabase Account** ([Sign up](https://supabase.com))
- **Binance Account** ([Sign up](https://www.binance.com))

### API Keys Required

You'll need API keys from:

1. **Binance** (for market data and trading)
   - Get Testnet keys: [Binance Testnet](https://testnet.binancefuture.com)
   - Production: [Binance API Management](https://www.binance.com/en/my/settings/api-management)

2. **Supabase** (for database)
   - Create project at [Supabase Dashboard](https://app.supabase.com)
   - Get URL and anon key from Settings > API

3. **Anthropic** (for Claude Sonnet 4 - LLM-A)
   - Get API key: [Anthropic Console](https://console.anthropic.com)

4. **DeepSeek** (for DeepSeek Reasoner - LLM-B)
   - Get API key: [DeepSeek Platform](https://platform.deepseek.com)

5. **OpenAI** (for GPT-4o - LLM-C)
   - Get API key: [OpenAI Platform](https://platform.openai.com)

---

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd crypto-llm-trading
```

### 2. Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install all required packages:
- FastAPI
- Uvicorn
- Supabase
- Anthropic
- OpenAI
- APScheduler
- And more...

---

## Database Setup

### 1. Create Supabase Project

1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Click **"New Project"**
3. Fill in project details:
   - Name: `crypto-llm-trading`
   - Database Password: (choose a strong password)
   - Region: (select closest to you)
4. Wait for project to be created (~2 minutes)

### 2. Get Supabase Credentials

Once project is ready:

1. Go to **Settings** > **API**
2. Copy:
   - **Project URL** (e.g., `https://xxxxx.supabase.co`)
   - **anon/public key** (starts with `eyJh...`)

### 3. Initialize Database Schema

1. Go to **SQL Editor** in Supabase Dashboard
2. Click **"New Query"**
3. Open `scripts/schema.sql` from this project
4. Copy entire SQL content and paste into query editor
5. Click **"Run"**
6. Verify tables were created:
   - Go to **Table Editor**
   - You should see 7 tables: `llm_accounts`, `positions`, `trades`, `orders`, `market_data`, `rejected_decisions`, `llm_api_calls`

### 4. Verify Database Initialization

```bash
python scripts/init_database.py --verify
```

You should see:
```
✅ llm_accounts
✅ positions
✅ trades
✅ orders
✅ market_data
✅ rejected_decisions
✅ llm_api_calls
```

---

## Configuration

### 1. Create `.env` File

Copy the example environment file:

```bash
cp .env.example .env
```

### 2. Configure Environment Variables

Edit `.env` file with your credentials:

```env
# ============================================================================
# ENVIRONMENT
# ============================================================================
ENVIRONMENT=development
DEBUG=True
USE_TESTNET=True  # IMPORTANT: Set to True for testing!

# ============================================================================
# BINANCE API
# ============================================================================
BINANCE_API_KEY=your_binance_testnet_api_key
BINANCE_SECRET_KEY=your_binance_testnet_secret_key
BINANCE_BASE_URL=https://testnet.binancefuture.com

# ============================================================================
# SUPABASE DATABASE
# ============================================================================
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJh...your_supabase_anon_key

# ============================================================================
# LLM API KEYS
# ============================================================================

# LLM-A: Claude Sonnet 4 (Anthropic)
LLM_A_PROVIDER=anthropic
LLM_A_MODEL=claude-sonnet-4-20250514
LLM_A_API_KEY=sk-ant-...your_anthropic_key
LLM_A_TEMPERATURE=0.7

# LLM-B: DeepSeek Reasoner
LLM_B_PROVIDER=deepseek
LLM_B_MODEL=deepseek-reasoner
LLM_B_API_KEY=sk-...your_deepseek_key
LLM_B_TEMPERATURE=0.7

# LLM-C: GPT-4o (OpenAI)
LLM_C_PROVIDER=openai
LLM_C_MODEL=gpt-4o
LLM_C_API_KEY=sk-...your_openai_key
LLM_C_TEMPERATURE=0.7

# ============================================================================
# TRADING CONFIGURATION
# ============================================================================
AVAILABLE_PAIRS=ETHUSDT,BNBUSDT,XRPUSDT,DOGEUSDT,ADAUSDT,AVAXUSDT
MIN_TRADE_SIZE_USD=10.0
MAX_TRADE_SIZE_USD=30.0
MAX_LEVERAGE=10
MAX_OPEN_POSITIONS=3
INITIAL_BALANCE_USD=100.0

# ============================================================================
# BACKGROUND JOBS
# ============================================================================
LLM_DECISION_INTERVAL_SECONDS=300  # 5 minutes
UPDATE_MARKET_DATA_INTERVAL=60     # 1 minute
```

### 3. Verify Configuration

Run the configuration verification script:

```bash
python scripts/verify_config.py
```

You should see all checks pass:
```
✅ Environment: development
✅ Debug: True
✅ Use Testnet: True
✅ Binance Config
✅ Supabase Config
✅ LLM Configuration
   ✅ LLM-A: Claude Sonnet 4
   ✅ LLM-B: DeepSeek Reasoner
   ✅ LLM-C: GPT-4o
✅ Trading Config
```

---

## Running the System

### Option 1: Using Shell Script (macOS/Linux)

```bash
./scripts/start.sh
```

With options:
```bash
# Verify config before starting
./scripts/start.sh --verify

# Use custom port
./scripts/start.sh --port 8080

# Disable auto-reload (production)
./scripts/start.sh --no-reload
```

### Option 2: Using Python Script (Cross-Platform)

```bash
python scripts/start.py
```

With options:
```bash
# Verify config before starting
python scripts/start.py --verify

# Use custom port
python scripts/start.py --port 8080

# Disable auto-reload (production)
python scripts/start.py --no-reload
```

### Option 3: Using Uvicorn Directly

```bash
uvicorn src.api.main:app --reload --port 8000
```

### Startup Output

When system starts successfully, you'll see:

```
============================================================================
  🚀 CRYPTO LLM TRADING SYSTEM
============================================================================

✅ Python 3.11.5
✅ .env file found
✅ All dependencies installed

============================================================================
📊 STARTUP CONFIGURATION
============================================================================
  Host:              0.0.0.0
  Port:              8000
  Auto-reload:       True
  Dashboard URL:     http://localhost:8000/dashboard/
  API Docs:          http://localhost:8000/docs
  WebSocket:         ws://localhost:8000/ws
============================================================================

🤖 ACTIVE LLMs:
  • LLM-A - Claude Sonnet 4
  • LLM-B - DeepSeek Reasoner
  • LLM-C - GPT-4o

📈 TRADING CONFIGURATION:
  • 6 symbols - ETH, BNB, XRP, DOGE, ADA, AVAX
  • 5-minute cycles - Automated trading
  • $100 per LLM - Virtual balance

💻 FEATURES:
  • Real-time WebSocket dashboard
  • Automated 5-minute trading cycles
  • REST API (23 endpoints)
  • Live market data
  • LLM leaderboard
  • Position tracking

============================================================================
🚀 STARTING SERVER...
============================================================================
```

---

## Accessing the Dashboard

Once the server is running:

### 1. WebSocket Dashboard (Real-Time Monitoring)

Open in browser: **http://localhost:8000/dashboard/**

Features:
- Live activity log (real-time events)
- System summary (equity, PnL, trades)
- LLM leaderboard (ranked by performance)
- Market data (6 symbols with prices)
- Open positions (all LLMs)
- Recent trades (last 10)
- Scheduler status

### 2. API Documentation

**Swagger UI**: http://localhost:8000/docs
**ReDoc**: http://localhost:8000/redoc

### 3. API Endpoints

#### Health
- `GET /` - API root
- `GET /health` - Health check

#### Trading (16 endpoints)
- `GET /trading/status` - Overall trading status
- `GET /trading/accounts` - All LLM accounts
- `GET /trading/accounts/{llm_id}` - Specific LLM account
- `GET /trading/positions` - All open positions
- `GET /trading/positions/{llm_id}` - LLM positions
- `GET /trading/trades` - Trade history
- `GET /trading/trades/{llm_id}` - LLM trades
- `GET /trading/leaderboard` - LLM rankings

#### Market (5 endpoints)
- `GET /market/snapshot` - All market data
- `GET /market/prices` - Current prices
- `GET /market/price/{symbol}` - Symbol price
- `GET /market/ticker/{symbol}` - Ticker data
- `GET /market/indicators/{symbol}` - Technical indicators

#### Scheduler (6 endpoints)
- `GET /scheduler/status` - Scheduler state
- `POST /scheduler/trigger` - Manual trading cycle
- `POST /scheduler/pause` - Pause scheduler
- `POST /scheduler/resume` - Resume scheduler
- `GET /scheduler/stats` - Job statistics
- `GET /scheduler/next-run` - Next execution time

#### WebSocket
- `WS /ws` - Real-time dashboard connection
- `GET /ws/stats` - WebSocket statistics

---

## Troubleshooting

### Common Issues

#### 1. "ModuleNotFoundError: No module named 'X'"

**Solution**: Install dependencies
```bash
pip install -r requirements.txt
```

#### 2. ".env file not found"

**Solution**: Create `.env` file from template
```bash
cp .env.example .env
# Then edit .env with your credentials
```

#### 3. "Failed to connect to Supabase"

**Solutions**:
- Verify `SUPABASE_URL` and `SUPABASE_KEY` in `.env`
- Check if database tables were created (run `schema.sql`)
- Verify Supabase project is active

#### 4. "Binance API Error"

**Solutions**:
- For testing, use `USE_TESTNET=True`
- Get testnet keys from: https://testnet.binancefuture.com
- Verify API key permissions include "Futures" trading

#### 5. "LLM API Error"

**Solutions**:
- Check API key is correct in `.env`
- Verify API key has sufficient credits
- Check rate limits aren't exceeded

#### 6. Port Already in Use

**Solution**: Use different port
```bash
python scripts/start.py --port 8080
```

#### 7. Dashboard Not Loading

**Solutions**:
- Check if server is running
- Try accessing: http://localhost:8000/health
- Check browser console for WebSocket errors
- Verify `static/index.html` exists

### Reset Database

To reset all LLM accounts to initial state ($100 each):

```bash
python scripts/init_database.py --reset
```

**WARNING**: This deletes all positions, trades, and resets balances!

---

## Architecture Overview

### System Components

```
┌──────────────────────────────────────────────────────────────┐
│                    CRYPTO LLM TRADING SYSTEM                  │
└──────────────────────────────────────────────────────────────┘

┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│   Frontend      │   │   Backend       │   │   External      │
│   (Browser)     │   │   (FastAPI)     │   │   Services      │
├─────────────────┤   ├─────────────────┤   ├─────────────────┤
│                 │   │                 │   │                 │
│  Dashboard      │◄──┤  WebSocket      │   │  Binance API    │
│  (index.html)   │   │  Manager        │   │  (Market Data)  │
│                 │   │                 │   │                 │
│  - Live Activity│   │  REST API       │   │  Supabase       │
│  - Leaderboard  │   │  (23 endpoints) │◄──┤  (PostgreSQL)   │
│  - Market Data  │   │                 │   │                 │
│  - Positions    │   │  Background     │   │  LLM APIs       │
│  - Trades       │   │  Scheduler      │   │  - Anthropic    │
│                 │   │  (5-min cycles) │◄──┤  - DeepSeek     │
│                 │   │                 │   │  - OpenAI       │
└─────────────────┘   └─────────────────┘   └─────────────────┘
```

### Data Flow

```
1. Scheduler triggers trading cycle (every 5 minutes)
2. Market Data Service fetches latest prices from Binance
3. LLM Decision Service queries all 3 LLMs for trading decisions
4. Risk Manager validates decisions (balance, limits, exposure)
5. Position Manager executes approved trades
6. Account Service updates balances and statistics
7. WebSocket Manager broadcasts events to dashboard
8. Supabase stores all trades, positions, and decisions
```

### File Structure

```
crypto-llm-trading/
├── config/
│   └── settings.py          # Configuration management
├── src/
│   ├── api/                 # FastAPI application
│   │   ├── main.py          # App entry point
│   │   ├── dependencies.py  # Service injection
│   │   ├── websocket_manager.py
│   │   ├── models/          # Pydantic schemas
│   │   └── routes/          # API endpoints
│   ├── background/          # Background jobs
│   │   ├── jobs.py
│   │   └── scheduler.py     # APScheduler
│   ├── core/                # Business logic
│   │   ├── llm_decision.py
│   │   ├── position_manager.py
│   │   └── risk_manager.py
│   ├── services/            # Service layer
│   │   ├── trading_service.py
│   │   ├── account_service.py
│   │   └── market_data_service.py
│   ├── database/            # Database layer
│   │   └── supabase_client.py
│   ├── external/            # External APIs
│   │   ├── binance_client.py
│   │   └── llm_clients.py
│   └── utils/               # Utilities
│       ├── logger.py
│       ├── helpers.py
│       └── exceptions.py
├── scripts/                 # Initialization scripts
│   ├── schema.sql           # Database schema
│   ├── init_database.py     # DB setup
│   ├── verify_config.py     # Config validation
│   ├── start.sh             # Startup (bash)
│   └── start.py             # Startup (python)
├── static/
│   └── index.html           # Dashboard UI
├── tests/                   # Test suite
├── .env                     # Environment variables
├── requirements.txt         # Python dependencies
└── README.md               # Documentation
```

---

## Next Steps

After setup is complete:

1. **Test Configuration**: `python scripts/verify_config.py`
2. **Verify Database**: `python scripts/init_database.py --verify`
3. **Start System**: `python scripts/start.py --verify`
4. **Open Dashboard**: http://localhost:8000/dashboard/
5. **Monitor Trading**: Watch live activity log
6. **Check API**: http://localhost:8000/docs

---

## Support

For issues or questions:

1. Check [Troubleshooting](#troubleshooting) section
2. Review logs in console output
3. Verify all API keys are correct
4. Check Supabase dashboard for database status

---

## System Requirements

- **Python**: 3.9 or higher
- **RAM**: Minimum 2GB
- **Disk**: ~100MB for application + database
- **Network**: Stable internet connection
- **Browser**: Modern browser (Chrome, Firefox, Safari, Edge)

---

## Security Notes

⚠️ **IMPORTANT**:

1. **Never commit `.env` file** to version control
2. Use **testnet** for development (`USE_TESTNET=True`)
3. Start with **small balances** in production
4. Monitor API rate limits
5. Rotate API keys regularly
6. Use strong Supabase database password

---

**Ready to start trading!** 🚀
