# Crypto LLM Trading System - Developer Guide

Complete guide for developers contributing to or extending the **Crypto LLM Trading System**.

---

## Table of Contents

1. [Development Setup](#development-setup)
2. [Project Structure](#project-structure)
3. [Coding Standards](#coding-standards)
4. [Adding New Features](#adding-new-features)
5. [Testing Guidelines](#testing-guidelines)
6. [Debugging](#debugging)
7. [Performance Optimization](#performance-optimization)
8. [Common Development Tasks](#common-development-tasks)

---

## Development Setup

### Prerequisites

- Python 3.9+ installed
- Git installed
- Code editor (VS Code recommended)
- PostgreSQL knowledge (for Supabase)
- API testing tool (Postman/Insomnia optional)

### Initial Setup

```bash
# 1. Clone repository
git clone <repository-url>
cd crypto-llm-trading

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install development dependencies
pip install -r requirements-dev.txt  # If exists
# Or manually:
pip install pytest pytest-cov black flake8 mypy

# 5. Copy environment template
cp .env.example .env

# 6. Edit .env with your credentials
nano .env  # or use your preferred editor

# 7. Verify setup
python scripts/verify_config.py
```

### IDE Setup (VS Code)

**Recommended Extensions**:
- Python (Microsoft)
- Pylance
- Python Test Explorer
- GitLens
- REST Client

**settings.json**:
```json
{
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "python.testing.pytestArgs": ["tests"],
  "editor.formatOnSave": true,
  "files.trimTrailingWhitespace": true
}
```

---

## Project Structure

### Directory Layout

```
crypto-llm-trading/
├── config/
│   └── settings.py              # Configuration management
├── src/
│   ├── api/                     # FastAPI application
│   │   ├── main.py              # App entry point
│   │   ├── dependencies.py      # Dependency injection
│   │   ├── websocket_manager.py # WebSocket manager
│   │   ├── models/              # Pydantic models
│   │   │   └── responses.py
│   │   └── routes/              # API endpoints
│   │       ├── __init__.py
│   │       ├── trading_routes.py
│   │       ├── market_routes.py
│   │       ├── health_routes.py
│   │       ├── scheduler_routes.py
│   │       └── websocket_routes.py
│   ├── background/              # Background jobs
│   │   ├── jobs.py              # Job definitions
│   │   └── scheduler.py         # APScheduler config
│   ├── core/                    # Core business logic
│   │   ├── llm_decision.py      # LLM decision service
│   │   ├── position_manager.py  # Position management
│   │   └── risk_manager.py      # Risk validation
│   ├── services/                # Service layer
│   │   ├── trading_service.py   # Main orchestrator
│   │   ├── account_service.py   # Account management
│   │   └── market_data_service.py
│   ├── database/                # Database layer
│   │   └── supabase_client.py   # Supabase operations
│   ├── external/                # External APIs
│   │   ├── binance_client.py    # Binance API
│   │   └── llm_clients.py       # LLM API clients
│   └── utils/                   # Utilities
│       ├── logger.py            # Logging setup
│       ├── helpers.py           # Helper functions
│       └── exceptions.py        # Custom exceptions
├── scripts/                     # Utility scripts
│   ├── schema.sql               # Database schema
│   ├── init_database.py         # DB initialization
│   ├── verify_config.py         # Config verification
│   ├── start.sh                 # Startup script (bash)
│   ├── start.py                 # Startup script (python)
│   ├── run_tests.sh             # Test runner (bash)
│   └── run_tests.py             # Test runner (python)
├── static/
│   └── index.html               # Dashboard UI
├── tests/                       # Test suite
│   ├── conftest.py              # Pytest configuration
│   ├── test_*.py                # Test files (11 files)
│   └── ...
├── logs/                        # Log files (gitignored)
│   ├── app.log
│   └── llm_decisions.log
├── .env                         # Environment variables (gitignored)
├── .env.example                 # Environment template
├── .gitignore
├── requirements.txt             # Python dependencies
├── README.md                    # Main documentation
├── SETUP.md                     # Setup guide
├── TESTING.md                   # Testing guide
├── ARCHITECTURE.md              # Architecture docs
├── API.md                       # API reference
├── DEVELOPER_GUIDE.md           # This file
├── DEPLOYMENT.md                # Deployment guide
└── PHASE*_SUMMARY.md            # Phase summaries
```

### Module Dependencies

```
┌─────────────┐
│   main.py   │  (Entry point)
└─────────────┘
       │
       ▼
┌─────────────────┐
│ dependencies.py │  (Service initialization)
└─────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│           SERVICES                   │
│  - TradingService                   │
│  - AccountService                   │
│  - MarketDataService                │
└─────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│        CORE LOGIC                    │
│  - LLMDecisionService               │
│  - PositionManager                  │
│  - RiskManager                      │
└─────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│      DATA ACCESS                     │
│  - SupabaseClient                   │
│  - BinanceClient                    │
│  - LLMClients                       │
└─────────────────────────────────────┘
```

---

## Coding Standards

### Python Style Guide

**Follow PEP 8** with these specifics:

**Line Length**: 100 characters (not 79)

**Imports**:
```python
# Standard library
import os
from datetime import datetime

# Third-party
from fastapi import FastAPI, Depends
from decimal import Decimal

# Local application
from config.settings import settings
from src.utils.logger import app_logger
```

**Type Hints**:
```python
def calculate_pnl(
    entry_price: Decimal,
    exit_price: Decimal,
    quantity: Decimal,
    side: str
) -> Decimal:
    """Calculate PnL for a trade."""
    # Implementation
```

**Docstrings** (Google style):
```python
def function_name(param1: str, param2: int) -> bool:
    """
    Short description.

    Longer description if needed.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When validation fails
    """
    pass
```

### Code Formatting

**Use Black**:
```bash
# Format all Python files
black src/ tests/ scripts/

# Check without modifying
black --check src/
```

**Linting with Flake8**:
```bash
# Run linter
flake8 src/ tests/

# With config (.flake8)
[flake8]
max-line-length = 100
exclude = .git,__pycache__,venv
ignore = E203,W503
```

### Naming Conventions

**Variables**: `snake_case`
```python
total_balance = 100.0
current_price = Decimal("2000.00")
```

**Functions**: `snake_case`
```python
def get_trading_status():
    pass

def calculate_unrealized_pnl():
    pass
```

**Classes**: `PascalCase`
```python
class TradingService:
    pass

class PositionManager:
    pass
```

**Constants**: `UPPER_SNAKE_CASE`
```python
MAX_LEVERAGE = 10
MIN_TRADE_SIZE_USD = 10.0
```

**Private Methods**: `_leading_underscore`
```python
def _validate_internal_state(self):
    pass
```

---

## Adding New Features

### Adding a New LLM Provider

**1. Create LLM Client** (`src/external/llm_clients.py`):

```python
class NewLLMClient:
    """Client for New LLM API."""

    def __init__(self, api_key: str, model: str, temperature: float):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature

    def get_trading_decision(
        self,
        market_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get trading decision from New LLM.

        Args:
            market_context: Market data and account state

        Returns:
            Decision dict with action, symbol, etc.
        """
        # Implementation
        pass
```

**2. Update Configuration** (`config/settings.py`):

```python
class LLMConfig(BaseModel):
    # Add new provider
    NEW_LLM_D_PROVIDER: str = "newllm"
    NEW_LLM_D_MODEL: str = "newllm-model"
    NEW_LLM_D_API_KEY: str = ""
    NEW_LLM_D_TEMPERATURE: float = 0.7
```

**3. Update Factory** (`src/external/llm_clients.py`):

```python
def get_llm_client(llm_id: str):
    """Factory function for LLM clients."""
    # ... existing code ...

    elif llm_id == "LLM-D":
        return NewLLMClient(
            api_key=settings.NEW_LLM_D_API_KEY,
            model=settings.NEW_LLM_D_MODEL,
            temperature=settings.NEW_LLM_D_TEMPERATURE
        )
```

**4. Add Database Record**:

```sql
INSERT INTO llm_accounts (llm_id, provider, model_name, balance)
VALUES ('LLM-D', 'newllm', 'newllm-model', 100.0);
```

**5. Write Tests**:

```python
def test_newllm_client():
    """Test New LLM client."""
    client = NewLLMClient(
        api_key="test-key",
        model="test-model",
        temperature=0.7
    )

    decision = client.get_trading_decision({...})

    assert decision["action"] in ["BUY", "SELL", "HOLD"]
```

### Adding a New Trading Symbol

**1. Update Configuration** (`.env`):

```env
AVAILABLE_PAIRS=ETHUSDT,BNBUSDT,XRPUSDT,DOGEUSDT,ADAUSDT,AVAXUSDT,NEWUSDT
```

**2. No Code Changes Needed**:
- MarketDataService automatically fetches data for all symbols in AVAILABLE_PAIRS
- LLMs can choose from any available symbol

**3. Test**:

```bash
# Verify config loads correctly
python scripts/verify_config.py

# Test market data fetch
pytest tests/test_binance_client.py::test_get_ticker -v
```

### Adding a New API Endpoint

**1. Create Route** (`src/api/routes/your_routes.py`):

```python
from fastapi import APIRouter, Depends
from src.api.models.responses import YourResponse

router = APIRouter(prefix="/your-prefix", tags=["Your Tag"])

@router.get("/endpoint", response_model=YourResponse)
async def your_endpoint(
    param: str,
    service = Depends(get_your_service)
):
    """
    Endpoint description.

    Args:
        param: Parameter description

    Returns:
        Response description
    """
    data = service.get_data(param)
    return YourResponse(**data)
```

**2. Create Response Model** (`src/api/models/responses.py`):

```python
class YourResponse(BaseModel):
    """Response model for your endpoint."""

    field1: str
    field2: int
    field3: Optional[float] = None

    class Config:
        json_schema_extra = {
            "example": {
                "field1": "example",
                "field2": 123,
                "field3": 45.67
            }
        }
```

**3. Register Router** (`src/api/main.py`):

```python
from src.api.routes.your_routes import router as your_router

app.include_router(your_router)
```

**4. Write Tests**:

```python
def test_your_endpoint(client):
    """Test your new endpoint."""
    response = client.get("/your-prefix/endpoint?param=value")

    assert response.status_code == 200
    assert "field1" in response.json()
```

---

## Testing Guidelines

### Writing Unit Tests

**Test File Structure**:

```python
"""
Test module for YourModule.

Tests cover:
- Feature 1
- Feature 2
- Edge cases
"""

import pytest
from unittest.mock import Mock, patch

from src.module import YourClass


@pytest.fixture
def mock_dependency():
    """Mock for dependencies."""
    return Mock()


class TestYourClass:
    """Test suite for YourClass."""

    def test_method_success(self, mock_dependency):
        """Test method with valid input."""
        # Arrange
        instance = YourClass(mock_dependency)
        input_data = {"key": "value"}

        # Act
        result = instance.method(input_data)

        # Assert
        assert result == expected_value

    def test_method_invalid_input(self):
        """Test method with invalid input."""
        with pytest.raises(ValueError):
            instance.method(invalid_input)
```

### Test Coverage Goals

| Module | Target |
|--------|--------|
| utils/ | 90%+ |
| external/ | 85%+ |
| database/ | 85%+ |
| core/ | 90%+ |
| services/ | 85%+ |
| api/ | 80%+ |

**Check Coverage**:

```bash
# Generate coverage report
pytest --cov=src --cov-report=html

# View in browser
open htmlcov/index.html
```

---

## Debugging

### Debugging Techniques

**1. Logging**:

```python
from src.utils.logger import app_logger

# In your code
app_logger.debug(f"Variable value: {variable}")
app_logger.info(f"Operation started: {operation}")
app_logger.warning(f"Potential issue: {issue}")
app_logger.error(f"Error occurred: {error}", exc_info=True)
```

**2. Interactive Debugger (pdb)**:

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use breakpoint() in Python 3.7+
breakpoint()
```

**3. VS Code Debugger**:

**launch.json**:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "src.api.main:app",
        "--reload",
        "--port",
        "8000"
      ],
      "jinja": true
    },
    {
      "name": "Python: Pytest",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": [
        "tests/",
        "-v"
      ]
    }
  ]
}
```

### Common Issues and Solutions

**Issue**: Import errors
```bash
# Solution: Add project root to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**Issue**: Database connection fails
```bash
# Solution: Verify Supabase credentials
python -c "from config.settings import settings; print(settings.SUPABASE_URL)"
```

**Issue**: Tests fail with mocking errors
```python
# Solution: Patch at the point of use, not where defined
# Wrong:
@patch('src.external.binance_client.BinanceClient')

# Right:
@patch('src.services.market_data_service.BinanceClient')
```

---

## Performance Optimization

### Profiling

**cProfile**:

```bash
# Profile trading cycle
python -m cProfile -s cumulative -m src.api.main
```

**line_profiler**:

```python
# Install
pip install line_profiler

# Add @profile decorator
@profile
def expensive_function():
    pass

# Run
kernprof -l -v script.py
```

### Optimization Checklist

- [ ] Use async/await for I/O operations
- [ ] Cache expensive computations
- [ ] Use database indexes
- [ ] Batch database operations
- [ ] Minimize LLM API calls
- [ ] Use connection pooling

---

## Common Development Tasks

### Running Development Server

```bash
# With auto-reload
uvicorn src.api.main:app --reload --port 8000

# Or use script
python scripts/start.py
```

### Running Tests

```bash
# All tests
pytest

# Specific file
pytest tests/test_api.py -v

# With coverage
pytest --cov=src --cov-report=html

# Run fast tests only
pytest -m "not slow"
```

### Database Operations

```bash
# Initialize database
python scripts/init_database.py

# Verify schema
python scripts/init_database.py --verify

# Reset (CAUTION: Deletes all data!)
python scripts/init_database.py --reset
```

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/your-feature

# Make changes
git add .
git commit -m "Add: Your feature description"

# Push
git push origin feature/your-feature

# Create pull request on GitHub
```

---

**Happy Coding!** 🚀
