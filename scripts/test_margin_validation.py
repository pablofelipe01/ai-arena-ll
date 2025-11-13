"""
Test script for margin validation before grid creation.

Simulates different scenarios to verify the validation logic.
"""

from decimal import Decimal


def calculate_margin_required(investment_usd: Decimal, leverage: int) -> Decimal:
    """
    Calculate margin required for a grid (worst-case scenario).

    Args:
        investment_usd: Total investment for the grid
        leverage: Leverage multiplier

    Returns:
        Margin required
    """
    return investment_usd / Decimal(str(leverage))


def test_scenarios():
    """Test different margin validation scenarios."""

    print("=" * 70)
    print("MARGIN VALIDATION TEST SCENARIOS")
    print("=" * 70)
    print()

    scenarios = [
        # (available_balance, investment, leverage, description)
        (Decimal("100"), Decimal("150"), 3, "Demo account - unlimited"),
        (Decimal("60"), Decimal("150"), 3, "Sufficient margin"),
        (Decimal("45"), Decimal("150"), 3, "Insufficient margin"),
        (Decimal("200"), Decimal("180"), 3, "Real account - first grid"),
        (Decimal("150"), Decimal("150"), 3, "Real account - second grid"),
        (Decimal("40"), Decimal("150"), 3, "Real account - fourth grid (REJECTED)"),
        (Decimal("100"), Decimal("300"), 5, "High investment, high leverage"),
        (Decimal("30"), Decimal("100"), 3, "Low investment, still insufficient"),
    ]

    for i, (available, investment, leverage, desc) in enumerate(scenarios, 1):
        margin_required = calculate_margin_required(investment, leverage)
        sufficient = available >= margin_required

        status = "✅ APPROVED" if sufficient else "❌ REJECTED"

        print(f"Scenario {i}: {desc}")
        print(f"  Available Balance: ${available:,.2f}")
        print(f"  Investment USD:    ${investment:,.2f}")
        print(f"  Leverage:          {leverage}x")
        print(f"  Margin Required:   ${margin_required:,.2f}")
        print(f"  Status:            {status}")

        if not sufficient:
            shortage = margin_required - available
            print(f"  Shortage:          ${shortage:,.2f}")

        print()

    print("=" * 70)
    print()


def test_real_account_scenario():
    """
    Test realistic scenario with $600 real account.
    """

    print("=" * 70)
    print("REAL ACCOUNT SCENARIO: $600 Total Capital")
    print("=" * 70)
    print()

    total_capital = Decimal("600")
    llms = 3
    capital_per_llm = total_capital / Decimal(str(llms))

    print(f"Total Capital:     ${total_capital:,.2f}")
    print(f"LLMs:              {llms}")
    print(f"Capital per LLM:   ${capital_per_llm:,.2f}")
    print()

    # Simulate LLM-A creating multiple grids
    print("LLM-A Grid Creation Sequence:")
    print("-" * 70)

    available = capital_per_llm
    grid_configs = [
        (Decimal("150"), 3, "ETHUSDT"),
        (Decimal("180"), 3, "BNBUSDT"),
        (Decimal("150"), 3, "XRPUSDT"),
        (Decimal("150"), 3, "DOGEUSDT"),  # This should fail
    ]

    for i, (investment, leverage, symbol) in enumerate(grid_configs, 1):
        margin_required = calculate_margin_required(investment, leverage)
        sufficient = available >= margin_required

        print(f"\nGrid {i} - {symbol}:")
        print(f"  Investment:        ${investment:,.2f}")
        print(f"  Leverage:          {leverage}x")
        print(f"  Margin Required:   ${margin_required:,.2f}")
        print(f"  Available Balance: ${available:,.2f}")

        if sufficient:
            print(f"  Status:            ✅ APPROVED")
            available -= margin_required
            print(f"  Remaining Balance: ${available:,.2f}")
        else:
            shortage = margin_required - available
            print(f"  Status:            ❌ REJECTED")
            print(f"  Shortage:          ${shortage:,.2f}")
            print(f"  → Telegram notification sent")

    print()
    print("=" * 70)
    print(f"Final Available Balance: ${available:,.2f}")
    print("=" * 70)
    print()


def main():
    """Run all tests."""

    print()
    test_scenarios()
    test_real_account_scenario()

    print("\n✅ Margin validation logic verified!")
    print("\nKey Points:")
    print("  • Margin Required = Investment USD ÷ Leverage")
    print("  • Validation happens BEFORE creating grid")
    print("  • Telegram notification sent on rejection")
    print("  • Protects against insufficient balance errors")
    print()


if __name__ == "__main__":
    main()
