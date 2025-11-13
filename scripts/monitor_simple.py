#!/usr/bin/env python3
"""
Simple Grid Trading Monitor - Shows real-time info without WebSocket
"""

import requests
import time
import os
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich import box

API_BASE_URL = "http://localhost:8000"
REFRESH_INTERVAL = 10  # seconds

console = Console()


def get_api_data(endpoint: str):
    """Fetch data from API."""
    try:
        response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return None


def create_dashboard():
    """Create the main dashboard layout."""
    # Fetch all data
    leaderboard_data = get_api_data("/trading/leaderboard")
    binance_data = get_api_data("/trading/binance-status")  # Real Binance data
    market_data = get_api_data("/market/prices")
    
    if not leaderboard_data:
        return Panel("[red]✗ Cannot connect to trading system[/red]", title="Error")
    
    # Create layout
    layout = Layout()
    layout.split_column(
        Layout(create_header(), size=3),
        Layout(name="main", ratio=1)
    )
    
    layout["main"].split_row(
        Layout(name="left", ratio=2),
        Layout(name="right", ratio=1)
    )
    
    # Left side
    layout["left"].split_column(
        Layout(create_leaderboard(leaderboard_data)),
        Layout(create_positions(binance_data))
    )

    # Right side
    layout["right"].split_column(
        Layout(create_summary(binance_data)),
        Layout(create_market(market_data))
    )
    
    return layout


def create_header():
    """Create header panel."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    text = f"[bold cyan]⚡ GRID TRADING MONITOR[/bold cyan]  |  {now}  |  Updates every {REFRESH_INTERVAL}s"
    return Panel(text, box=box.DOUBLE, style="cyan")


def create_leaderboard(data):
    """Create leaderboard table."""
    table = Table(
        title="🏆 LEADERBOARD",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold magenta"
    )
    
    table.add_column("LLM", style="cyan", width=8)
    table.add_column("Equity", justify="right", width=12)
    table.add_column("PnL", justify="right", width=12)
    table.add_column("ROI %", justify="right", width=10)
    table.add_column("Positions", justify="center", width=10)
    table.add_column("Trades", justify="center", width=8)
    
    if not data or "leaderboard" not in data:
        table.add_row("—", "No data", "—", "—", "—", "—")
        return table
    
    for llm in data["leaderboard"]:
        pnl = llm["total_pnl"]
        pnl_pct = llm["total_pnl_pct"]
        
        # Color code PnL
        if pnl > 0:
            pnl_str = f"[green]+${pnl:.2f}[/green]"
            pnl_pct_str = f"[green]+{pnl_pct:.2f}%[/green]"
        elif pnl < 0:
            pnl_str = f"[red]${pnl:.2f}[/red]"
            pnl_pct_str = f"[red]{pnl_pct:.2f}%[/red]"
        else:
            pnl_str = f"${pnl:.2f}"
            pnl_pct_str = f"{pnl_pct:.2f}%"
        
        # LLM color
        llm_color = {"LLM-A": "blue", "LLM-B": "green", "LLM-C": "yellow"}.get(llm["llm_id"], "white")
        
        table.add_row(
            f"[{llm_color}]{llm['llm_id']}[/{llm_color}]",
            f"${llm['equity_usdt']:.2f}",
            pnl_str,
            pnl_pct_str,
            str(llm["open_positions"]),
            str(llm["total_trades"])
        )
    
    return table


def create_positions(data):
    """Create positions table from Binance data."""
    table = Table(
        title="📊 OPEN POSITIONS (Live from Binance)",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold green"
    )

    table.add_column("LLM", width=8)
    table.add_column("Symbol", width=10)
    table.add_column("Side", justify="center", width=6)
    table.add_column("Entry", justify="right", width=10)
    table.add_column("Qty", justify="right", width=10)
    table.add_column("Lev", justify="center", width=5)
    table.add_column("PnL", justify="right", width=12)
    table.add_column("ROI%", justify="right", width=8)

    if not data or "positions" not in data:
        table.add_row("—", "No data", "—", "—", "—", "—", "—", "—")
        return table

    total_positions = 0
    for llm_id, positions in data["positions"].items():
        for pos in positions:
            side_style = "green" if pos["side"] == "LONG" else "red"
            pnl = pos.get("unrealized_pnl_usd", 0)
            roi = pos.get("roi_pct", 0)

            pnl_str = f"[green]+${pnl:.2f}[/green]" if pnl > 0 else f"[red]${pnl:.2f}[/red]" if pnl < 0 else f"${pnl:.2f}"
            roi_str = f"[green]+{roi:.2f}%[/green]" if roi > 0 else f"[red]{roi:.2f}%[/red]" if roi < 0 else f"{roi:.2f}%"

            symbol_short = pos["symbol"].replace("USDT", "")

            table.add_row(
                llm_id,
                symbol_short,
                f"[{side_style}]{pos['side']}[/{side_style}]",
                f"${pos['entry_price']:.4f}",
                f"{pos['quantity']:.3f}",
                f"{pos['leverage']}x",
                pnl_str,
                roi_str
            )
            total_positions += 1

    if total_positions == 0:
        table.add_row("—", "No positions", "—", "—", "—", "—", "—", "—")

    return table


def create_summary(data):
    """Create summary panel from Binance data."""
    if not data or "balance" not in data:
        return Panel("[red]No data[/red]", title="📈 Live Summary (Binance)")

    balance = data["balance"]
    total_balance = balance.get("total_balance", 0)
    available_balance = balance.get("available_balance", 0)
    total_unrealized_pnl = balance.get("total_unrealized_pnl", 0)

    # Open orders info
    orders_info = data.get("open_orders", {})
    total_orders = orders_info.get("total", 0)
    orders_by_llm = orders_info.get("by_llm", {})

    # Summary info
    summary_info = data.get("summary", {})
    total_positions = summary_info.get("total_positions", 0)

    # Color code PnL
    if total_unrealized_pnl > 0:
        pnl_color = "green"
        pnl_sign = "+"
    elif total_unrealized_pnl < 0:
        pnl_color = "red"
        pnl_sign = ""
    else:
        pnl_color = "white"
        pnl_sign = ""

    text = f"""[bold]Balance:[/bold] [cyan]${total_balance:.2f}[/cyan]
[bold]Available:[/bold] ${available_balance:.2f}
[bold]Unrealized PnL:[/bold] [{pnl_color}]{pnl_sign}${total_unrealized_pnl:.2f}[/{pnl_color}]

[bold]Positions:[/bold] {total_positions}
[bold]Open Orders:[/bold] {total_orders}
  • LLM-A: {orders_by_llm.get('LLM-A', 0)}
  • LLM-B: {orders_by_llm.get('LLM-B', 0)}
  • LLM-C: {orders_by_llm.get('LLM-C', 0)}"""

    return Panel(text, title="📈 Live Summary (Binance)", box=box.ROUNDED, border_style="green")


def create_market(data):
    """Create market snapshot."""
    table = Table(
        title="💹 Prices",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold blue"
    )
    
    table.add_column("Symbol", width=8)
    table.add_column("Price", justify="right", width=12)
    
    if not data:
        table.add_row("—", "No data")
        return table
    
    for symbol, price in sorted(data.items()):
        symbol_short = symbol.replace("USDT", "")
        table.add_row(symbol_short, f"${price:.4f}")
    
    return table


def main():
    """Main monitor loop."""
    console.clear()
    console.print("\n[bold cyan]🚀 Starting Grid Trading Monitor...[/bold cyan]\n")
    console.print(f"[dim]API: {API_BASE_URL}[/dim]")
    console.print(f"[dim]Refresh: {REFRESH_INTERVAL}s[/dim]\n")
    
    # Test connection
    health = get_api_data("/health")
    if not health:
        console.print("[red]✗ Cannot connect to API. Is the server running?[/red]")
        console.print(f"[yellow]Start with: python3 scripts/start.py[/yellow]\n")
        return
    
    console.print("[green]✓ Connected to trading system[/green]\n")
    time.sleep(1)
    
    # Start live dashboard
    try:
        with Live(create_dashboard(), refresh_per_second=1/REFRESH_INTERVAL, console=console, screen=True) as live:
            while True:
                time.sleep(REFRESH_INTERVAL)
                live.update(create_dashboard())
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Monitor stopped[/yellow]")


if __name__ == "__main__":
    main()
