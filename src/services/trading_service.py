"""
Trading Service - Orchestrates the complete trading flow.

Main workflow:
1. Fetch market data and calculate indicators
2. Get trading decisions from each LLM
3. Validate and execute decisions
4. Update accounts and sync to database
5. Handle automatic triggers (stop loss/take profit)
"""

from typing import Dict, List, Any, Optional
from decimal import Decimal
from datetime import datetime

from src.services.market_data_service import MarketDataService
from src.services.indicator_service import IndicatorService
from src.services.account_service import AccountService
from src.core.risk_manager import RiskManager
from src.core.trade_executor import TradeExecutor
from src.clients.llm_client import BaseLLMClient
from src.database.supabase_client import SupabaseClient
from src.utils.logger import app_logger
from src.utils.exceptions import TradingError


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

        app_logger.info(
            f"TradingService initialized with {len(llm_clients)} LLM clients"
        )

    def execute_trading_cycle(self) -> Dict[str, Any]:
        """
        Execute one complete trading cycle for all LLMs.

        Workflow:
        1. Fetch market data and indicators
        2. Check and execute automatic triggers (SL/TP)
        3. Get decisions from each LLM
        4. Execute validated decisions
        5. Sync state to database

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

            # Step 2: Calculate indicators
            app_logger.info("Step 2: Calculating technical indicators...")
            all_indicators = self.indicators.calculate_indicators_for_all_symbols()

            # Step 3: Handle automatic triggers (SL/TP)
            app_logger.info("Step 3: Checking automatic triggers...")
            trigger_results = self._handle_automatic_triggers(current_prices)

            # Step 4: Get LLM decisions and execute
            app_logger.info("Step 4: Getting LLM decisions...")
            decision_results = self._process_llm_decisions(
                current_prices,
                all_indicators
            )

            # Step 5: Update unrealized PnL for all accounts
            app_logger.info("Step 5: Updating unrealized PnL...")
            for llm_id, account in self.accounts.get_all_accounts().items():
                account.update_unrealized_pnl(current_prices)

            # Step 6: Sync to database
            app_logger.info("Step 6: Syncing to database...")
            self.accounts.sync_all_accounts()

            # Step 7: Save market data snapshot
            self._save_market_snapshot(market_snapshot, all_indicators)

            # Build results
            cycle_duration = (datetime.utcnow() - cycle_start).total_seconds()

            results = {
                "success": True,
                "cycle_start": cycle_start.isoformat(),
                "cycle_duration_seconds": cycle_duration,
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

    def _process_llm_decisions(
        self,
        current_prices: Dict[str, Decimal],
        indicators: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Get decisions from all LLMs and execute them.

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
