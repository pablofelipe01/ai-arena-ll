"""
Background Jobs - Trading cycle execution and management.

Defines jobs to be executed by APScheduler.
"""

from typing import Dict, Any
from datetime import datetime
from decimal import Decimal

from src.services.trading_service import TradingService
from src.utils.logger import app_logger


# Global job state tracking
_job_state = {
    "is_running": False,
    "last_execution": None,
    "last_duration": None,
    "last_result": None,
    "total_executions": 0,
    "total_errors": 0,
    "last_error": None
}


def get_job_state() -> Dict[str, Any]:
    """
    Get current job execution state.

    Returns:
        Dict with job statistics and status
    """
    return {
        **_job_state,
        "last_execution": _job_state["last_execution"].isoformat() if _job_state["last_execution"] else None
    }


def reset_job_state() -> None:
    """Reset job state counters (for testing)."""
    global _job_state
    _job_state = {
        "is_running": False,
        "last_execution": None,
        "last_duration": None,
        "last_result": None,
        "total_executions": 0,
        "total_errors": 0,
        "last_error": None
    }


def execute_trading_cycle(trading_service: TradingService) -> Dict[str, Any]:
    """
    Execute one complete trading cycle.

    This job is scheduled to run every 5 minutes by APScheduler.

    Workflow:
    1. Check if a cycle is already running (prevent overlap)
    2. Execute trading cycle via TradingService
    3. Update job state with results
    4. Handle errors gracefully

    Args:
        trading_service: Initialized TradingService instance

    Returns:
        Dict with cycle execution results
    """
    global _job_state

    # Prevent concurrent executions
    if _job_state["is_running"]:
        app_logger.warning("Trading cycle already running, skipping this execution")
        return {
            "status": "SKIPPED",
            "reason": "Previous cycle still running",
            "timestamp": datetime.utcnow().isoformat()
        }

    # Mark as running
    _job_state["is_running"] = True
    _job_state["last_execution"] = datetime.utcnow()

    app_logger.info("=" * 80)
    app_logger.info("SCHEDULED TRADING CYCLE STARTING")
    app_logger.info("=" * 80)

    try:
        # Execute trading cycle
        start_time = datetime.utcnow()
        result = trading_service.execute_trading_cycle()
        duration = (datetime.utcnow() - start_time).total_seconds()

        # Update state
        _job_state["last_duration"] = duration
        _job_state["last_result"] = result
        _job_state["total_executions"] += 1

        app_logger.info("=" * 80)
        app_logger.info(f"TRADING CYCLE COMPLETED (Duration: {duration:.2f}s)")
        app_logger.info("=" * 80)

        # Log summary
        if result.get("success"):
            app_logger.info(f"Market data: {result['market_data']['symbols_tracked']} symbols")
            app_logger.info(f"Decisions made: {len(result['decisions'])}")
            app_logger.info(f"Accounts tracked: {len(result['accounts'])}")
            app_logger.info(f"Total equity: ${result['summary']['total_equity_usdt']:.2f}")
            app_logger.info(f"Total PnL: ${result['summary']['total_pnl']:.2f}")

        return {
            "status": "SUCCESS",
            "duration_seconds": duration,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        # Update error state
        _job_state["total_errors"] += 1
        _job_state["last_error"] = str(e)

        app_logger.error("=" * 80)
        app_logger.error(f"TRADING CYCLE FAILED: {e}")
        app_logger.error("=" * 80)
        app_logger.error("Error details:", exc_info=True)

        return {
            "status": "ERROR",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

    finally:
        # Always mark as not running
        _job_state["is_running"] = False


def manual_trading_cycle(trading_service: TradingService) -> Dict[str, Any]:
    """
    Execute trading cycle manually (triggered via API endpoint).

    Same as execute_trading_cycle but for manual/on-demand execution.

    Args:
        trading_service: Initialized TradingService instance

    Returns:
        Dict with cycle execution results
    """
    app_logger.info("Manual trading cycle triggered")
    return execute_trading_cycle(trading_service)


# Additional utility jobs (optional for future use)

def health_check_job() -> Dict[str, Any]:
    """
    Periodic health check job.

    Can be used to verify system health, check API connectivity,
    validate database connection, etc.

    Returns:
        Dict with health check results
    """
    app_logger.info("Running health check job")

    try:
        # Basic health checks
        checks = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "healthy",
            "checks": {
                "job_scheduler": "ok",
                "last_cycle": "ok" if _job_state["last_execution"] else "no_executions"
            }
        }

        return checks

    except Exception as e:
        app_logger.error(f"Health check failed: {e}", exc_info=True)
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "unhealthy",
            "error": str(e)
        }


def sync_accounts_job(trading_service: TradingService) -> Dict[str, Any]:
    """
    Periodic account sync to database.

    Ensures all account states are persisted to Supabase.

    Args:
        trading_service: Initialized TradingService instance

    Returns:
        Dict with sync results
    """
    app_logger.info("Running account sync job")

    try:
        # Sync all accounts to database
        trading_service.accounts.sync_all_accounts()

        return {
            "status": "SUCCESS",
            "timestamp": datetime.utcnow().isoformat(),
            "accounts_synced": len(trading_service.accounts.get_all_accounts())
        }

    except Exception as e:
        app_logger.error(f"Account sync failed: {e}", exc_info=True)
        return {
            "status": "ERROR",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
