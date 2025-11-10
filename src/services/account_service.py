"""
Account Service - Manages LLM trading accounts and database synchronization.

Provides:
- Management of 3 LLM accounts (LLM-A, LLM-B, LLM-C)
- Account state persistence to database
- Performance tracking and leaderboard
"""

from typing import Dict, List, Any, Optional
from decimal import Decimal
from datetime import datetime

from src.core.llm_account import LLMAccount, Position, Trade
from src.database.supabase_client import SupabaseClient
from src.utils.logger import app_logger


class AccountService:
    """
    Service for managing LLM trading accounts.

    Maintains 3 virtual accounts (one per LLM) and synchronizes
    state with the database.
    """

    def __init__(
        self,
        supabase_client: SupabaseClient,
        initial_balance: Decimal = Decimal("100.00")
    ):
        """
        Initialize account service.

        Args:
            supabase_client: Supabase database client
            initial_balance: Initial balance for each LLM account
        """
        self.db = supabase_client
        self.initial_balance = initial_balance

        # Initialize 3 LLM accounts
        self.accounts: Dict[str, LLMAccount] = {
            "LLM-A": LLMAccount("LLM-A", initial_balance),
            "LLM-B": LLMAccount("LLM-B", initial_balance),
            "LLM-C": LLMAccount("LLM-C", initial_balance)
        }

        app_logger.info(
            f"AccountService initialized with 3 LLM accounts "
            f"(${initial_balance} each)"
        )

    def get_account(self, llm_id: str) -> LLMAccount:
        """
        Get account for a specific LLM.

        Args:
            llm_id: LLM identifier

        Returns:
            LLMAccount instance

        Raises:
            ValueError: If llm_id is invalid
        """
        if llm_id not in self.accounts:
            raise ValueError(f"Invalid LLM ID: {llm_id}. Must be one of {list(self.accounts.keys())}")

        return self.accounts[llm_id]

    def get_all_accounts(self) -> Dict[str, LLMAccount]:
        """Get all LLM accounts."""
        return self.accounts

    def sync_account_to_db(self, llm_id: str) -> None:
        """
        Sync account state to database.

        Args:
            llm_id: LLM identifier
        """
        account = self.get_account(llm_id)

        try:
            # Upsert account state
            account_data = {
                "llm_id": llm_id,
                "balance_usdt": float(account.balance_usdt),
                "margin_used": float(account.margin_used),
                "unrealized_pnl": float(account.unrealized_pnl),
                "equity_usdt": float(account.equity_usdt),
                "total_trades": account.total_trades,
                "winning_trades": account.winning_trades,
                "losing_trades": account.losing_trades,
                "total_realized_pnl": float(account.total_realized_pnl),
                "updated_at": datetime.utcnow().isoformat()
            }

            self.db.upsert_llm_account(account_data)

            app_logger.debug(f"Synced {llm_id} account to database")

        except Exception as e:
            app_logger.error(f"Failed to sync {llm_id} account to DB: {e}")

    def sync_position_to_db(self, llm_id: str, position: Position) -> None:
        """
        Sync position to database.

        Args:
            llm_id: LLM identifier
            position: Position to sync
        """
        try:
            position_data = {
                "position_id": position.position_id,
                "llm_id": llm_id,
                "symbol": position.symbol,
                "side": position.side,
                "entry_price": float(position.entry_price),
                "quantity": float(position.quantity),
                "leverage": position.leverage,
                "margin_used": float(position.margin_used),
                "stop_loss_price": float(position.stop_loss_price) if position.stop_loss_price else None,
                "take_profit_price": float(position.take_profit_price) if position.take_profit_price else None,
                "opened_at": position.opened_at.isoformat(),
                "status": "OPEN"
            }

            self.db.upsert_position(position_data)

            app_logger.debug(f"Synced position {position.position_id} to database")

        except Exception as e:
            app_logger.error(f"Failed to sync position to DB: {e}")

    def close_position_in_db(self, position_id: str, trade: Trade) -> None:
        """
        Mark position as closed and save trade to database.

        Args:
            position_id: Position identifier
            trade: Completed trade
        """
        try:
            # Update position status
            self.db.update_position_status(position_id, "CLOSED")

            # Save trade record
            trade_data = {
                "trade_id": trade.trade_id,
                "llm_id": trade.trade_id.split("-")[0] if "-" in trade.trade_id else "UNKNOWN",  # Extract from position_id
                "symbol": trade.symbol,
                "side": trade.side,
                "entry_price": float(trade.entry_price),
                "exit_price": float(trade.exit_price),
                "quantity": float(trade.quantity),
                "leverage": trade.leverage,
                "pnl_usdt": float(trade.pnl_usd),
                "pnl_pct": float(trade.pnl_pct),
                "exit_reason": trade.exit_reason,
                "opened_at": trade.opened_at.isoformat(),
                "closed_at": trade.closed_at.isoformat()
            }

            self.db.insert_trade(trade_data)

            app_logger.debug(f"Closed position {position_id} in database")

        except Exception as e:
            app_logger.error(f"Failed to close position in DB: {e}")

    def sync_all_accounts(self) -> None:
        """Sync all account states to database."""
        for llm_id in self.accounts.keys():
            self.sync_account_to_db(llm_id)

    def get_leaderboard(self) -> List[Dict[str, Any]]:
        """
        Get LLM leaderboard sorted by total PnL.

        Returns:
            List of account summaries sorted by performance
        """
        leaderboard = []

        for llm_id, account in self.accounts.items():
            leaderboard.append({
                "llm_id": llm_id,
                "equity_usdt": float(account.equity_usdt),
                "total_pnl": float(account.total_pnl),
                "total_pnl_pct": float(account.total_pnl_pct),
                "total_trades": account.total_trades,
                "winning_trades": account.winning_trades,
                "losing_trades": account.losing_trades,
                "win_rate": float(account.win_rate),
                "open_positions": len(account.open_positions),
                "balance_usdt": float(account.balance_usdt)
            })

        # Sort by total PnL (descending)
        leaderboard.sort(key=lambda x: x["total_pnl"], reverse=True)

        return leaderboard

    def get_all_open_positions(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all open positions across all LLMs.

        Returns:
            Dict of llm_id -> list of positions
        """
        all_positions = {}

        for llm_id, account in self.accounts.items():
            positions = [
                pos.to_dict()
                for pos in account.open_positions.values()
            ]
            all_positions[llm_id] = positions

        return all_positions

    def get_recent_trades(self, llm_id: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent trades for an LLM or all LLMs.

        Args:
            llm_id: LLM identifier (None for all)
            limit: Number of trades to return per LLM

        Returns:
            List of recent trades
        """
        all_trades = []

        if llm_id:
            # Get trades for specific LLM
            account = self.get_account(llm_id)
            trades = account.get_recent_trades(limit)
            all_trades.extend([trade.to_dict() for trade in trades])
        else:
            # Get trades from all LLMs
            for account in self.accounts.values():
                trades = account.get_recent_trades(limit)
                all_trades.extend([trade.to_dict() for trade in trades])

            # Sort by close time (most recent first)
            all_trades.sort(
                key=lambda x: x["closed_at"],
                reverse=True
            )

            # Limit total trades
            all_trades = all_trades[:limit]

        return all_trades

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics across all LLMs.

        Returns:
            Dict with aggregated statistics
        """
        total_equity = sum(float(acc.equity_usdt) for acc in self.accounts.values())
        total_trades = sum(acc.total_trades for acc in self.accounts.values())
        total_wins = sum(acc.winning_trades for acc in self.accounts.values())
        total_losses = sum(acc.losing_trades for acc in self.accounts.values())
        total_pnl = sum(float(acc.total_pnl) for acc in self.accounts.values())

        avg_win_rate = (
            (total_wins / total_trades * 100) if total_trades > 0 else 0
        )

        return {
            "total_equity_usdt": total_equity,
            "total_initial_balance": float(self.initial_balance * 3),
            "total_pnl": total_pnl,
            "total_pnl_pct": (total_pnl / float(self.initial_balance * 3) * 100),
            "total_trades": total_trades,
            "total_wins": total_wins,
            "total_losses": total_losses,
            "average_win_rate": avg_win_rate,
            "active_llms": len(self.accounts),
            "leaderboard": self.get_leaderboard()
        }

    def reset_account(self, llm_id: str) -> None:
        """
        Reset an LLM account to initial state.

        Args:
            llm_id: LLM identifier

        Warning:
            This will clear all positions and trades!
        """
        app_logger.warning(f"Resetting {llm_id} account to initial state")

        # Close all positions
        account = self.get_account(llm_id)

        for position_id in list(account.open_positions.keys()):
            position = account.open_positions[position_id]
            # Close at current entry price (no PnL)
            account.close_position(position_id, position.entry_price, "RESET")

        # Recreate account
        self.accounts[llm_id] = LLMAccount(llm_id, self.initial_balance)

        # Sync to DB
        self.sync_account_to_db(llm_id)

        app_logger.info(f"{llm_id} account reset complete")

    def __repr__(self) -> str:
        """String representation."""
        total_equity = sum(float(acc.equity_usdt) for acc in self.accounts.values())
        return f"<AccountService accounts=3 total_equity=${total_equity:.2f}>"
