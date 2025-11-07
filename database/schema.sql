-- ============================================
-- CRYPTO LLM TRADING SYSTEM - DATABASE SCHEMA
-- ============================================
--
-- Este schema soporta el sistema de trading multi-LLM donde cada
-- LLM tiene su propia cuenta virtual de $100 USDT y compite con los demás.
--
-- Tablas principales:
-- 1. llm_accounts: Cuentas virtuales de cada LLM con su configuración
-- 2. positions: Posiciones abiertas por cada LLM
-- 3. trades: Historial de trades ejecutados
-- 4. orders: Órdenes enviadas a Binance
-- 5. market_data: Caché de datos de mercado
-- 6. rejected_decisions: Sample de decisiones rechazadas (10%)
-- 7. llm_api_calls: Log de llamadas a APIs de LLM para debugging
--
-- ============================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- TABLE: llm_accounts
-- ============================================
-- Cuentas virtuales de cada LLM con balance y configuración

CREATE TABLE IF NOT EXISTS llm_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    llm_id VARCHAR(10) UNIQUE NOT NULL,  -- 'LLM-A', 'LLM-B', 'LLM-C'

    -- LLM Configuration
    provider VARCHAR(20) NOT NULL,  -- 'claude', 'deepseek', 'openai'
    model VARCHAR(50) NOT NULL,  -- 'claude-sonnet-4-20250514', etc.
    temperature DECIMAL(3, 2) NOT NULL,  -- 0.5, 0.7, 0.9
    max_tokens INTEGER DEFAULT 1000,

    -- Virtual Balance (starts at $100 USDT per LLM)
    balance DECIMAL(20, 8) NOT NULL DEFAULT 100.00,
    initial_balance DECIMAL(20, 8) NOT NULL DEFAULT 100.00,

    -- Position Tracking
    margin_used DECIMAL(20, 8) DEFAULT 0.00,
    available_balance DECIMAL(20, 8) GENERATED ALWAYS AS (balance - margin_used) STORED,
    open_positions INTEGER DEFAULT 0,

    -- Performance Metrics
    total_pnl DECIMAL(20, 8) DEFAULT 0.00,
    realized_pnl DECIMAL(20, 8) DEFAULT 0.00,
    unrealized_pnl DECIMAL(20, 8) DEFAULT 0.00,

    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    win_rate DECIMAL(5, 2) GENERATED ALWAYS AS (
        CASE WHEN total_trades > 0
             THEN (winning_trades::DECIMAL / total_trades::DECIMAL) * 100
             ELSE 0
        END
    ) STORED,

    -- Risk Metrics
    max_drawdown DECIMAL(10, 2) DEFAULT 0.00,
    sharpe_ratio DECIMAL(10, 4) DEFAULT 0.00,

    -- Rate Limiting (para no exceder límites de APIs)
    api_calls_today INTEGER DEFAULT 0,
    api_calls_this_hour INTEGER DEFAULT 0,
    last_decision_at TIMESTAMP WITH TIME ZONE,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_trading_enabled BOOLEAN DEFAULT TRUE,
    last_error TEXT,
    error_count INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT llm_id_format CHECK (llm_id ~ '^LLM-[A-C]$'),
    CONSTRAINT balance_positive CHECK (balance >= 0),
    CONSTRAINT margin_valid CHECK (margin_used >= 0 AND margin_used <= balance),
    CONSTRAINT positions_valid CHECK (open_positions >= 0)
);

-- Index for quick lookups
CREATE INDEX idx_llm_accounts_llm_id ON llm_accounts(llm_id);
CREATE INDEX idx_llm_accounts_active ON llm_accounts(is_active, is_trading_enabled);

-- ============================================
-- TABLE: positions
-- ============================================
-- Posiciones abiertas por cada LLM

CREATE TABLE IF NOT EXISTS positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    llm_id VARCHAR(10) NOT NULL REFERENCES llm_accounts(llm_id) ON DELETE CASCADE,

    -- Position Details
    symbol VARCHAR(20) NOT NULL,  -- 'ETHUSDT', 'BNBUSDT', etc.
    side VARCHAR(10) NOT NULL,  -- 'LONG' or 'SHORT'

    -- Entry Info
    entry_price DECIMAL(20, 8) NOT NULL,
    quantity DECIMAL(20, 8) NOT NULL,
    leverage INTEGER NOT NULL DEFAULT 1,

    -- Margin & Value
    margin_used DECIMAL(20, 8) NOT NULL,
    notional_value DECIMAL(20, 8) GENERATED ALWAYS AS (quantity * entry_price) STORED,

    -- Current Status
    current_price DECIMAL(20, 8),
    unrealized_pnl DECIMAL(20, 8) DEFAULT 0.00,
    pnl_percentage DECIMAL(10, 4) DEFAULT 0.00,

    -- Risk Management
    liquidation_price DECIMAL(20, 8) NOT NULL,
    stop_loss DECIMAL(20, 8),
    take_profit DECIMAL(20, 8),

    -- LLM Decision Info
    reasoning TEXT,  -- Por qué el LLM abrió esta posición
    confidence DECIMAL(3, 2),  -- 0.00 - 1.00
    strategy VARCHAR(50),  -- 'momentum', 'mean_reversion', etc.

    -- Binance Order IDs
    entry_order_id VARCHAR(50),
    binance_position_id VARCHAR(50),

    -- Status
    status VARCHAR(20) DEFAULT 'OPEN',  -- 'OPEN', 'CLOSED', 'LIQUIDATED'

    -- Timestamps
    opened_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    closed_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_side CHECK (side IN ('LONG', 'SHORT')),
    CONSTRAINT valid_leverage CHECK (leverage >= 1 AND leverage <= 125),
    CONSTRAINT positive_quantity CHECK (quantity > 0),
    CONSTRAINT positive_entry_price CHECK (entry_price > 0),
    CONSTRAINT valid_status CHECK (status IN ('OPEN', 'CLOSED', 'LIQUIDATED'))
);

-- Indexes for efficient queries
CREATE INDEX idx_positions_llm_id ON positions(llm_id);
CREATE INDEX idx_positions_symbol ON positions(symbol);
CREATE INDEX idx_positions_status ON positions(status);
CREATE INDEX idx_positions_llm_symbol_status ON positions(llm_id, symbol, status);

-- ============================================
-- TABLE: trades
-- ============================================
-- Historial completo de trades ejecutados

CREATE TABLE IF NOT EXISTS trades (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    llm_id VARCHAR(10) NOT NULL REFERENCES llm_accounts(llm_id) ON DELETE CASCADE,
    position_id UUID REFERENCES positions(id) ON DELETE SET NULL,

    -- Trade Details
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,  -- 'BUY' or 'SELL'
    trade_type VARCHAR(20) NOT NULL,  -- 'OPEN', 'CLOSE', 'STOP_LOSS', 'TAKE_PROFIT', 'LIQUIDATION'

    -- Execution Details
    price DECIMAL(20, 8) NOT NULL,
    quantity DECIMAL(20, 8) NOT NULL,
    notional_value DECIMAL(20, 8) GENERATED ALWAYS AS (quantity * price) STORED,

    -- P&L (solo para trades de cierre)
    pnl DECIMAL(20, 8),
    pnl_percentage DECIMAL(10, 4),
    fees DECIMAL(20, 8) NOT NULL,
    net_pnl DECIMAL(20, 8),

    -- LLM Decision Info
    reasoning TEXT NOT NULL,  -- Reasoning del LLM para este trade
    confidence DECIMAL(3, 2),  -- Confianza del LLM (0.00 - 1.00)
    strategy VARCHAR(50),  -- Estrategia utilizada
    llm_response_time_ms INTEGER,  -- Tiempo que tardó el LLM en responder

    -- Binance Order Info
    binance_order_id VARCHAR(50),
    commission DECIMAL(20, 8),
    commission_asset VARCHAR(10),

    -- Status
    status VARCHAR(20) DEFAULT 'EXECUTED',  -- 'PENDING', 'EXECUTED', 'FAILED', 'CANCELLED'
    error_message TEXT,

    -- Timestamps
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_trade_side CHECK (side IN ('BUY', 'SELL')),
    CONSTRAINT valid_trade_type CHECK (trade_type IN ('OPEN', 'CLOSE', 'STOP_LOSS', 'TAKE_PROFIT', 'LIQUIDATION')),
    CONSTRAINT valid_trade_status CHECK (status IN ('PENDING', 'EXECUTED', 'FAILED', 'CANCELLED')),
    CONSTRAINT positive_trade_quantity CHECK (quantity > 0),
    CONSTRAINT positive_trade_price CHECK (price > 0)
);

-- Indexes for performance
CREATE INDEX idx_trades_llm_id ON trades(llm_id);
CREATE INDEX idx_trades_symbol ON trades(symbol);
CREATE INDEX idx_trades_executed_at ON trades(executed_at DESC);
CREATE INDEX idx_trades_llm_symbol_executed ON trades(llm_id, symbol, executed_at DESC);
CREATE INDEX idx_trades_position_id ON trades(position_id);

-- ============================================
-- TABLE: orders
-- ============================================
-- Todas las órdenes enviadas a Binance

CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    llm_id VARCHAR(10) NOT NULL REFERENCES llm_accounts(llm_id) ON DELETE CASCADE,
    position_id UUID REFERENCES positions(id) ON DELETE SET NULL,

    -- Order Details
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,  -- 'BUY' or 'SELL'
    order_type VARCHAR(20) NOT NULL,  -- 'MARKET', 'LIMIT', 'STOP_LOSS', 'TAKE_PROFIT'

    -- Quantity & Price
    quantity DECIMAL(20, 8) NOT NULL,
    price DECIMAL(20, 8),  -- NULL para órdenes MARKET
    stop_price DECIMAL(20, 8),  -- Para STOP_LOSS orders

    -- Binance Response
    binance_order_id VARCHAR(50) UNIQUE,
    client_order_id VARCHAR(50),
    binance_status VARCHAR(20),

    -- Execution
    executed_quantity DECIMAL(20, 8) DEFAULT 0,
    executed_price DECIMAL(20, 8),

    -- Status
    status VARCHAR(20) DEFAULT 'PENDING',  -- 'PENDING', 'SUBMITTED', 'FILLED', 'PARTIALLY_FILLED', 'CANCELLED', 'REJECTED', 'EXPIRED'
    error_message TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    submitted_at TIMESTAMP WITH TIME ZONE,
    filled_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_order_side CHECK (side IN ('BUY', 'SELL')),
    CONSTRAINT valid_order_type CHECK (order_type IN ('MARKET', 'LIMIT', 'STOP_LOSS', 'TAKE_PROFIT', 'STOP_MARKET')),
    CONSTRAINT valid_order_status CHECK (status IN ('PENDING', 'SUBMITTED', 'FILLED', 'PARTIALLY_FILLED', 'CANCELLED', 'REJECTED', 'EXPIRED')),
    CONSTRAINT positive_order_quantity CHECK (quantity > 0)
);

-- Indexes
CREATE INDEX idx_orders_llm_id ON orders(llm_id);
CREATE INDEX idx_orders_symbol ON orders(symbol);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_binance_order_id ON orders(binance_order_id);
CREATE INDEX idx_orders_created_at ON orders(created_at DESC);

-- ============================================
-- TABLE: market_data
-- ============================================
-- Caché de datos de mercado para los símbolos

CREATE TABLE IF NOT EXISTS market_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL,

    -- Current Price Data
    price DECIMAL(20, 8) NOT NULL,
    bid DECIMAL(20, 8),
    ask DECIMAL(20, 8),
    volume_24h DECIMAL(30, 8),

    -- Price Changes
    price_change_24h DECIMAL(20, 8),
    price_change_pct_24h DECIMAL(10, 4),

    -- Technical Indicators (calculados por el sistema)
    rsi_14 DECIMAL(10, 4),
    macd DECIMAL(20, 8),
    macd_signal DECIMAL(20, 8),
    bb_upper DECIMAL(20, 8),
    bb_middle DECIMAL(20, 8),
    bb_lower DECIMAL(20, 8),

    -- Additional Market Info
    funding_rate DECIMAL(10, 8),
    open_interest DECIMAL(30, 8),

    -- Timestamps
    data_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT positive_price CHECK (price > 0)
);

-- Indexes for fast lookups
CREATE INDEX idx_market_data_symbol ON market_data(symbol);
CREATE INDEX idx_market_data_timestamp ON market_data(data_timestamp DESC);
CREATE INDEX idx_market_data_symbol_timestamp ON market_data(symbol, data_timestamp DESC);

-- Unique constraint: One record per symbol per minute
CREATE UNIQUE INDEX idx_market_data_symbol_minute ON market_data(symbol, DATE_TRUNC('minute', data_timestamp));

-- ============================================
-- TABLE: rejected_decisions
-- ============================================
-- Sample del 10% de decisiones rechazadas por validación

CREATE TABLE IF NOT EXISTS rejected_decisions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    llm_id VARCHAR(10) NOT NULL REFERENCES llm_accounts(llm_id) ON DELETE CASCADE,

    -- Decision Details
    symbol VARCHAR(20) NOT NULL,
    action VARCHAR(20) NOT NULL,  -- 'BUY', 'SELL', 'CLOSE', 'HOLD'

    -- LLM Response
    llm_reasoning TEXT NOT NULL,
    llm_confidence DECIMAL(3, 2),
    llm_strategy VARCHAR(50),
    llm_response_time_ms INTEGER,
    raw_llm_response JSONB,  -- Full LLM response for debugging

    -- Rejection Details
    rejection_reason VARCHAR(100) NOT NULL,  -- 'INSUFFICIENT_BALANCE', 'MAX_POSITIONS_REACHED', etc.
    rejection_details JSONB,  -- Additional context
    validator VARCHAR(50),  -- Qué validador rechazó la decisión

    -- Market Context at rejection time
    market_price DECIMAL(20, 8),
    account_balance DECIMAL(20, 8),
    open_positions_count INTEGER,

    -- Timestamps
    rejected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_rejected_action CHECK (action IN ('BUY', 'SELL', 'CLOSE', 'HOLD'))
);

-- Indexes
CREATE INDEX idx_rejected_decisions_llm_id ON rejected_decisions(llm_id);
CREATE INDEX idx_rejected_decisions_symbol ON rejected_decisions(symbol);
CREATE INDEX idx_rejected_decisions_rejected_at ON rejected_decisions(rejected_at DESC);
CREATE INDEX idx_rejected_decisions_rejection_reason ON rejected_decisions(rejection_reason);

-- ============================================
-- TABLE: llm_api_calls
-- ============================================
-- Log de todas las llamadas a APIs de LLM (para debugging y costos)

CREATE TABLE IF NOT EXISTS llm_api_calls (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    llm_id VARCHAR(10) NOT NULL REFERENCES llm_accounts(llm_id) ON DELETE CASCADE,

    -- API Call Details
    provider VARCHAR(20) NOT NULL,  -- 'claude', 'deepseek', 'openai'
    model VARCHAR(50) NOT NULL,

    -- Request
    prompt_tokens INTEGER,
    request_payload JSONB,  -- Full request for debugging

    -- Response
    completion_tokens INTEGER,
    total_tokens INTEGER,
    response_time_ms INTEGER NOT NULL,
    response_payload JSONB,  -- Full response

    -- Cost Estimation (en USD)
    estimated_cost_usd DECIMAL(10, 6),

    -- Status
    status VARCHAR(20) NOT NULL,  -- 'SUCCESS', 'TIMEOUT', 'ERROR', 'RATE_LIMITED'
    error_message TEXT,
    http_status_code INTEGER,

    -- Timestamps
    called_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_api_call_status CHECK (status IN ('SUCCESS', 'TIMEOUT', 'ERROR', 'RATE_LIMITED'))
);

-- Indexes
CREATE INDEX idx_llm_api_calls_llm_id ON llm_api_calls(llm_id);
CREATE INDEX idx_llm_api_calls_called_at ON llm_api_calls(called_at DESC);
CREATE INDEX idx_llm_api_calls_status ON llm_api_calls(status);
CREATE INDEX idx_llm_api_calls_provider ON llm_api_calls(provider);

-- ============================================
-- TRIGGERS
-- ============================================

-- Trigger para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Aplicar trigger a tablas relevantes
CREATE TRIGGER update_llm_accounts_updated_at BEFORE UPDATE ON llm_accounts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_positions_updated_at BEFORE UPDATE ON positions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_market_data_updated_at BEFORE UPDATE ON market_data FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- INITIAL DATA
-- ============================================

-- Insertar las 3 cuentas LLM iniciales
INSERT INTO llm_accounts (llm_id, provider, model, temperature, balance, initial_balance)
VALUES
    ('LLM-A', 'claude', 'claude-sonnet-4-20250514', 0.5, 100.00, 100.00),
    ('LLM-B', 'deepseek', 'deepseek-chat', 0.7, 100.00, 100.00),
    ('LLM-C', 'openai', 'gpt-4o', 0.9, 100.00, 100.00)
ON CONFLICT (llm_id) DO NOTHING;

-- ============================================
-- VIEWS
-- ============================================

-- Vista para leaderboard de LLMs
CREATE OR REPLACE VIEW llm_leaderboard AS
SELECT
    llm_id,
    provider,
    model,
    temperature,
    balance,
    total_pnl,
    ROUND(((balance - initial_balance) / initial_balance * 100)::NUMERIC, 2) as roi_percentage,
    total_trades,
    win_rate,
    open_positions,
    sharpe_ratio,
    max_drawdown,
    is_active,
    is_trading_enabled
FROM llm_accounts
ORDER BY balance DESC;

-- Vista para posiciones activas con P&L actualizado
CREATE OR REPLACE VIEW active_positions_summary AS
SELECT
    p.llm_id,
    p.symbol,
    p.side,
    p.entry_price,
    p.current_price,
    p.quantity,
    p.leverage,
    p.unrealized_pnl,
    p.pnl_percentage,
    p.liquidation_price,
    p.opened_at,
    EXTRACT(EPOCH FROM (NOW() - p.opened_at))/3600 as hours_open
FROM positions p
WHERE p.status = 'OPEN'
ORDER BY p.unrealized_pnl DESC;

-- Vista para estadísticas de trading por LLM
CREATE OR REPLACE VIEW llm_trading_stats AS
SELECT
    a.llm_id,
    a.provider,
    a.total_trades,
    a.winning_trades,
    a.losing_trades,
    a.win_rate,
    a.total_pnl,
    a.realized_pnl,
    a.unrealized_pnl,
    COUNT(p.id) as current_open_positions,
    SUM(p.unrealized_pnl) as total_open_pnl
FROM llm_accounts a
LEFT JOIN positions p ON a.llm_id = p.llm_id AND p.status = 'OPEN'
GROUP BY a.llm_id, a.provider, a.total_trades, a.winning_trades, a.losing_trades,
         a.win_rate, a.total_pnl, a.realized_pnl, a.unrealized_pnl;

-- ============================================
-- COMMENTS
-- ============================================

COMMENT ON TABLE llm_accounts IS 'Cuentas virtuales de cada LLM con balance de $100 USDT';
COMMENT ON TABLE positions IS 'Posiciones abiertas por cada LLM';
COMMENT ON TABLE trades IS 'Historial completo de trades ejecutados con reasoning del LLM';
COMMENT ON TABLE orders IS 'Órdenes enviadas a Binance';
COMMENT ON TABLE market_data IS 'Caché de datos de mercado con indicadores técnicos';
COMMENT ON TABLE rejected_decisions IS 'Sample del 10% de decisiones rechazadas por validación';
COMMENT ON TABLE llm_api_calls IS 'Log de llamadas a APIs de LLM para debugging y tracking de costos';

-- ============================================
-- END OF SCHEMA
-- ============================================
