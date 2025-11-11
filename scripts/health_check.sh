#!/bin/bash

# Health check script for Crypto LLM Trading System
# Can be used for monitoring, cron jobs, or systemd health checks

# Configuration
HEALTH_URL="${HEALTH_URL:-http://localhost:8000/health}"
TIMEOUT="${TIMEOUT:-5}"
CHECK_INTERVAL="${CHECK_INTERVAL:-60}"
MAX_FAILURES="${MAX_FAILURES:-3}"
ALERT_EMAIL="${ALERT_EMAIL:-}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check health endpoint
check_health() {
    local response
    local status_code

    response=$(curl -s -w "\n%{http_code}" --max-time "$TIMEOUT" "$HEALTH_URL" 2>/dev/null)
    status_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | sed '$d')

    if [ "$status_code" = "200" ]; then
        echo "$body" | python3 -c "import sys, json; data=json.load(sys.stdin); print('healthy' if data.get('status') == 'healthy' else 'unhealthy')" 2>/dev/null || echo "unhealthy"
    else
        echo "unreachable"
    fi
}

# Single check mode
single_check() {
    echo "Checking system health..."
    echo "URL: $HEALTH_URL"
    echo ""

    result=$(check_health)

    if [ "$result" = "healthy" ]; then
        echo -e "${GREEN}System is HEALTHY${NC}"
        exit 0
    elif [ "$result" = "unhealthy" ]; then
        echo -e "${YELLOW}System is UNHEALTHY${NC}"
        exit 1
    else
        echo -e "${RED}System is UNREACHABLE${NC}"
        exit 2
    fi
}

# Continuous monitoring mode
monitor() {
    echo "Starting health monitor..."
    echo "URL: $HEALTH_URL"
    echo "Check interval: ${CHECK_INTERVAL}s"
    echo "Max failures: $MAX_FAILURES"
    echo "Press Ctrl+C to stop"
    echo ""

    local failure_count=0

    while true; do
        timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        result=$(check_health)

        if [ "$result" = "healthy" ]; then
            echo -e "${timestamp} - ${GREEN}HEALTHY${NC}"
            failure_count=0
        elif [ "$result" = "unhealthy" ]; then
            echo -e "${timestamp} - ${YELLOW}UNHEALTHY${NC}"
            ((failure_count++))
        else
            echo -e "${timestamp} - ${RED}UNREACHABLE${NC}"
            ((failure_count++))
        fi

        # Check if max failures exceeded
        if [ $failure_count -ge $MAX_FAILURES ]; then
            echo -e "${RED}ALERT: Max failures ($MAX_FAILURES) exceeded!${NC}"

            if [ -n "$ALERT_EMAIL" ]; then
                echo "System unhealthy" | mail -s "Trading System Alert" "$ALERT_EMAIL" 2>/dev/null || true
            fi

            failure_count=0
        fi

        sleep "$CHECK_INTERVAL"
    done
}

# Usage
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Health check script for Crypto LLM Trading System.

OPTIONS:
    -h, --help          Show this help message
    -m, --monitor       Continuous monitoring mode
    -u, --url URL       Health check URL (default: http://localhost:8000/health)
    -t, --timeout SEC   Timeout in seconds (default: 5)
    -i, --interval SEC  Check interval for monitor mode (default: 60)
    -f, --failures N    Max failures before alert (default: 3)
    -e, --email EMAIL   Alert email address

EXAMPLES:
    # Single health check
    $0

    # Continuous monitoring
    $0 --monitor

    # Custom URL and interval
    $0 --monitor --url http://example.com:8000/health --interval 30

    # With email alerts
    $0 --monitor --email admin@example.com --failures 5
EOF
}

# Parse arguments
MONITOR_MODE=0

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -m|--monitor)
            MONITOR_MODE=1
            shift
            ;;
        -u|--url)
            HEALTH_URL="$2"
            shift 2
            ;;
        -t|--timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        -i|--interval)
            CHECK_INTERVAL="$2"
            shift 2
            ;;
        -f|--failures)
            MAX_FAILURES="$2"
            shift 2
            ;;
        -e|--email)
            ALERT_EMAIL="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Run
if [ $MONITOR_MODE -eq 1 ]; then
    monitor
else
    single_check
fi
