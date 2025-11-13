-- ============================================================================
-- CLEANUP SCRIPT - DROP ALL EXISTING TABLES
-- ============================================================================
-- Este script elimina TODAS las tablas, vistas, triggers y funciones
-- para empezar desde cero con el schema de Grid Trading
--
-- EJECUTA ESTE SCRIPT PRIMERO, luego ejecuta grid_trading_schema.sql
-- ============================================================================

-- Drop all views first (they depend on tables)
DROP VIEW IF EXISTS llm_leaderboard CASCADE;
DROP VIEW IF EXISTS active_positions_summary CASCADE;
DROP VIEW IF EXISTS llm_trading_stats CASCADE;
DROP VIEW IF EXISTS grid_performance_summary CASCADE;

-- Drop all triggers
DROP TRIGGER IF EXISTS update_llm_accounts_updated_at ON llm_accounts;
DROP TRIGGER IF EXISTS update_grids_updated_at ON grids;

-- Drop all functions
DROP FUNCTION IF EXISTS update_updated_at_column();
DROP FUNCTION IF EXISTS cleanup_old_market_data();
DROP FUNCTION IF EXISTS cleanup_old_rejected_decisions();
DROP FUNCTION IF EXISTS cleanup_old_api_calls();

-- Drop all tables (in reverse dependency order)
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS llm_api_calls CASCADE;
DROP TABLE IF EXISTS rejected_decisions CASCADE;
DROP TABLE IF EXISTS market_data CASCADE;
DROP TABLE IF EXISTS closed_trades CASCADE;
DROP TABLE IF EXISTS trades CASCADE;
DROP TABLE IF EXISTS positions CASCADE;
DROP TABLE IF EXISTS grids CASCADE;
DROP TABLE IF EXISTS llm_decisions CASCADE;
DROP TABLE IF EXISTS llm_accounts CASCADE;

-- ============================================================================
-- CLEANUP COMPLETE
-- ============================================================================
-- Todas las tablas, vistas, triggers y funciones han sido eliminadas.
--
-- SIGUIENTE PASO:
-- Ahora ejecuta el archivo: grid_trading_schema.sql
-- ============================================================================
