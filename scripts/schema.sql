-- ============================================================================
-- Crypto LLM Trading System - Database Schema
-- ============================================================================
-- Supabase PostgreSQL schema for the multi-LLM trading system
-- Run this script in your Supabase SQL Editor to initialize the database
-- ============================================================================

-- ============================================================================
-- 1. LLM ACCOUNTS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS llm_accounts (
    llm_id VARCHAR(20) PRIMARY KEY,
    provider VARCHAR(50) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    balance DECIMAL(20, 8) NOT NULL DEFAULT 100.0,
    margin_used DECIMAL(20, 8) NOT NULL DEFAULT 0.0,
    total_pnl DECIMAL(20, 8) NOT NULL DEFAULT 0.0,
    realized_pnl DECIMAL(20, 8) NOT NULL DEFAULT 0.0,
    unrealized_pnl DECIMAL(20, 8) NOT NULL DEFAULT 0.0,
    total_trades INTEGER NOT NULL DEFAULT 0,
    winning_trades INTEGER NOT NULL DEFAULT 0,
    losing_trades INTEGER NOT NULL DEFAULT 0,
    sharpe_ratio DECIMAL(10, 4) DEFAULT NULL,
    max_drawdown DECIMAL(10, 4) DEFAULT NULL,
    open_positions INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_trading_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    api_calls_this_hour INTEGER NOT NULL DEFAULT 0,
    api_calls_today INTEGER NOT NULL DEFAULT 0,
    last_decision_at TIMESTAMP DEFAULT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_llm_accounts_active ON llm_accounts(is_active, is_trading_enabled);
CREATE INDEX IF NOT EXISTS idx_llm_accounts_balance ON llm_accounts(balance DESC);

-- ============================================================================
-- 2. POSITIONS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS positions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    llm_id VARCHAR(20) NOT NULL REFERENCES llm_accounts(llm_id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL CHECK (side IN ('LONG', 'SHORT')),
    entry_price DECIMAL(20, 8) NOT NULL,
    current_price DECIMAL(20, 8) NOT NULL,
    quantity DECIMAL(20, 8) NOT NULL,
    leverage INTEGER NOT NULL DEFAULT 1,
    margin DECIMAL(20, 8) NOT NULL,
    unrealized_pnl DECIMAL(20, 8) NOT NULL DEFAULT 0.0,
    liquidation_price DECIMAL(20, 8) DEFAULT NULL,
    stop_loss DECIMAL(20, 8) DEFAULT NULL,
    take_profit DECIMAL(20, 8) DEFAULT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'OPEN' CHECK (status IN ('OPEN', 'CLOSED', 'LIQUIDATED')),
    opened_at TIMESTAMP NOT NULL DEFAULT NOW(),
    closed_at TIMESTAMP DEFAULT NULL,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_positions_llm_id ON positions(llm_id);
CREATE INDEX IF NOT EXISTS idx_positions_symbol ON positions(symbol);
CREATE INDEX IF NOT EXISTS idx_positions_status ON positions(status);
CREATE INDEX IF NOT EXISTS idx_positions_open ON positions(llm_id, status) WHERE status = 'OPEN';

-- ============================================================================
-- 3. TRADES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS trades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    llm_id VARCHAR(20) NOT NULL REFERENCES llm_accounts(llm_id) ON DELETE CASCADE,
    position_id UUID REFERENCES positions(id) ON DELETE SET NULL,
    symbol VARCHAR(20) NOT NULL,
    action VARCHAR(10) NOT NULL CHECK (action IN ('BUY', 'SELL', 'CLOSE')),
    side VARCHAR(10) NOT NULL CHECK (side IN ('LONG', 'SHORT')),
    entry_price DECIMAL(20, 8) NOT NULL,
    exit_price DECIMAL(20, 8) DEFAULT NULL,
    quantity DECIMAL(20, 8) NOT NULL,
    leverage INTEGER NOT NULL DEFAULT 1,
    realized_pnl DECIMAL(20, 8) DEFAULT NULL,
    pnl_percentage DECIMAL(10, 4) DEFAULT NULL,
    fees DECIMAL(20, 8) NOT NULL DEFAULT 0.0,
    exit_reason VARCHAR(50) DEFAULT NULL,
    executed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    closed_at TIMESTAMP DEFAULT NULL,
    duration_seconds INTEGER DEFAULT NULL,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_trades_llm_id ON trades(llm_id);
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
CREATE INDEX IF NOT EXISTS idx_trades_executed_at ON trades(executed_at DESC);
CREATE INDEX IF NOT EXISTS idx_trades_position_id ON trades(position_id);

-- ============================================================================
-- 4. ORDERS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    llm_id VARCHAR(20) NOT NULL REFERENCES llm_accounts(llm_id) ON DELETE CASCADE,
    position_id UUID REFERENCES positions(id) ON DELETE SET NULL,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL CHECK (side IN ('BUY', 'SELL')),
    order_type VARCHAR(20) NOT NULL CHECK (order_type IN ('MARKET', 'LIMIT', 'STOP_LOSS', 'TAKE_PROFIT')),
    quantity DECIMAL(20, 8) NOT NULL,
    price DECIMAL(20, 8) DEFAULT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'FILLED', 'CANCELLED', 'REJECTED')),
    filled_quantity DECIMAL(20, 8) NOT NULL DEFAULT 0.0,
    average_price DECIMAL(20, 8) DEFAULT NULL,
    binance_order_id VARCHAR(100) DEFAULT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    filled_at TIMESTAMP DEFAULT NULL,
    cancelled_at TIMESTAMP DEFAULT NULL,
    error_message TEXT DEFAULT NULL,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_orders_llm_id ON orders(llm_id);
CREATE INDEX IF NOT EXISTS idx_orders_symbol ON orders(symbol);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at DESC);

-- ============================================================================
-- 5. MARKET DATA TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS market_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol VARCHAR(20) NOT NULL,
    price DECIMAL(20, 8) NOT NULL,
    bid DECIMAL(20, 8) DEFAULT NULL,
    ask DECIMAL(20, 8) DEFAULT NULL,
    volume_24h DECIMAL(30, 8) DEFAULT NULL,
    price_change_24h DECIMAL(20, 8) DEFAULT NULL,
    price_change_pct_24h DECIMAL(10, 4) DEFAULT NULL,
    high_24h DECIMAL(20, 8) DEFAULT NULL,
    low_24h DECIMAL(20, 8) DEFAULT NULL,
    data_timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb,
    UNIQUE(symbol, data_timestamp)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_market_data_symbol ON market_data(symbol);
CREATE INDEX IF NOT EXISTS idx_market_data_timestamp ON market_data(data_timestamp DESC);

-- ============================================================================
-- 6. REJECTED DECISIONS TABLE (10% sample for analysis)
-- ============================================================================

CREATE TABLE IF NOT EXISTS rejected_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    llm_id VARCHAR(20) NOT NULL REFERENCES llm_accounts(llm_id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    decision VARCHAR(10) NOT NULL,
    reasoning TEXT NOT NULL,
    rejection_reason VARCHAR(100) NOT NULL,
    confidence DECIMAL(5, 2) DEFAULT NULL,
    market_price DECIMAL(20, 8) DEFAULT NULL,
    account_balance DECIMAL(20, 8) DEFAULT NULL,
    open_positions_count INTEGER DEFAULT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_rejected_decisions_llm_id ON rejected_decisions(llm_id);
CREATE INDEX IF NOT EXISTS idx_rejected_decisions_created_at ON rejected_decisions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_rejected_decisions_reason ON rejected_decisions(rejection_reason);

-- ============================================================================
-- 7. LLM API CALLS TABLE (for tracking API usage)
-- ============================================================================

CREATE TABLE IF NOT EXISTS llm_api_calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    llm_id VARCHAR(20) NOT NULL REFERENCES llm_accounts(llm_id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL,
    response_time_ms INTEGER NOT NULL,
    prompt_tokens INTEGER DEFAULT NULL,
    completion_tokens INTEGER DEFAULT NULL,
    total_tokens INTEGER DEFAULT NULL,
    estimated_cost DECIMAL(10, 6) DEFAULT NULL,
    success BOOLEAN NOT NULL DEFAULT TRUE,
    error_message TEXT DEFAULT NULL,
    called_at TIMESTAMP NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_llm_api_calls_llm_id ON llm_api_calls(llm_id);
CREATE INDEX IF NOT EXISTS idx_llm_api_calls_called_at ON llm_api_calls(called_at DESC);
CREATE INDEX IF NOT EXISTS idx_llm_api_calls_provider ON llm_api_calls(provider);

-- ============================================================================
-- VIEWS
-- ============================================================================

-- View: LLM Leaderboard
CREATE OR REPLACE VIEW llm_leaderboard AS
SELECT
    llm_id,
    provider,
    model_name,
    balance,
    total_pnl,
    total_pnl / NULLIF(100.0, 0) * 100 AS roi_percentage,
    total_trades,
    winning_trades,
    losing_trades,
    CASE
        WHEN total_trades > 0 THEN (winning_trades::DECIMAL / total_trades::DECIMAL * 100)
        ELSE 0
    END AS win_rate,
    sharpe_ratio,
    max_drawdown,
    open_positions,
    last_decision_at,
    updated_at
FROM llm_accounts
WHERE is_active = TRUE
ORDER BY balance DESC, total_pnl DESC;

-- View: Active Positions Summary
CREATE OR REPLACE VIEW active_positions_summary AS
SELECT
    p.id,
    p.llm_id,
    a.provider,
    a.model_name,
    p.symbol,
    p.side,
    p.entry_price,
    p.current_price,
    p.quantity,
    p.leverage,
    p.margin,
    p.unrealized_pnl,
    p.liquidation_price,
    p.stop_loss,
    p.take_profit,
    p.opened_at,
    EXTRACT(EPOCH FROM (NOW() - p.opened_at))::INTEGER AS duration_seconds,
    (p.unrealized_pnl / p.margin * 100) AS pnl_percentage
FROM positions p
JOIN llm_accounts a ON p.llm_id = a.llm_id
WHERE p.status = 'OPEN'
ORDER BY p.opened_at DESC;

-- View: LLM Trading Stats
CREATE OR REPLACE VIEW llm_trading_stats AS
SELECT
    a.llm_id,
    a.provider,
    a.model_name,
    a.balance,
    a.total_pnl,
    a.realized_pnl,
    a.unrealized_pnl,
    a.total_trades,
    a.winning_trades,
    a.losing_trades,
    CASE
        WHEN a.total_trades > 0 THEN (a.winning_trades::DECIMAL / a.total_trades::DECIMAL * 100)
        ELSE 0
    END AS win_rate,
    a.sharpe_ratio,
    a.max_drawdown,
    a.open_positions,
    COUNT(DISTINCT p.id) FILTER (WHERE p.status = 'OPEN') AS current_open_positions,
    SUM(p.unrealized_pnl) FILTER (WHERE p.status = 'OPEN') AS total_unrealized_pnl,
    a.api_calls_this_hour,
    a.api_calls_today,
    a.last_decision_at,
    a.updated_at
FROM llm_accounts a
LEFT JOIN positions p ON a.llm_id = p.llm_id
WHERE a.is_active = TRUE
GROUP BY a.llm_id, a.provider, a.model_name, a.balance, a.total_pnl,
         a.realized_pnl, a.unrealized_pnl, a.total_trades, a.winning_trades,
         a.losing_trades, a.sharpe_ratio, a.max_drawdown, a.open_positions,
         a.api_calls_this_hour, a.api_calls_today, a.last_decision_at, a.updated_at
ORDER BY a.balance DESC;

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_llm_accounts_updated_at
    BEFORE UPDATE ON llm_accounts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- INITIAL DATA
-- ============================================================================

-- Insert initial LLM accounts (3 LLMs with $100 each)
INSERT INTO llm_accounts (llm_id, provider, model_name, balance)
VALUES
    ('LLM-A', 'anthropic', 'claude-sonnet-4-20250514', 100.0),
    ('LLM-B', 'deepseek', 'deepseek-reasoner', 100.0),
    ('LLM-C', 'openai', 'gpt-4o', 100.0)
ON CONFLICT (llm_id) DO NOTHING;

-- ============================================================================
-- PERMISSIONS (Optional - adjust based on your Supabase setup)
-- ============================================================================

-- Grant permissions to authenticated users (adjust as needed)
-- ALTER TABLE llm_accounts ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE positions ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE trades ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE market_data ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE rejected_decisions ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE llm_api_calls ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- CLEANUP FUNCTIONS (Optional)
-- ============================================================================

-- Function to clean old market data (keep last 30 days)
CREATE OR REPLACE FUNCTION cleanup_old_market_data()
RETURNS void AS $$
BEGIN
    DELETE FROM market_data
    WHERE data_timestamp < NOW() - INTERVAL '30 days';
END;
$$ LANGUAGE plpgsql;

-- Function to clean old rejected decisions (keep last 90 days)
CREATE OR REPLACE FUNCTION cleanup_old_rejected_decisions()
RETURNS void AS $$
BEGIN
    DELETE FROM rejected_decisions
    WHERE created_at < NOW() - INTERVAL '90 days';
END;
$$ LANGUAGE plpgsql;

-- Function to clean old API call logs (keep last 30 days)
CREATE OR REPLACE FUNCTION cleanup_old_api_calls()
RETURNS void AS $$
BEGIN
    DELETE FROM llm_api_calls
    WHERE called_at < NOW() - INTERVAL '30 days';
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- SCHEMA COMPLETE
-- ============================================================================
-- Tables: 7 (llm_accounts, positions, trades, orders, market_data, rejected_decisions, llm_api_calls)
-- Views: 3 (llm_leaderboard, active_positions_summary, llm_trading_stats)
-- Triggers: 1 (auto-update updated_at)
-- Initial Data: 3 LLM accounts
-- ============================================================================
