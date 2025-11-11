#!/bin/bash

# ============================================================================
# Test Runner Script (Bash) for Crypto LLM Trading System
# ============================================================================
# Quick test execution without Python script overhead
#
# Usage:
#   ./scripts/run_tests.sh              # Run all tests
#   ./scripts/run_tests.sh unit         # Unit tests only
#   ./scripts/run_tests.sh integration  # Integration tests only
#   ./scripts/run_tests.sh performance  # Performance tests only
#   ./scripts/run_tests.sh coverage     # All tests with coverage
# ============================================================================

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Default
TEST_TYPE="${1:-all}"

echo -e "${BOLD}${CYAN}"
echo "======================================================================"
echo "  🧪 CRYPTO LLM TRADING SYSTEM - TEST RUNNER"
echo "======================================================================"
echo -e "${NC}"

echo "Started at: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${YELLOW}⚠️  pytest not found, installing...${NC}"
    pip install pytest pytest-cov
fi

# Run tests based on type
case "$TEST_TYPE" in
    unit)
        echo -e "${BOLD}${BLUE}======================================================================"
        echo "  RUNNING UNIT TESTS"
        echo "======================================================================${NC}"
        echo ""

        pytest \
            tests/test_helpers.py \
            tests/test_database.py \
            tests/test_binance_client.py \
            tests/test_llm_clients.py \
            tests/test_core.py \
            tests/test_services.py \
            tests/test_api.py \
            tests/test_scheduler.py \
            -v

        if [ $? -eq 0 ]; then
            echo ""
            echo -e "${GREEN}✅ UNIT TESTS PASSED${NC}"
        else
            echo ""
            echo -e "${RED}❌ UNIT TESTS FAILED${NC}"
            exit 1
        fi
        ;;

    integration)
        echo -e "${BOLD}${BLUE}======================================================================"
        echo "  RUNNING INTEGRATION TESTS"
        echo "======================================================================${NC}"
        echo ""

        pytest \
            tests/test_integration_e2e.py \
            tests/test_trading_cycles.py \
            -v

        if [ $? -eq 0 ]; then
            echo ""
            echo -e "${GREEN}✅ INTEGRATION TESTS PASSED${NC}"
        else
            echo ""
            echo -e "${RED}❌ INTEGRATION TESTS FAILED${NC}"
            exit 1
        fi
        ;;

    performance)
        echo -e "${BOLD}${BLUE}======================================================================"
        echo "  RUNNING PERFORMANCE TESTS"
        echo "======================================================================${NC}"
        echo ""

        pytest tests/test_performance.py -v

        if [ $? -eq 0 ]; then
            echo ""
            echo -e "${GREEN}✅ PERFORMANCE TESTS PASSED${NC}"
        else
            echo ""
            echo -e "${RED}❌ PERFORMANCE TESTS FAILED${NC}"
            exit 1
        fi
        ;;

    coverage)
        echo -e "${BOLD}${BLUE}======================================================================"
        echo "  RUNNING ALL TESTS WITH COVERAGE"
        echo "======================================================================${NC}"
        echo ""

        pytest \
            tests/ \
            --cov=src \
            --cov-report=term-missing \
            --cov-report=html \
            -v

        if [ $? -eq 0 ]; then
            echo ""
            echo -e "${GREEN}✅ ALL TESTS PASSED${NC}"
            echo -e "${CYAN}ℹ️  Coverage report saved to: htmlcov/index.html${NC}"
        else
            echo ""
            echo -e "${RED}❌ TESTS FAILED${NC}"
            exit 1
        fi
        ;;

    all|*)
        echo -e "${BOLD}${BLUE}======================================================================"
        echo "  RUNNING FULL TEST SUITE"
        echo "======================================================================${NC}"
        echo ""

        pytest tests/ -v

        if [ $? -eq 0 ]; then
            echo ""
            echo -e "${GREEN}✅ ALL TESTS PASSED${NC}"
        else
            echo ""
            echo -e "${RED}❌ TESTS FAILED${NC}"
            exit 1
        fi
        ;;
esac

echo ""
echo "======================================================================"
echo "Finished at: $(date '+%Y-%m-%d %H:%M:%S')"
echo "======================================================================"
echo ""
