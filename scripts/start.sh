#!/bin/bash

# ============================================================================
# Crypto LLM Trading System - Startup Script
# ============================================================================
# This script starts the FastAPI server with the WebSocket dashboard
# and background trading scheduler.
#
# Usage:
#   ./scripts/start.sh              # Start with default settings
#   ./scripts/start.sh --verify     # Verify config before starting
#   ./scripts/start.sh --port 8080  # Start on custom port
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
PORT=8000
HOST="0.0.0.0"
VERIFY_CONFIG=false
RELOAD=true

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --verify)
            VERIFY_CONFIG=true
            shift
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        --no-reload)
            RELOAD=false
            shift
            ;;
        --help)
            echo "Crypto LLM Trading System - Startup Script"
            echo ""
            echo "Usage:"
            echo "  ./scripts/start.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --verify        Verify configuration before starting"
            echo "  --port PORT     Port to run on (default: 8000)"
            echo "  --host HOST     Host to bind to (default: 0.0.0.0)"
            echo "  --no-reload     Disable auto-reload (for production)"
            echo "  --help          Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./scripts/start.sh"
            echo "  ./scripts/start.sh --verify"
            echo "  ./scripts/start.sh --port 8080"
            echo "  ./scripts/start.sh --no-reload --port 8000"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}"
echo "============================================================================"
echo "  🚀 CRYPTO LLM TRADING SYSTEM"
echo "============================================================================"
echo -e "${NC}"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python 3 found: $(python3 --version)${NC}"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env file not found${NC}"
    echo -e "${YELLOW}Please create a .env file with required configuration${NC}"
    echo -e "${YELLOW}See .env.example for reference${NC}"
    exit 1
fi

echo -e "${GREEN}✅ .env file found${NC}"

# Verify configuration if requested
if [ "$VERIFY_CONFIG" = true ]; then
    echo ""
    echo -e "${BLUE}🔍 Verifying configuration...${NC}"
    python3 scripts/verify_config.py

    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Configuration verification failed${NC}"
        exit 1
    fi
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}⚠️  No virtual environment detected${NC}"
    echo -e "${YELLOW}   It's recommended to use a virtual environment${NC}"
    echo ""
fi

# Install dependencies if needed
echo ""
echo -e "${BLUE}📦 Checking dependencies...${NC}"

if ! python3 -c "import fastapi" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  FastAPI not found, installing dependencies...${NC}"
    pip install -r requirements.txt
else
    echo -e "${GREEN}✅ Dependencies installed${NC}"
fi

# Display startup information
echo ""
echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}📊 STARTUP CONFIGURATION${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo -e "  Host:              ${GREEN}$HOST${NC}"
echo -e "  Port:              ${GREEN}$PORT${NC}"
echo -e "  Auto-reload:       ${GREEN}$RELOAD${NC}"
echo -e "  Dashboard URL:     ${GREEN}http://localhost:$PORT/dashboard/${NC}"
echo -e "  API Docs:          ${GREEN}http://localhost:$PORT/docs${NC}"
echo -e "  WebSocket:         ${GREEN}ws://localhost:$PORT/ws${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

# Display system features
echo -e "${BLUE}🤖 ACTIVE LLMs:${NC}"
echo -e "  • ${GREEN}LLM-A${NC} - Claude Sonnet 4"
echo -e "  • ${GREEN}LLM-B${NC} - DeepSeek Reasoner"
echo -e "  • ${GREEN}LLM-C${NC} - GPT-4o"
echo ""

echo -e "${BLUE}📈 TRADING CONFIGURATION:${NC}"
echo -e "  • ${GREEN}6 symbols${NC} - ETH, BNB, XRP, DOGE, ADA, AVAX"
echo -e "  • ${GREEN}5-minute cycles${NC} - Automated trading"
echo -e "  • ${GREEN}\$100 per LLM${NC} - Virtual balance"
echo ""

echo -e "${BLUE}💻 FEATURES:${NC}"
echo -e "  • ${GREEN}Real-time WebSocket dashboard${NC}"
echo -e "  • ${GREEN}Automated 5-minute trading cycles${NC}"
echo -e "  • ${GREEN}REST API (23 endpoints)${NC}"
echo -e "  • ${GREEN}Live market data${NC}"
echo -e "  • ${GREEN}LLM leaderboard${NC}"
echo -e "  • ${GREEN}Position tracking${NC}"
echo ""

# Countdown before starting
echo -e "${YELLOW}Starting server in 3 seconds...${NC}"
sleep 1
echo -e "${YELLOW}2...${NC}"
sleep 1
echo -e "${YELLOW}1...${NC}"
sleep 1

echo ""
echo -e "${GREEN}============================================================================${NC}"
echo -e "${GREEN}🚀 STARTING SERVER...${NC}"
echo -e "${GREEN}============================================================================${NC}"
echo ""

# Build uvicorn command
UVICORN_CMD="uvicorn src.api.main:app --host $HOST --port $PORT --log-level info"

if [ "$RELOAD" = true ]; then
    UVICORN_CMD="$UVICORN_CMD --reload"
fi

# Start the server
$UVICORN_CMD
