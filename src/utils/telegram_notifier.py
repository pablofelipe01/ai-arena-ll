"""
Telegram Notifier - Send alerts and notifications to Telegram.

Provides real-time notifications for:
- Server startup/shutdown
- Trading events (grid created, cycle completed, etc.)
- Errors and critical issues
- Daily/hourly summaries
"""

import requests
from typing import Optional, Dict, Any
from datetime import datetime
from src.utils.logger import app_logger


class TelegramNotifier:
    """
    Telegram notification service.

    Sends formatted messages to a Telegram chat via bot API.
    """

    def __init__(self, bot_token: str, chat_id: str, enabled: bool = True):
        """
        Initialize Telegram notifier.

        Args:
            bot_token: Telegram bot token from @BotFather
            chat_id: Chat ID where messages will be sent
            enabled: Enable/disable notifications
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.enabled = enabled
        self.api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

        if not bot_token or not chat_id:
            app_logger.warning("Telegram notifications disabled: missing bot_token or chat_id")
            self.enabled = False

    def send_message(
        self,
        message: str,
        parse_mode: str = "Markdown",
        disable_notification: bool = False
    ) -> bool:
        """
        Send a message to Telegram.

        Args:
            message: Message text (supports Markdown)
            parse_mode: Parse mode (Markdown or HTML)
            disable_notification: Send silently

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            return False

        try:
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode,
                "disable_notification": disable_notification
            }

            response = requests.post(self.api_url, json=payload, timeout=10)
            response.raise_for_status()

            app_logger.debug(f"Telegram message sent: {message[:50]}...")
            return True

        except Exception as e:
            app_logger.error(f"Failed to send Telegram message: {e}")
            return False

    # ========================================================================
    # System Events
    # ========================================================================

    def notify_server_started(self, grids_recovered: int = 0):
        """Notify that server has started."""
        message = f"""
🚀 *SERVER STARTED*

Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Grids Recovered: {grids_recovered}

System is now online and trading.
"""
        return self.send_message(message)

    def notify_server_stopped(self):
        """Notify that server is stopping."""
        message = f"""
⛔ *SERVER STOPPED*

Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

System is shutting down.
"""
        return self.send_message(message)

    def notify_error(self, error_type: str, error_msg: str, details: Optional[str] = None):
        """Notify about an error."""
        message = f"""
❌ *ERROR: {error_type}*

{error_msg}
"""
        if details:
            message += f"\nDetails: {details}"

        message += f"\n\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        return self.send_message(message)

    # ========================================================================
    # Trading Events
    # ========================================================================

    def notify_grid_created(self, llm_id: str, symbol: str, grid_id: str, config: Dict[str, Any]):
        """Notify when a new grid is created."""
        message = f"""
📊 *GRID CREATED*

LLM: {llm_id}
Symbol: {symbol}
Grid ID: `{grid_id}`

Config:
• Range: ${config.get('lower_limit', 0):.2f} - ${config.get('upper_limit', 0):.2f}
• Levels: {config.get('grid_levels', 0)}
• Spacing: {config.get('spacing_type', 'N/A')}
• Leverage: {config.get('leverage', 1)}x
• Investment: ${config.get('investment_usd', 0):.2f}

Time: {datetime.now().strftime("%H:%M:%S")}
"""
        return self.send_message(message, disable_notification=True)

    def notify_grid_cycle_completed(
        self,
        llm_id: str,
        symbol: str,
        buy_price: float,
        sell_price: float,
        profit: float,
        cycle_number: int
    ):
        """Notify when a grid cycle completes."""
        profit_emoji = "💰" if profit > 0 else "📉"

        message = f"""
{profit_emoji} *GRID CYCLE COMPLETED*

LLM: {llm_id}
Symbol: {symbol}
Cycle: #{cycle_number}

Buy: ${buy_price:.4f}
Sell: ${sell_price:.4f}
Profit: ${profit:.2f}

Time: {datetime.now().strftime("%H:%M:%S")}
"""
        return self.send_message(message)

    def notify_stop_loss_triggered(
        self,
        llm_id: str,
        symbol: str,
        grid_id: str,
        current_price: float,
        stop_price: float
    ):
        """Notify when stop loss is triggered."""
        message = f"""
🛑 *STOP LOSS TRIGGERED*

LLM: {llm_id}
Symbol: {symbol}
Grid: `{grid_id}`

Current Price: ${current_price:.4f}
Stop Price: ${stop_price:.4f}

Grid has been stopped.

Time: {datetime.now().strftime("%H:%M:%S")}
"""
        return self.send_message(message)

    def notify_position_opened(
        self,
        llm_id: str,
        symbol: str,
        side: str,
        price: float,
        quantity: float,
        leverage: int
    ):
        """Notify when a position is opened."""
        side_emoji = "🟢" if side == "LONG" else "🔴"

        message = f"""
{side_emoji} *POSITION OPENED*

LLM: {llm_id}
Symbol: {symbol}
Side: {side}

Entry: ${price:.4f}
Quantity: {quantity:.3f}
Leverage: {leverage}x
Notional: ${price * quantity:.2f}

Time: {datetime.now().strftime("%H:%M:%S")}
"""
        return self.send_message(message, disable_notification=True)

    def notify_position_closed(
        self,
        llm_id: str,
        symbol: str,
        side: str,
        entry_price: float,
        exit_price: float,
        quantity: float,
        pnl: float
    ):
        """Notify when a position is closed."""
        pnl_emoji = "✅" if pnl > 0 else "❌"

        message = f"""
{pnl_emoji} *POSITION CLOSED*

LLM: {llm_id}
Symbol: {symbol}
Side: {side}

Entry: ${entry_price:.4f}
Exit: ${exit_price:.4f}
Quantity: {quantity:.3f}

PnL: ${pnl:.2f}

Time: {datetime.now().strftime("%H:%M:%S")}
"""
        return self.send_message(message)

    # ========================================================================
    # Summary Reports
    # ========================================================================

    def notify_hourly_summary(self, summary: Dict[str, Any]):
        """Send hourly performance summary."""
        message = f"""
📈 *HOURLY SUMMARY*

Total Grids: {summary.get('total_grids', 0)}
Active Grids: {summary.get('active_grids', 0)}
Cycles Completed: {summary.get('cycles_completed', 0)}
Total Profit: ${summary.get('total_profit', 0):.2f}

LLMs Performance:
"""
        for llm_id, stats in summary.get('llm_stats', {}).items():
            message += f"\n{llm_id}:"
            message += f"\n  • Grids: {stats.get('grids', 0)}"
            message += f"\n  • Profit: ${stats.get('profit', 0):.2f}"

        message += f"\n\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        return self.send_message(message, disable_notification=True)

    def notify_daily_summary(self, summary: Dict[str, Any]):
        """Send daily performance summary."""
        message = f"""
📊 *DAILY SUMMARY*
{datetime.now().strftime("%Y-%m-%d")}

Total Balance: ${summary.get('total_balance', 0):.2f}
Total PnL: ${summary.get('total_pnl', 0):.2f} ({summary.get('total_pnl_pct', 0):.2f}%)

Grids:
• Active: {summary.get('active_grids', 0)}
• Cycles: {summary.get('total_cycles', 0)}
• Profit: ${summary.get('grid_profit', 0):.2f}

Positions:
• Open: {summary.get('open_positions', 0)}
• Trades: {summary.get('total_trades', 0)}

Top Performer: {summary.get('top_llm', 'N/A')}

Time: {datetime.now().strftime('%H:%M:%S')}
"""
        return self.send_message(message)

    # ========================================================================
    # Test & Utility
    # ========================================================================

    def send_test_message(self):
        """Send a test message to verify configuration."""
        message = f"""
✅ *TELEGRAM NOTIFICATIONS ENABLED*

Bot is connected and ready to send alerts.

Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
        return self.send_message(message)


# Singleton instance (will be initialized from settings)
_telegram_notifier: Optional[TelegramNotifier] = None


def get_telegram_notifier() -> Optional[TelegramNotifier]:
    """Get the global Telegram notifier instance."""
    return _telegram_notifier


def initialize_telegram_notifier(bot_token: str, chat_id: str, enabled: bool = True):
    """Initialize the global Telegram notifier."""
    global _telegram_notifier
    _telegram_notifier = TelegramNotifier(bot_token, chat_id, enabled)
    return _telegram_notifier
