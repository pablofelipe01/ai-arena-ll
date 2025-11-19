-- ============================================================================
-- GRID TRADING SYSTEM - DATABASE SCHEMA FOR SUPABASE
-- ============================================================================
-- Este es el schema correcto para el sistema de Grid Trading
-- Ejecuta este script completo en el SQL Editor de Supabase
-- ============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- 1. LLM ACCOUNTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS llm_accounts (
    llm_id VARCHAR(20) PRIMARY KEY,
    provider VARCHAR(50) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    current_balance DECIMAL(20, 8) NOT NULL DEFAULT 200.0,
    initial_balance DECIMAL(20, 8) NOT NULL DEFAULT 200.0,
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

CREATE INDEX IF NOT EXISTS idx_llm_accounts_active ON llm_accounts(is_active, is_trading_enabled);
CREATE INDEX IF NOT EXISTS idx_llm_accounts_balance ON llm_accounts(current_balance DESC);

-- ============================================================================
-- 2. GRIDS TABLE (Grid Trading Configurations)
-- ============================================================================
CREATE TABLE IF NOT EXISTS grids (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    grid_id VARCHAR(100) UNIQUE NOT NULL,
    llm_id VARCHAR(20) NOT NULL REFERENCES llm_accounts(llm_id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',

    -- Grid Configuration
    upper_limit DECIMAL(20, 8) NOT NULL,
    lower_limit DECIMAL(20, 8) NOT NULL,
    grid_levels INTEGER NOT NULL,
    spacing_type VARCHAR(20) NOT NULL,
    leverage INTEGER NOT NULL DEFAULT 1,
    investment_usd DECIMAL(20, 8) NOT NULL,
    stop_loss_pct DECIMAL(10, 4) NOT NULL,

    -- Performance Metrics
    cycles_completed INTEGER NOT NULL DEFAULT 0,
    total_profit_usdt DECIMAL(20, 8) NOT NULL DEFAULT 0.0,
    total_fees_usdt DECIMAL(20, 8) NOT NULL DEFAULT 0.0,

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    stopped_at TIMESTAMP DEFAULT NULL,

    -- Grid State (JSON)
    grid_state JSONB DEFAULT '{}'::jsonb,

    CHECK (status IN ('ACTIVE', 'PAUSED', 'STOPPED')),
    CHECK (spacing_type IN ('arithmetic', 'geometric')),
    CHECK (leverage BETWEEN 1 AND 5),
    CHECK (grid_levels BETWEEN 5 AND 8)
);

CREATE INDEX IF NOT EXISTS idx_grids_llm_id ON grids(llm_id);
CREATE INDEX IF NOT EXISTS idx_grids_symbol ON grids(symbol);
CREATE INDEX IF NOT EXISTS idx_grids_status ON grids(status);
CREATE INDEX IF NOT EXISTS idx_grids_created_at ON grids(created_at DESC);

-- ============================================================================
-- 3. POSITIONS TABLE (Open Positions from Grids)
-- ============================================================================
CREATE TABLE IF NOT EXISTS positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    position_id VARCHAR(100) UNIQUE NOT NULL,
    llm_id VARCHAR(20) NOT NULL REFERENCES llm_accounts(llm_id) ON DELETE CASCADE,
    grid_id VARCHAR(100) REFERENCES grids(grid_id) ON DELETE SET NULL,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,
    entry_price DECIMAL(20, 8) NOT NULL,
    current_price DECIMAL(20, 8) NOT NULL,
    quantity DECIMAL(20, 8) NOT NULL,
    leverage INTEGER NOT NULL DEFAULT 1,
    margin DECIMAL(20, 8) NOT NULL,
    unrealized_pnl DECIMAL(20, 8) NOT NULL DEFAULT 0.0,
    liquidation_price DECIMAL(20, 8) DEFAULT NULL,
    stop_loss DECIMAL(20, 8) DEFAULT NULL,
    take_profit DECIMAL(20, 8) DEFAULT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'OPEN',
    binance_position_id VARCHAR(100) DEFAULT NULL,
    opened_at TIMESTAMP NOT NULL DEFAULT NOW(),
    closed_at TIMESTAMP DEFAULT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,

    CHECK (side IN ('LONG', 'SHORT')),
    CHECK (status IN ('OPEN', 'CLOSED', 'LIQUIDATED'))
);

CREATE INDEX IF NOT EXISTS idx_positions_llm_id ON positions(llm_id);
CREATE INDEX IF NOT EXISTS idx_positions_grid_id ON positions(grid_id);
CREATE INDEX IF NOT EXISTS idx_positions_symbol ON positions(symbol);
CREATE INDEX IF NOT EXISTS idx_positions_status ON positions(status);

-- ============================================================================
-- 4. CLOSED_TRADES TABLE (Trade History)
-- ============================================================================
CREATE TABLE IF NOT EXISTS closed_trades (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    trade_id VARCHAR(100) UNIQUE NOT NULL,
    llm_id VARCHAR(20) NOT NULL REFERENCES llm_accounts(llm_id) ON DELETE CASCADE,
    grid_id VARCHAR(100) REFERENCES grids(grid_id) ON DELETE SET NULL,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,
    entry_price DECIMAL(20, 8) NOT NULL,
    exit_price DECIMAL(20, 8) NOT NULL,
    quantity DECIMAL(20, 8) NOT NULL,
    leverage INTEGER NOT NULL DEFAULT 1,
    realized_pnl DECIMAL(20, 8) NOT NULL,
    pnl_percentage DECIMAL(10, 4) NOT NULL,
    fees DECIMAL(20, 8) NOT NULL DEFAULT 0.0,
    exit_reason VARCHAR(50) DEFAULT NULL,
    opened_at TIMESTAMP NOT NULL,
    closed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    duration_seconds INTEGER DEFAULT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,

    CHECK (side IN ('LONG', 'SHORT'))
);

CREATE INDEX IF NOT EXISTS idx_closed_trades_llm_id ON closed_trades(llm_id);
CREATE INDEX IF NOT EXISTS idx_closed_trades_grid_id ON closed_trades(grid_id);
CREATE INDEX IF NOT EXISTS idx_closed_trades_symbol ON closed_trades(symbol);
CREATE INDEX IF NOT EXISTS idx_closed_trades_closed_at ON closed_trades(closed_at DESC);

-- ============================================================================
-- 5. LLM_DECISIONS TABLE (Log of LLM Trading Decisions)
-- ============================================================================
CREATE TABLE IF NOT EXISTS llm_decisions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    llm_id VARCHAR(20) NOT NULL REFERENCES llm_accounts(llm_id) ON DELETE CASCADE,
    decision_type VARCHAR(50) NOT NULL,
    symbol VARCHAR(20) DEFAULT NULL,
    action VARCHAR(50) NOT NULL,
    reasoning TEXT NOT NULL,
    confidence DECIMAL(5, 2) DEFAULT NULL,

    -- Grid Decision Details
    grid_config JSONB DEFAULT NULL,

    -- Market Context
    market_price DECIMAL(20, 8) DEFAULT NULL,
    account_balance DECIMAL(20, 8) DEFAULT NULL,

    -- Decision Outcome
    executed BOOLEAN NOT NULL DEFAULT FALSE,
    rejection_reason VARCHAR(200) DEFAULT NULL,

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    executed_at TIMESTAMP DEFAULT NULL,

    -- Full Response
    llm_response JSONB DEFAULT '{}'::jsonb,

    CHECK (action IN ('CREATE_GRID', 'STOP_GRID', 'ADJUST_GRID', 'HOLD'))
);

CREATE INDEX IF NOT EXISTS idx_llm_decisions_llm_id ON llm_decisions(llm_id);
CREATE INDEX IF NOT EXISTS idx_llm_decisions_created_at ON llm_decisions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_llm_decisions_executed ON llm_decisions(executed);

-- ============================================================================
-- 6. MARKET DATA TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS market_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
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

CREATE INDEX IF NOT EXISTS idx_market_data_symbol ON market_data(symbol);
CREATE INDEX IF NOT EXISTS idx_market_data_timestamp ON market_data(data_timestamp DESC);

-- ============================================================================
-- 7. ORDERS TABLE (Binance Orders)
-- ============================================================================
CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id VARCHAR(100) UNIQUE NOT NULL,
    llm_id VARCHAR(20) NOT NULL REFERENCES llm_accounts(llm_id) ON DELETE CASCADE,
    grid_id VARCHAR(100) REFERENCES grids(grid_id) ON DELETE SET NULL,
    position_id VARCHAR(100) DEFAULT NULL,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,
    order_type VARCHAR(20) NOT NULL,
    quantity DECIMAL(20, 8) NOT NULL,
    price DECIMAL(20, 8) DEFAULT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    filled_quantity DECIMAL(20, 8) NOT NULL DEFAULT 0.0,
    average_price DECIMAL(20, 8) DEFAULT NULL,
    binance_order_id VARCHAR(100) DEFAULT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    filled_at TIMESTAMP DEFAULT NULL,
    cancelled_at TIMESTAMP DEFAULT NULL,
    error_message TEXT DEFAULT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,

    CHECK (side IN ('BUY', 'SELL')),
    CHECK (order_type IN ('MARKET', 'LIMIT', 'STOP_LOSS', 'TAKE_PROFIT')),
    CHECK (status IN ('PENDING', 'FILLED', 'CANCELLED', 'REJECTED'))
);

CREATE INDEX IF NOT EXISTS idx_orders_llm_id ON orders(llm_id);
CREATE INDEX IF NOT EXISTS idx_orders_grid_id ON orders(grid_id);
CREATE INDEX IF NOT EXISTS idx_orders_symbol ON orders(symbol);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);

-- ============================================================================
-- VIEWS FOR ANALYTICS
-- ============================================================================

-- View: Grid Performance Summary
CREATE OR REPLACE VIEW grid_performance_summary AS
SELECT
    g.grid_id,
    g.llm_id,
    a.provider,
    g.symbol,
    g.status,
    g.cycles_completed,
    g.total_profit_usdt,
    g.total_fees_usdt,
    g.investment_usd,
    CASE
        WHEN g.investment_usd > 0 THEN (g.total_profit_usdt / g.investment_usd * 100)
        ELSE 0
    END AS roi_percentage,
    g.created_at,
    g.updated_at,
    EXTRACT(EPOCH FROM (COALESCE(g.stopped_at, NOW()) - g.created_at))::INTEGER AS duration_seconds
FROM grids g
JOIN llm_accounts a ON g.llm_id = a.llm_id
ORDER BY g.created_at DESC;

-- View: LLM Leaderboard
CREATE OR REPLACE VIEW llm_leaderboard AS
SELECT
    llm_id,
    provider,
    model_name,
    current_balance,
    initial_balance,
    total_pnl,
    (total_pnl / initial_balance * 100) AS roi_percentage,
    total_trades,
    winning_trades,
    losing_trades,
    CASE
        WHEN total_trades > 0 THEN (winning_trades::DECIMAL / total_trades::DECIMAL * 100)
        ELSE 0
    END AS win_rate,
    open_positions,
    last_decision_at,
    updated_at
FROM llm_accounts
WHERE is_active = TRUE
ORDER BY current_balance DESC, total_pnl DESC;

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

CREATE TRIGGER update_grids_updated_at
    BEFORE UPDATE ON grids
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- INITIAL DATA
-- ============================================================================

-- Insert initial LLM accounts (3 LLMs with $200 each for mainnet)
INSERT INTO llm_accounts (llm_id, provider, model_name, current_balance, initial_balance)
VALUES
    ('LLM-A', 'anthropic', 'claude-sonnet-4-20250514', 200.0, 200.0),
    ('LLM-B', 'deepseek', 'deepseek-chat', 200.0, 200.0),
    ('LLM-C', 'openai', 'gpt-4o', 200.0, 200.0)
ON CONFLICT (llm_id) DO UPDATE SET
    current_balance = EXCLUDED.current_balance,
    initial_balance = EXCLUDED.initial_balance,
    total_pnl = 0,
    total_trades = 0,
    winning_trades = 0,
    losing_trades = 0,
    margin_used = 0,
    open_positions = 0;

-- ============================================================================
-- SCHEMA COMPLETE
-- ============================================================================
-- Grid Trading System Ready!
--
-- Tables Created:
-- 1. llm_accounts - LLM configurations and balances
-- 2. grids - Grid trading configurations and performance
-- 3. positions - Open positions from grid trading
-- 4. closed_trades - Historical trades
-- 5. llm_decisions - Log of all LLM decisions
-- 6. market_data - Market price data cache
-- 7. orders - Binance order tracking
--
-- Views Created:
-- 1. grid_performance_summary - Grid performance metrics
-- 2. llm_leaderboard - LLM rankings
--
-- Ready for Mainnet Trading!
-- ============================================================================
