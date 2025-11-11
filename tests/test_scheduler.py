"""
Tests for background scheduler and jobs.

Tests APScheduler integration and trading cycle execution.
"""

import pytest
import time
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from src.background.scheduler import TradingScheduler, initialize_scheduler, cleanup_scheduler
from src.background.jobs import (
    execute_trading_cycle,
    manual_trading_cycle,
    get_job_state,
    reset_job_state,
    health_check_job,
    sync_accounts_job
)
from src.services.trading_service import TradingService
from src.services.account_service import AccountService


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def mock_trading_service():
    """Mock TradingService for testing."""
    mock = Mock(spec=TradingService)

    # Mock execute_trading_cycle
    mock.execute_trading_cycle.return_value = {
        "success": True,
        "cycle_start": "2025-01-10T12:00:00Z",
        "cycle_duration_seconds": 2.5,
        "market_data": {
            "symbols_tracked": 6,
            "gainers": ["ETHUSDT"],
            "losers": []
        },
        "triggers": {
            "stop_loss_count": 0,
            "take_profit_count": 0,
            "results": {}
        },
        "decisions": {
            "LLM-A": {"decision": {"action": "HOLD"}},
            "LLM-B": {"decision": {"action": "HOLD"}},
            "LLM-C": {"decision": {"action": "HOLD"}}
        },
        "accounts": [],
        "summary": {
            "total_equity_usdt": 300.0,
            "total_pnl": 0.0,
            "total_trades": 0
        }
    }

    # Mock accounts service
    mock_accounts = Mock(spec=AccountService)
    mock_accounts.sync_all_accounts.return_value = None
    mock_accounts.get_all_accounts.return_value = {
        "LLM-A": Mock(),
        "LLM-B": Mock(),
        "LLM-C": Mock()
    }
    mock.accounts = mock_accounts

    return mock


@pytest.fixture(autouse=True)
def reset_state():
    """Reset job state before each test."""
    reset_job_state()
    cleanup_scheduler()
    yield
    reset_job_state()
    cleanup_scheduler()


# ============================================================================
# Job Tests
# ============================================================================

class TestTradingJobs:
    """Tests for trading cycle jobs."""

    def test_execute_trading_cycle_success(self, mock_trading_service):
        """Test successful trading cycle execution."""
        result = execute_trading_cycle(mock_trading_service)

        assert result["status"] == "SUCCESS"
        assert "duration_seconds" in result
        assert "result" in result

        # Verify service was called
        mock_trading_service.execute_trading_cycle.assert_called_once()

        # Check job state updated
        state = get_job_state()
        assert state["total_executions"] == 1
        assert state["total_errors"] == 0
        assert state["last_execution"] is not None

    def test_execute_trading_cycle_error(self, mock_trading_service):
        """Test trading cycle execution with error."""
        # Configure mock to raise exception
        mock_trading_service.execute_trading_cycle.side_effect = Exception("Test error")

        result = execute_trading_cycle(mock_trading_service)

        assert result["status"] == "ERROR"
        assert "error" in result
        assert result["error"] == "Test error"

        # Check error state
        state = get_job_state()
        assert state["total_errors"] == 1
        assert state["last_error"] == "Test error"

    def test_execute_trading_cycle_prevents_overlap(self, mock_trading_service):
        """Test that concurrent executions are prevented."""
        # Manually set the is_running flag to simulate a running cycle
        from src.background import jobs
        jobs._job_state["is_running"] = True

        # Try to execute while marked as running
        result = execute_trading_cycle(mock_trading_service)

        # Should be skipped
        assert result["status"] == "SKIPPED"
        assert "running" in result["reason"].lower()

        # Reset state
        jobs._job_state["is_running"] = False

    def test_manual_trading_cycle(self, mock_trading_service):
        """Test manual trading cycle execution."""
        result = manual_trading_cycle(mock_trading_service)

        assert result["status"] == "SUCCESS"
        mock_trading_service.execute_trading_cycle.assert_called_once()

    def test_health_check_job(self):
        """Test health check job."""
        result = health_check_job()

        assert result["status"] == "healthy"
        assert "timestamp" in result
        assert "checks" in result

    def test_sync_accounts_job(self, mock_trading_service):
        """Test account sync job."""
        result = sync_accounts_job(mock_trading_service)

        assert result["status"] == "SUCCESS"
        assert result["accounts_synced"] == 3
        mock_trading_service.accounts.sync_all_accounts.assert_called_once()

    def test_job_state_tracking(self, mock_trading_service):
        """Test job state tracking."""
        # Initial state
        state = get_job_state()
        assert state["total_executions"] == 0
        assert state["total_errors"] == 0

        # Execute successful cycle
        execute_trading_cycle(mock_trading_service)

        state = get_job_state()
        assert state["total_executions"] == 1
        assert state["total_errors"] == 0
        assert state["last_duration"] is not None

        # Execute failed cycle
        mock_trading_service.execute_trading_cycle.side_effect = Exception("Error")
        execute_trading_cycle(mock_trading_service)

        state = get_job_state()
        assert state["total_executions"] == 1  # Doesn't increment on error
        assert state["total_errors"] == 1


# ============================================================================
# Scheduler Tests
# ============================================================================

class TestTradingScheduler:
    """Tests for TradingScheduler."""

    def test_scheduler_initialization(self, mock_trading_service):
        """Test scheduler initialization."""
        scheduler = TradingScheduler(mock_trading_service)

        assert scheduler is not None
        assert scheduler.trading_service == mock_trading_service
        assert scheduler.is_running is False
        assert scheduler.scheduler is None

    def test_scheduler_start_and_stop(self, mock_trading_service):
        """Test starting and stopping scheduler."""
        scheduler = TradingScheduler(mock_trading_service)

        # Start scheduler
        scheduler.start(interval_minutes=1, start_immediately=False)

        assert scheduler.is_running is True
        assert scheduler.scheduler is not None

        # Get status
        status = scheduler.get_status()
        assert status["is_running"] is True
        assert len(status["jobs"]) >= 1  # At least trading cycle job

        # Stop scheduler
        scheduler.stop()

        assert scheduler.is_running is False

    def test_scheduler_manual_trigger(self, mock_trading_service):
        """Test manual cycle trigger."""
        scheduler = TradingScheduler(mock_trading_service)
        scheduler.start(interval_minutes=1, start_immediately=False)

        # Trigger manual cycle
        result = scheduler.trigger_manual_cycle()

        assert result["status"] == "SUCCESS"
        mock_trading_service.execute_trading_cycle.assert_called()

        scheduler.stop()

    def test_scheduler_pause_and_resume(self, mock_trading_service):
        """Test pausing and resuming scheduler."""
        scheduler = TradingScheduler(mock_trading_service)
        scheduler.start(interval_minutes=1, start_immediately=False)

        # Pause
        scheduler.pause()
        # Note: We can't easily test that jobs don't execute when paused

        # Resume
        scheduler.resume()

        scheduler.stop()

    def test_scheduler_get_next_run_time(self, mock_trading_service):
        """Test getting next run time."""
        scheduler = TradingScheduler(mock_trading_service)
        scheduler.start(interval_minutes=1, start_immediately=False)

        next_run = scheduler.get_next_run_time("trading_cycle")

        assert next_run is not None
        assert isinstance(next_run, datetime)

        scheduler.stop()

    def test_scheduler_start_immediately(self, mock_trading_service):
        """Test scheduler with start_immediately=True."""
        scheduler = TradingScheduler(mock_trading_service)

        # Start with immediate execution
        scheduler.start(interval_minutes=1, start_immediately=True)

        # Give it a moment to execute
        time.sleep(0.1)

        # Should have executed once
        assert mock_trading_service.execute_trading_cycle.call_count >= 1

        scheduler.stop()

    def test_initialize_and_cleanup_scheduler(self, mock_trading_service):
        """Test global scheduler initialization and cleanup."""
        # Initialize
        scheduler = initialize_scheduler(mock_trading_service)

        assert scheduler is not None
        assert isinstance(scheduler, TradingScheduler)

        # Cleanup
        cleanup_scheduler()

        # Verify scheduler is cleaned up
        from src.background.scheduler import get_scheduler
        assert get_scheduler() is None

    def test_scheduler_double_start(self, mock_trading_service):
        """Test that starting scheduler twice doesn't cause issues."""
        scheduler = TradingScheduler(mock_trading_service)

        scheduler.start(interval_minutes=1)
        scheduler.start(interval_minutes=1)  # Should log warning

        assert scheduler.is_running is True

        scheduler.stop()


# ============================================================================
# Integration Tests
# ============================================================================

class TestSchedulerIntegration:
    """Integration tests with FastAPI."""

    def test_scheduler_lifecycle_with_api(self, mock_trading_service):
        """Test scheduler lifecycle integrated with API."""
        # Simulate API startup
        scheduler = initialize_scheduler(mock_trading_service)
        scheduler.start(interval_minutes=1, start_immediately=False)

        # Verify running
        assert scheduler.is_running is True

        # Simulate API shutdown
        cleanup_scheduler()

        # Verify stopped
        assert scheduler.is_running is False


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
