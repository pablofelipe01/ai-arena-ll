#!/usr/bin/env python3
"""
LLM Trading Competition - Live Monitor
Real-time terminal dashboard for monitoring the 24-hour trading competition
"""

import requests
import time
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich import box

# API Configuration
API_BASE_URL = "http://localhost:8000"
REFRESH_INTERVAL = 30  # seconds

console = Console()


def get_api_data(endpoint: str) -> Dict[str, Any]:
    """Fetch data from API endpoint."""
    try:
        response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        console.print(f"[red]Error fetching {endpoint}: {e}[/red]")
        return {}


def format_currency(value: float) -> str:
    """Format currency with color based on positive/negative."""
    if value > 0:
        return f"[green]+${value:.2f}[/green]"
    elif value < 0:
        return f"[red]${value:.2f}[/red]"
    else:
        return f"${value:.2f}"


def format_percentage(value: float) -> str:
    """Format percentage with color."""
    if value > 0:
        return f"[green]+{value:.2f}%[/green]"
    elif value < 0:
        return f"[red]{value:.2f}%[/red]"
    else:
        return f"{value:.2f}%"


def create_header(uptime: str, last_update: str) -> Panel:
    """Create header panel."""
    header_text = Text()
    header_text.append("🏆 LLM TRADING COMPETITION - LIVE MONITOR 🏆\n", style="bold cyan")
    header_text.append(f"Uptime: {uptime} | Last Update: {last_update}", style="dim")

    return Panel(
        header_text,
        box=box.DOUBLE,
        style="cyan",
        padding=(0, 2)
    )


def create_leaderboard_table(leaderboard_data: List[Dict[str, Any]]) -> Table:
    """Create leaderboard table."""
    table = Table(
        title="📊 LEADERBOARD",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold magenta",
        title_style="bold yellow"
    )

    table.add_column("Rank", justify="center", style="cyan", width=6)
    table.add_column("LLM", justify="left", style="bold", width=8)
    table.add_column("Equity", justify="right", width=12)
    table.add_column("PnL", justify="right", width=12)
    table.add_column("PnL %", justify="right", width=10)
    table.add_column("Trades", justify="center", width=8)
    table.add_column("Win Rate", justify="right", width=10)
    table.add_column("Open Pos", justify="center", width=10)

    medals = ["🥇", "🥈", "🥉"]

    for idx, llm in enumerate(leaderboard_data, 1):
        rank = medals[idx - 1] if idx <= 3 else f"{idx}"

        # Color code LLM names
        llm_name = llm["llm_id"]
        if llm_name == "LLM-A":
            llm_style = "blue"
        elif llm_name == "LLM-B":
            llm_style = "green"
        else:
            llm_style = "yellow"

        table.add_row(
            rank,
            f"[{llm_style}]{llm_name}[/{llm_style}]",
            f"${llm['equity_usdt']:.2f}",
            format_currency(llm['total_pnl']),
            format_percentage(llm['total_pnl_pct']),
            str(llm['total_trades']),
            f"{llm['win_rate']:.1f}%",
            str(llm['open_positions'])
        )

    return table


def create_summary_panel(summary: Dict[str, Any]) -> Panel:
    """Create summary statistics panel."""
    text = Text()

    total_equity = summary.get("total_equity_usdt", 0)
    total_pnl = summary.get("total_pnl", 0)
    total_pnl_pct = summary.get("total_pnl_pct", 0)
    total_trades = summary.get("total_trades", 0)
    avg_win_rate = summary.get("average_win_rate", 0)

    text.append("💰 Total Portfolio: ", style="bold")
    text.append(f"${total_equity:.2f}\n", style="cyan")

    text.append("📈 Total PnL: ", style="bold")
    if total_pnl > 0:
        text.append(f"+${total_pnl:.2f} ({total_pnl_pct:+.2f}%)\n", style="green")
    else:
        text.append(f"${total_pnl:.2f} ({total_pnl_pct:.2f}%)\n", style="red")

    text.append("🎯 Total Trades: ", style="bold")
    text.append(f"{total_trades}\n", style="white")

    text.append("✨ Avg Win Rate: ", style="bold")
    text.append(f"{avg_win_rate:.1f}%", style="yellow")

    return Panel(text, title="📊 Overall Statistics", box=box.ROUNDED, border_style="green")


def create_recent_trades_table(trades: List[Dict[str, Any]]) -> Table:
    """Create recent trades table."""
    table = Table(
        title="💼 RECENT TRADES",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
        title_style="bold yellow"
    )

    table.add_column("Time", justify="left", width=10)
    table.add_column("LLM", justify="left", width=8)
    table.add_column("Symbol", justify="left", width=10)
    table.add_column("Side", justify="center", width=6)
    table.add_column("Entry", justify="right", width=10)
    table.add_column("Exit", justify="right", width=10)
    table.add_column("PnL", justify="right", width=12)
    table.add_column("Reason", justify="left")

    for trade in trades[:10]:  # Show last 10 trades
        side_style = "green" if trade["side"] == "LONG" else "red"
        pnl_value = trade.get("pnl_usdt", 0)

        # Parse closed_at timestamp
        try:
            closed_dt = datetime.fromisoformat(trade["closed_at"].replace("Z", "+00:00"))
            time_str = closed_dt.strftime("%H:%M:%S")
        except:
            time_str = "N/A"

        table.add_row(
            time_str,
            trade["llm_id"],
            trade["symbol"],
            f"[{side_style}]{trade['side']}[/{side_style}]",
            f"${trade['entry_price']:.4f}",
            f"${trade['exit_price']:.4f}",
            format_currency(pnl_value),
            trade.get("exit_reason", "N/A")[:20]
        )

    return table


def create_open_positions_table(positions_data: Dict[str, List[Dict[str, Any]]]) -> Table:
    """Create open positions table."""
    table = Table(
        title="🎯 OPEN POSITIONS",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold green",
        title_style="bold yellow"
    )

    table.add_column("LLM", justify="left", width=8)
    table.add_column("Symbol", justify="left", width=10)
    table.add_column("Side", justify="center", width=6)
    table.add_column("Entry", justify="right", width=10)
    table.add_column("Quantity", justify="right", width=10)
    table.add_column("Leverage", justify="center", width=8)
    table.add_column("Unrealized PnL", justify="right", width=14)
    table.add_column("ROI %", justify="right", width=10)

    total_positions = 0
    for llm_id, positions in positions_data.items():
        for pos in positions:
            side_style = "green" if pos["side"] == "LONG" else "red"
            unrealized_pnl = pos.get("unrealized_pnl_usd", 0)
            roi_pct = pos.get("roi_pct", 0)

            table.add_row(
                llm_id,
                pos["symbol"],
                f"[{side_style}]{pos['side']}[/{side_style}]",
                f"${pos['entry_price']:.4f}",
                f"{pos['quantity']:.2f}",
                f"{pos['leverage']}x",
                format_currency(unrealized_pnl),
                format_percentage(roi_pct)
            )
            total_positions += 1

    if total_positions == 0:
        table.add_row("—", "No open positions", "—", "—", "—", "—", "—", "—")

    return table


def create_market_snapshot_table(market_data: Dict[str, Any]) -> Table:
    """Create market snapshot table."""
    table = Table(
        title="📈 MARKET SNAPSHOT",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold blue",
        title_style="bold yellow"
    )

    table.add_column("Symbol", justify="left", width=12)
    table.add_column("Price", justify="right", width=12)
    table.add_column("24h Change", justify="right", width=12)

    if not market_data:
        table.add_row("—", "No data", "—")
        return table

    for symbol, price in market_data.items():
        # For now just show price, we'd need 24h data from another endpoint
        table.add_row(
            symbol.replace("USDT", ""),
            f"${price:.4f}",
            "—"
        )

    return table


def create_dashboard() -> Layout:
    """Create the main dashboard layout."""
    # Fetch data from API
    leaderboard_data = get_api_data("/trading/leaderboard")
    positions_response = get_api_data("/trading/positions")
    positions_data = positions_response.get("positions", {}) if positions_response else {}
    market_prices = get_api_data("/market/prices")

    # Get leaderboard and summary
    leaderboard = leaderboard_data.get("leaderboard", [])
    summary = leaderboard_data.get("summary", {})

    # Get recent trades (we'll need to add this endpoint or get from leaderboard)
    recent_trades = []  # For now empty, can add endpoint later

    # Calculate uptime (mock for now)
    start_time = datetime.now() - timedelta(hours=2, minutes=15)
    uptime = str(datetime.now() - start_time).split('.')[0]
    last_update = datetime.now().strftime("%H:%M:%S")

    # Create layout
    layout = Layout()

    layout.split_column(
        Layout(create_header(uptime, last_update), size=3),
        Layout(name="main")
    )

    layout["main"].split_row(
        Layout(name="left"),
        Layout(name="right")
    )

    layout["left"].split_column(
        Layout(create_leaderboard_table(leaderboard), size=12),
        Layout(create_summary_panel(summary), size=8)
    )

    layout["right"].split_column(
        Layout(create_open_positions_table(positions_data)),
        Layout(create_market_snapshot_table(market_prices), size=12)
    )

    return layout


def main():
    """Main monitor loop."""
    console.clear()
    console.print("\n[bold cyan]🚀 Starting LLM Trading Monitor...[/bold cyan]\n")
    console.print(f"[dim]Connecting to API: {API_BASE_URL}[/dim]")
    console.print(f"[dim]Refresh interval: {REFRESH_INTERVAL} seconds[/dim]\n")

    # Test API connection
    try:
        health = get_api_data("/health")
        if health:
            console.print("[green]✓ Connected to trading system[/green]\n")
        else:
            console.print("[red]✗ Failed to connect to API. Is the server running?[/red]")
            console.print(f"[yellow]Start the server with: python3 scripts/start.py[/yellow]\n")
            sys.exit(1)
    except Exception as e:
        console.print(f"[red]✗ Connection error: {e}[/red]")
        sys.exit(1)

    # Start live dashboard
    try:
        with Live(create_dashboard(), refresh_per_second=1/REFRESH_INTERVAL, console=console) as live:
            while True:
                time.sleep(REFRESH_INTERVAL)
                live.update(create_dashboard())
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Monitor stopped by user[/yellow]")
        sys.exit(0)


if __name__ == "__main__":
    main()
