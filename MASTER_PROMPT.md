# 🤖 LLM Trading Competition - Master Prompt

**Version:** 1.0
**Last Updated:** November 2024

---

## 📋 Project Overview

You are about to help me build an **automated crypto trading system** where **multiple AI models (LLMs) compete against each other**.

### Core Premise
- **3 LLMs compete independently**: LLM-A, LLM-B, LLM-C
- Each LLM has **independent capital** (e.g., $200 each)
- Each LLM makes **autonomous trading decisions**
- **ALL LLMs have IDENTICAL configuration** (same temperature, max_tokens, prompts)
- **ONLY the AI model/provider varies** (e.g., Claude vs DeepSeek vs GPT-4o)
- Goal: Determine which LLM/model generates the **best ROI**
- All trading happens on **Binance Futures** (testnet first, then mainnet)

### Key Principles
1. **Start SLOW**: Verify every step before moving forward
2. **Testnet FIRST**: Never touch mainnet until thoroughly tested
3. **No hardcoding**: Everything configurable via .env
4. **Safety first**: Emergency shutdown scripts from day 1
5. **Full tracking**: Database logs every decision and trade
6. **Monitoring**: Real-time dashboard and Telegram alerts

---

## 🎯 Your Role

You will guide me through building this system in **multiple phases**:

### Phase 1: Foundation Setup (VERY SLOW, STEP BY STEP)
- ✅ Verify Python version (3.9+)
- ✅ Create project structure
- ✅ Set up virtual environment
- ✅ Install dependencies
- ✅ **ASK USER: Which trading pairs to use?** (e.g., low-price <$1 or major pairs)
- ✅ Configure environment variables
- ✅ Test Binance Futures connection (testnet)
- ✅ Set up Supabase database
- ✅ Create base architecture

### Phase 2: Strategy Definition (PAUSE HERE)
**⚠️ IMPORTANT**: After Phase 1 is complete, you MUST stop and ask me:

> "The foundation is ready. What quantitative trading strategy would you like to implement?"

I will then provide the specific strategy (e.g., mean reversion, momentum, statistical arbitrage, pairs trading, etc.)

### Phase 3: Strategy Implementation
- Implement the specific strategy I provided
- Create LLM decision-making system
- Build execution engine
- Add monitoring and alerts

### Phase 4: Testing & Deployment
- Test on testnet extensively
- Verify margin calculations
- Run paper trading
- Deploy to mainnet when ready

---

## 📂 Proven Architecture

Based on successful implementation, use this structure:

```
project_root/
├── config/
│   └── settings.py              # Centralized configuration (reads from .env)
├── src/
│   ├── api/
│   │   ├── main.py             # FastAPI server
│   │   ├── dependencies.py      # Shared dependencies
│   │   ├── models/             # Pydantic models
│   │   └── routes/             # API endpoints
│   │       ├── trading_routes.py
│   │       ├── market_routes.py
│   │       └── monitoring_routes.py
│   ├── clients/
│   │   ├── binance_client.py   # Binance Futures API wrapper
│   │   └── prompts.py          # LLM system prompts
│   ├── core/
│   │   └── strategy_engine.py  # Main trading logic (strategy-specific)
│   ├── services/
│   │   ├── trading_service.py
│   │   ├── market_data_service.py
│   │   ├── indicator_service.py
│   │   └── llm_decision_service.py
│   ├── database/
│   │   └── supabase_client.py  # Database client
│   └── utils/
│       ├── logger.py           # Centralized logging
│       ├── exceptions.py       # Custom exceptions
│       └── telegram_notifier.py
├── scripts/
│   ├── emergency_shutdown.py   # Cancel all orders + close positions (NO CONFIRMATIONS)
│   ├── clean_database.py       # Reset database to clean state
│   ├── check_binance_status.py # Quick status check
│   └── monitor_simple.py       # Real-time monitoring
├── tests/                       # Unit tests
├── logs/                        # Log files
├── docs/                        # Documentation
├── .env                         # NEVER commit to git
├── .env.example                 # Template for .env
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🔧 Phase 1: Foundation Setup

### Step 1: Initial Verification

**Before anything else, verify:**

```bash
# Check Python version (need 3.9+)
python3 --version

# Check pip
pip3 --version

# Check git
git --version
```

If Python < 3.9, STOP and help me upgrade first.

### Step 2: Project Structure

Create the project folder structure shown above. Use `mkdir -p` to create nested directories.

### Step 3: Virtual Environment

```bash
# Create venv
python3 -m venv venv

# Activate (macOS/Linux)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Verify activation
which python
```

### Step 4: Dependencies

Create `requirements.txt` with these **proven, stable** dependencies:

```txt
# Core
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-dotenv==1.0.0
pydantic==2.5.0
pydantic-settings==2.1.0

# Binance
python-binance==1.0.19

# Database
supabase==2.3.0

# LLM APIs
anthropic==0.34.0
openai==1.3.0

# Data & Analysis
pandas==2.1.3
numpy==1.26.2
ta==0.11.0

# Utils
httpx==0.25.2
python-telegram-bot==20.7

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
```

**Install:**
```bash
pip install -r requirements.txt
```

### Step 5: Environment Configuration

Create `.env.example` as template:

```env
# ============================================
# ENVIRONMENT
# ============================================
ENVIRONMENT=testnet
DEBUG=true

# ============================================
# BINANCE TESTNET API (USDⓈ-M Futures)
# ============================================
BINANCE_TESTNET_API_KEY=your_testnet_api_key_here
BINANCE_TESTNET_SECRET_KEY=your_testnet_secret_key_here
BINANCE_TESTNET_BASE_URL=https://testnet.binancefuture.com

# Binance Production (for future use)
BINANCE_API_KEY=your_production_api_key_here
BINANCE_SECRET_KEY=your_production_secret_key_here
BINANCE_BASE_URL=https://fapi.binance.com

# ============================================
# SUPABASE
# ============================================
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key_here

# ============================================
# TELEGRAM NOTIFICATIONS
# ============================================
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
TELEGRAM_NOTIFICATIONS_ENABLED=false

# ============================================
# LLM API KEYS
# ============================================
CLAUDE_API_KEY=your_claude_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# ============================================
# LLM CONFIGURATION
# ============================================
# IMPORTANT: All LLMs must have IDENTICAL configuration for fair competition
# Only the provider/model should differ

# LLM-A (Claude)
LLM_A_PROVIDER=claude
LLM_A_MODEL=claude-sonnet-4-20250514
LLM_A_MAX_TOKENS=4000
LLM_A_TEMPERATURE=0.7

# LLM-B (DeepSeek)
LLM_B_PROVIDER=deepseek
LLM_B_MODEL=deepseek-chat
LLM_B_MAX_TOKENS=4000
LLM_B_TEMPERATURE=0.7
LLM_B_BASE_URL=https://api.deepseek.com

# LLM-C (GPT-4o)
LLM_C_PROVIDER=openai
LLM_C_MODEL=gpt-4o
LLM_C_MAX_TOKENS=4000
LLM_C_TEMPERATURE=0.7

# ============================================
# TRADING CONFIGURATION
# ============================================
USE_TESTNET=true
INITIAL_BALANCE_PER_LLM=200.0
TOTAL_LLMS=3

# Trading pairs (comma-separated, NO SPACES)
# Examples: BTCUSDT,ETHUSDT,SOLUSDT or DOGEUSDT,TRXUSDT,ADAUSDT
# User will specify these during setup
AVAILABLE_PAIRS=PLACEHOLDER_PAIRS_HERE

# Risk management
MAX_LEVERAGE=5
MAX_OPEN_POSITIONS=5
MAX_MARGIN_USAGE=0.80

# ============================================
# DECISION MAKING
# ============================================
LLM_DECISION_INTERVAL_SECONDS=300
LLM_MAX_DECISIONS_PER_HOUR=12

# ============================================
# API SERVER
# ============================================
API_HOST=0.0.0.0
API_PORT=8000

# ============================================
# LOGGING
# ============================================
LOG_LEVEL=INFO
LOG_FILE_PATH=logs/app.log
```

**Then create actual `.env` file** by copying `.env.example` and filling in real values.

### Step 6: Centralized Settings

Create `config/settings.py` using **Pydantic Settings**:

```python
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, List


class Settings(BaseSettings):
    """Centralized configuration."""

    # Environment
    ENVIRONMENT: str = "testnet"
    DEBUG: bool = True

    # Binance
    BINANCE_TESTNET_API_KEY: str
    BINANCE_TESTNET_SECRET_KEY: str
    BINANCE_TESTNET_BASE_URL: str = "https://testnet.binancefuture.com"

    BINANCE_API_KEY: str = ""
    BINANCE_SECRET_KEY: str = ""
    BINANCE_BASE_URL: str = "https://fapi.binance.com"

    USE_TESTNET: bool = True

    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str

    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    TELEGRAM_NOTIFICATIONS_ENABLED: bool = False

    # LLM API Keys
    CLAUDE_API_KEY: Optional[str] = None
    DEEPSEEK_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    # LLM Configurations (MUST BE IDENTICAL for fair competition)
    LLM_A_PROVIDER: str
    LLM_A_MODEL: str
    LLM_A_MAX_TOKENS: int = 4000
    LLM_A_TEMPERATURE: float = 0.7

    LLM_B_PROVIDER: str
    LLM_B_MODEL: str
    LLM_B_MAX_TOKENS: int = 4000
    LLM_B_TEMPERATURE: float = 0.7
    LLM_B_BASE_URL: str = "https://api.deepseek.com"

    LLM_C_PROVIDER: str
    LLM_C_MODEL: str
    LLM_C_MAX_TOKENS: int = 4000
    LLM_C_TEMPERATURE: float = 0.7

    # Trading
    INITIAL_BALANCE_PER_LLM: float = 200.0
    TOTAL_LLMS: int = 3
    AVAILABLE_PAIRS: str  # User will specify during setup

    MAX_LEVERAGE: int = 5
    MAX_OPEN_POSITIONS: int = 5
    MAX_MARGIN_USAGE: float = 0.80

    # Decision Making
    LLM_DECISION_INTERVAL_SECONDS: int = 300
    LLM_MAX_DECISIONS_PER_HOUR: int = 12

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE_PATH: str = "logs/app.log"

    @property
    def available_pairs_list(self) -> List[str]:
        """Parse comma-separated pairs into list."""
        return [p.strip() for p in self.AVAILABLE_PAIRS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
```

### Step 7: Database Setup (Supabase)

**Supabase Tables Schema:**

```sql
-- LLM Accounts
CREATE TABLE llm_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    llm_id TEXT UNIQUE NOT NULL,
    current_balance NUMERIC NOT NULL DEFAULT 200.0,
    total_pnl NUMERIC DEFAULT 0.0,
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- LLM Decisions
CREATE TABLE llm_decisions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    llm_id TEXT NOT NULL,
    decision_type TEXT NOT NULL,
    symbol TEXT,
    reasoning TEXT,
    confidence NUMERIC,
    full_response JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Positions
CREATE TABLE positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    llm_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    entry_price NUMERIC NOT NULL,
    quantity NUMERIC NOT NULL,
    leverage INTEGER NOT NULL,
    status TEXT DEFAULT 'OPEN',
    unrealized_pnl NUMERIC DEFAULT 0.0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Closed Trades
CREATE TABLE closed_trades (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    llm_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    entry_price NUMERIC NOT NULL,
    exit_price NUMERIC NOT NULL,
    quantity NUMERIC NOT NULL,
    pnl NUMERIC NOT NULL,
    fees NUMERIC NOT NULL,
    opened_at TIMESTAMPTZ NOT NULL,
    closed_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add indexes
CREATE INDEX idx_llm_accounts_llm_id ON llm_accounts(llm_id);
CREATE INDEX idx_llm_decisions_llm_id ON llm_decisions(llm_id);
CREATE INDEX idx_positions_llm_id ON positions(llm_id);
CREATE INDEX idx_positions_status ON positions(status);
CREATE INDEX idx_closed_trades_llm_id ON closed_trades(llm_id);
```

**Supabase Client** (`src/database/supabase_client.py`):

```python
from supabase import create_client, Client
from config.settings import settings
from src.utils.logger import app_logger


class SupabaseClient:
    """Wrapper for Supabase client."""

    def __init__(self):
        self._client: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY
        )
        app_logger.info("✅ Successfully connected to Supabase")

    @property
    def client(self) -> Client:
        return self._client


# Global instance
_supabase_client: SupabaseClient | None = None


def get_supabase_client() -> SupabaseClient:
    """Get or create Supabase client singleton."""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = SupabaseClient()
    return _supabase_client
```

### Step 8: Binance Client Skeleton

Create `src/clients/binance_client.py` with:
- Connection handling
- Authentication (HMAC SHA256 signatures)
- Market data methods
- Order placement methods
- Position management methods
- Error handling

**Key methods needed:**
- `get_ticker_price(symbol)`
- `get_account_info()`
- `get_position_risk()`
- `create_order(symbol, side, order_type, quantity, ...)`
- `cancel_order(symbol, order_id)`
- `get_open_orders(symbol)`

### Step 9: Logging System

Create `src/utils/logger.py`:

```python
import logging
import sys
from pathlib import Path
from config.settings import settings

# Create logs directory
Path(settings.LOG_FILE_PATH).parent.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(settings.LOG_FILE_PATH),
        logging.StreamHandler(sys.stdout)
    ]
)

app_logger = logging.getLogger("app")
```

### Step 10: Emergency Scripts

**CRITICAL**: Create these scripts from day 1:

**`scripts/emergency_shutdown.py`** - Cancel all orders and close all positions (NO confirmations):
```python
#!/usr/bin/env python3
"""Emergency shutdown - cancel all orders and close all positions."""

from src.clients.binance_client import BinanceClient
from config.settings import settings

def main():
    client = BinanceClient(testnet=settings.USE_TESTNET)

    # Cancel all orders
    for symbol in settings.available_pairs_list:
        try:
            orders = client.get_open_orders(symbol)
            for order in orders:
                client.cancel_order(symbol, order['orderId'])
        except Exception as e:
            print(f"Error cancelling {symbol}: {e}")

    # Close all positions
    positions = client.get_position_risk()
    for pos in positions:
        if float(pos['positionAmt']) != 0:
            symbol = pos['symbol']
            qty = abs(float(pos['positionAmt']))
            side = 'SELL' if float(pos['positionAmt']) > 0 else 'BUY'
            client.create_market_order(symbol, side, qty, reduce_only=True)

    print("✅ Emergency shutdown complete")

if __name__ == "__main__":
    main()
```

### Step 11: Trading Pairs Selection

**⚠️ STOP AND ASK USER:**

> "Before we proceed with testing, I need to know which trading pairs you want to use.
>
> **Options:**
> 1. **Low-price assets** (<$1): Better margin efficiency for small capital
>    - Examples: DOGEUSDT, TRXUSDT, HBARUSDT, XLMUSDT, ADAUSDT, ALGOUSDT
> 2. **Major pairs**: Higher liquidity, more stable
>    - Examples: BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT
> 3. **Custom selection**: Specify your own pairs
>
> **Important considerations:**
> - Binance Futures only (not all pairs are available)
> - Minimum 3 pairs recommended (for diversification)
> - Maximum 6-8 pairs (for manageability)
> - Consider your total capital when choosing
>
> Please provide your desired trading pairs (comma-separated, e.g., DOGEUSDT,TRXUSDT,ADAUSDT)"

Once user provides the pairs:
1. Verify each pair exists on Binance Futures
2. Update `.env` file with `AVAILABLE_PAIRS=USER_PAIRS_HERE`
3. Test that you can fetch prices for all pairs
4. Document the selection in README.md

### Step 12: Initial Testing

Before moving forward, test:

1. ✅ Environment variables load correctly
2. ✅ Supabase connection works
3. ✅ Binance testnet connection works
4. ✅ Can fetch ticker prices
5. ✅ Can get account info
6. ✅ Logging works

**Create `scripts/test_connections.py`:**

```python
#!/usr/bin/env python3
"""Test all connections before starting."""

from src.clients.binance_client import BinanceClient
from src.database.supabase_client import get_supabase_client
from config.settings import settings

print("Testing connections...\n")

# Test Binance
print("1. Testing Binance...")
try:
    client = BinanceClient(testnet=True)
    price = client.get_ticker_price("BTCUSDT")
    print(f"   ✅ Binance OK - BTC Price: ${price}")
except Exception as e:
    print(f"   ❌ Binance Error: {e}")

# Test Supabase
print("2. Testing Supabase...")
try:
    supabase = get_supabase_client()
    result = supabase.client.table('llm_accounts').select('*').limit(1).execute()
    print(f"   ✅ Supabase OK")
except Exception as e:
    print(f"   ❌ Supabase Error: {e}")

print("\n✅ All systems operational!")
```

---

## ⏸️ STOP HERE - Phase 1 Complete

At this point, you should have:
- ✅ Project structure created
- ✅ Virtual environment set up
- ✅ Dependencies installed
- ✅ Configuration working
- ✅ Database connected
- ✅ Binance client working
- ✅ Logging functional
- ✅ Emergency scripts ready

**NOW ASK ME:**

> "Phase 1 complete! The foundation is ready.
>
> What quantitative trading strategy would you like to implement?
>
> Examples:
> - Mean reversion (RSI-based)
> - Momentum trading
> - Statistical arbitrage
> - Pairs trading
> - Market making
> - Trend following
> - Custom strategy
>
> Please describe the strategy you want, and I'll implement it with the LLM competition framework."

---

## 📚 Critical Lessons Learned

### ❌ DON'T
1. **Never hardcode** trading pairs, API keys, or configuration values
2. **Never skip** testnet testing phase
3. **Never deploy** without emergency shutdown scripts
4. **Never use** mutable global state without proper locking
5. **Never forget** margin validation before placing orders
6. **Never commit** .env files to git

### ✅ DO
1. **Always use** centralized configuration (settings.py + .env)
2. **Always validate** margin requirements before trading
3. **Always test** on testnet first
4. **Always log** every decision and trade
5. **Always have** emergency shutdown capability
6. **Always clean** Python cache (`__pycache__`) after config changes
7. **Always use** dynamic imports (not hardcoded lists)

### 🎯 Architecture Patterns That Work

1. **Dependency Injection**: Use FastAPI's `Depends()` for services
2. **Singleton Pattern**: For database and API clients
3. **Service Layer**: Separate business logic from API routes
4. **Repository Pattern**: For database operations
5. **Strategy Pattern**: For different LLM implementations
6. **Factory Pattern**: For creating orders/strategies

### 🚨 Margin Management

**Critical for Futures trading:**

```python
def validate_margin(position_size_usd: float, leverage: int) -> bool:
    """Ensure sufficient margin before trading."""
    required_margin = position_size_usd / leverage
    available = get_available_balance()

    # Need buffer for price fluctuations
    return available > (required_margin * 1.2)
```

### 📊 Monitoring

**Essential endpoints:**
- `GET /status` - System health
- `GET /llm-accounts` - Current balances and PnL
- `GET /positions` - Open positions
- `GET /decisions` - Recent LLM decisions
- `GET /leaderboard` - LLM performance ranking

---

## 🤝 Working Together

**Your approach:**
1. Move **VERY slowly**
2. Verify each step works before continuing
3. Ask clarifying questions if anything is unclear
4. Show me code snippets for approval before creating files
5. Test everything on testnet first
6. Keep me informed of progress

**My commitment:**
- I'll test every step thoroughly
- I'll provide API keys and credentials
- I'll tell you when something doesn't work
- I'll make final decisions on architecture choices

---

## 🚀 Ready to Start

When you're ready, begin with:

**"Let's start building your LLM trading competition system. First, let's verify your Python environment. Please run: `python3 --version`"**

Then proceed step by step through Phase 1.

Remember: **STOP after Phase 1 and ask me for the trading strategy!**

---

**Good luck, Claude! Let's build something amazing! 🎉**
