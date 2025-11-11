"""
Job Scheduler - APScheduler configuration and management.

Manages scheduled trading cycles and background jobs.
"""

from typing import Optional, Dict, Any
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from src.services.trading_service import TradingService
from src.background.jobs import (
    execute_trading_cycle,
    health_check_job,
    sync_accounts_job,
    get_job_state
)
from src.utils.logger import app_logger


class TradingScheduler:
    """
    Background job scheduler for trading cycles.

    Uses APScheduler to execute trading cycles every 5 minutes
    and manage other periodic tasks.
    """

    def __init__(self, trading_service: TradingService):
        """
        Initialize scheduler.

        Args:
            trading_service: Initialized TradingService instance
        """
        self.trading_service = trading_service
        self.scheduler: Optional[BackgroundScheduler] = None
        self.is_running = False

        app_logger.info("TradingScheduler initialized")

    def start(
        self,
        interval_minutes: int = 5,
        start_immediately: bool = False
    ) -> None:
        """
        Start the scheduler.

        Args:
            interval_minutes: Trading cycle interval (default: 5 minutes)
            start_immediately: Run first cycle immediately (default: False)
        """
        if self.is_running:
            app_logger.warning("Scheduler already running")
            return

        app_logger.info("=" * 60)
        app_logger.info("Starting background job scheduler...")
        app_logger.info("=" * 60)

        # Create scheduler
        self.scheduler = BackgroundScheduler(
            timezone="UTC",
            job_defaults={
                "coalesce": True,  # Combine missed executions
                "max_instances": 1,  # Only one instance of each job
                "misfire_grace_time": 30  # Allow 30s grace period
            }
        )

        # Add event listeners
        self.scheduler.add_listener(
            self._job_executed_listener,
            EVENT_JOB_EXECUTED
        )
        self.scheduler.add_listener(
            self._job_error_listener,
            EVENT_JOB_ERROR
        )

        # Schedule trading cycle job
        self.scheduler.add_job(
            func=execute_trading_cycle,
            trigger=IntervalTrigger(minutes=interval_minutes),
            args=[self.trading_service],
            id="trading_cycle",
            name="Trading Cycle",
            replace_existing=True
        )

        app_logger.info(f"Trading cycle scheduled every {interval_minutes} minutes")

        # Optional: Schedule health check job (every 15 minutes)
        self.scheduler.add_job(
            func=health_check_job,
            trigger=IntervalTrigger(minutes=15),
            id="health_check",
            name="Health Check",
            replace_existing=True
        )

        app_logger.info("Health check scheduled every 15 minutes")

        # Optional: Schedule account sync job (every 10 minutes)
        self.scheduler.add_job(
            func=sync_accounts_job,
            trigger=IntervalTrigger(minutes=10),
            args=[self.trading_service],
            id="account_sync",
            name="Account Sync",
            replace_existing=True
        )

        app_logger.info("Account sync scheduled every 10 minutes")

        # Start scheduler
        self.scheduler.start()
        self.is_running = True

        app_logger.info("=" * 60)
        app_logger.info("Background scheduler started successfully")
        app_logger.info("=" * 60)

        # Print scheduled jobs
        self._print_scheduled_jobs()

        # Execute first cycle immediately if requested
        if start_immediately:
            app_logger.info("Executing first trading cycle immediately...")
            self.trigger_manual_cycle()

    def stop(self) -> None:
        """Stop the scheduler."""
        if not self.is_running:
            app_logger.warning("Scheduler not running")
            return

        app_logger.info("Stopping background scheduler...")

        if self.scheduler:
            self.scheduler.shutdown(wait=True)

        self.is_running = False
        app_logger.info("Background scheduler stopped")

    def pause(self) -> None:
        """Pause all scheduled jobs."""
        if not self.is_running:
            app_logger.warning("Scheduler not running")
            return

        if self.scheduler:
            self.scheduler.pause()

        app_logger.info("Background scheduler paused")

    def resume(self) -> None:
        """Resume all scheduled jobs."""
        if not self.is_running:
            app_logger.warning("Scheduler not running")
            return

        if self.scheduler:
            self.scheduler.resume()

        app_logger.info("Background scheduler resumed")

    def trigger_manual_cycle(self) -> Dict[str, Any]:
        """
        Trigger trading cycle manually (outside of schedule).

        Returns:
            Dict with execution results
        """
        app_logger.info("Triggering manual trading cycle...")

        result = execute_trading_cycle(self.trading_service)

        app_logger.info(f"Manual cycle completed: {result.get('status')}")

        return result

    def get_status(self) -> Dict[str, Any]:
        """
        Get scheduler status.

        Returns:
            Dict with scheduler state and job information
        """
        jobs_info = []

        if self.scheduler:
            for job in self.scheduler.get_jobs():
                jobs_info.append({
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                    "trigger": str(job.trigger)
                })

        return {
            "is_running": self.is_running,
            "jobs": jobs_info,
            "job_state": get_job_state(),
            "timestamp": datetime.utcnow().isoformat()
        }

    def get_next_run_time(self, job_id: str = "trading_cycle") -> Optional[datetime]:
        """
        Get next scheduled run time for a job.

        Args:
            job_id: Job identifier (default: "trading_cycle")

        Returns:
            Next run time or None if job not found
        """
        if not self.scheduler:
            return None

        job = self.scheduler.get_job(job_id)
        if job:
            return job.next_run_time

        return None

    def _job_executed_listener(self, event) -> None:
        """
        Event listener for successful job execution.

        Args:
            event: APScheduler job execution event
        """
        app_logger.info(
            f"Job '{event.job_id}' executed successfully at {datetime.utcnow()}"
        )

    def _job_error_listener(self, event) -> None:
        """
        Event listener for job execution errors.

        Args:
            event: APScheduler job error event
        """
        app_logger.error(
            f"Job '{event.job_id}' failed: {event.exception}",
            exc_info=True
        )

    def _print_scheduled_jobs(self) -> None:
        """Print all scheduled jobs (for debugging)."""
        if not self.scheduler:
            return

        app_logger.info("Scheduled jobs:")
        for job in self.scheduler.get_jobs():
            next_run = job.next_run_time.isoformat() if job.next_run_time else "N/A"
            app_logger.info(f"  - {job.name} ({job.id}): Next run at {next_run}")

    def __repr__(self) -> str:
        """String representation."""
        return f"<TradingScheduler running={self.is_running}>"


# Global scheduler instance
_scheduler_instance: Optional[TradingScheduler] = None


def get_scheduler() -> Optional[TradingScheduler]:
    """
    Get global scheduler instance.

    Returns:
        TradingScheduler instance or None if not initialized
    """
    return _scheduler_instance


def initialize_scheduler(trading_service: TradingService) -> TradingScheduler:
    """
    Initialize and return global scheduler instance.

    Args:
        trading_service: Initialized TradingService instance

    Returns:
        TradingScheduler instance
    """
    global _scheduler_instance

    if _scheduler_instance is None:
        _scheduler_instance = TradingScheduler(trading_service)

    return _scheduler_instance


def cleanup_scheduler() -> None:
    """Cleanup global scheduler instance."""
    global _scheduler_instance

    if _scheduler_instance and _scheduler_instance.is_running:
        _scheduler_instance.stop()

    _scheduler_instance = None
