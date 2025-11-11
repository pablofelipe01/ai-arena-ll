# 24-Hour Trading Demo Guide

Complete guide for preparing, running, and monitoring the **24-hour LLM trading competition demo**.

---

## Table of Contents

1. [Overview](#overview)
2. [Pre-Demo Preparation](#pre-demo-preparation)
3. [Demo Day Checklist](#demo-day-checklist)
4. [Starting the Demo](#starting-the-demo)
5. [Monitoring During Demo](#monitoring-during-demo)
6. [Troubleshooting](#troubleshooting)
7. [Post-Demo Analysis](#post-demo-analysis)

---

## Overview

### What is the 24-Hour Demo?

The 24-hour demo is a **live trading competition** where 3 Large Language Models trade cryptocurrency futures autonomously for 24 consecutive hours. Each LLM:

- Starts with **$100 virtual balance**
- Makes independent trading decisions every **5 minutes**
- Competes to maximize profit through intelligent trading
- Operates **completely autonomously** with no human intervention

### Demo Goals

- Demonstrate system reliability and stability
- Showcase LLM decision-making capabilities
- Generate performance data for analysis
- Validate automated trading logic
- Create engaging competitive narrative

---

## Pre-Demo Preparation

### 1 Week Before Demo

#### System Testing

- [ ] **Complete testnet run (24 hours)**
  ```bash
  # Ensure USE_TESTNET=True in .env
  python scripts/verify_config.py
  python scripts/start.py
  # Let run for 24 hours, monitor for issues
  ```

- [ ] **Verify all tests pass**
  ```bash
  pytest --cov=src --cov-report=html
  # Target: 85%+ coverage, all tests green
  ```

- [ ] **Performance benchmarks**
  ```bash
  pytest tests/test_performance.py -v
  # Verify all benchmarks meet targets
  ```

- [ ] **Stress test system**
  ```bash
  pytest tests/test_performance.py::TestStressConditions -v
  # Ensure system handles load
  ```

#### API Key Verification

- [ ] **Binance API**
  - API key and secret configured
  - Futures trading enabled
  - Sufficient testnet funds (or real funds if production)
  - IP whitelisting configured (production only)
  - Rate limits verified

- [ ] **LLM APIs**
  - Anthropic (Claude) API key valid, sufficient credits
  - DeepSeek API key valid, sufficient credits
  - OpenAI (GPT-4o) API key valid, sufficient credits
  - Test all LLM connections:
    ```bash
    python scripts/verify_config.py
    ```

#### Database Preparation

- [ ] **Database health**
  ```bash
  python scripts/init_database.py --verify
  ```

- [ ] **Create backup** (if using production data)
  - Export via Supabase dashboard
  - Store backup securely
  - Document restore procedure

- [ ] **Test database performance**
  - Verify query response times
  - Check connection pooling
  - Monitor for slow queries

#### Documentation Review

- [ ] **Emergency procedures documented**
  - How to stop trading immediately
  - How to close all positions
  - Emergency contact information
  - Backup plan if system fails

- [ ] **Monitoring setup**
  - Dashboard accessible
  - Health check scripts tested
  - Alert mechanisms configured
  - Log rotation enabled

### 3 Days Before Demo

#### Final Configuration

- [ ] **Review all settings**
  ```bash
  cat .env | grep -v "SECRET\|KEY" | grep -v "^#"
  # Verify all configuration values
  ```

- [ ] **Set production parameters** (if applicable)
  ```env
  USE_TESTNET=False  # ⚠️ Only if doing real money demo!
  DEBUG=False
  ENVIRONMENT=production
  ```

- [ ] **Verify trading limits**
  ```env
  MIN_TRADE_SIZE_USD=10.0
  MAX_TRADE_SIZE_USD=30.0
  MAX_LEVERAGE=10
  MAX_OPEN_POSITIONS=3
  ```

#### Deployment Preparation

- [ ] **Decide deployment method**
  - Local machine (simplest)
  - Docker (recommended for isolation)
  - Cloud VPS (best for 24/7 uptime)

- [ ] **If using Docker:**
  ```bash
  docker-compose build
  docker-compose up -d
  docker-compose ps  # Verify running
  ```

- [ ] **If using cloud:**
  - Server provisioned and configured
  - systemd service configured
  - Firewall rules set
  - SSH access verified

#### Communication Setup

- [ ] **Demo announcement prepared**
  - Start time communicated
  - Dashboard URL shared
  - What to expect documented
  - How to follow along explained

- [ ] **Monitoring team ready**
  - Who will monitor system
  - Contact information shared
  - Escalation procedure defined
  - Coverage schedule (if 24/7 monitoring)

### 1 Day Before Demo

#### Final System Check

- [ ] **Complete dry run**
  ```bash
  # Start system
  python scripts/start.py --verify

  # Run for 2-3 hours
  # Monitor everything

  # Stop system
  curl -X POST http://localhost:8000/scheduler/pause
  ```

- [ ] **Review logs**
  ```bash
  tail -n 100 logs/app.log
  tail -n 100 logs/llm_decisions.log
  # Check for any warnings or errors
  ```

- [ ] **Test emergency stop**
  ```bash
  curl -X POST http://localhost:8000/scheduler/pause
  # Verify trading stops immediately
  ```

- [ ] **Test monitoring scripts**
  ```bash
  python scripts/monitor_demo.py --interval 10
  # Run for 1 minute, verify output
  # Ctrl+C to stop

  ./scripts/health_check.sh
  # Should show "HEALTHY"
  ```

#### Final Preparation

- [ ] **Reset database for demo**
  ```bash
  # ⚠️ WARNING: This deletes all data!
  python scripts/init_database.py --reset
  # Verify all accounts created with $100 each
  ```

- [ ] **Clear old logs**
  ```bash
  > logs/app.log
  > logs/llm_decisions.log
  ```

- [ ] **Verify initial state**
  ```bash
  curl http://localhost:8000/trading/accounts
  # Should show 3 accounts, $100 each, 0 trades
  ```

---

## Demo Day Checklist

### Morning of Demo (2-3 hours before start)

- [ ] **System health check**
  ```bash
  ./scripts/health_check.sh
  ```

- [ ] **Verify all services**
  ```bash
  # Check database
  python scripts/init_database.py --verify

  # Check API keys
  python scripts/verify_config.py

  # Check system resources
  htop  # Or Activity Monitor on macOS
  ```

- [ ] **Start monitoring**
  ```bash
  # Terminal 1: System logs
  tail -f logs/app.log

  # Terminal 2: Demo monitor
  python scripts/monitor_demo.py --interval 30

  # Terminal 3: Dashboard
  open http://localhost:8000/dashboard/
  ```

### 30 Minutes Before Start

- [ ] **Final verification**
  ```bash
  curl http://localhost:8000/health
  # Should return: {"status": "healthy"}

  curl http://localhost:8000/trading/status
  # Verify correct initial state
  ```

- [ ] **Communication**
  - [ ] Announce demo start time
  - [ ] Share dashboard URL
  - [ ] Confirm monitoring team ready

---

## Starting the Demo

### Startup Procedure

**Step 1: Start System**
```bash
# If running locally
python scripts/start.py --verify

# If using Docker
docker-compose up -d
docker-compose logs -f

# If using systemd
sudo systemctl start crypto-llm-trading
sudo systemctl status crypto-llm-trading
```

**Step 2: Verify Startup**
```bash
# Wait 30 seconds for initialization

# Check health
curl http://localhost:8000/health

# Check scheduler
curl http://localhost:8000/scheduler/status
# Should show: "is_running": true
```

**Step 3: Verify First Cycle**
```bash
# Wait 5 minutes for first trading cycle

# Check logs
tail -f logs/app.log | grep "Trading cycle"

# Check if decisions were made
curl http://localhost:8000/trading/leaderboard
```

**Step 4: Confirm Everything Running**
```bash
# All checks should pass:
./scripts/health_check.sh  # HEALTHY
curl http://localhost:8000/scheduler/status  # is_running: true
curl http://localhost:8000/trading/status  # Check data looks correct
```

### What to Expect

**First Hour:**
- System initializes and stabilizes
- Each LLM makes 12 trading decisions (every 5 minutes)
- Some positions may be opened
- Dashboard shows real-time updates

**Hours 1-6:**
- Trading patterns emerge
- PnL diverges as LLMs make different decisions
- Leaderboard rankings fluctuate
- System should be stable

**Hours 6-12:**
- Midpoint of demo
- Performance trends become clearer
- Some LLMs may pull ahead
- Good time for performance check

**Hours 12-18:**
- Strategies continue to play out
- Market conditions may change
- System should maintain stability

**Hours 18-24:**
- Final stretch
- Last trading decisions
- Final rankings determined
- Prepare for post-demo analysis

---

## Monitoring During Demo

### Monitoring Schedule

**Hour 0 (Start):**
- [ ] System started successfully
- [ ] All 3 LLMs responding
- [ ] First cycle completed
- [ ] Dashboard showing data
- [ ] No errors in logs

**Hour 1:**
- [ ] At least 12 cycles completed
- [ ] All LLMs made decisions
- [ ] Some trades executed
- [ ] PnL being calculated
- [ ] System stable

**Hour 6:**
- [ ] ~72 cycles completed
- [ ] Review PnL trends
- [ ] Check for any errors
- [ ] Verify API rate limits okay
- [ ] Database performance good

**Hour 12 (Midpoint):**
- [ ] ~144 cycles completed
- [ ] System stability verified
- [ ] Review leaderboard
- [ ] Check resource usage (CPU, memory)
- [ ] Export midpoint data

**Hour 18:**
- [ ] ~216 cycles completed
- [ ] Final stretch begins
- [ ] Verify no errors
- [ ] Check all LLMs still active

**Hour 24 (End):**
- [ ] All cycles completed (~288 total)
- [ ] Final rankings determined
- [ ] Export all data
- [ ] Stop system gracefully
- [ ] Begin analysis

### Continuous Monitoring

**Use monitoring script:**
```bash
python scripts/monitor_demo.py --interval 30
```

**Check these metrics every hour:**
- [ ] Trading cycles executing (every 5 min)
- [ ] All 3 LLMs making decisions
- [ ] Positions opening/closing correctly
- [ ] PnL calculations accurate
- [ ] No system errors
- [ ] API rate limits not exceeded
- [ ] Database connections stable
- [ ] System resources healthy

### Alert Conditions

**Immediate Action Required:**
- System health check fails
- Scheduler stops running
- LLM API errors (all 3 failing)
- Database connection lost
- Server/container crash

**Monitor Closely:**
- Single LLM API errors (1-2 LLMs failing)
- Slow response times (>5s per cycle)
- Unusual trading behavior
- Memory leaks (increasing usage)
- High CPU usage (>80%)

---

## Troubleshooting

### Issue: Trading Cycles Not Executing

**Symptoms:** No new trades, scheduler inactive

**Check:**
```bash
curl http://localhost:8000/scheduler/status
```

**Fix:**
```bash
# If scheduler paused
curl -X POST http://localhost:8000/scheduler/resume

# If scheduler stopped
# Restart system
```

### Issue: LLM API Errors

**Symptoms:** Errors in logs about LLM API calls failing

**Check:**
```bash
# Check specific LLM
grep "LLM-A" logs/llm_decisions.log | tail -n 20
grep "ERROR" logs/app.log | grep "LLM"
```

**Fix:**
```bash
# Verify API keys
python scripts/verify_config.py

# Check API status
# Anthropic: https://status.anthropic.com
# OpenAI: https://status.openai.com
# DeepSeek: Check their status page

# Check rate limits
curl http://localhost:8000/scheduler/stats
```

### Issue: Database Errors

**Symptoms:** Errors about database connections or queries

**Check:**
```bash
python scripts/init_database.py --verify
grep "database\|Database" logs/app.log | tail -n 20
```

**Fix:**
```bash
# Check Supabase status
# Visit: https://status.supabase.com

# Verify credentials
echo $SUPABASE_URL
echo $SUPABASE_KEY | cut -c1-10  # First 10 chars
```

### Emergency Stop Procedure

**If you need to stop trading immediately:**

```bash
# Method 1: Pause scheduler (keeps system running)
curl -X POST http://localhost:8000/scheduler/pause

# Method 2: Stop entire system
# If running locally:
# Ctrl+C in terminal

# If using Docker:
docker-compose down

# If using systemd:
sudo systemctl stop crypto-llm-trading
```

**To manually close all positions:**
- Use Binance web interface
- Go to Futures > Positions
- Close all open positions manually

---

## Post-Demo Analysis

### Data Export

**Export all data:**
```bash
# Create export directory
mkdir -p demo_results_$(date +%Y%m%d)

# Export trades
curl http://localhost:8000/trading/trades?limit=10000 > demo_results_$(date +%Y%m%d)/all_trades.json

# Export leaderboard
curl http://localhost:8000/trading/leaderboard > demo_results_$(date +%Y%m%d)/final_leaderboard.json

# Export each LLM data
curl http://localhost:8000/trading/accounts/LLM-A > demo_results_$(date +%Y%m%d)/llm_a_account.json
curl http://localhost:8000/trading/accounts/LLM-B > demo_results_$(date +%Y%m%d)/llm_b_account.json
curl http://localhost:8000/trading/accounts/LLM-C > demo_results_$(date +%Y%m%d)/llm_c_account.json

# Export all positions
curl http://localhost:8000/trading/positions > demo_results_$(date +%Y%m%d)/all_positions.json

# Copy logs
cp logs/app.log demo_results_$(date +%Y%m%d)/
cp logs/llm_decisions.log demo_results_$(date +%Y%m%d)/
```

### Analysis Checklist

- [ ] **Calculate total statistics**
  - Total trades per LLM
  - Win rate per LLM
  - Total PnL per LLM
  - Average trade size
  - Average position duration

- [ ] **Identify patterns**
  - Which symbols were most traded
  - Long vs short bias per LLM
  - Leverage usage patterns
  - Risk management behavior

- [ ] **Performance analysis**
  - Best performing LLM and why
  - Worst performing LLM and why
  - Most profitable trades
  - Biggest losses
  - Sharpe ratio / risk-adjusted returns

- [ ] **System analysis**
  - Total uptime percentage
  - Average cycle execution time
  - API call success rates
  - Any errors or issues encountered
  - Resource usage patterns

- [ ] **Market analysis**
  - Market conditions during demo
  - Volatility patterns
  - How market affected each LLM
  - Correlation with crypto market

### Presentation

**Create summary report including:**
1. Executive summary (1 page)
2. Competition results (leaderboard, stats)
3. Individual LLM performance analysis
4. Trading pattern analysis
5. System performance metrics
6. Lessons learned
7. Next steps

---

## Quick Reference

### Essential Commands

```bash
# Start system
python scripts/start.py --verify

# Check health
curl http://localhost:8000/health

# Monitor demo
python scripts/monitor_demo.py --interval 30

# Pause trading
curl -X POST http://localhost:8000/scheduler/pause

# Resume trading
curl -X POST http://localhost:8000/scheduler/resume

# View logs
tail -f logs/app.log

# Dashboard
open http://localhost:8000/dashboard/
```

### Important URLs

- Dashboard: http://localhost:8000/dashboard/
- API Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health
- Status: http://localhost:8000/trading/status
- Leaderboard: http://localhost:8000/trading/leaderboard

---

**Ready to run an epic 24-hour LLM trading competition!** 🚀🤖💰
