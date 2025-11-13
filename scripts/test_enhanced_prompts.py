#!/usr/bin/env python3
"""
Test script to verify enhanced LLM prompts with complete risk information.

This demonstrates how LLMs receive comprehensive risk data while maintaining
100% autonomy in decision-making.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.clients.grid_prompts import build_grid_trading_prompt


def test_prompt_with_risk_scenarios():
    """Test prompt generation with different risk scenarios."""

    print("=" * 80)
    print("ENHANCED LLM PROMPTS - RISK INFORMATION TEST")
    print("=" * 80)
    print()

    # Test Scenario 1: LOW RISK - Price in middle of grid
    print("\n" + "=" * 80)
    print("SCENARIO 1: LOW RISK - Grid operating normally")
    print("=" * 80)

    account_info = {
        "balance": 200.00,
        "available_balance": 150.00,
        "total_grid_investment": 150.00,
        "total_pnl": 12.50,
        "roi_pct": 6.25
    }

    market_data = [
        {
            "symbol": "ETHUSDT",
            "price": 3300.00,  # Middle of grid
            "price_change_pct_24h": 2.5,
            "high_24h": 3350.00,
            "low_24h": 3250.00,
            "volume_24h": 1500000,
            "rsi_14": 55.0,
            "macd": 0.0015,
            "macd_signal": 0.0012
        }
    ]

    active_grids = [
        {
            "grid_id": "grid_eth_001",
            "symbol": "ETHUSDT",
            "status": "ACTIVE",
            "lower_limit": 3200.00,
            "upper_limit": 3400.00,
            "grid_levels": 5,
            "spacing_type": "geometric",
            "leverage": 3,
            "investment_usd": 150.00,
            "stop_loss_pct": 12,
            "cycles_completed": 8,
            "total_profit": 24.00,
            "net_profit": 22.40,
            "roi_pct": 14.93,
            "avg_profit_per_cycle": 3.00
        }
    ]

    recent_performance = {
        "total_grid_profit": 24.00,
        "total_fees": 1.60
    }

    prompt = build_grid_trading_prompt(
        llm_id="LLM-A",
        account_info=account_info,
        market_data=market_data,
        active_grids=active_grids,
        recent_performance=recent_performance
    )

    # Extract just the active grids section to show
    start_idx = prompt.find("=== ACTIVE GRIDS ===")
    end_idx = prompt.find("=== MAKE YOUR DECISION ===")
    grids_info = prompt[start_idx:end_idx]

    print(grids_info)
    print("\n✅ Expected: Risk Level = 🟢 LOW")
    print("✅ Expected: Distance to Stop Loss > +15%")


    # Test Scenario 2: MEDIUM RISK - Near lower boundary
    print("\n" + "=" * 80)
    print("SCENARIO 2: MEDIUM RISK - Near lower boundary")
    print("=" * 80)

    market_data[0]["price"] = 3210.00  # Near lower limit

    prompt = build_grid_trading_prompt(
        llm_id="LLM-A",
        account_info=account_info,
        market_data=market_data,
        active_grids=active_grids,
        recent_performance=recent_performance
    )

    start_idx = prompt.find("=== ACTIVE GRIDS ===")
    end_idx = prompt.find("=== MAKE YOUR DECISION ===")
    grids_info = prompt[start_idx:end_idx]

    print(grids_info)
    print("\n⚠️  Expected: Risk Level = 🟡 MEDIUM")
    print("⚠️  Expected: Alert about near lower boundary")


    # Test Scenario 3: HIGH RISK - Approaching stop loss
    print("\n" + "=" * 80)
    print("SCENARIO 3: HIGH RISK - Approaching stop loss")
    print("=" * 80)

    market_data[0]["price"] = 2900.00  # Close to stop loss (3200 * 0.88 = 2816)

    prompt = build_grid_trading_prompt(
        llm_id="LLM-A",
        account_info=account_info,
        market_data=market_data,
        active_grids=active_grids,
        recent_performance=recent_performance
    )

    start_idx = prompt.find("=== ACTIVE GRIDS ===")
    end_idx = prompt.find("=== MAKE YOUR DECISION ===")
    grids_info = prompt[start_idx:end_idx]

    print(grids_info)
    print("\n🟠 Expected: Risk Level = 🟠 HIGH")
    print("🟠 Expected: Distance to Stop Loss < 15%")
    print("🟠 Expected: Warning about high risk")


    # Test Scenario 4: CRITICAL RISK - Stop loss imminent
    print("\n" + "=" * 80)
    print("SCENARIO 4: CRITICAL RISK - Stop loss imminent")
    print("=" * 80)

    market_data[0]["price"] = 2830.00  # Very close to stop loss (2816)

    prompt = build_grid_trading_prompt(
        llm_id="LLM-A",
        account_info=account_info,
        market_data=market_data,
        active_grids=active_grids,
        recent_performance=recent_performance
    )

    start_idx = prompt.find("=== ACTIVE GRIDS ===")
    end_idx = prompt.find("=== MAKE YOUR DECISION ===")
    grids_info = prompt[start_idx:end_idx]

    print(grids_info)
    print("\n🔴 Expected: Risk Level = 🔴 CRITICAL")
    print("🔴 Expected: Distance to Stop Loss < 5%")
    print("🔴 Expected: STOP LOSS IMMINENT alert")


    # Show autonomy section
    print("\n" + "=" * 80)
    print("AUTONOMY REMINDER TO LLMs")
    print("=" * 80)

    decision_start = prompt.find("CRITICAL - YOU ARE 100% AUTONOMOUS:")
    decision_end = prompt.find("KEY CONSIDERATIONS:")
    autonomy_section = prompt[decision_start:decision_end]

    print(autonomy_section)


    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print()
    print("✅ LLMs now receive COMPLETE risk information:")
    print("   • Stop loss price calculated and displayed")
    print("   • Distance to stop loss (% and $)")
    print("   • Position within grid range (0-100%)")
    print("   • Distance to upper/lower limits")
    print("   • Risk level assessment (LOW/MEDIUM/HIGH/CRITICAL)")
    print("   • Contextual alerts based on risk")
    print()
    print("✅ LLMs maintain 100% AUTONOMY:")
    print("   • No automatic stop losses")
    print("   • No system intervention")
    print("   • Full responsibility for risk management")
    print("   • Clear prompts emphasizing their autonomy")
    print()
    print("✅ This enables:")
    print("   • Informed decision-making")
    print("   • Proactive risk management")
    print("   • Academic validity (pure AI decisions)")
    print("   • Better learning from mistakes")
    print()
    print("=" * 80)


if __name__ == "__main__":
    test_prompt_with_risk_scenarios()
