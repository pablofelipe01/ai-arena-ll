# Crypto LLM Trading System - Deployment Guide

Complete deployment guide for running the **Crypto LLM Trading System** in production or staging environments.

---

## Table of Contents

1. [Deployment Options](#deployment-options)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Local Production Deployment](#local-production-deployment)
4. [Docker Deployment](#docker-deployment)
5. [Cloud Deployment](#cloud-deployment)
6. [Environment Configuration](#environment-configuration)
7. [Database Setup](#database-setup)
8. [Security Considerations](#security-considerations)
9. [Monitoring & Logging](#monitoring--logging)
10. [24-Hour Demo Setup](#24-hour-demo-setup)

---

## Deployment Options

### Option 1: Local Production
- Run directly on your machine
- Best for: Testing, development, small-scale demo
- Pros: Simple setup, full control
- Cons: Not scalable, requires active machine

### Option 2: Docker
- Containerized deployment
- Best for: Consistent environments, easy scaling
- Pros: Reproducible, isolated, portable
- Cons: Requires Docker knowledge

### Option 3: Cloud (VPS/EC2)
- Deploy to cloud server
- Best for: Production, long-term operation, high availability
- Pros: 24/7 uptime, professional hosting
- Cons: Costs, more complex setup

---

## Pre-Deployment Checklist

### Required Accounts & API Keys

- [ ] **Binance Account**
  - [ ] API key created
  - [ ] Secret key secured
  - [ ] Futures trading enabled
  - [ ] IP whitelisting configured (production)
  - [ ] Testnet account for testing

- [ ] **Supabase Project**
  - [ ] Project created
  - [ ] Database schema executed (schema.sql)
  - [ ] URL and anon key copied
  - [ ] Database verified with init_database.py

- [ ] **LLM API Keys**
  - [ ] Anthropic (Claude) API key
  - [ ] DeepSeek API key
  - [ ] OpenAI API key
  - [ ] Sufficient credits on all accounts

### System Requirements

- [ ] Python 3.9+ installed
- [ ] Git installed
- [ ] 2GB+ RAM available
- [ ] 100MB+ disk space
- [ ] Stable internet connection
- [ ] PostgreSQL client (optional, for direct DB access)

### Configuration Files

- [ ] `.env` file created with all keys
- [ ] `USE_TESTNET=True` for testing (IMPORTANT)
- [ ] All environment variables validated
- [ ] Logs directory created

---

## Local Production Deployment

### Step 1: Clone and Setup

```bash
# Clone repository
git clone <repository-url>
cd crypto-llm-trading

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env  # or your preferred editor

# IMPORTANT: Set these for production
# USE_TESTNET=False  # Only after thorough testing!
# DEBUG=False
# ENVIRONMENT=production
```

### Step 3: Database Initialization

```bash
# Verify database schema
python scripts/init_database.py --verify

# If verification fails, run schema.sql in Supabase SQL Editor
# Then verify again
```

### Step 4: Configuration Verification

```bash
# Run verification script
python scripts/verify_config.py

# Should see all green checkmarks
```

### Step 5: Start System

```bash
# Option 1: Using Python script
python scripts/start.py --verify

# Option 2: Using bash script (macOS/Linux)
./scripts/start.sh --verify

# Option 3: Direct uvicorn
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

### Step 6: Verify System

```bash
# Check health endpoint
curl http://localhost:8000/health

# Access dashboard
open http://localhost:8000/dashboard/

# Check API docs
open http://localhost:8000/docs
```

---

## Docker Deployment

### Dockerfile

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  app:
    build: .
    container_name: crypto-llm-trading
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### Build and Run

```bash
# Build image
docker-compose build

# Start container
docker-compose up -d

# View logs
docker-compose logs -f

# Stop container
docker-compose down

# Restart container
docker-compose restart
```

### Docker Commands

```bash
# Check container status
docker-compose ps

# Execute command in container
docker-compose exec app python scripts/verify_config.py

# View logs
docker-compose logs -f app

# Stop and remove
docker-compose down -v  # -v removes volumes
```

---

## Cloud Deployment

### AWS EC2 Deployment

**1. Launch EC2 Instance**:
- AMI: Ubuntu 22.04 LTS
- Instance Type: t3.small (2GB RAM minimum)
- Security Group: Allow inbound on port 8000 (and 22 for SSH)
- Storage: 20GB

**2. Connect to Instance**:
```bash
ssh -i your-key.pem ubuntu@your-ec2-ip
```

**3. Install Dependencies**:
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3-pip git -y

# Install Docker (optional)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu
```

**4. Deploy Application**:
```bash
# Clone repository
git clone <repository-url>
cd crypto-llm-trading

# Setup virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure .env
nano .env

# Run with systemd (recommended)
sudo cp deployment/crypto-llm-trading.service /etc/systemd/system/
sudo systemctl enable crypto-llm-trading
sudo systemctl start crypto-llm-trading
```

**5. Setup Systemd Service**:

Create `/etc/systemd/system/crypto-llm-trading.service`:

```ini
[Unit]
Description=Crypto LLM Trading System
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/crypto-llm-trading
Environment="PATH=/home/ubuntu/crypto-llm-trading/venv/bin"
ExecStart=/home/ubuntu/crypto-llm-trading/venv/bin/uvicorn src.api.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**6. Manage Service**:
```bash
# Start service
sudo systemctl start crypto-llm-trading

# Check status
sudo systemctl status crypto-llm-trading

# View logs
sudo journalctl -u crypto-llm-trading -f

# Restart service
sudo systemctl restart crypto-llm-trading
```

---

## Environment Configuration

### Production .env Template

```env
# ============================================================================
# PRODUCTION ENVIRONMENT CONFIGURATION
# ============================================================================

# Environment
ENVIRONMENT=production
DEBUG=False
USE_TESTNET=False  # ⚠️ CAUTION: This uses real money!

# API Server
HOST=0.0.0.0
PORT=8000

# Binance API (Production)
BINANCE_API_KEY=your_production_api_key
BINANCE_SECRET_KEY=your_production_secret_key
BINANCE_BASE_URL=https://fapi.binance.com

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key

# LLM APIs
LLM_A_PROVIDER=anthropic
LLM_A_MODEL=claude-sonnet-4-20250514
LLM_A_API_KEY=your_claude_api_key
LLM_A_TEMPERATURE=0.7

LLM_B_PROVIDER=deepseek
LLM_B_MODEL=deepseek-reasoner
LLM_B_API_KEY=your_deepseek_api_key
LLM_B_TEMPERATURE=0.7

LLM_C_PROVIDER=openai
LLM_C_MODEL=gpt-4o
LLM_C_API_KEY=your_openai_api_key
LLM_C_TEMPERATURE=0.7

# Trading Configuration
AVAILABLE_PAIRS=ETHUSDT,BNBUSDT,XRPUSDT,DOGEUSDT,ADAUSDT,AVAXUSDT
MIN_TRADE_SIZE_USD=10.0
MAX_TRADE_SIZE_USD=30.0
MAX_LEVERAGE=10
MAX_OPEN_POSITIONS=3
INITIAL_BALANCE_USD=100.0

# Background Jobs
LLM_DECISION_INTERVAL_SECONDS=300  # 5 minutes
UPDATE_MARKET_DATA_INTERVAL=60
```

---

## Database Setup

### Production Database Checklist

- [ ] Supabase project created
- [ ] Schema executed (scripts/schema.sql)
- [ ] Initial LLM accounts created (3 accounts)
- [ ] Database verified: `python scripts/init_database.py --verify`
- [ ] Backup strategy configured
- [ ] Connection pool limits set

### Database Backup

```bash
# Export database (via Supabase Dashboard)
# Go to: Database > Backups > Download Backup

# Or use pg_dump (if direct access available)
pg_dump -h your-db-host -U postgres -d your-db > backup.sql
```

---

## Security Considerations

### Production Security Checklist

- [ ] **API Keys**:
  - [ ] All API keys stored in .env (not hardcoded)
  - [ ] .env file in .gitignore
  - [ ] Restricted permissions on .env (chmod 600)

- [ ] **Binance Security**:
  - [ ] IP whitelisting enabled
  - [ ] Withdraw permission disabled
  - [ ] Trading-only API key
  - [ ] API key expiration set

- [ ] **Server Security**:
  - [ ] Firewall configured (ufw/iptables)
  - [ ] SSH key-only authentication
  - [ ] Regular system updates
  - [ ] Non-root user for app

- [ ] **Application Security**:
  - [ ] DEBUG=False in production
  - [ ] CORS configured properly
  - [ ] Rate limiting enabled
  - [ ] Input validation on all endpoints

- [ ] **Monitoring**:
  - [ ] Health checks configured
  - [ ] Alerts for critical errors
  - [ ] Log rotation enabled
  - [ ] Backup strategy in place

---

## Monitoring & Logging

### Log Files

```bash
# Application logs
logs/app.log              # General application logs
logs/llm_decisions.log    # LLM decision audit trail

# View logs
tail -f logs/app.log
tail -f logs/llm_decisions.log

# Search logs
grep "ERROR" logs/app.log
grep "LLM-A" logs/llm_decisions.log
```

### System Monitoring

**Monitor with systemd (Linux)**:
```bash
# Service status
sudo systemctl status crypto-llm-trading

# View logs
sudo journalctl -u crypto-llm-trading -f

# Check resource usage
htop
```

**Monitor with Docker**:
```bash
# Container stats
docker stats crypto-llm-trading

# Container logs
docker logs -f crypto-llm-trading

# Container health
docker inspect crypto-llm-trading | grep Health
```

### Health Checks

```bash
# Automated health check script
#!/bin/bash
HEALTH_URL="http://localhost:8000/health"

while true; do
    RESPONSE=$(curl -s $HEALTH_URL)
    STATUS=$(echo $RESPONSE | jq -r '.status')

    if [ "$STATUS" != "healthy" ]; then
        echo "ALERT: System unhealthy!"
        # Send alert (email, Slack, etc.)
    fi

    sleep 60  # Check every minute
done
```

---

## 24-Hour Demo Setup

### Pre-Demo Checklist

**1 Week Before**:
- [ ] System tested on testnet
- [ ] All LLMs responding correctly
- [ ] Database backup created
- [ ] Monitoring scripts tested
- [ ] Alert system configured

**1 Day Before**:
- [ ] Final testnet run (24h)
- [ ] All tests passing
- [ ] Logs reviewed
- [ ] Performance verified
- [ ] Emergency stop procedure documented

**Demo Day**:
- [ ] System health verified
- [ ] All balances confirmed ($100 each)
- [ ] Dashboard accessible
- [ ] Monitoring active
- [ ] Communication channel ready

### Starting the Demo

```bash
# 1. Verify configuration
python scripts/verify_config.py

# 2. Reset database (if needed)
python scripts/init_database.py --reset  # ⚠️ Deletes all data!

# 3. Verify health
curl http://localhost:8000/health

# 4. Start system
python scripts/start.py

# 5. Verify first cycle
# Wait 5 minutes and check logs
tail -f logs/app.log | grep "Trading cycle"

# 6. Monitor dashboard
open http://localhost:8000/dashboard/
```

### During the Demo

**Monitoring Schedule**:
- Hour 0: Start demo, verify all LLMs active
- Hour 1: Check first few cycles completed
- Hour 6: Review PnL and positions
- Hour 12: Midpoint check, verify stability
- Hour 18: Check for any errors
- Hour 24: Final results, export data

**What to Monitor**:
- [ ] Trading cycles executing every 5 minutes
- [ ] All 3 LLMs making decisions
- [ ] Positions opening/closing correctly
- [ ] PnL calculations accurate
- [ ] No system errors
- [ ] API rate limits not exceeded
- [ ] Database connections stable

### Emergency Procedures

**Stop Trading Immediately**:
```bash
# Pause scheduler (keeps system running)
curl -X POST http://localhost:8000/scheduler/pause

# Or stop entire system
# Ctrl+C if running in terminal
# OR
sudo systemctl stop crypto-llm-trading  # If using systemd
# OR
docker-compose down  # If using Docker
```

**Close All Positions**:
```bash
# Manual intervention required
# Use Binance web interface to close positions
# Or implement emergency close script
```

---

## Performance Optimization

### Production Optimizations

**1. Database Connection Pooling**:
- Configure Supabase connection limits
- Reuse connections (already implemented)

**2. API Response Caching**:
- Market data cached (60s TTL)
- Account data cached appropriately

**3. Async Operations**:
- All I/O operations async (FastAPI)
- Non-blocking LLM calls

**4. Log Rotation**:
```bash
# Configure logrotate
sudo nano /etc/logrotate.d/crypto-llm-trading

# Add:
/home/ubuntu/crypto-llm-trading/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
```

---

## Troubleshooting

### Common Issues

**Issue**: Trading cycles not executing
```bash
# Check scheduler status
curl http://localhost:8000/scheduler/status

# Check logs
tail -f logs/app.log | grep "scheduler"

# Manually trigger cycle
curl -X POST http://localhost:8000/scheduler/trigger
```

**Issue**: LLM API errors
```bash
# Check API keys
python scripts/verify_config.py

# Check LLM service logs
tail -f logs/llm_decisions.log

# Check rate limits
curl http://localhost:8000/scheduler/stats
```

**Issue**: Database connection errors
```bash
# Verify database
python scripts/init_database.py --verify

# Check Supabase status
# Visit: https://status.supabase.com

# Check logs
grep "database" logs/app.log
```

---

## Post-Demo Analysis

### Data Export

```bash
# Export trades
curl http://localhost:8000/trading/trades?limit=1000 > trades.json

# Export leaderboard
curl http://localhost:8000/trading/leaderboard > leaderboard.json

# Export logs
cp logs/app.log demo_logs/app_$(date +%Y%m%d).log
cp logs/llm_decisions.log demo_logs/decisions_$(date +%Y%m%d).log
```

### Results Analysis

Analyze:
- Total trades per LLM
- Win rate per LLM
- Total PnL per LLM
- Best/worst trades
- Market conditions during demo
- LLM decision patterns

---

**System ready for production deployment and 24-hour demo!** 🚀
