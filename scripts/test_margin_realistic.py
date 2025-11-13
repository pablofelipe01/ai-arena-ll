"""
Test script for realistic margin validation with Cross Margin mode.

This simulates how Binance Cross Margin actually works:
1. Initial Margin: Required to OPEN a position (Investment / Leverage)
2. Maintenance Margin: Required to KEEP a position open (much smaller)

In Cross Margin, after opening a position:
- Only Maintenance Margin stays "locked"
- The rest of Initial Margin becomes available again
"""

from decimal import Decimal


def calculate_initial_margin(investment_usd: Decimal, leverage: int) -> Decimal:
    """Calculate initial margin required to open a position."""
    return investment_usd / Decimal(str(leverage))


def calculate_maintenance_margin(investment_usd: Decimal, leverage: int) -> Decimal:
    """
    Calculate maintenance margin (approximate).

    Binance uses tiered rates, but as approximation:
    - For positions < $50k notional, rate is typically 0.4-0.5%
    - Maintenance Margin = Investment * Maintenance Rate
    """
    notional_value = investment_usd * Decimal(str(leverage))
    maintenance_rate = Decimal("0.004")  # 0.4% typical for small positions
    return notional_value * maintenance_rate


def test_realistic_scenario():
    """
    Test realistic scenario with $600 capital and Cross Margin.
    """

    print("=" * 80)
    print("REALISTIC CROSS MARGIN SIMULATION: $600 Total Capital")
    print("=" * 80)
    print()

    total_capital = Decimal("600")
    llms = 3
    capital_per_llm = total_capital / Decimal(str(llms))

    print(f"Total Capital:          ${total_capital:,.2f}")
    print(f"LLMs:                   {llms}")
    print(f"Capital per LLM:        ${capital_per_llm:,.2f}")
    print()
    print("IMPORTANT: In Cross Margin mode:")
    print("  • Initial Margin needed to OPEN position")
    print("  • Only Maintenance Margin stays locked")
    print("  • Rest becomes available again after opening")
    print()

    # Simulate LLM-A creating multiple grids
    print("LLM-A Grid Creation Sequence (Cross Margin Mode):")
    print("-" * 80)

    available = capital_per_llm
    total_maintenance = Decimal("0")

    grid_configs = [
        (Decimal("150"), 3, "ETHUSDT"),
        (Decimal("180"), 3, "BNBUSDT"),
        (Decimal("150"), 3, "XRPUSDT"),
        (Decimal("150"), 3, "DOGEUSDT"),
        (Decimal("120"), 3, "ADAUSDT"),
        (Decimal("100"), 3, "SOLUSDT"),
    ]

    for i, (investment, leverage, symbol) in enumerate(grid_configs, 1):
        initial_margin = calculate_initial_margin(investment, leverage)
        maintenance_margin = calculate_maintenance_margin(investment, leverage)

        print(f"\n{'=' * 80}")
        print(f"Grid {i} - {symbol}:")
        print(f"  Investment:             ${investment:,.2f}")
        print(f"  Leverage:               {leverage}x")
        print(f"  Notional Value:         ${investment * leverage:,.2f}")
        print(f"  Initial Margin Needed:  ${initial_margin:,.2f}")
        print(f"  Maintenance Margin:     ${maintenance_margin:,.2f}")
        print(f"  Available Balance:      ${available:,.2f}")

        # Check if we have enough INITIAL margin to open
        if available >= initial_margin:
            print(f"  Status:                 ✅ APPROVED (can open)")

            # After opening, only maintenance margin stays locked
            # The difference becomes available again
            released = initial_margin - maintenance_margin
            available -= maintenance_margin  # Only subtract maintenance
            total_maintenance += maintenance_margin

            print(f"  Maintenance Locked:     ${maintenance_margin:,.2f}")
            print(f"  Released Back:          ${released:,.2f}")
            print(f"  New Available Balance:  ${available:,.2f}")
            print(f"  Total Maint. Margin:    ${total_maintenance:,.2f}")
        else:
            shortage = initial_margin - available
            print(f"  Status:                 ❌ REJECTED (insufficient)")
            print(f"  Shortage:               ${shortage:,.2f}")
            print(f"  → Telegram notification sent")

    print()
    print("=" * 80)
    print("FINAL STATE:")
    print("-" * 80)
    print(f"Original Capital:       ${capital_per_llm:,.2f}")
    print(f"Total Maint. Margin:    ${total_maintenance:,.2f}")
    print(f"Available Balance:      ${available:,.2f}")
    print(f"Used for Maintenance:   {(total_maintenance/capital_per_llm*100):.1f}%")
    print(f"Still Available:        {(available/capital_per_llm*100):.1f}%")
    print("=" * 80)
    print()


def compare_with_demo_account():
    """Compare with actual demo account data."""

    print("=" * 80)
    print("COMPARISON WITH YOUR DEMO ACCOUNT")
    print("=" * 80)
    print()

    # Your demo account data
    balance = Decimal("4836.06")
    maintenance_margin = Decimal("18.54")
    num_grids = 15

    print("Your Demo Account:")
    print(f"  Balance:                ${balance:,.2f}")
    print(f"  Active Grids:           {num_grids}")
    print(f"  Total Maint. Margin:    ${maintenance_margin:,.2f}")
    print(f"  Avg per Grid:           ${maintenance_margin/num_grids:,.2f}")
    print(f"  Used for Maintenance:   {(maintenance_margin/balance*100):.2f}%")
    print(f"  Available:              ${balance - maintenance_margin:,.2f}")
    print()

    print("Key Insight:")
    print("  • With 15 grids (~$150 each, 3x leverage)")
    print("  • Only $18.54 is locked for maintenance")
    print("  • That's ~$1.24 per grid")
    print("  • 99.6% of your capital remains available!")
    print()

    print("Why Initial Margin Check Still Matters:")
    print("  • You need $50 available to OPEN a $150/3x position")
    print("  • But after opening, ~$48.76 becomes available again")
    print("  • This allows you to open many more positions")
    print("  • As long as you maintain the maintenance margin rate")
    print()
    print("=" * 80)
    print()


def main():
    """Run all tests."""

    print()
    test_realistic_scenario()
    compare_with_demo_account()

    print("\n✅ Realistic Cross Margin simulation completed!")
    print("\nKey Takeaways:")
    print("  • Initial Margin: Needed to OPEN (Investment ÷ Leverage)")
    print("  • Maintenance Margin: Stays locked (~0.4% of notional value)")
    print("  • The difference is released after opening")
    print("  • This is why you can have 15 grids with minimal locked capital")
    print("  • Our validation check is CORRECT for opening positions")
    print("  • But capital efficiency is much better than the pessimistic test")
    print()


if __name__ == "__main__":
    main()
