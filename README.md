# Crypto LLM Trading System

**100% automated cryptocurrency trading system where 3 Large Language Models compete in live trading on Binance Futures.**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg)](https://fastapi.tiangolo.com)
[![Code Coverage](https://img.shields.io/badge/coverage-87%25-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 Project Overview

This project implements a **fully automated algorithmic trading system** where 3 Large Language Models (Claude Sonnet 4, DeepSeek Reasoner, GPT-4o) compete against each other trading cryptocurrency futures. Each LLM starts with **$100 virtual balance** and makes independent trading decisions every **5 minutes**.

### 🤖 The Competitors

| LLM | Provider | Model | Personality | Temperature |
|-----|----------|-------|-------------|-------------|
| **LLM-A** | Anthropic | claude-sonnet-4-20250514 | Conservative | 0.7 |
| **LLM-B** | DeepSeek | deepseek-reasoner | Balanced | 0.7 |
| **LLM-C** | OpenAI | gpt-4o | Aggressive | 0.7 |

### 📈 Trading Configuration

- **Symbols**: ETHUSDT, BNBUSDT, XRPUSDT, DOGEUSDT, ADAUSDT, AVAXUSDT
- **Initial Balance**: $100 per LLM (total $300)
- **Trading Cycle**: Every 5 minutes (automated)
- **Leverage**: Up to 10x
- **Position Limits**: Maximum 3 open positions per LLM
- **Trade Size**: $10 - $30 per trade

### ⭐ Key Features

- ✅ **Fully Automated**: No human intervention required
- ✅ **Real-time Dashboard**: WebSocket-powered live monitoring
- ✅ **Complete Audit Trail**: All decisions and trades logged
- ✅ **Risk Management**: Built-in limits and validation
- ✅ **REST API**: 23 endpoints for data access
- ✅ **Performance Tracking**: Leaderboard, PnL, win rates
- ✅ **Background Scheduler**: Automated 5-minute trading cycles
- ✅ **Multi-LLM Competition**: Independent decision-making
- ✅ **Database Persistence**: Supabase (PostgreSQL)

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+ installed
- Binance account ([Testnet](https://testnet.binancefuture.com) recommended)
- Supabase account ([Sign up](https://supabase.com))
- LLM API keys:
  - [Anthropic (Claude)](https://console.anthropic.com)
  - [DeepSeek](https://platform.deepseek.com)
  - [OpenAI (GPT-4o)](https://platform.openai.com)

### Installation

```bash
# 1. Clone repository
git clone <repository-url>
cd crypto-llm-trading

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Setup environment
cp .env.example .env
# Edit .env with your API keys

# 5. Initialize database
# Run schema.sql in Supabase SQL Editor
python scripts/init_database.py --verify

# 6. Start system
python scripts/start.py --verify
```

### Access Dashboard

Open browser: **http://localhost:8000/dashboard/**

---

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [SETUP.md](docs/SETUP.md) | Complete setup and installation guide |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture and design |
| [API.md](docs/API.md) | Complete API reference (23 endpoints) |
| [TESTING.md](docs/TESTING.md) | Testing guide and test suite documentation |
| [DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md) | Developer guide for contributors |
| [DEPLOYMENT.md](docs/DEPLOYMENT.md) | Production deployment guide |
| [DEMO_GUIDE.md](docs/DEMO_GUIDE.md) | 24-hour demo preparation guide |

---

## 🏗️ System Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   External      │
│   (Browser)     │    │    (FastAPI)    │    │   Services      │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│                 │    │                 │    │                 │
│  Dashboard      │◄───┤  WebSocket      │    │  Binance API    │
│  (index.html)   │    │  Manager        │    │  (Market Data)  │
│                 │    │                 │    │                 │
│  - Live Updates │    │  REST API       │    │  Supabase       │
│  - Leaderboard  │    │  (23 endpoints) │◄───┤  (PostgreSQL)   │
│  - Positions    │    │                 │    │                 │
│  - Trades       │    │  Background     │    │  LLM APIs       │
│                 │    │  Scheduler      │    │  - Anthropic    │
│                 │    │  (5-min cycles) │◄───┤  - DeepSeek     │
│                 │    │                 │    │  - OpenAI       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Trading Cycle Flow

```
Every 5 minutes:
1. Fetch market data (Binance) → 6 symbols, prices, indicators
2. For each LLM (A, B, C):
   a. Prepare context (account, positions, market)
   b. Call LLM API → Get decision (BUY/SELL/HOLD)
   c. Validate decision (risk checks)
   d. Execute trade (if approved)
3. Update positions → Calculate PnL
4. Broadcast updates → WebSocket clients
```

---

## 🔌 API Endpoints

### REST API (23 endpoints)

**Health** (2):
- `GET /` - API root
- `GET /health` - Health check

**Trading** (8):
- `GET /trading/status` - Overall status
- `GET /trading/accounts` - All LLM accounts
- `GET /trading/accounts/{llm_id}` - Specific account
- `GET /trading/positions` - All positions
- `GET /trading/positions/{llm_id}` - LLM positions
- `GET /trading/trades` - Trade history
- `GET /trading/trades/{llm_id}` - LLM trades
- `GET /trading/leaderboard` - LLM rankings

**Market** (5):
- `GET /market/snapshot` - All market data
- `GET /market/prices` - Current prices
- `GET /market/price/{symbol}` - Symbol price
- `GET /market/ticker/{symbol}` - Ticker data
- `GET /market/indicators/{symbol}` - Technical indicators

**Scheduler** (6):
- `GET /scheduler/status` - Scheduler state
- `POST /scheduler/trigger` - Manual cycle
- `POST /scheduler/pause` - Pause scheduler
- `POST /scheduler/resume` - Resume scheduler
- `GET /scheduler/stats` - Job statistics
- `GET /scheduler/next-run` - Next execution

**WebSocket** (2):
- `WS /ws` - Real-time connection
- `GET /ws/stats` - Connection stats

**API Documentation**: http://localhost:8000/docs

---

## 🧪 Testing

### Test Suite

**115 tests** across **11 test files**:
- **Unit Tests** (8 files, ~80 tests): Component testing
- **Integration Tests** (2 files, ~35 tests): E2E workflows
- **Performance Tests** (1 file, ~12 tests): Benchmarks & stress tests

**Code Coverage**: 87% (target: 85%+)

### Run Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Using test runner
python scripts/run_tests.py --coverage

# Specific category
python scripts/run_tests.py --integration
```

---

## 📊 Tech Stack

### Backend

- **Python 3.9+**
- **FastAPI** - Async web framework
- **Uvicorn** - ASGI server
- **APScheduler** - Background jobs
- **Supabase** - PostgreSQL database
- **Pydantic v2** - Data validation

### External Services

- **Binance Futures API** - Market data & trading
- **Anthropic API** - Claude Sonnet 4
- **DeepSeek API** - DeepSeek Reasoner
- **OpenAI API** - GPT-4o
- **Supabase** - PostgreSQL hosting

### Frontend

- **HTML5 + CSS3 + JavaScript** - Dashboard UI
- **WebSocket API** - Real-time updates
- **Chart.js** - Data visualization

### Development

- **pytest** - Testing framework
- **pytest-cov** - Coverage reporting
- **Black** - Code formatting
- **Git** - Version control

---

## 📁 Project Structure

```
crypto-llm-trading/
├── config/
│   └── settings.py              # Configuration
├── src/
│   ├── api/                     # FastAPI app
│   │   ├── main.py              # Entry point
│   │   ├── routes/              # API endpoints
│   │   ├── models/              # Pydantic models
│   │   └── websocket_manager.py
│   ├── background/              # Background jobs
│   │   ├── jobs.py
│   │   └── scheduler.py
│   ├── core/                    # Business logic
│   │   ├── llm_decision.py
│   │   ├── position_manager.py
│   │   └── risk_manager.py
│   ├── services/                # Service layer
│   │   ├── trading_service.py
│   │   ├── account_service.py
│   │   └── market_data_service.py
│   ├── database/                # Database layer
│   │   └── supabase_client.py
│   ├── external/                # External APIs
│   │   ├── binance_client.py
│   │   └── llm_clients.py
│   └── utils/                   # Utilities
│       ├── logger.py
│       ├── helpers.py
│       └── exceptions.py
├── scripts/                     # Utility scripts
│   ├── schema.sql
│   ├── init_database.py
│   ├── start.py / start.sh
│   └── run_tests.py / run_tests.sh
├── static/
│   └── index.html               # Dashboard
├── tests/                       # Test suite (11 files)
├── .env.example                 # Environment template
├── requirements.txt
└── README.md                    # This file
```

---

## 🎯 Project Phases

| Phase | Description | Status |
|-------|-------------|--------|
| **0** | Project Setup & Structure | ✅ Complete |
| **1** | Configuration & Utils | ✅ Complete |
| **2** | Database & Binance Client | ✅ Complete |
| **3** | LLM Client Integration | ✅ Complete |
| **4-5** | Core Business Logic | ✅ Complete |
| **6** | Service Layer | ✅ Complete |
| **7** | FastAPI REST API | ✅ Complete |
| **8** | Background Jobs (Scheduler) | ✅ Complete |
| **9** | WebSocket Dashboard | ✅ Complete |
| **10** | System Initialization | ✅ Complete |
| **11** | E2E Integration Testing | ✅ Complete |
| **12** | Complete Documentation | ✅ Complete |
| **13** | Deployment & 24h Demo | 🔄 Next |

**Current Status**: Phases 0-12 completed (12/13)

---

## 🔧 Configuration

### Environment Variables

Required in `.env` file:

```env
# Environment
ENVIRONMENT=development
DEBUG=True
USE_TESTNET=True  # IMPORTANT for testing

# Binance
BINANCE_API_KEY=your_binance_key
BINANCE_SECRET_KEY=your_binance_secret

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_key

# LLM APIs
LLM_A_API_KEY=your_claude_key      # Anthropic
LLM_B_API_KEY=your_deepseek_key    # DeepSeek
LLM_C_API_KEY=your_openai_key      # OpenAI

# Trading Config
AVAILABLE_PAIRS=ETHUSDT,BNBUSDT,XRPUSDT,DOGEUSDT,ADAUSDT,AVAXUSDT
MAX_LEVERAGE=10
MAX_OPEN_POSITIONS=3
```

---

## 📈 Performance Benchmarks

| Operation | Target | Actual |
|-----------|--------|--------|
| Trading Cycle | < 5s | ~2-3s ✅ |
| Get All Accounts | < 100ms | ~50ms ✅ |
| Market Snapshot | < 1s | ~500ms ✅ |
| Risk Validation | < 1ms | ~0.5ms ✅ |

**Stress Tests**:
- ✅ 50 rapid cycles: >90% success rate
- ✅ 100 positions query: Success
- ✅ Memory leaks: None detected

---

## ⚠️ Important Warnings

**This system trades real money (or testnet funds).**

- ⚠️ Always start with **testnet** (`USE_TESTNET=True`)
- ⚠️ Never use more capital than you can afford to lose
- ⚠️ LLMs can make unpredictable decisions
- ⚠️ Monitor the system constantly
- ⚠️ No guarantee of profitability
- ⚠️ This is experimental research, not financial advice

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Write tests for new features
4. Ensure tests pass (`pytest`)
5. Format code with Black (`black src/ tests/`)
6. Submit a pull request

See [DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md) for details.

---

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🔗 Links

- **Live Demo**: Coming soon (Phase 13)
- **API Docs**: http://localhost:8000/docs
- **Dashboard**: http://localhost:8000/dashboard/
- **GitHub Issues**: [Report bugs](https://github.com/your-repo/issues)

---

## 📧 Contact

**GitHub**: [@pablofelipe01](https://github.com/pablofelipe01)

---

**Built with FastAPI, 3 LLMs, and a lot of experimentation.** 🚀

---

### Acknowledgments

- Anthropic for Claude API
- DeepSeek for DeepSeek Reasoner API
- OpenAI for GPT-4o API
- Binance for trading infrastructure
- Supabase for database hosting
