"""
Trading Routes - Account, position, trade, and leaderboard endpoints.

All endpoints are GET-only (read-only).
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from src.services.trading_service import TradingService
from src.services.account_service import AccountService
from src.api.dependencies import (
    get_trading_service_dependency,
    get_account_service_dependency
)
from src.api.models.responses import (
    AccountResponse,
    AccountsResponse,
    PositionResponse,
    PositionsResponse,
    TradeResponse,
    TradesResponse,
    LeaderboardEntry,
    LeaderboardResponse,
    TradingStatusResponse,
    ErrorResponse
)
from src.utils.logger import app_logger


router = APIRouter(prefix="/trading", tags=["Trading"])


# ============================================================================
# Status Endpoint
# ============================================================================

@router.get(
    "/status",
    response_model=TradingStatusResponse,
    summary="Get trading system status",
    description="Returns current trading system status including accounts, positions, and statistics."
)
async def get_trading_status(
    service: TradingService = Depends(get_trading_service_dependency)
) -> TradingStatusResponse:
    """
    Get trading system status.

    Returns:
    - LLM count and symbols tracked
    - Total open positions and equity
    - Total PnL across all LLMs
    - Account summaries
    """
    try:
        status = service.get_trading_status()

        # Calculate totals
        total_positions = sum(
            len(positions) for positions in status["open_positions"].values()
        )

        return TradingStatusResponse(
            timestamp=datetime.fromisoformat(status["timestamp"]),
            llm_count=status["llm_count"],
            symbols_tracked=status["symbols_tracked"],
            total_open_positions=total_positions,
            total_equity=status["summary"]["total_equity_usdt"],
            total_pnl=status["summary"]["total_pnl"],
            cycle_status="idle",  # Will be "running" during cycle execution
            last_cycle_duration=None,  # Will be populated by background job
            accounts_summary=status["accounts"]
        )

    except Exception as e:
        app_logger.error(f"Error getting trading status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Account Endpoints
# ============================================================================

@router.get(
    "/accounts",
    response_model=AccountsResponse,
    summary="Get all LLM accounts",
    description="Returns all 3 LLM trading accounts with balances, positions, and statistics."
)
async def get_all_accounts(
    service: AccountService = Depends(get_account_service_dependency)
) -> AccountsResponse:
    """
    Get all LLM accounts.

    Returns:
    - All 3 LLM accounts (LLM-A, LLM-B, LLM-C)
    - Balance, equity, PnL for each
    - Open positions for each account
    - Aggregated statistics
    """
    try:
        all_accounts = service.get_all_accounts()
        summary = service.get_summary()

        accounts_list = []
        for llm_id, account in all_accounts.items():
            # Get open positions
            positions = [
                PositionResponse(
                    position_id=pos.position_id,
                    symbol=pos.symbol,
                    side=pos.side,
                    entry_price=float(pos.entry_price),
                    quantity=float(pos.quantity),
                    leverage=pos.leverage,
                    margin_used=float(pos.margin_used),
                    unrealized_pnl_usd=float(pos.unrealized_pnl_usd),
                    unrealized_pnl_pct=float(pos.unrealized_pnl_pct),
                    roi_pct=float(pos.roi_pct),
                    stop_loss_price=float(pos.stop_loss_price) if pos.stop_loss_price else None,
                    take_profit_price=float(pos.take_profit_price) if pos.take_profit_price else None,
                    liquidation_price=float(pos.liquidation_price),
                    opened_at=pos.opened_at
                )
                for pos in account.open_positions.values()
            ]

            accounts_list.append(AccountResponse(
                llm_id=llm_id,
                balance_usdt=float(account.balance_usdt),
                margin_used=float(account.margin_used),
                unrealized_pnl=float(account.unrealized_pnl),
                equity_usdt=float(account.equity_usdt),
                total_trades=account.total_trades,
                winning_trades=account.winning_trades,
                losing_trades=account.losing_trades,
                win_rate=float(account.win_rate),
                total_realized_pnl=float(account.total_realized_pnl),
                total_pnl=float(account.total_pnl),
                total_pnl_pct=float(account.total_pnl_pct),
                open_positions_count=len(account.open_positions),
                open_positions=positions
            ))

        return AccountsResponse(
            accounts=accounts_list,
            total_equity=summary["total_equity_usdt"],
            total_pnl=summary["total_pnl"],
            total_trades=summary["total_trades"],
            timestamp=datetime.utcnow()
        )

    except Exception as e:
        app_logger.error(f"Error getting accounts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/accounts/{llm_id}",
    response_model=AccountResponse,
    summary="Get specific LLM account",
    description="Returns details for a specific LLM account (LLM-A, LLM-B, or LLM-C)."
)
async def get_account(
    llm_id: str,
    service: AccountService = Depends(get_account_service_dependency)
) -> AccountResponse:
    """
    Get specific LLM account.

    Parameters:
    - llm_id: LLM identifier (LLM-A, LLM-B, or LLM-C)

    Returns:
    - Account balance and equity
    - Open positions
    - Trading statistics
    """
    try:
        account = service.get_account(llm_id)

        # Get open positions
        positions = [
            PositionResponse(
                position_id=pos.position_id,
                symbol=pos.symbol,
                side=pos.side,
                entry_price=float(pos.entry_price),
                quantity=float(pos.quantity),
                leverage=pos.leverage,
                margin_used=float(pos.margin_used),
                unrealized_pnl_usd=float(pos.unrealized_pnl_usd),
                unrealized_pnl_pct=float(pos.unrealized_pnl_pct),
                roi_pct=float(pos.roi_pct),
                stop_loss_price=float(pos.stop_loss_price) if pos.stop_loss_price else None,
                take_profit_price=float(pos.take_profit_price) if pos.take_profit_price else None,
                liquidation_price=float(pos.liquidation_price),
                opened_at=pos.opened_at
            )
            for pos in account.open_positions.values()
        ]

        return AccountResponse(
            llm_id=llm_id,
            balance_usdt=float(account.balance_usdt),
            margin_used=float(account.margin_used),
            unrealized_pnl=float(account.unrealized_pnl),
            equity_usdt=float(account.equity_usdt),
            total_trades=account.total_trades,
            winning_trades=account.winning_trades,
            losing_trades=account.losing_trades,
            win_rate=float(account.win_rate),
            total_realized_pnl=float(account.total_realized_pnl),
            total_pnl=float(account.total_pnl),
            total_pnl_pct=float(account.total_pnl_pct),
            open_positions_count=len(account.open_positions),
            open_positions=positions
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        app_logger.error(f"Error getting account {llm_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Position Endpoints
# ============================================================================

@router.get(
    "/positions",
    response_model=PositionsResponse,
    summary="Get all open positions",
    description="Returns all open positions across all LLMs."
)
async def get_all_positions(
    service: AccountService = Depends(get_account_service_dependency)
) -> PositionsResponse:
    """
    Get all open positions.

    Returns:
    - Open positions for each LLM
    - Total margin used
    - Total unrealized PnL
    """
    try:
        all_positions_dict = service.get_all_open_positions()

        # Convert to response format
        positions_response = {}
        total_margin = 0.0
        total_unrealized_pnl = 0.0
        total_count = 0

        for llm_id, positions_list in all_positions_dict.items():
            positions_response[llm_id] = [
                PositionResponse(
                    position_id=pos["position_id"],
                    symbol=pos["symbol"],
                    side=pos["side"],
                    entry_price=pos["entry_price"],
                    quantity=pos["quantity"],
                    leverage=pos["leverage"],
                    margin_used=pos["margin_used"],
                    unrealized_pnl_usd=pos["unrealized_pnl_usd"],
                    unrealized_pnl_pct=pos["unrealized_pnl_pct"],
                    roi_pct=pos["roi_pct"],
                    stop_loss_price=pos.get("stop_loss_price"),
                    take_profit_price=pos.get("take_profit_price"),
                    liquidation_price=pos["liquidation_price"],
                    opened_at=datetime.fromisoformat(pos["opened_at"])
                )
                for pos in positions_list
            ]

            # Aggregate totals
            for pos in positions_list:
                total_margin += pos["margin_used"]
                total_unrealized_pnl += pos["unrealized_pnl_usd"]
                total_count += 1

        return PositionsResponse(
            positions=positions_response,
            total_count=total_count,
            total_margin_used=total_margin,
            total_unrealized_pnl=total_unrealized_pnl,
            timestamp=datetime.utcnow()
        )

    except Exception as e:
        app_logger.error(f"Error getting positions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/positions/{llm_id}",
    response_model=List[PositionResponse],
    summary="Get positions for specific LLM",
    description="Returns open positions for a specific LLM account."
)
async def get_positions_by_llm(
    llm_id: str,
    service: AccountService = Depends(get_account_service_dependency)
) -> List[PositionResponse]:
    """
    Get positions for specific LLM.

    Parameters:
    - llm_id: LLM identifier (LLM-A, LLM-B, or LLM-C)

    Returns:
    - List of open positions for the LLM
    """
    try:
        account = service.get_account(llm_id)

        positions = [
            PositionResponse(
                position_id=pos.position_id,
                symbol=pos.symbol,
                side=pos.side,
                entry_price=float(pos.entry_price),
                quantity=float(pos.quantity),
                leverage=pos.leverage,
                margin_used=float(pos.margin_used),
                unrealized_pnl_usd=float(pos.unrealized_pnl_usd),
                unrealized_pnl_pct=float(pos.unrealized_pnl_pct),
                roi_pct=float(pos.roi_pct),
                stop_loss_price=float(pos.stop_loss_price) if pos.stop_loss_price else None,
                take_profit_price=float(pos.take_profit_price) if pos.take_profit_price else None,
                liquidation_price=float(pos.liquidation_price),
                opened_at=pos.opened_at
            )
            for pos in account.open_positions.values()
        ]

        return positions

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        app_logger.error(f"Error getting positions for {llm_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Trade History Endpoints
# ============================================================================

@router.get(
    "/trades",
    response_model=TradesResponse,
    summary="Get trade history",
    description="Returns recent closed trades across all LLMs."
)
async def get_trades(
    limit: int = Query(default=10, ge=1, le=100, description="Number of trades to return"),
    service: AccountService = Depends(get_account_service_dependency)
) -> TradesResponse:
    """
    Get recent trades.

    Parameters:
    - limit: Number of trades to return (1-100, default 10)

    Returns:
    - List of recent closed trades
    - Total trade count
    """
    try:
        trades_list = service.get_recent_trades(llm_id=None, limit=limit)

        trades = [
            TradeResponse(
                trade_id=trade["trade_id"],
                symbol=trade["symbol"],
                side=trade["side"],
                entry_price=trade["entry_price"],
                exit_price=trade["exit_price"],
                quantity=trade["quantity"],
                leverage=trade["leverage"],
                pnl_usd=trade["pnl_usd"],
                pnl_pct=trade["pnl_pct"],
                exit_reason=trade["exit_reason"],
                opened_at=datetime.fromisoformat(trade["opened_at"]),
                closed_at=datetime.fromisoformat(trade["closed_at"]),
                duration_minutes=trade["duration_minutes"]
            )
            for trade in trades_list
        ]

        return TradesResponse(
            trades=trades,
            total_count=len(trades),
            llm_id=None,
            timestamp=datetime.utcnow()
        )

    except Exception as e:
        app_logger.error(f"Error getting trades: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/trades/{llm_id}",
    response_model=TradesResponse,
    summary="Get trades for specific LLM",
    description="Returns recent closed trades for a specific LLM account."
)
async def get_trades_by_llm(
    llm_id: str,
    limit: int = Query(default=10, ge=1, le=100, description="Number of trades to return"),
    service: AccountService = Depends(get_account_service_dependency)
) -> TradesResponse:
    """
    Get trades for specific LLM.

    Parameters:
    - llm_id: LLM identifier (LLM-A, LLM-B, or LLM-C)
    - limit: Number of trades to return (1-100, default 10)

    Returns:
    - List of recent trades for the LLM
    """
    try:
        trades_list = service.get_recent_trades(llm_id=llm_id, limit=limit)

        trades = [
            TradeResponse(
                trade_id=trade["trade_id"],
                symbol=trade["symbol"],
                side=trade["side"],
                entry_price=trade["entry_price"],
                exit_price=trade["exit_price"],
                quantity=trade["quantity"],
                leverage=trade["leverage"],
                pnl_usd=trade["pnl_usd"],
                pnl_pct=trade["pnl_pct"],
                exit_reason=trade["exit_reason"],
                opened_at=datetime.fromisoformat(trade["opened_at"]),
                closed_at=datetime.fromisoformat(trade["closed_at"]),
                duration_minutes=trade["duration_minutes"]
            )
            for trade in trades_list
        ]

        return TradesResponse(
            trades=trades,
            total_count=len(trades),
            llm_id=llm_id,
            timestamp=datetime.utcnow()
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        app_logger.error(f"Error getting trades for {llm_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Leaderboard Endpoint
# ============================================================================

@router.get(
    "/leaderboard",
    response_model=LeaderboardResponse,
    summary="Get LLM leaderboard",
    description="Returns LLM performance leaderboard sorted by total PnL."
)
async def get_leaderboard(
    service: AccountService = Depends(get_account_service_dependency)
) -> LeaderboardResponse:
    """
    Get LLM leaderboard.

    Returns:
    - Leaderboard sorted by total PnL (highest to lowest)
    - Rank, equity, PnL, win rate for each LLM
    - Summary statistics
    """
    try:
        leaderboard_data = service.get_leaderboard()
        summary = service.get_summary()

        # Add ranks
        leaderboard = [
            LeaderboardEntry(
                rank=idx + 1,
                llm_id=entry["llm_id"],
                equity_usdt=entry["equity_usdt"],
                total_pnl=entry["total_pnl"],
                total_pnl_pct=entry["total_pnl_pct"],
                total_trades=entry["total_trades"],
                winning_trades=entry["winning_trades"],
                losing_trades=entry["losing_trades"],
                win_rate=entry["win_rate"],
                open_positions=entry["open_positions"]
            )
            for idx, entry in enumerate(leaderboard_data)
        ]

        return LeaderboardResponse(
            leaderboard=leaderboard,
            summary={
                "total_equity_usdt": summary["total_equity_usdt"],
                "total_pnl": summary["total_pnl"],
                "total_pnl_pct": summary["total_pnl_pct"],
                "total_trades": summary["total_trades"],
                "average_win_rate": summary["average_win_rate"]
            },
            timestamp=datetime.utcnow()
        )

    except Exception as e:
        app_logger.error(f"Error getting leaderboard: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
