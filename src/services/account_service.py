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
from src.clients.binance_client import BinanceClient
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
        binance_client: Optional[BinanceClient] = None,
        initial_balance: Decimal = Decimal("100.00")
    ):
        """
        Initialize account service.

        Args:
            supabase_client: Supabase database client
            binance_client: Binance client for syncing real positions (optional)
            initial_balance: Initial balance for each LLM account
        """
        self.db = supabase_client
        self.binance = binance_client
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
            # Get LLM configuration from settings
            from config.settings import settings

            # Map LLM ID to config
            llm_config_map = {
                "LLM-A": {
                    "provider": settings.LLM_A_PROVIDER,
                    "model": settings.LLM_A_MODEL,
                    "temperature": settings.LLM_A_TEMPERATURE,
                    "max_tokens": settings.LLM_A_MAX_TOKENS
                },
                "LLM-B": {
                    "provider": settings.LLM_B_PROVIDER,
                    "model": settings.LLM_B_MODEL,
                    "temperature": settings.LLM_B_TEMPERATURE,
                    "max_tokens": settings.LLM_B_MAX_TOKENS
                },
                "LLM-C": {
                    "provider": settings.LLM_C_PROVIDER,
                    "model": settings.LLM_C_MODEL,
                    "temperature": settings.LLM_C_TEMPERATURE,
                    "max_tokens": settings.LLM_C_MAX_TOKENS
                }
            }

            llm_config = llm_config_map.get(llm_id, {})

            # Upsert account state (using correct Supabase column names)
            account_data = {
                "llm_id": llm_id,
                "provider": llm_config.get("provider", "unknown"),
                "model_name": llm_config.get("model", "unknown"),
                "temperature": float(llm_config.get("temperature", 0.7)),
                "max_tokens": llm_config.get("max_tokens", 1000),
                "balance": float(account.balance_usdt),
                "margin_used": float(account.margin_used),
                "unrealized_pnl": float(account.unrealized_pnl),
                "total_pnl": float(account.total_realized_pnl + account.unrealized_pnl),
                "total_trades": account.total_trades,
                "winning_trades": account.winning_trades,
                "losing_trades": account.losing_trades,
                "realized_pnl": float(account.total_realized_pnl),
                "updated_at": datetime.utcnow().isoformat()
            }

            self.db.upsert_account(account_data)

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
            # Extract llm_id from trade_id format: "TRD-LLM-A-symbol-timestamp"
            llm_id = "UNKNOWN"
            if hasattr(trade, 'llm_id'):
                llm_id = trade.llm_id
            elif "-" in trade.trade_id:
                parts = trade.trade_id.split("-")
                if len(parts) >= 3:
                    llm_id = f"{parts[1]}-{parts[2]}"  # "LLM-A", "LLM-B", etc.

            trade_data = {
                "trade_id": trade.trade_id,
                "llm_id": llm_id,
                "symbol": trade.symbol,
                "side": trade.side,
                "entry_price": float(trade.entry_price),
                "exit_price": float(trade.exit_price),
                "quantity": float(trade.quantity),
                "leverage": trade.leverage,
                "realized_pnl": float(trade.pnl_usd),
                "pnl_percentage": float(trade.pnl_pct),
                "exit_reason": trade.exit_reason,
                "opened_at": trade.opened_at.isoformat(),
                "closed_at": trade.closed_at.isoformat()
            }

            self.db.create_trade(trade_data)

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
            Dict of llm_id -> list of positions with calculated PnL
        """
        from src.api.dependencies import get_market_data_service

        # Get current market prices
        market_service = get_market_data_service()
        current_prices = market_service.get_current_prices()

        all_positions = {}

        for llm_id, account in self.accounts.items():
            positions = []
            for pos in account.open_positions.values():
                # Get position dict
                pos_dict = pos.to_dict()

                # Calculate PnL with current price
                current_price = current_prices.get(pos.symbol, pos.entry_price)
                pnl_data = pos.calculate_pnl(current_price)

                # Add PnL fields
                pos_dict["unrealized_pnl_usd"] = float(pnl_data["unrealized_pnl_usd"])
                pos_dict["unrealized_pnl_pct"] = float(pnl_data["unrealized_pnl_pct"])
                pos_dict["roi_pct"] = float(pnl_data["roi_pct"])

                positions.append(pos_dict)

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

    def sync_from_binance(self, current_prices: Dict[str, Decimal]) -> Dict[str, Any]:
        """
        Sync all accounts with real positions from Binance.

        This method:
        1. Fetches real positions from Binance
        2. Updates virtual accounts to match reality
        3. Syncs to database

        Args:
            current_prices: Current market prices for PnL calculation

        Returns:
            Dict with sync results
        """
        if not self.binance:
            app_logger.warning("Cannot sync from Binance: client not available")
            return {
                "success": False,
                "message": "Binance client not configured"
            }

        try:
            app_logger.info("Syncing accounts from Binance...")

            # Get all real positions from Binance WITH clientOrderIds
            binance_positions = self.binance.get_open_positions_with_client_ids()

            # Group positions by LLM (parsed from clientOrderId)
            positions_by_llm = {}
            for pos in binance_positions:
                # Parse clientOrderId to get LLM owner
                # Format 1 (regular): LLM-A_BTCUSDT_1234567890
                # Format 2 (grid): GRID_LLM-A_BTCUSDT_hash_SIDE_level
                client_order_id = pos.get("clientOrderId")
                llm_owner = None

                if client_order_id:
                    parts = client_order_id.split("_")
                    # Check for grid order format first (starts with "GRID")
                    if len(parts) >= 2 and parts[0] == "GRID" and parts[1] in self.accounts:
                        llm_owner = parts[1]
                    # Then check regular order format
                    elif len(parts) >= 1 and parts[0] in self.accounts:
                        llm_owner = parts[0]

                # If we can't determine owner, skip this position
                if not llm_owner:
                    app_logger.warning(
                        f"Cannot determine LLM owner for {pos['symbol']} "
                        f"(clientOrderId: {client_order_id}), skipping..."
                    )
                    continue

                if llm_owner not in positions_by_llm:
                    positions_by_llm[llm_owner] = []

                positions_by_llm[llm_owner].append(pos)

            sync_stats = {
                "positions_synced": 0,
                "positions_added": 0,
                "positions_removed": 0,
                "positions_updated": 0,
                "by_llm": {}
            }

            # Sync each LLM account
            for llm_id in self.accounts.keys():
                account = self.get_account(llm_id)
                real_positions_for_llm = positions_by_llm.get(llm_id, [])

                # Convert to dict keyed by symbol for easy lookup
                real_positions_by_symbol = {
                    pos["symbol"]: pos
                    for pos in real_positions_for_llm
                }

                llm_stats = {
                    "positions_synced": 0,
                    "positions_added": 0,
                    "positions_removed": 0,
                    "positions_updated": 0
                }

                # Track which virtual positions we've seen
                virtual_symbols = set(pos.symbol for pos in account.open_positions.values())
                real_symbols = set(real_positions_by_symbol.keys())

                # Update existing positions with real data
                for position in list(account.open_positions.values()):
                    symbol = position.symbol

                    if symbol in real_positions_by_symbol:
                        real_pos = real_positions_by_symbol[symbol]
                        real_quantity = abs(Decimal(real_pos["positionAmt"]))
                        real_entry = Decimal(real_pos["entryPrice"])
                        real_leverage = int(real_pos["leverage"])

                        # Update position with real data
                        position.quantity = real_quantity
                        position.entry_price = real_entry
                        position.leverage = real_leverage

                        # Recalculate margin
                        position.margin_used = (real_quantity * real_entry) / Decimal(str(real_leverage))

                        # Update PnL
                        if symbol in current_prices:
                            pnl_data = position.calculate_pnl(current_prices[symbol])
                            position.unrealized_pnl_usd = pnl_data["unrealized_pnl_usd"]
                            position.unrealized_pnl_pct = pnl_data["unrealized_pnl_pct"]
                            position.roi_pct = pnl_data["roi_pct"]

                        llm_stats["positions_updated"] += 1
                        sync_stats["positions_updated"] += 1
                        app_logger.info(
                            f"[{llm_id}] Updated {symbol}: {real_quantity} @ ${real_entry}"
                        )

                    else:
                        # Position closed in Binance but still open in virtual account
                        # Close it with current price
                        exit_price = current_prices.get(symbol, position.entry_price)
                        account.close_position(
                            position_id=position.position_id,
                            exit_price=exit_price,
                            exit_reason="SYNC_CLOSED"
                        )
                        llm_stats["positions_removed"] += 1
                        sync_stats["positions_removed"] += 1
                        app_logger.info(f"[{llm_id}] Closed virtual position {symbol} (not in Binance)")

                # Add positions that exist in Binance but not in virtual account
                for symbol, real_pos in real_positions_by_symbol.items():
                    if symbol not in virtual_symbols:
                        # New position found in Binance
                        real_quantity = abs(Decimal(real_pos["positionAmt"]))
                        real_entry = Decimal(real_pos["entryPrice"])
                        real_leverage = int(real_pos["leverage"])
                        position_amt = Decimal(real_pos["positionAmt"])

                        # Determine side
                        side = "LONG" if position_amt > 0 else "SHORT"

                        # Calculate position size in USD
                        quantity_usd = real_quantity * real_entry

                        # Create position in virtual account
                        try:
                            new_position = account.open_position(
                                symbol=symbol,
                                side=side,
                                entry_price=real_entry,
                                quantity_usd=quantity_usd,
                                leverage=real_leverage
                            )

                            # Update with exact quantity from Binance
                            new_position.quantity = real_quantity

                            llm_stats["positions_added"] += 1
                            sync_stats["positions_added"] += 1
                            app_logger.info(
                                f"[{llm_id}] Added position from Binance: {symbol} {side} "
                                f"{real_quantity} @ ${real_entry}"
                            )
                        except Exception as e:
                            app_logger.error(f"[{llm_id}] Failed to add position {symbol}: {e}")

                # Recalculate account totals
                account.update_unrealized_pnl(current_prices)

                # Sync to database
                self.sync_account_to_db(llm_id)

                # Sync all positions to DB
                for position in account.open_positions.values():
                    self.sync_position_to_db(llm_id, position)

                llm_stats["positions_synced"] = len(account.open_positions)
                sync_stats["positions_synced"] += len(account.open_positions)
                sync_stats["by_llm"][llm_id] = llm_stats

            app_logger.info(
                f"Binance sync complete: {sync_stats['positions_synced']} total positions, "
                f"{sync_stats['positions_added']} added, "
                f"{sync_stats['positions_updated']} updated, "
                f"{sync_stats['positions_removed']} removed"
            )

            # Log per-LLM stats
            for llm_id, llm_stats in sync_stats["by_llm"].items():
                app_logger.info(
                    f"  [{llm_id}]: {llm_stats['positions_synced']} positions "
                    f"(+{llm_stats['positions_added']} ~{llm_stats['positions_updated']} "
                    f"-{llm_stats['positions_removed']})"
                )

            return {
                "success": True,
                "stats": sync_stats
            }

        except Exception as e:
            app_logger.error(f"Failed to sync from Binance: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
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
