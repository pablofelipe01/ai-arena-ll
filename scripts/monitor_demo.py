#!/usr/bin/env python3
"""
Monitoring script for 24-hour trading demo.

This script continuously monitors the trading system during the demo,
checking health status, trading cycles, LLM decisions, and system performance.
"""

import sys
import os
import time
import requests
from datetime import datetime
from typing import Dict, Any, Optional

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class DemoMonitor:
    """Monitor trading system during 24-hour demo."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize monitor.

        Args:
            base_url: Base URL of the trading API
        """
        self.base_url = base_url.rstrip('/')
        self.start_time = datetime.now()

    def check_health(self) -> Dict[str, Any]:
        """Check system health."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def get_trading_status(self) -> Dict[str, Any]:
        """Get current trading status."""
        try:
            response = requests.get(f"{self.base_url}/trading/status", timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def get_scheduler_status(self) -> Dict[str, Any]:
        """Get scheduler status."""
        try:
            response = requests.get(f"{self.base_url}/scheduler/status", timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def get_leaderboard(self) -> Dict[str, Any]:
        """Get current leaderboard."""
        try:
            response = requests.get(f"{self.base_url}/trading/leaderboard", timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def format_uptime(self) -> str:
        """Format monitor uptime."""
        uptime = datetime.now() - self.start_time
        hours = uptime.seconds // 3600
        minutes = (uptime.seconds % 3600) // 60
        seconds = uptime.seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def create_dashboard(self) -> str:
        """Create dashboard display."""
        health = self.check_health()
        status = self.get_trading_status()
        scheduler = self.get_scheduler_status()
        leaderboard = self.get_leaderboard()

        lines = []
        lines.append("=" * 80)
        lines.append(f"  CRYPTO LLM TRADING DEMO - MONITOR")
        lines.append(f"  Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"  Uptime: {self.format_uptime()}")
        lines.append("=" * 80)
        lines.append("")

        # Health Status
        lines.append("HEALTH STATUS")
        lines.append("-" * 80)
        if health.get("status") == "healthy":
            lines.append("  Status: HEALTHY")
        else:
            lines.append(f"  Status: {health.get('status', 'UNKNOWN').upper()}")
            if "error" in health:
                lines.append(f"  Error: {health['error']}")
        lines.append("")

        # Scheduler Status
        lines.append("SCHEDULER STATUS")
        lines.append("-" * 80)
        if "error" not in scheduler:
            lines.append(f"  Running: {'Yes' if scheduler.get('is_running') else 'No'}")
            lines.append(f"  Jobs: {scheduler.get('jobs_count', 0)}")
            if scheduler.get('next_run_time'):
                lines.append(f"  Next Cycle: {scheduler['next_run_time']}")
        else:
            lines.append(f"  Error: {scheduler['error']}")
        lines.append("")

        # Trading Status
        lines.append("TRADING STATUS")
        lines.append("-" * 80)
        if "error" not in status:
            lines.append(f"  Accounts: {status.get('total_accounts', 0)}")
            lines.append(f"  Active Positions: {status.get('total_positions', 0)}")
            lines.append(f"  Total Trades: {status.get('total_trades', 0)}")
            lines.append(f"  Total Balance: ${status.get('total_balance', 0):.2f}")
            lines.append(f"  Total PnL: ${status.get('total_pnl', 0):.2f}")
        else:
            lines.append(f"  Error: {status['error']}")
        lines.append("")

        # Leaderboard
        lines.append("LEADERBOARD")
        lines.append("-" * 80)
        if "error" not in leaderboard and leaderboard.get("leaderboard"):
            for idx, account in enumerate(leaderboard["leaderboard"], 1):
                medal = ["1st", "2nd", "3rd"][idx - 1] if idx <= 3 else f"{idx}th"
                lines.append(
                    f"  {medal} {account['llm_id']}: "
                    f"${account['balance']:.2f} | "
                    f"PnL: ${account['total_pnl']:.2f} | "
                    f"Win Rate: {account['win_rate']:.1f}% | "
                    f"Trades: {account['total_trades']}"
                )
        else:
            lines.append("  No leaderboard data available")
        lines.append("")

        lines.append("=" * 80)
        lines.append(f"  Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("  Press Ctrl+C to stop monitoring")
        lines.append("=" * 80)

        return "\n".join(lines)

    def run(self, interval: int = 30):
        """Run monitoring loop."""
        print("\nStarting Demo Monitor...")
        print(f"   Monitoring: {self.base_url}")
        print(f"   Update Interval: {interval} seconds")
        print(f"   Press Ctrl+C to stop\n")

        try:
            while True:
                os.system('clear' if os.name == 'posix' else 'cls')
                dashboard = self.create_dashboard()
                print(dashboard)
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n\nMonitor stopped by user")
            print(f"   Total uptime: {self.format_uptime()}")
            sys.exit(0)
        except Exception as e:
            print(f"\n\nMonitor error: {e}")
            sys.exit(1)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Monitor Crypto LLM Trading Demo")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL of trading API")
    parser.add_argument("--interval", type=int, default=30, help="Update interval in seconds")
    args = parser.parse_args()

    monitor = DemoMonitor(base_url=args.url)
    monitor.run(interval=args.interval)


if __name__ == "__main__":
    main()
