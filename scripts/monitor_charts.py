#!/usr/bin/env python3
"""
LLM Trading Competition - Live Monitor with Charts
Real-time terminal dashboard with performance charts
"""

import requests
import time
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any
from collections import defaultdict

from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich import box

import plotext as plt

# API Configuration
API_BASE_URL = "http://localhost:8000"
REFRESH_INTERVAL = 30  # seconds

console = Console()

# Store historical data
equity_history = defaultdict(list)
timestamp_history = []


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


def create_equity_chart(leaderboard: List[Dict[str, Any]]) -> str:
    """Create equity performance chart using plotext."""
    global equity_history, timestamp_history

    # Record current equity
    current_time = datetime.now()
    timestamp_history.append(current_time)

    for llm in leaderboard:
        llm_id = llm["llm_id"]
        equity_history[llm_id].append(llm["equity_usdt"])

    # Keep only last 20 data points
    if len(timestamp_history) > 20:
        timestamp_history = timestamp_history[-20:]
        for llm_id in equity_history:
            equity_history[llm_id] = equity_history[llm_id][-20:]

    # Create chart
    plt.clf()
    plt.theme('dark')
    plt.title("LLM Equity Performance Over Time")

    # Plot each LLM
    colors = ['cyan', 'green', 'yellow']
    for idx, llm in enumerate(leaderboard):
        llm_id = llm["llm_id"]
        if llm_id in equity_history and len(equity_history[llm_id]) > 0:
            x_data = list(range(len(equity_history[llm_id])))
            plt.plot(x_data, equity_history[llm_id], label=llm_id, marker="braille")

    plt.xlabel("Time Points")
    plt.ylabel("Equity (USDT)")
    plt.plotsize(80, 15)

    return plt.build()


def create_pnl_bar_chart(leaderboard: List[Dict[str, Any]]) -> str:
    """Create PnL bar chart."""
    plt.clf()
    plt.theme('dark')
    plt.title("Current PnL by LLM")

    llm_ids = [llm["llm_id"] for llm in leaderboard]
    pnls = [llm["total_pnl"] for llm in leaderboard]

    # Color bars based on positive/negative
    colors = ['green+' if pnl > 0 else 'red+' if pnl < 0 else 'white+' for pnl in pnls]

    plt.bar(llm_ids, pnls, color=colors)
    plt.xlabel("LLM")
    plt.ylabel("PnL (USDT)")
    plt.plotsize(80, 12)

    return plt.build()


def create_win_rate_chart(leaderboard: List[Dict[str, Any]]) -> str:
    """Create win rate comparison chart."""
    plt.clf()
    plt.theme('dark')
    plt.title("Win Rate Comparison")

    llm_ids = [llm["llm_id"] for llm in leaderboard]
    win_rates = [llm["win_rate"] for llm in leaderboard]

    plt.bar(llm_ids, win_rates, color='cyan+')
    plt.xlabel("LLM")
    plt.ylabel("Win Rate (%)")
    plt.ylim(0, 100)
    plt.plotsize(80, 12)

    return plt.build()


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


def create_dashboard() -> Layout:
    """Create the main dashboard layout."""
    # Fetch data from API
    leaderboard_data = get_api_data("/trading/leaderboard")

    # Get leaderboard and summary
    leaderboard = leaderboard_data.get("leaderboard", [])
    summary = leaderboard_data.get("summary", {})

    # Calculate uptime (mock for now)
    start_time = datetime.now() - timedelta(hours=2, minutes=15)
    uptime = str(datetime.now() - start_time).split('.')[0]
    last_update = datetime.now().strftime("%H:%M:%S")

    # Create layout
    layout = Layout()

    layout.split_column(
        Layout(create_header(uptime, last_update), name="header", size=3),
        Layout(name="body")
    )

    # Split body into charts and data
    layout["body"].split_column(
        Layout(name="charts", ratio=2),
        Layout(name="data", ratio=1)
    )

    # Create charts if we have data
    if leaderboard and len(equity_history) > 0:
        equity_chart = create_equity_chart(leaderboard)
        pnl_chart = create_pnl_bar_chart(leaderboard)
        win_rate_chart = create_win_rate_chart(leaderboard)

        layout["charts"].split_row(
            Layout(Panel(equity_chart, title="📈 Equity Over Time", border_style="cyan")),
        )

        layout["data"].split_column(
            Layout(create_leaderboard_table(leaderboard), ratio=2),
            Layout(name="bottom_row", ratio=1)
        )

        layout["data"]["bottom_row"].split_row(
            Layout(create_summary_panel(summary)),
            Layout(Panel(pnl_chart, title="💰 Current PnL", border_style="green")),
            Layout(Panel(win_rate_chart, title="🎯 Win Rates", border_style="yellow"))
        )
    else:
        # First run - no charts yet
        layout["charts"].update(
            Panel(
                "[yellow]Collecting data... Charts will appear after first update[/yellow]",
                title="📊 Performance Charts",
                border_style="yellow"
            )
        )

        layout["data"].split_row(
            Layout(create_leaderboard_table(leaderboard)),
            Layout(create_summary_panel(summary))
        )

    return layout


def main():
    """Main monitor loop."""
    console.clear()
    console.print("\n[bold cyan]🚀 Starting LLM Trading Monitor with Charts...[/bold cyan]\n")
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
        with Live(create_dashboard(), refresh_per_second=1/REFRESH_INTERVAL, console=console, screen=True) as live:
            while True:
                time.sleep(REFRESH_INTERVAL)
                live.update(create_dashboard())
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Monitor stopped by user[/yellow]")
        sys.exit(0)


if __name__ == "__main__":
    main()
