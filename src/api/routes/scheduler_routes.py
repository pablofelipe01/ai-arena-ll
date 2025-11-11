"""
Scheduler Routes - Background job control endpoints.

Provides endpoints to:
- Get scheduler status
- Trigger manual trading cycle
- Pause/resume scheduler
- Get job statistics
"""

from typing import Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from src.background.scheduler import get_scheduler
from src.background.jobs import get_job_state
from src.utils.logger import app_logger


router = APIRouter(prefix="/scheduler", tags=["Scheduler"])


# ============================================================================
# Scheduler Status Endpoint
# ============================================================================

@router.get(
    "/status",
    summary="Get scheduler status",
    description="Returns scheduler status, scheduled jobs, and execution statistics."
)
async def get_scheduler_status() -> Dict[str, Any]:
    """
    Get scheduler status.

    Returns:
    - Scheduler running state
    - Scheduled jobs and next run times
    - Job execution statistics
    - Last execution results
    """
    try:
        scheduler = get_scheduler()

        if not scheduler:
            return {
                "status": "NOT_INITIALIZED",
                "is_running": False,
                "message": "Scheduler not initialized",
                "timestamp": datetime.utcnow().isoformat()
            }

        status = scheduler.get_status()

        return {
            "status": "RUNNING" if status["is_running"] else "STOPPED",
            "is_running": status["is_running"],
            "jobs": status["jobs"],
            "execution_stats": status["job_state"],
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        app_logger.error(f"Error getting scheduler status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Manual Cycle Trigger Endpoint
# ============================================================================

@router.post(
    "/trigger",
    summary="Trigger manual trading cycle",
    description="Manually execute a trading cycle outside of the regular schedule."
)
async def trigger_manual_cycle() -> Dict[str, Any]:
    """
    Trigger manual trading cycle.

    This endpoint allows executing a trading cycle on-demand,
    independent of the scheduled 5-minute intervals.

    Returns:
    - Cycle execution results
    - Duration and status
    - Market data summary
    """
    try:
        scheduler = get_scheduler()

        if not scheduler:
            raise HTTPException(
                status_code=503,
                detail="Scheduler not initialized"
            )

        app_logger.info("Manual trading cycle triggered via API")

        result = scheduler.trigger_manual_cycle()

        return {
            "triggered_at": datetime.utcnow().isoformat(),
            "result": result,
            "message": "Manual trading cycle completed"
        }

    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error triggering manual cycle: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Scheduler Control Endpoints
# ============================================================================

@router.post(
    "/pause",
    summary="Pause scheduler",
    description="Pause all scheduled jobs (trading cycles will not execute)."
)
async def pause_scheduler() -> Dict[str, Any]:
    """
    Pause scheduler.

    Pauses all scheduled jobs. Jobs will not execute until resumed.

    Returns:
    - Status confirmation
    """
    try:
        scheduler = get_scheduler()

        if not scheduler:
            raise HTTPException(
                status_code=503,
                detail="Scheduler not initialized"
            )

        if not scheduler.is_running:
            raise HTTPException(
                status_code=400,
                detail="Scheduler is not running"
            )

        scheduler.pause()

        app_logger.info("Scheduler paused via API")

        return {
            "status": "PAUSED",
            "message": "Scheduler paused successfully",
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error pausing scheduler: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/resume",
    summary="Resume scheduler",
    description="Resume all paused scheduled jobs."
)
async def resume_scheduler() -> Dict[str, Any]:
    """
    Resume scheduler.

    Resumes all scheduled jobs after being paused.

    Returns:
    - Status confirmation
    """
    try:
        scheduler = get_scheduler()

        if not scheduler:
            raise HTTPException(
                status_code=503,
                detail="Scheduler not initialized"
            )

        if not scheduler.is_running:
            raise HTTPException(
                status_code=400,
                detail="Scheduler is not running"
            )

        scheduler.resume()

        app_logger.info("Scheduler resumed via API")

        return {
            "status": "RUNNING",
            "message": "Scheduler resumed successfully",
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error resuming scheduler: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Job Statistics Endpoint
# ============================================================================

@router.get(
    "/stats",
    summary="Get job execution statistics",
    description="Returns detailed statistics about job executions."
)
async def get_job_statistics() -> Dict[str, Any]:
    """
    Get job execution statistics.

    Returns:
    - Total executions
    - Error count
    - Last execution time and duration
    - Last error (if any)
    """
    try:
        job_state = get_job_state()

        return {
            "total_executions": job_state["total_executions"],
            "total_errors": job_state["total_errors"],
            "success_rate": (
                (job_state["total_executions"] - job_state["total_errors"]) /
                job_state["total_executions"] * 100
                if job_state["total_executions"] > 0 else 0
            ),
            "last_execution": job_state["last_execution"],
            "last_duration": job_state["last_duration"],
            "last_error": job_state["last_error"],
            "is_currently_running": job_state["is_running"],
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        app_logger.error(f"Error getting job statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Next Run Time Endpoint
# ============================================================================

@router.get(
    "/next-run",
    summary="Get next scheduled run time",
    description="Returns the next scheduled execution time for the trading cycle."
)
async def get_next_run_time() -> Dict[str, Any]:
    """
    Get next scheduled run time.

    Returns:
    - Next run time for trading cycle job
    - Time until next execution
    """
    try:
        scheduler = get_scheduler()

        if not scheduler:
            raise HTTPException(
                status_code=503,
                detail="Scheduler not initialized"
            )

        next_run = scheduler.get_next_run_time("trading_cycle")

        if not next_run:
            return {
                "next_run": None,
                "message": "No scheduled runs",
                "timestamp": datetime.utcnow().isoformat()
            }

        time_until = (next_run - datetime.utcnow()).total_seconds()

        return {
            "next_run": next_run.isoformat(),
            "seconds_until_next_run": time_until,
            "minutes_until_next_run": time_until / 60,
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error getting next run time: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
