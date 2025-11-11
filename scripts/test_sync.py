#!/usr/bin/env python3
"""
Test Binance Sync - Verifica que la sincronización funcione correctamente.

Este script:
1. Lee las posiciones reales de Binance
2. Sincroniza las cuentas virtuales
3. Muestra un reporte comparativo
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from decimal import Decimal
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from src.api.dependencies import (
    get_binance_client,
    get_account_service,
    get_market_data_service
)

console = Console()


def main():
    """Test Binance sync functionality."""
    console.print("\n[bold cyan]🔄 Testing Binance Sync[/bold cyan]\n")

    try:
        # Initialize services
        console.print("Initializing services...")
        binance = get_binance_client()
        market_service = get_market_data_service()
        account_service = get_account_service()

        # Get current prices
        console.print("Fetching current prices...")
        current_prices = market_service.get_current_prices(use_cache=False)

        # Get real positions from Binance WITH clientOrderIds
        console.print("\n[yellow]📊 Reading REAL positions from Binance...[/yellow]\n")
        real_positions = binance.get_open_positions_with_client_ids()

        # Display real positions
        if real_positions:
            real_table = Table(
                title="BINANCE REAL POSITIONS",
                box=box.ROUNDED,
                show_header=True,
                header_style="bold green"
            )
            real_table.add_column("LLM Owner", style="magenta")
            real_table.add_column("Symbol", style="cyan")
            real_table.add_column("Side", justify="center")
            real_table.add_column("Quantity", justify="right")
            real_table.add_column("Entry Price", justify="right")
            real_table.add_column("Leverage", justify="center")
            real_table.add_column("Client Order ID", style="dim")

            for pos in real_positions:
                position_amt = Decimal(pos["positionAmt"])
                side = "LONG" if position_amt > 0 else "SHORT"
                side_color = "green" if side == "LONG" else "red"
                quantity = abs(position_amt)
                entry_price = Decimal(pos["entryPrice"])
                leverage = int(pos["leverage"])

                # Extract LLM owner from clientOrderId
                client_order_id = pos.get("clientOrderId", "Unknown")
                llm_owner = "?"
                if client_order_id and "_" in client_order_id:
                    parts = client_order_id.split("_")
                    if len(parts) >= 1:
                        llm_owner = parts[0]

                real_table.add_row(
                    f"[bold]{llm_owner}[/bold]",
                    pos["symbol"],
                    f"[{side_color}]{side}[/{side_color}]",
                    f"{quantity:.4f}",
                    f"${entry_price:.4f}",
                    f"{leverage}x",
                    client_order_id[:30] if client_order_id else "N/A"
                )

            console.print(real_table)
        else:
            console.print("[yellow]No open positions found in Binance[/yellow]")

        # Get virtual positions BEFORE sync
        console.print("\n[yellow]💾 Virtual positions BEFORE sync...[/yellow]\n")
        virtual_before = account_service.get_all_open_positions()

        before_table = Table(
            title="VIRTUAL POSITIONS (BEFORE SYNC)",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold blue"
        )
        before_table.add_column("LLM", style="cyan")
        before_table.add_column("Symbol", style="cyan")
        before_table.add_column("Side", justify="center")
        before_table.add_column("Quantity", justify="right")
        before_table.add_column("Entry Price", justify="right")
        before_table.add_column("Leverage", justify="center")

        total_before = 0
        for llm_id, positions in virtual_before.items():
            for pos in positions:
                side_color = "green" if pos["side"] == "LONG" else "red"
                before_table.add_row(
                    llm_id,
                    pos["symbol"],
                    f"[{side_color}]{pos['side']}[/{side_color}]",
                    f"{pos['quantity']:.4f}",
                    f"${pos['entry_price']:.4f}",
                    f"{pos['leverage']}x"
                )
                total_before += 1

        if total_before > 0:
            console.print(before_table)
        else:
            console.print("[yellow]No virtual positions found[/yellow]")

        # Perform sync
        console.print("\n[bold yellow]⚡ Running Binance sync...[/bold yellow]\n")
        sync_result = account_service.sync_from_binance(current_prices)

        if sync_result.get("success"):
            stats = sync_result.get("stats", {})

            # Build stats text with per-LLM breakdown
            stats_text = f"[green]✓ Sync completed successfully[/green]\n\n"
            stats_text += f"[bold]Total:[/bold]\n"
            stats_text += f"  Positions synced: [cyan]{stats.get('positions_synced', 0)}[/cyan]\n"
            stats_text += f"  Positions added: [green]+{stats.get('positions_added', 0)}[/green]\n"
            stats_text += f"  Positions updated: [yellow]~{stats.get('positions_updated', 0)}[/yellow]\n"
            stats_text += f"  Positions removed: [red]-{stats.get('positions_removed', 0)}[/red]\n"

            # Per-LLM breakdown
            by_llm = stats.get("by_llm", {})
            if by_llm:
                stats_text += "\n[bold]By LLM:[/bold]\n"
                for llm_id, llm_stats in by_llm.items():
                    stats_text += f"  [{llm_id}]: {llm_stats['positions_synced']} positions "
                    stats_text += f"(+{llm_stats['positions_added']} "
                    stats_text += f"~{llm_stats['positions_updated']} "
                    stats_text += f"-{llm_stats['positions_removed']})\n"

            # Display sync stats
            stats_panel = Panel(
                stats_text,
                title="Sync Results",
                border_style="green"
            )
            console.print(stats_panel)

            # Get virtual positions AFTER sync
            console.print("\n[yellow]💾 Virtual positions AFTER sync...[/yellow]\n")
            virtual_after = account_service.get_all_open_positions()

            after_table = Table(
                title="VIRTUAL POSITIONS (AFTER SYNC)",
                box=box.ROUNDED,
                show_header=True,
                header_style="bold magenta"
            )
            after_table.add_column("LLM", style="cyan")
            after_table.add_column("Symbol", style="cyan")
            after_table.add_column("Side", justify="center")
            after_table.add_column("Quantity", justify="right")
            after_table.add_column("Entry Price", justify="right")
            after_table.add_column("Leverage", justify="center")
            after_table.add_column("Unrealized PnL", justify="right")

            total_after = 0
            for llm_id, positions in virtual_after.items():
                for pos in positions:
                    side_color = "green" if pos["side"] == "LONG" else "red"
                    pnl = pos.get("unrealized_pnl_usd", 0)
                    pnl_color = "green" if pnl > 0 else "red" if pnl < 0 else "white"

                    after_table.add_row(
                        llm_id,
                        pos["symbol"],
                        f"[{side_color}]{pos['side']}[/{side_color}]",
                        f"{pos['quantity']:.4f}",
                        f"${pos['entry_price']:.4f}",
                        f"{pos['leverage']}x",
                        f"[{pnl_color}]${pnl:.2f}[/{pnl_color}]"
                    )
                    total_after += 1

            if total_after > 0:
                console.print(after_table)
            else:
                console.print("[yellow]No virtual positions after sync[/yellow]")

            # Summary
            console.print("\n[bold green]✅ Sync test completed![/bold green]")
            console.print(f"Real positions in Binance: {len(real_positions)}")
            console.print(f"Virtual positions before sync: {total_before}")
            console.print(f"Virtual positions after sync: {total_after}")

            if len(real_positions) == total_after:
                console.print("\n[bold green]✓ Virtual positions now match Binance! 🎉[/bold green]\n")
            else:
                console.print("\n[yellow]⚠ Position counts don't match - this may be normal if positions are distributed across multiple LLMs[/yellow]\n")

        else:
            error = sync_result.get("error", "Unknown error")
            console.print(f"\n[bold red]✗ Sync failed: {error}[/bold red]\n")

    except Exception as e:
        console.print(f"\n[bold red]Error: {e}[/bold red]\n")
        import traceback
        console.print(traceback.format_exc())
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
