"""
Trading Service - Orchestrates the complete trading flow.

Main workflow:
1. Fetch market data and calculate indicators
2. Get grid trading decisions from each LLM
3. Execute grid actions (setup/update/stop grids)
4. Monitor grid cycles and track performance
5. Update accounts and sync to database
6. Handle automatic triggers (stop loss/take profit)
"""

from typing import Dict, List, Any, Optional
from decimal import Decimal
from datetime import datetime

from src.services.market_data_service import MarketDataService
from src.services.indicator_service import IndicatorService
from src.services.account_service import AccountService
from src.core.risk_manager import RiskManager
from src.core.trade_executor import TradeExecutor
from src.core.grid_engine import GridEngine, GridConfig
from src.clients.llm_client import BaseLLMClient
from src.database.supabase_client import SupabaseClient
from src.utils.logger import app_logger
from src.utils.exceptions import TradingError
from src.utils.telegram_notifier import get_telegram_notifier


class TradingService:
    """
    Main trading orchestration service.

    Coordinates the entire trading workflow from market data
    collection to LLM decision-making to trade execution and
    database persistence.
    """

    def __init__(
        self,
        market_data_service: MarketDataService,
        indicator_service: IndicatorService,
        account_service: AccountService,
        risk_manager: RiskManager,
        trade_executor: TradeExecutor,
        llm_clients: Dict[str, BaseLLMClient],
        supabase_client: SupabaseClient
    ):
        """
        Initialize trading service.

        Args:
            market_data_service: Market data service
            indicator_service: Technical indicator service
            account_service: Account management service
            risk_manager: Risk validation manager
            trade_executor: Trade execution engine
            llm_clients: Dict of llm_id -> LLM client
            supabase_client: Database client
        """
        self.market_data = market_data_service
        self.indicators = indicator_service
        self.accounts = account_service
        self.risk_manager = risk_manager
        self.executor = trade_executor
        self.llm_clients = llm_clients
        self.db = supabase_client

        # Initialize Grid Trading Engine
        self.grid_engine = GridEngine()
        self._grid_synced = False  # Track if we've synced grids from Binance

        app_logger.info(
            f"TradingService initialized with {len(llm_clients)} LLM clients and Grid Engine"
        )

    def initialize(self) -> Dict[str, Any]:
        """
        Initialize trading service state from Binance.

        Must be called once after construction, before executing trading cycles.
        Synchronizes grid state from existing orders on Binance.

        Returns:
            Dict with initialization statistics
        """
        if self._grid_synced:
            app_logger.warning("TradingService already initialized, skipping")
            return {"already_initialized": True}

        app_logger.info("=" * 60)
        app_logger.info("INITIALIZING TRADING SERVICE")
        app_logger.info("=" * 60)

        try:
            # Step 1: Recover grids from Supabase database
            app_logger.info("Step 1: Recovering grids from database...")
            db_grids = []
            try:
                db_grids = self.db.get_all_active_grids()
                app_logger.info(f"Found {len(db_grids)} active grids in database")

                # Restore grids to grid engine
                grids_restored = 0
                for db_grid in db_grids:
                    try:
                        restored = self.grid_engine.restore_grid_from_db(db_grid)
                        if restored:
                            grids_restored += 1
                            app_logger.info(f"Restored grid {db_grid['grid_id']} for {db_grid['symbol']}")
                    except Exception as e:
                        app_logger.error(f"Failed to restore grid {db_grid.get('grid_id', 'UNKNOWN')}: {e}")

                app_logger.info(f"Restored {grids_restored}/{len(db_grids)} grids from database")

            except Exception as e:
                app_logger.warning(f"Could not recover grids from database: {e}")

            # Step 2: Sync with Binance to update order status
            app_logger.info("Step 2: Syncing with Binance...")
            sync_result = self.grid_engine.sync_from_binance(self.executor.binance)

            self._grid_synced = True

            app_logger.info("TradingService initialization complete")
            return {
                "success": True,
                "grids_from_db": len(db_grids),
                "grid_sync": sync_result
            }

        except Exception as e:
            app_logger.error(f"Failed to initialize TradingService: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    def execute_trading_cycle(self) -> Dict[str, Any]:
        """
        Execute one complete trading cycle for all LLMs.

        Workflow:
        1. Fetch market data and current prices
        2. Sync virtual accounts with real Binance positions
        3. Calculate technical indicators
        4. Check and execute automatic triggers (SL/TP)
        5. Get decisions from each LLM
        6. Execute validated decisions
        7. Update unrealized PnL
        8. Sync state to database

        Returns:
            Dict with cycle results and statistics
        """
        cycle_start = datetime.utcnow()

        app_logger.info("=" * 60)
        app_logger.info("Starting trading cycle")
        app_logger.info("=" * 60)

        try:
            # Step 1: Fetch market data
            app_logger.info("Step 1: Fetching market data...")
            current_prices = self.market_data.get_current_prices(use_cache=False)
            market_snapshot = self.market_data.get_market_snapshot()

            # Step 2: Sync accounts with Binance real positions
            app_logger.info("Step 2: Syncing accounts from Binance...")
            sync_result = self.accounts.sync_from_binance(current_prices)
            if sync_result.get("success"):
                app_logger.info(f"Binance sync: {sync_result.get('stats', {})}")
            else:
                app_logger.warning(f"Binance sync failed: {sync_result.get('error', 'Unknown')}")

            # Step 3: Calculate indicators
            app_logger.info("Step 3: Calculating technical indicators...")
            all_indicators = self.indicators.calculate_indicators_for_all_symbols()

            # Step 4: Handle automatic triggers (SL/TP)
            app_logger.info("Step 4: Checking automatic triggers...")
            trigger_results = self._handle_automatic_triggers(current_prices)

            # Step 4.5: Monitor active grids for filled orders and completed cycles
            app_logger.info("Step 4.5: Monitoring active grids...")
            grid_monitoring_results = self._monitor_active_grids()

            # Step 5: Get grid trading decisions from LLMs and execute
            app_logger.info("Step 5: Getting grid trading decisions from LLMs...")
            decision_results = self._process_grid_decisions(
                current_prices,
                all_indicators
            )

            # Step 6: Update unrealized PnL for all accounts
            app_logger.info("Step 6: Updating unrealized PnL...")
            for llm_id, account in self.accounts.get_all_accounts().items():
                account.update_unrealized_pnl(current_prices)

            # Step 7: Sync to database
            app_logger.info("Step 7: Syncing to database...")
            self.accounts.sync_all_accounts()

            # Step 8: Save market data snapshot
            self._save_market_snapshot(market_snapshot, all_indicators)

            # Build results
            cycle_duration = (datetime.utcnow() - cycle_start).total_seconds()

            results = {
                "success": True,
                "cycle_start": cycle_start.isoformat(),
                "cycle_duration_seconds": cycle_duration,
                "binance_sync": sync_result,
                "market_data": {
                    "symbols_tracked": len(current_prices),
                    "gainers": market_snapshot["summary"]["gainers"],
                    "losers": market_snapshot["summary"]["losers"]
                },
                "triggers": {
                    "stop_loss_count": len(trigger_results.get("stop_loss", [])),
                    "take_profit_count": len(trigger_results.get("take_profit", [])),
                    "results": trigger_results
                },
                "grid_monitoring": {
                    "total_fills": grid_monitoring_results.get("total_fills", 0),
                    "total_cycles": grid_monitoring_results.get("total_cycles", 0),
                    "per_llm": grid_monitoring_results.get("per_llm", {})
                },
                "grid_stats": self.grid_engine.get_performance_summary(),
                "decisions": decision_results,
                "accounts": self.accounts.get_leaderboard(),
                "summary": self.accounts.get_summary()
            }

            app_logger.info(f"Trading cycle completed in {cycle_duration:.2f}s")
            app_logger.info("=" * 60)

            return results

        except Exception as e:
            app_logger.error(f"Trading cycle failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "cycle_start": cycle_start.isoformat()
            }

    def _handle_automatic_triggers(
        self,
        current_prices: Dict[str, Decimal]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Handle automatic stop loss and take profit triggers.

        Args:
            current_prices: Current market prices

        Returns:
            Dict with trigger results
        """
        results = {
            "stop_loss": [],
            "take_profit": []
        }

        for llm_id, account in self.accounts.get_all_accounts().items():
            # Execute auto-close triggers
            closed_positions = self.executor.auto_close_triggers(
                account=account,
                current_prices=current_prices
            )

            for result in closed_positions:
                if result["status"] == "SUCCESS":
                    trigger_type = result["trigger"]

                    # Sync to database
                    if "trade" in result:
                        trade_data = result["trade"]
                        self.accounts.close_position_in_db(
                            position_id=trade_data["trade_id"],
                            trade=account.closed_trades[-1]  # Get last closed trade
                        )

                    # Record result
                    results[trigger_type.lower()].append({
                        "llm_id": llm_id,
                        "symbol": result["symbol"],
                        "pnl_usd": result.get("pnl_usd", 0),
                        "trigger": trigger_type
                    })

                    app_logger.info(
                        f"{llm_id}: Auto-closed {result['symbol']} "
                        f"({trigger_type}), PnL: ${result.get('pnl_usd', 0):.2f}"
                    )

        return results

    def _monitor_active_grids(self) -> Dict[str, Any]:
        """
        Monitor all active grids for filled orders and completed cycles.

        Returns:
            Dict with monitoring results per LLM
        """
        monitoring_results = {}
        total_fills = 0
        total_cycles = 0

        active_grids = self.grid_engine.get_all_active_grids()

        for grid in active_grids:
            try:
                # Monitor this grid
                result = self.executor.monitor_grid_orders(grid, grid.llm_id)

                fills = len(result["filled_orders"])
                cycles = len(result["cycles_detected"])

                total_fills += fills
                total_cycles += cycles

                if fills > 0 or cycles > 0:
                    app_logger.info(
                        f"[{grid.llm_id}] Grid {grid.config.symbol}: "
                        f"{fills} fills, {cycles} cycles completed"
                    )

                    # Send Telegram notification for completed cycles
                    if cycles > 0:
                        telegram = get_telegram_notifier()
                        if telegram and telegram.enabled:
                            # Get cycle details from the result
                            for cycle_data in result.get("cycles_detected", []):
                                telegram.notify_grid_cycle_completed(
                                    llm_id=grid.llm_id,
                                    symbol=grid.config.symbol,
                                    buy_price=float(cycle_data.get("buy_price", 0)),
                                    sell_price=float(cycle_data.get("sell_price", 0)),
                                    profit=float(cycle_data.get("profit", 0)),
                                    cycle_number=grid.cycles_completed
                                )

                    # Store result
                    if grid.llm_id not in monitoring_results:
                        monitoring_results[grid.llm_id] = []

                    monitoring_results[grid.llm_id].append({
                        "grid_id": grid.grid_id,
                        "symbol": grid.config.symbol,
                        "fills": fills,
                        "cycles": cycles,
                        "total_cycles": grid.cycles_completed,
                        "total_profit": float(grid.total_profit_usdt)
                    })

            except Exception as e:
                app_logger.error(
                    f"[{grid.llm_id}] Failed to monitor grid {grid.grid_id}: {e}",
                    exc_info=True
                )

        if total_fills > 0 or total_cycles > 0:
            app_logger.info(
                f"Grid monitoring complete: {total_fills} total fills, "
                f"{total_cycles} total cycles across all LLMs"
            )

        return {
            "total_fills": total_fills,
            "total_cycles": total_cycles,
            "per_llm": monitoring_results
        }

    def _process_grid_decisions(
        self,
        current_prices: Dict[str, Decimal],
        indicators: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Get grid trading decisions from all LLMs and execute them.

        Args:
            current_prices: Current market prices
            indicators: Technical indicators

        Returns:
            Dict with grid decision results per LLM
        """
        decision_results = {}

        # Format market data for LLMs
        market_data = self.market_data.format_market_data_for_llm(
            include_indicators=True,
            indicator_data=indicators
        )

        for llm_id, llm_client in self.llm_clients.items():
            try:
                app_logger.info(f"Getting grid decision from {llm_id}...")

                # Get account
                account = self.accounts.get_account(llm_id)

                # Get active grids for this LLM
                active_grids = self.grid_engine.get_llm_grids(llm_id)
                active_grids_data = [grid.to_dict() for grid in active_grids]

                # Get recent grid performance
                grid_performance = self.grid_engine.get_performance_summary()

                # Get grid decision from LLM
                llm_response = llm_client.get_grid_decision(
                    account_info=account.to_dict(),
                    market_data=market_data,
                    active_grids=active_grids_data,
                    recent_performance=grid_performance
                )

                decision = llm_response["decision"]
                metadata = {
                    k: v for k, v in llm_response.items() if k != "decision"
                }

                # Execute grid action
                execution_result = self._execute_grid_action(
                    llm_id=llm_id,
                    decision=decision,
                    account=account,
                    current_prices=current_prices
                )

                # Save grid decision to database
                self._save_grid_decision(llm_id, decision, metadata, execution_result)

                # Sync account state
                self.accounts.sync_account_to_db(llm_id)

                # Record result
                decision_results[llm_id] = {
                    "decision": decision,
                    "execution": execution_result,
                    "metadata": metadata
                }

                app_logger.info(
                    f"{llm_id}: {decision['action']} - "
                    f"{execution_result.get('message', 'N/A')}"
                )

            except Exception as e:
                app_logger.error(f"Failed to process {llm_id} grid decision: {e}", exc_info=True)
                decision_results[llm_id] = {
                    "error": str(e),
                    "status": "ERROR"
                }

        return decision_results

    def _execute_grid_action(
        self,
        llm_id: str,
        decision: Dict[str, Any],
        account: Any,
        current_prices: Dict[str, Decimal]
    ) -> Dict[str, Any]:
        """
        Execute grid trading action based on LLM decision.

        Args:
            llm_id: LLM identifier
            decision: Grid trading decision
            account: Trading account
            current_prices: Current market prices

        Returns:
            Execution result dict
        """
        action = decision["action"]
        symbol = decision.get("symbol")

        try:
            if action == "SETUP_GRID":
                # Create new grid
                grid_config_data = decision["grid_config"]

                # Validate symbol
                if symbol not in self.market_data.symbols:
                    return {
                        "status": "REJECTED",
                        "action": action,
                        "message": f"Invalid symbol: {symbol}"
                    }

                # Check if grid already exists for this symbol (only ACTIVE grids)
                existing_grids = self.grid_engine.get_llm_grids(llm_id)
                active_grids = [g for g in existing_grids if g.status == "ACTIVE"]
                if any(g.config.symbol == symbol for g in active_grids):
                    return {
                        "status": "REJECTED",
                        "action": action,
                        "message": f"Grid already exists for {symbol}"
                    }

                # Check available balance for margin requirement (worst-case scenario)
                investment_usd = Decimal(str(grid_config_data["investment_usd"]))
                leverage = grid_config_data["leverage"]
                margin_required = investment_usd / Decimal(str(leverage))

                available_balance = self.executor.binance.get_available_balance()

                if available_balance < margin_required:
                    error_msg = (
                        f"Insufficient margin: ${available_balance:.2f} available, "
                        f"${margin_required:.2f} required (${investment_usd} / {leverage}x)"
                    )

                    app_logger.warning(f"[{llm_id}] Grid creation rejected: {error_msg}")

                    # Send Telegram notification
                    telegram = get_telegram_notifier()
                    if telegram and telegram.enabled:
                        telegram.notify_error(
                            error_type="Insufficient Margin",
                            error_msg=f"{llm_id} - {symbol}",
                            details=f"Required: ${margin_required:.2f}, Available: ${available_balance:.2f}"
                        )

                    return {
                        "status": "REJECTED",
                        "action": action,
                        "message": error_msg
                    }

                # Create grid configuration
                grid_config = GridConfig(
                    symbol=symbol,
                    upper_limit=Decimal(str(grid_config_data["upper_limit"])),
                    lower_limit=Decimal(str(grid_config_data["lower_limit"])),
                    grid_levels=grid_config_data["grid_levels"],
                    spacing_type=grid_config_data["spacing_type"],
                    leverage=grid_config_data["leverage"],
                    investment_usd=Decimal(str(grid_config_data["investment_usd"])),
                    stop_loss_pct=Decimal(str(grid_config_data["stop_loss_pct"]))
                )

                # Create grid
                grid = self.grid_engine.create_grid(llm_id, grid_config)

                # Place grid orders on Binance
                placement_result = self.executor.place_grid_orders(grid, llm_id)

                if placement_result["status"] != "SUCCESS":
                    # Failed to place orders, stop grid
                    self.grid_engine.stop_grid(grid.grid_id, reason="ORDER_PLACEMENT_FAILED")
                    return {
                        "status": "ERROR",
                        "action": action,
                        "message": f"Failed to place grid orders: {placement_result['message']}",
                        "grid_id": grid.grid_id,
                        "symbol": symbol
                    }

                app_logger.info(
                    f"[{llm_id}] Grid created and orders placed for {symbol}: "
                    f"${grid_config.lower_limit}-${grid_config.upper_limit}, "
                    f"{grid_config.grid_levels} levels, {grid_config.spacing_type} spacing, "
                    f"{len(placement_result['placed'])} orders placed"
                )

                # Save grid to database
                try:
                    self.db.create_grid({
                        "grid_id": grid.grid_id,
                        "llm_id": llm_id,
                        "symbol": symbol,
                        "status": "ACTIVE",
                        "upper_limit": float(grid_config.upper_limit),
                        "lower_limit": float(grid_config.lower_limit),
                        "grid_levels": grid_config.grid_levels,
                        "spacing_type": grid_config.spacing_type,
                        "leverage": grid_config.leverage,
                        "investment_usd": float(grid_config.investment_usd),
                        "stop_loss_pct": float(grid_config.stop_loss_pct),
                        "cycles_completed": 0,
                        "total_profit_usdt": 0.0,
                        "total_fees_usdt": 0.0,
                        "orders_placed": len(placement_result['placed'])
                    })
                    app_logger.info(f"[{llm_id}] Grid {grid.grid_id} saved to database")
                except Exception as e:
                    app_logger.error(f"[{llm_id}] Failed to save grid to database: {e}")

                # Send Telegram notification
                telegram = get_telegram_notifier()
                if telegram and telegram.enabled:
                    telegram.notify_grid_created(
                        llm_id=llm_id,
                        symbol=symbol,
                        grid_id=grid.grid_id,
                        config=grid_config.to_dict()
                    )

                return {
                    "status": "SUCCESS",
                    "action": action,
                    "message": f"Grid created for {symbol} with {len(placement_result['placed'])} orders",
                    "grid_id": grid.grid_id,
                    "symbol": symbol,
                    "orders_placed": len(placement_result['placed'])
                }

            elif action == "UPDATE_GRID":
                # Update existing grid
                existing_grids = self.grid_engine.get_llm_grids(llm_id)
                target_grid = next((g for g in existing_grids if g.config.symbol == symbol), None)

                if not target_grid:
                    return {
                        "status": "REJECTED",
                        "action": action,
                        "message": f"No existing grid for {symbol}"
                    }

                # Cancel old grid orders
                cancel_result = self.executor.cancel_grid_orders(target_grid, llm_id)
                app_logger.info(
                    f"[{llm_id}] Cancelled {len(cancel_result['cancelled'])} orders from old grid"
                )

                # Stop old grid
                self.grid_engine.stop_grid(target_grid.grid_id, reason="UPDATE")

                # Update old grid status in database
                try:
                    self.db.stop_grid(target_grid.grid_id, "UPDATE")
                    app_logger.info(f"[{llm_id}] Old grid {target_grid.grid_id} stopped in database")
                except Exception as e:
                    app_logger.error(f"[{llm_id}] Failed to stop old grid in database: {e}")

                # Create new grid with updated parameters
                grid_config_data = decision["grid_config"]
                grid_config = GridConfig(
                    symbol=symbol,
                    upper_limit=Decimal(str(grid_config_data["upper_limit"])),
                    lower_limit=Decimal(str(grid_config_data["lower_limit"])),
                    grid_levels=grid_config_data["grid_levels"],
                    spacing_type=grid_config_data["spacing_type"],
                    leverage=grid_config_data["leverage"],
                    investment_usd=Decimal(str(grid_config_data["investment_usd"])),
                    stop_loss_pct=Decimal(str(grid_config_data["stop_loss_pct"]))
                )

                new_grid = self.grid_engine.create_grid(llm_id, grid_config)

                # Place new grid orders
                placement_result = self.executor.place_grid_orders(new_grid, llm_id)

                if placement_result["status"] != "SUCCESS":
                    # Failed to place orders, stop grid
                    self.grid_engine.stop_grid(new_grid.grid_id, reason="ORDER_PLACEMENT_FAILED")
                    return {
                        "status": "ERROR",
                        "action": action,
                        "message": f"Failed to place updated grid orders: {placement_result['message']}",
                        "grid_id": new_grid.grid_id,
                        "symbol": symbol
                    }

                app_logger.info(
                    f"[{llm_id}] Grid updated for {symbol}: "
                    f"{len(placement_result['placed'])} new orders placed"
                )

                # Save new grid to database
                try:
                    self.db.create_grid({
                        "grid_id": new_grid.grid_id,
                        "llm_id": llm_id,
                        "symbol": symbol,
                        "status": "ACTIVE",
                        "upper_limit": float(grid_config.upper_limit),
                        "lower_limit": float(grid_config.lower_limit),
                        "grid_levels": grid_config.grid_levels,
                        "spacing_type": grid_config.spacing_type,
                        "leverage": grid_config.leverage,
                        "investment_usd": float(grid_config.investment_usd),
                        "stop_loss_pct": float(grid_config.stop_loss_pct),
                        "cycles_completed": 0,
                        "total_profit_usdt": 0.0,
                        "total_fees_usdt": 0.0,
                        "orders_placed": len(placement_result['placed'])
                    })
                    app_logger.info(f"[{llm_id}] New grid {new_grid.grid_id} saved to database")
                except Exception as e:
                    app_logger.error(f"[{llm_id}] Failed to save new grid to database: {e}")

                return {
                    "status": "SUCCESS",
                    "action": action,
                    "message": f"Grid updated for {symbol} with {len(placement_result['placed'])} orders",
                    "grid_id": new_grid.grid_id,
                    "symbol": symbol,
                    "orders_placed": len(placement_result['placed'])
                }

            elif action == "STOP_GRID":
                # Stop existing grid
                existing_grids = self.grid_engine.get_llm_grids(llm_id)
                target_grid = next((g for g in existing_grids if g.config.symbol == symbol), None)

                if not target_grid:
                    return {
                        "status": "REJECTED",
                        "action": action,
                        "message": f"No active grid for {symbol}"
                    }

                # Cancel all pending grid orders
                cancel_result = self.executor.cancel_grid_orders(target_grid, llm_id)

                # Stop grid
                self.grid_engine.stop_grid(target_grid.grid_id, reason="LLM_DECISION")

                # Update grid status in database
                try:
                    self.db.stop_grid(target_grid.grid_id, "LLM_DECISION")
                    app_logger.info(f"[{llm_id}] Grid {target_grid.grid_id} stopped in database")
                except Exception as e:
                    app_logger.error(f"[{llm_id}] Failed to stop grid in database: {e}")

                app_logger.info(
                    f"[{llm_id}] Grid stopped for {symbol}: "
                    f"{len(cancel_result['cancelled'])} orders cancelled"
                )

                return {
                    "status": "SUCCESS",
                    "action": action,
                    "message": f"Grid stopped for {symbol}, {len(cancel_result['cancelled'])} orders cancelled",
                    "grid_id": target_grid.grid_id,
                    "symbol": symbol,
                    "orders_cancelled": len(cancel_result['cancelled'])
                }

            elif action == "HOLD":
                # No action taken
                return {
                    "status": "SUCCESS",
                    "action": action,
                    "message": "No grid action taken (HOLD decision)"
                }

            else:
                return {
                    "status": "REJECTED",
                    "action": action,
                    "message": f"Unknown action: {action}"
                }

        except Exception as e:
            app_logger.error(f"[{llm_id}] Failed to execute grid action {action}: {e}", exc_info=True)
            return {
                "status": "ERROR",
                "action": action,
                "message": str(e)
            }

    def _save_grid_decision(
        self,
        llm_id: str,
        decision: Dict[str, Any],
        metadata: Dict[str, Any],
        execution_result: Dict[str, Any]
    ) -> None:
        """
        Save grid trading decision to database.

        Args:
            llm_id: LLM identifier
            decision: Grid decision
            metadata: LLM response metadata
            execution_result: Execution result
        """
        try:
            grid_config = decision.get("grid_config", {})

            decision_data = {
                "llm_id": llm_id,
                "action": decision["action"],
                "symbol": decision.get("symbol"),
                "quantity_usd": grid_config.get("investment_usd"),
                "leverage": grid_config.get("leverage"),
                "stop_loss_pct": grid_config.get("stop_loss_pct"),
                "take_profit_pct": None,  # Grid trading doesn't use take profit
                "reasoning": decision.get("reasoning"),
                "confidence": decision.get("confidence"),
                "strategy": "grid_trading",
                "execution_status": execution_result["status"],
                "execution_message": execution_result.get("message"),
                "tokens_used": metadata.get("tokens", {}).get("total", 0),
                "cost_usd": metadata.get("cost_usd", 0.0),
                "response_time_ms": metadata.get("response_time_ms", 0),
                "created_at": datetime.utcnow().isoformat()
            }

            self.db.insert_llm_decision(decision_data)

        except Exception as e:
            app_logger.error(f"Failed to save {llm_id} grid decision to DB: {e}")

    def _process_llm_decisions_DEPRECATED(
        self,
        current_prices: Dict[str, Decimal],
        indicators: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        [DEPRECATED] Get decisions from all LLMs and execute them.
        Kept for reference. System now uses grid trading decisions.

        Args:
            current_prices: Current market prices
            indicators: Technical indicators

        Returns:
            Dict with decision results per LLM
        """
        decision_results = {}

        # Format market data for LLMs
        market_data = self.market_data.format_market_data_for_llm(
            include_indicators=True,
            indicator_data=indicators
        )

        for llm_id, llm_client in self.llm_clients.items():
            try:
                app_logger.info(f"Getting decision from {llm_id}...")

                # Get account
                account = self.accounts.get_account(llm_id)

                # Prepare data for LLM
                account_info = account.to_dict()

                open_positions = [
                    pos.to_dict()
                    for pos in account.open_positions.values()
                ]

                recent_trades = [
                    trade.to_dict()
                    for trade in account.get_recent_trades(5)
                ]

                # Get decision from LLM
                llm_response = llm_client.get_trading_decision(
                    account_info=account_info,
                    market_data=market_data,
                    open_positions=open_positions,
                    recent_trades=recent_trades
                )

                decision = llm_response["decision"]
                metadata = {
                    k: v for k, v in llm_response.items() if k != "decision"
                }

                # Execute decision
                execution_result = self.executor.execute_decision(
                    decision=decision,
                    account=account,
                    current_prices=current_prices
                )

                # Save to database
                self._save_llm_decision(llm_id, decision, metadata, execution_result)

                # Sync account/position changes
                if execution_result["status"] == "SUCCESS":
                    action = execution_result["action"]

                    if action in ["BUY", "SELL"]:
                        # New position opened
                        position_id = list(account.open_positions.keys())[-1]
                        position = account.open_positions[position_id]
                        self.accounts.sync_position_to_db(llm_id, position)

                    elif action == "CLOSE":
                        # Position closed
                        if account.closed_trades:
                            trade = account.closed_trades[-1]
                            self.accounts.close_position_in_db(
                                position_id=trade.trade_id,
                                trade=trade
                            )

                    # Always sync account state
                    self.accounts.sync_account_to_db(llm_id)

                # Record result
                decision_results[llm_id] = {
                    "decision": decision,
                    "execution": execution_result,
                    "metadata": metadata
                }

                app_logger.info(
                    f"{llm_id}: {execution_result['action']} - "
                    f"{execution_result.get('message', 'N/A')}"
                )

            except Exception as e:
                app_logger.error(f"Failed to process {llm_id} decision: {e}", exc_info=True)
                decision_results[llm_id] = {
                    "error": str(e),
                    "status": "ERROR"
                }

        return decision_results

    def _save_llm_decision(
        self,
        llm_id: str,
        decision: Dict[str, Any],
        metadata: Dict[str, Any],
        execution_result: Dict[str, Any]
    ) -> None:
        """
        Save LLM decision to database.

        Args:
            llm_id: LLM identifier
            decision: Trading decision
            metadata: LLM response metadata (tokens, cost, etc.)
            execution_result: Execution result
        """
        try:
            decision_data = {
                "llm_id": llm_id,
                "action": decision["action"],
                "symbol": decision.get("symbol"),
                "quantity_usd": decision.get("quantity_usd"),
                "leverage": decision.get("leverage"),
                "stop_loss_pct": decision.get("stop_loss_pct"),
                "take_profit_pct": decision.get("take_profit_pct"),
                "reasoning": decision.get("reasoning"),
                "confidence": decision.get("confidence"),
                "strategy": decision.get("strategy"),
                "execution_status": execution_result["status"],
                "execution_message": execution_result.get("message"),
                "tokens_used": metadata.get("tokens", {}).get("total", 0),
                "cost_usd": metadata.get("cost_usd", 0.0),
                "response_time_ms": metadata.get("response_time_ms", 0),
                "created_at": datetime.utcnow().isoformat()
            }

            self.db.insert_llm_decision(decision_data)

        except Exception as e:
            app_logger.error(f"Failed to save {llm_id} decision to DB: {e}")

    def _save_market_snapshot(
        self,
        snapshot: Dict[str, Any],
        indicators: Dict[str, Dict[str, Any]]
    ) -> None:
        """
        Save market data snapshot to database.

        Args:
            snapshot: Market snapshot
            indicators: Technical indicators
        """
        try:
            for symbol, data in snapshot["symbols"].items():
                # Get indicators for this symbol
                symbol_indicators = indicators.get(symbol, {})

                market_data = {
                    "symbol": symbol,
                    "price": float(data["price"]),
                    "price_change_pct_24h": float(data["price_change_pct_24h"]),
                    "volume_24h": float(data["volume_24h"]),
                    "high_24h": float(data["high_24h"]),
                    "low_24h": float(data["low_24h"]),
                    "rsi": symbol_indicators.get("rsi", 0.0),
                    "macd": symbol_indicators.get("macd", 0.0),
                    "macd_signal": symbol_indicators.get("macd_signal", 0.0),
                    "data_timestamp": snapshot["timestamp"].isoformat()
                }

                self.db.insert_market_data(market_data)

        except Exception as e:
            app_logger.error(f"Failed to save market snapshot to DB: {e}")

    def get_trading_status(self) -> Dict[str, Any]:
        """
        Get current trading system status.

        Returns:
            Dict with system status and statistics
        """
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "llm_count": len(self.llm_clients),
            "symbols_tracked": len(self.market_data.symbols),
            "accounts": self.accounts.get_leaderboard(),
            "open_positions": self.accounts.get_all_open_positions(),
            "recent_trades": self.accounts.get_recent_trades(limit=10),
            "summary": self.accounts.get_summary()
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<TradingService "
            f"llms={len(self.llm_clients)} "
            f"symbols={len(self.market_data.symbols)}>"
        )
