-- ============================================================================
-- FIX SCHEMA - Actualizar tablas para que coincidan con el código
-- ============================================================================

-- 1. Agregar columna 'balance' como alias de 'current_balance' en llm_accounts
-- (para mantener compatibilidad con el código que usa 'balance')
ALTER TABLE llm_accounts ADD COLUMN IF NOT EXISTS balance DECIMAL(20, 8);
UPDATE llm_accounts SET balance = current_balance WHERE balance IS NULL;

-- 2. Recrear tabla llm_decisions con las columnas correctas
DROP TABLE IF EXISTS llm_decisions CASCADE;

CREATE TABLE llm_decisions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    llm_id VARCHAR(20) NOT NULL REFERENCES llm_accounts(llm_id) ON DELETE CASCADE,
    action VARCHAR(50) NOT NULL,
    symbol VARCHAR(20) DEFAULT NULL,

    -- Trading parameters
    quantity_usd DECIMAL(20, 8) DEFAULT NULL,
    leverage INTEGER DEFAULT NULL,
    stop_loss_pct DECIMAL(10, 4) DEFAULT NULL,
    take_profit_pct DECIMAL(10, 4) DEFAULT NULL,

    -- Decision details
    reasoning TEXT NOT NULL,
    confidence DECIMAL(5, 2) DEFAULT NULL,
    strategy VARCHAR(50) DEFAULT NULL,

    -- Execution result
    execution_status VARCHAR(50) DEFAULT NULL,
    execution_message TEXT DEFAULT NULL,

    -- API metrics
    tokens_used INTEGER DEFAULT NULL,
    cost_usd DECIMAL(10, 6) DEFAULT NULL,
    response_time_ms INTEGER DEFAULT NULL,

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_llm_decisions_llm_id ON llm_decisions(llm_id);
CREATE INDEX IF NOT EXISTS idx_llm_decisions_created_at ON llm_decisions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_llm_decisions_action ON llm_decisions(action);

-- 3. Agregar método insert_market_data necesario
-- (La tabla market_data ya existe, solo aseguramos que esté bien)

-- ============================================================================
-- FIX COMPLETADO
-- ============================================================================
