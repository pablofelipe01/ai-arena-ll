## Crypto LLM Trading System - Testing Guide

Comprehensive testing documentation for the **Crypto LLM Trading System**. This guide covers all test suites, how to run them, and what they validate.

---

## Table of Contents

1. [Test Overview](#test-overview)
2. [Test Categories](#test-categories)
3. [Running Tests](#running-tests)
4. [Test Coverage](#test-coverage)
5. [Writing Tests](#writing-tests)
6. [Continuous Integration](#continuous-integration)

---

## Test Overview

The system has **comprehensive test coverage** across all components:

- **Unit Tests** (8 files): Test individual components in isolation
- **Integration Tests** (2 files): Test complete workflows and system integration
- **Performance Tests** (1 file): Test system performance and stress conditions

**Total Test Files**: 11
**Estimated Test Count**: 100+ tests
**Coverage Target**: >80%

---

## Test Categories

### 1. Unit Tests

Test individual components and modules in isolation with mocked dependencies.

#### `tests/test_helpers.py`
**Purpose**: Test utility helper functions

**Tests**:
- Money formatting (`format_usd()`)
- PnL calculations (`calculate_pnl()`)
- Liquidation price calculation
- Sharpe ratio calculation
- Date/time utilities

**Run**:
```bash
pytest tests/test_helpers.py -v
```

---

#### `tests/test_database.py`
**Purpose**: Test Supabase database client

**Tests**:
- Database connection
- LLM account CRUD operations
- Position management
- Trade recording
- Market data storage
- Error handling

**Run**:
```bash
pytest tests/test_database.py -v
```

---

#### `tests/test_binance_client.py`
**Purpose**: Test Binance API client

**Tests**:
- Connection establishment
- Ticker data fetching
- Kline/candlestick data
- Account balance queries
- Error handling (rate limits, timeouts)
- Testnet vs production mode

**Run**:
```bash
pytest tests/test_binance_client.py -v
```

---

#### `tests/test_llm_clients.py`
**Purpose**: Test LLM API clients (Claude, DeepSeek, GPT-4o)

**Tests**:
- Client initialization
- Trading decision requests
- Response parsing
- Error handling (API errors, invalid responses)
- Rate limiting
- Token counting

**Run**:
```bash
pytest tests/test_llm_clients.py -v
```

---

#### `tests/test_core.py`
**Purpose**: Test core business logic

**Tests**:
- **LLMDecisionService**: Decision making logic
- **PositionManager**: Position opening/closing
- **RiskManager**: Risk validation rules
  - Balance checks
  - Leverage limits
  - Position limits
  - Exposure management

**Run**:
```bash
pytest tests/test_core.py -v
```

---

#### `tests/test_services.py`
**Purpose**: Test service layer

**Tests**:
- **AccountService**: Account management
- **MarketDataService**: Market data aggregation
- **TradingService**: Trading orchestration

**Run**:
```bash
pytest tests/test_services.py -v
```

---

#### `tests/test_api.py`
**Purpose**: Test FastAPI REST API endpoints

**Tests**:
- Health check endpoints
- Trading endpoints (17 tests)
  - `/trading/status`
  - `/trading/accounts`
  - `/trading/positions`
  - `/trading/trades`
  - `/trading/leaderboard`
- Market data endpoints (6 tests)
  - `/market/snapshot`
  - `/market/prices`
  - `/market/ticker/{symbol}`
- Response validation

**Run**:
```bash
pytest tests/test_api.py -v
```

---

#### `tests/test_scheduler.py`
**Purpose**: Test background job scheduler

**Tests**:
- Scheduler initialization
- Job scheduling
- Job execution
- Interval triggers (5/10/15 minutes)
- Manual cycle triggering
- Pause/resume functionality
- Error handling

**Run**:
```bash
pytest tests/test_scheduler.py -v
```

---

### 2. Integration Tests

Test complete workflows with all components working together.

#### `tests/test_integration_e2e.py`
**Purpose**: End-to-end system integration tests

**Test Classes**:

**TestSystemInitialization**:
- All services initialize correctly
- Database connectivity
- External API connections

**TestCompleteTradingCycle**:
- Complete trading cycle execution
- Market data updates
- LLM decision making (all 3 LLMs)
- Position opening during cycle
- Account updates

**TestMultiLLMInteraction**:
- All 3 LLMs participate
- Independent decision making
- LLM isolation (failures don't affect others)

**TestDataPersistence**:
- Positions saved to database
- Trades recorded
- Account balances persisted

**TestErrorHandlingAndRecovery**:
- Database error recovery
- Binance API error handling
- LLM API error handling
- Invalid decision handling

**TestTradingStatusAndReporting**:
- Get trading status
- Get LLM account details
- Get all positions
- Get leaderboard

**Run**:
```bash
pytest tests/test_integration_e2e.py -v
```

---

#### `tests/test_trading_cycles.py`
**Purpose**: Complete trading cycle scenarios

**Test Classes**:

**TestCompleteBuySellCycle**:
- Opening BUY (LONG) positions
- Opening SELL (SHORT) positions
- Closing positions with profit
- Closing positions with loss

**TestMultiplePositions**:
- Multiple positions on different symbols
- Position limit enforcement (max 3)
- Total margin tracking

**TestStopLossAndTakeProfit**:
- Stop loss trigger logic
- Take profit trigger logic

**TestAccountBalanceAndPnL**:
- Balance changes on position open
- PnL calculation for winning trades
- PnL calculation for losing trades
- PnL calculation for SHORT positions
- Cumulative PnL tracking

**TestFullTradingScenarios**:
- Profitable trading day (all wins)
- Losing trading day (all losses)
- Mixed trading day (wins + losses)

**Run**:
```bash
pytest tests/test_trading_cycles.py -v
```

---

### 3. Performance Tests

Test system performance, throughput, and stress conditions.

#### `tests/test_performance.py`
**Purpose**: Performance benchmarking and stress testing

**Test Classes**:

**TestExecutionTime**:
- Single trading cycle execution time (< 5s)
- Account service performance (< 100ms)
- Market data service performance (< 1s)
- Risk manager performance (< 1ms per validation)

**TestThroughput**:
- Multiple sequential trading cycles
- Concurrent account queries
- Position creation throughput

**TestStressConditions**:
- High-frequency trading cycles (50 cycles)
- Many positions stress test (100 positions)
- Rapid account updates (100 updates)

**TestMemoryAndResources**:
- Memory leak detection
- Object count growth monitoring

**Benchmark Summary**:
- Comprehensive performance report
- All key operations timed
- Performance assertions

**Run**:
```bash
pytest tests/test_performance.py -v
```

---

## Running Tests

### Quick Start

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_api.py

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=src --cov-report=html
```

### Using Test Runner Scripts

#### Python Script (Cross-Platform)

```bash
# All tests
python scripts/run_tests.py

# Unit tests only
python scripts/run_tests.py --unit

# Integration tests only
python scripts/run_tests.py --integration

# Performance tests only
python scripts/run_tests.py --performance

# With coverage report
python scripts/run_tests.py --coverage

# Verbose output
python scripts/run_tests.py -v --coverage
```

#### Bash Script (macOS/Linux)

```bash
# All tests
./scripts/run_tests.sh

# Unit tests only
./scripts/run_tests.sh unit

# Integration tests only
./scripts/run_tests.sh integration

# Performance tests only
./scripts/run_tests.sh performance

# With coverage
./scripts/run_tests.sh coverage
```

### Running Specific Tests

```bash
# Run single test function
pytest tests/test_api.py::test_health_check -v

# Run test class
pytest tests/test_integration_e2e.py::TestCompleteTradingCycle -v

# Run tests matching pattern
pytest -k "test_position" -v

# Run tests with marker
pytest -m "slow" -v
```

---

## Test Coverage

### Generating Coverage Reports

```bash
# Terminal report with missing lines
pytest --cov=src --cov-report=term-missing

# HTML report (recommended)
pytest --cov=src --cov-report=html

# XML report (for CI/CD)
pytest --cov=src --cov-report=xml

# Multiple formats
pytest --cov=src --cov-report=html --cov-report=term-missing
```

### Viewing HTML Coverage Report

```bash
# Generate report
pytest --cov=src --cov-report=html

# Open in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Coverage Targets

| Module | Target Coverage | Current |
|--------|----------------|---------|
| `src/utils/` | 90%+ | ✅ |
| `src/external/` | 85%+ | ✅ |
| `src/database/` | 85%+ | ✅ |
| `src/core/` | 90%+ | ✅ |
| `src/services/` | 85%+ | ✅ |
| `src/api/` | 80%+ | ✅ |
| **Overall** | **85%+** | ✅ |

---

## Writing Tests

### Test Structure

```python
"""
Module docstring explaining what's being tested.
"""

import pytest
from unittest.mock import Mock, patch

# Import module under test
from src.module import ClassToTest


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_dependency():
    """Fixture for mocking dependencies."""
    mock = Mock()
    mock.method.return_value = "expected_value"
    return mock


# ============================================================================
# Test Class
# ============================================================================

class TestClassName:
    """Test class for ClassToTest."""

    def test_method_does_something(self, mock_dependency):
        """Test that method does something."""
        # Arrange
        instance = ClassToTest(mock_dependency)
        input_data = {"key": "value"}

        # Act
        result = instance.method(input_data)

        # Assert
        assert result == "expected_result"
        mock_dependency.method.assert_called_once()
```

### Best Practices

1. **Use descriptive test names**: Test names should explain what is being tested
   ```python
   # Good
   def test_position_opening_decreases_available_balance():

   # Bad
   def test_position():
   ```

2. **Follow AAA pattern**: Arrange, Act, Assert
   ```python
   def test_example():
       # Arrange - Set up test data
       data = create_test_data()

       # Act - Execute the code being tested
       result = function_under_test(data)

       # Assert - Verify the result
       assert result == expected_value
   ```

3. **Use fixtures for common setup**:
   ```python
   @pytest.fixture
   def trading_service():
       """Common setup for trading service tests."""
       # ... setup code ...
       return service
   ```

4. **Mock external dependencies**:
   ```python
   @patch('src.external.binance_client.BinanceClient')
   def test_with_mocked_binance(mock_binance):
       mock_binance.get_ticker.return_value = {"price": "2000.0"}
       # ... test code ...
   ```

5. **Test edge cases and errors**:
   ```python
   def test_handles_invalid_input():
       with pytest.raises(ValueError):
           function_with_validation(invalid_input)
   ```

---

## Test Commands Reference

### Basic Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run quietly (less output)
pytest -q

# Stop on first failure
pytest -x

# Show local variables in tracebacks
pytest -l

# Run last failed tests
pytest --lf

# Run new tests first
pytest --nf
```

### Coverage Commands

```bash
# Basic coverage
pytest --cov=src

# Coverage with missing lines
pytest --cov=src --cov-report=term-missing

# HTML coverage report
pytest --cov=src --cov-report=html

# Fail if coverage below threshold
pytest --cov=src --cov-fail-under=80
```

### Performance Commands

```bash
# Show slowest tests
pytest --durations=10

# Time each test
pytest --durations=0

# Profile test execution
pytest --profile
```

### Debugging Commands

```bash
# Drop into debugger on failure
pytest --pdb

# Drop into debugger on first failure
pytest -x --pdb

# Show print statements
pytest -s

# Verbose with print statements
pytest -vv -s
```

---

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.11

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov

    - name: Run tests with coverage
      run: |
        pytest --cov=src --cov-report=xml --cov-report=term-missing

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v2
```

---

## Troubleshooting

### Common Issues

**1. Import errors**
```bash
# Solution: Add project root to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest
```

**2. pytest not found**
```bash
# Solution: Install pytest
pip install pytest pytest-cov
```

**3. Tests fail due to missing dependencies**
```bash
# Solution: Install all requirements
pip install -r requirements.txt
```

**4. Coverage reports not generating**
```bash
# Solution: Ensure pytest-cov is installed
pip install pytest-cov
pytest --cov=src --cov-report=html
```

**5. Tests run slow**
```bash
# Solution: Run only fast tests, skip performance tests
pytest tests/ --ignore=tests/test_performance.py
```

---

## Test Summary

| Category | Files | Tests | Purpose |
|----------|-------|-------|---------|
| **Unit Tests** | 8 | ~80 | Component testing |
| **Integration Tests** | 2 | ~20 | E2E workflows |
| **Performance Tests** | 1 | ~15 | Performance benchmarking |
| **Total** | **11** | **~115** | **Complete coverage** |

---

## Quick Reference

```bash
# Development workflow
pytest tests/test_api.py -v              # Test specific module
pytest --cov=src --cov-report=html       # Full coverage report

# Pre-commit checks
./scripts/run_tests.sh unit              # Fast unit tests
./scripts/run_tests.sh integration       # Integration check
python scripts/run_tests.py --coverage   # Full check with coverage

# Performance validation
pytest tests/test_performance.py -v -s   # With output

# Debugging
pytest tests/test_core.py::test_name -vv -s --pdb
```

---

**All tests passing = System ready for deployment!** ✅
