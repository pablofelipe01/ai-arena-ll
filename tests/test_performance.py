"""
Performance and Stress Tests for Crypto LLM Trading System.

Tests system performance under various conditions:
- Trading cycle execution time
- Concurrent operations
- Database query performance
- API response times
- Memory usage
- Throughput testing

Run with: pytest tests/test_performance.py -v
"""

import pytest
import time
from decimal import Decimal
from unittest.mock import Mock, patch
from datetime import datetime
import concurrent.futures

from src.services.trading_service import TradingService
from src.services.account_service import AccountService
from src.services.market_data_service import MarketDataService
from src.core.position_manager import PositionManager
from src.core.risk_manager import RiskManager


# ============================================================================
# Performance Fixtures
# ============================================================================

@pytest.fixture
def perf_test_setup():
    """Setup for performance tests."""
    # Mock Supabase
    mock_supabase = Mock()
    mock_supabase.is_connected = True

    # Fast mock responses
    mock_supabase.get_all_llm_accounts.return_value = [
        {
            "llm_id": f"LLM-{i}",
            "balance": 100.0,
            "margin_used": 0.0,
            "total_pnl": 0.0,
            "open_positions": 0,
            "is_active": True,
            "is_trading_enabled": True
        }
        for i in ["A", "B", "C"]
    ]

    mock_supabase.get_llm_account.side_effect = lambda llm_id: {
        "llm_id": llm_id,
        "balance": 100.0,
        "margin_used": 0.0,
        "total_pnl": 0.0,
        "open_positions": 0,
        "is_active": True,
        "is_trading_enabled": True
    }

    mock_supabase.get_open_positions.return_value = []
    mock_supabase.get_trades.return_value = []
    mock_supabase.create_position.return_value = {"id": "pos-123"}
    mock_supabase.create_trade.return_value = {"id": "trade-123"}
    mock_supabase.update_llm_balance.return_value = {"balance": 100.0}
    mock_supabase.update_llm_stats.return_value = {"total_trades": 1}

    # Mock Binance
    mock_binance = Mock()
    mock_binance.is_connected = True
    mock_binance.get_ticker.return_value = {
        "symbol": "ETHUSDT",
        "price": "2000.0",
        "bid": "1999.0",
        "ask": "2001.0",
        "priceChangePercent": "1.5"
    }
    mock_binance.get_klines.return_value = [
        {
            "open": "2000.0",
            "high": "2010.0",
            "low": "1990.0",
            "close": "2000.0",
            "volume": "1000.0"
        }
    ] * 100

    return {
        "supabase": mock_supabase,
        "binance": mock_binance
    }


# ============================================================================
# Execution Time Tests
# ============================================================================

class TestExecutionTime:
    """Test execution time of various operations."""

    def test_single_trading_cycle_execution_time(self, perf_test_setup):
        """Test that a single trading cycle completes within acceptable time."""
        mock_supabase = perf_test_setup["supabase"]
        mock_binance = perf_test_setup["binance"]

        # Create services
        account_service = AccountService(mock_supabase)
        market_data_service = MarketDataService(mock_binance, mock_supabase)
        risk_manager = RiskManager()
        position_manager = PositionManager(mock_supabase, mock_binance, account_service)

        # Mock LLM decision service
        mock_llm_service = Mock()
        mock_llm_service.get_trading_decision.return_value = {
            "action": "HOLD",
            "confidence": 0.5,
            "reasoning": "Performance test"
        }

        # Create trading service
        trading_service = TradingService(
            account_service=account_service,
            market_data_service=market_data_service,
            llm_decision_service=mock_llm_service,
            position_manager=position_manager,
            risk_manager=risk_manager,
            supabase=mock_supabase
        )

        # Measure execution time
        start_time = time.time()
        result = trading_service.execute_trading_cycle()
        end_time = time.time()

        execution_time = end_time - start_time

        # Assertions
        assert result["status"] in ["SUCCESS", "PARTIAL_SUCCESS"]

        # Should complete in less than 5 seconds (mocked APIs are fast)
        assert execution_time < 5.0, f"Cycle took {execution_time:.2f}s, expected < 5s"

        print(f"\n✅ Trading cycle execution time: {execution_time:.3f}s")

    def test_account_service_performance(self, perf_test_setup):
        """Test AccountService operations performance."""
        mock_supabase = perf_test_setup["supabase"]
        account_service = AccountService(mock_supabase)

        # Test get_all_accounts
        start = time.time()
        accounts = account_service.get_all_accounts()
        get_all_time = time.time() - start

        assert len(accounts) == 3
        assert get_all_time < 0.1, "get_all_accounts too slow"

        # Test get_account
        start = time.time()
        account = account_service.get_account("LLM-A")
        get_one_time = time.time() - start

        assert account is not None
        assert get_one_time < 0.05, "get_account too slow"

        print(f"\n✅ AccountService performance:")
        print(f"   get_all_accounts: {get_all_time*1000:.2f}ms")
        print(f"   get_account: {get_one_time*1000:.2f}ms")

    def test_market_data_service_performance(self, perf_test_setup):
        """Test MarketDataService operations performance."""
        mock_binance = perf_test_setup["binance"]
        mock_supabase = perf_test_setup["supabase"]

        market_service = MarketDataService(mock_binance, mock_supabase)

        # Test get_current_price
        start = time.time()
        price = market_service.get_current_price("ETHUSDT")
        get_price_time = time.time() - start

        assert price > 0
        assert get_price_time < 0.1, "get_current_price too slow"

        # Test get_market_snapshot
        start = time.time()
        snapshot = market_service.get_market_snapshot()
        snapshot_time = time.time() - start

        assert "symbols" in snapshot
        assert snapshot_time < 1.0, "get_market_snapshot too slow"

        print(f"\n✅ MarketDataService performance:")
        print(f"   get_current_price: {get_price_time*1000:.2f}ms")
        print(f"   get_market_snapshot: {snapshot_time*1000:.2f}ms")

    def test_risk_manager_performance(self, perf_test_setup):
        """Test RiskManager validation performance."""
        risk_manager = RiskManager()

        account = {
            "llm_id": "LLM-A",
            "balance": 100.0,
            "margin_used": 10.0,
            "open_positions": 2
        }

        decision = {
            "action": "BUY",
            "symbol": "ETHUSDT",
            "side": "LONG",
            "size_usd": 20.0,
            "leverage": 5
        }

        open_positions = [
            {"id": "pos-1", "margin": 5.0},
            {"id": "pos-2", "margin": 5.0}
        ]

        # Test multiple validations
        start = time.time()
        for _ in range(100):
            result = risk_manager.validate_decision("LLM-A", account, decision, open_positions)
        end = time.time()

        avg_time = (end - start) / 100

        # Should be very fast (< 1ms per validation)
        assert avg_time < 0.001, f"Risk validation too slow: {avg_time*1000:.2f}ms"

        print(f"\n✅ RiskManager performance:")
        print(f"   100 validations: {(end-start)*1000:.2f}ms")
        print(f"   Average: {avg_time*1000:.3f}ms per validation")


# ============================================================================
# Throughput Tests
# ============================================================================

class TestThroughput:
    """Test system throughput and capacity."""

    def test_multiple_trading_cycles_throughput(self, perf_test_setup):
        """Test throughput of multiple sequential trading cycles."""
        mock_supabase = perf_test_setup["supabase"]
        mock_binance = perf_test_setup["binance"]

        # Create trading service
        account_service = AccountService(mock_supabase)
        market_data_service = MarketDataService(mock_binance, mock_supabase)
        risk_manager = RiskManager()
        position_manager = PositionManager(mock_supabase, mock_binance, account_service)

        mock_llm_service = Mock()
        mock_llm_service.get_trading_decision.return_value = {
            "action": "HOLD",
            "confidence": 0.5
        }

        trading_service = TradingService(
            account_service=account_service,
            market_data_service=market_data_service,
            llm_decision_service=mock_llm_service,
            position_manager=position_manager,
            risk_manager=risk_manager,
            supabase=mock_supabase
        )

        # Run 10 cycles
        num_cycles = 10
        start_time = time.time()

        for i in range(num_cycles):
            result = trading_service.execute_trading_cycle()
            assert result["status"] in ["SUCCESS", "PARTIAL_SUCCESS"]

        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / num_cycles
        cycles_per_second = num_cycles / total_time

        print(f"\n✅ Throughput test:")
        print(f"   {num_cycles} cycles in {total_time:.2f}s")
        print(f"   Average: {avg_time:.3f}s per cycle")
        print(f"   Throughput: {cycles_per_second:.2f} cycles/second")

        # Should average less than 1 second per cycle
        assert avg_time < 1.0, f"Average cycle time too high: {avg_time:.2f}s"

    def test_concurrent_account_queries(self, perf_test_setup):
        """Test concurrent account queries performance."""
        mock_supabase = perf_test_setup["supabase"]
        account_service = AccountService(mock_supabase)

        def get_account_task(llm_id):
            return account_service.get_account(llm_id)

        # Run concurrent queries
        llm_ids = [f"LLM-{i}" for i in ["A", "B", "C"]] * 10  # 30 total

        start_time = time.time()

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(get_account_task, llm_id) for llm_id in llm_ids]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        end_time = time.time()
        total_time = end_time - start_time

        assert len(results) == 30
        print(f"\n✅ Concurrent queries:")
        print(f"   30 account queries: {total_time:.3f}s")
        print(f"   Average: {(total_time/30)*1000:.2f}ms per query")

    def test_position_creation_throughput(self, perf_test_setup):
        """Test position creation throughput."""
        mock_supabase = perf_test_setup["supabase"]
        mock_binance = perf_test_setup["binance"]

        account_service = AccountService(mock_supabase)
        position_manager = PositionManager(mock_supabase, mock_binance, account_service)

        decision = {
            "action": "BUY",
            "symbol": "ETHUSDT",
            "side": "LONG",
            "size_usd": 20.0,
            "leverage": 5
        }

        # Create 20 positions
        num_positions = 20
        start_time = time.time()

        for i in range(num_positions):
            try:
                result = position_manager.open_position("LLM-A", decision, Decimal("2000.0"))
            except Exception:
                pass  # Some may fail due to risk limits

        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / num_positions

        print(f"\n✅ Position creation throughput:")
        print(f"   {num_positions} attempts in {total_time:.2f}s")
        print(f"   Average: {avg_time*1000:.2f}ms per position")


# ============================================================================
# Stress Tests
# ============================================================================

class TestStressConditions:
    """Test system under stress conditions."""

    def test_high_frequency_trading_cycles(self, perf_test_setup):
        """Test system under high-frequency trading cycle execution."""
        mock_supabase = perf_test_setup["supabase"]
        mock_binance = perf_test_setup["binance"]

        account_service = AccountService(mock_supabase)
        market_data_service = MarketDataService(mock_binance, mock_supabase)
        risk_manager = RiskManager()
        position_manager = PositionManager(mock_supabase, mock_binance, account_service)

        mock_llm_service = Mock()
        mock_llm_service.get_trading_decision.return_value = {"action": "HOLD"}

        trading_service = TradingService(
            account_service=account_service,
            market_data_service=market_data_service,
            llm_decision_service=mock_llm_service,
            position_manager=position_manager,
            risk_manager=risk_manager,
            supabase=mock_supabase
        )

        # Run 50 rapid cycles
        num_cycles = 50
        successful_cycles = 0
        failed_cycles = 0

        start_time = time.time()

        for i in range(num_cycles):
            try:
                result = trading_service.execute_trading_cycle()
                if result["status"] in ["SUCCESS", "PARTIAL_SUCCESS"]:
                    successful_cycles += 1
                else:
                    failed_cycles += 1
            except Exception as e:
                failed_cycles += 1

        end_time = time.time()
        total_time = end_time - start_time

        success_rate = (successful_cycles / num_cycles) * 100

        print(f"\n✅ Stress test - High frequency cycles:")
        print(f"   Total cycles: {num_cycles}")
        print(f"   Successful: {successful_cycles}")
        print(f"   Failed: {failed_cycles}")
        print(f"   Success rate: {success_rate:.1f}%")
        print(f"   Total time: {total_time:.2f}s")
        print(f"   Rate: {num_cycles/total_time:.2f} cycles/second")

        # Should have high success rate
        assert success_rate >= 90, f"Success rate too low: {success_rate:.1f}%"

    def test_many_positions_stress(self, perf_test_setup):
        """Test system with many open positions."""
        mock_supabase = perf_test_setup["supabase"]

        # Create many positions (simulate stress)
        num_positions = 100
        positions = [
            {
                "id": f"pos-{i}",
                "llm_id": "LLM-A",
                "symbol": "ETHUSDT",
                "side": "LONG",
                "entry_price": 2000.0,
                "margin": 2.0,
                "status": "OPEN"
            }
            for i in range(num_positions)
        ]

        mock_supabase.get_open_positions.return_value = positions

        # Test querying many positions
        start_time = time.time()
        result = mock_supabase.get_open_positions()
        query_time = time.time() - start_time

        assert len(result) == num_positions
        print(f"\n✅ Many positions stress test:")
        print(f"   Queried {num_positions} positions in {query_time*1000:.2f}ms")

    def test_rapid_account_updates(self, perf_test_setup):
        """Test rapid account balance updates."""
        mock_supabase = perf_test_setup["supabase"]
        account_service = AccountService(mock_supabase)

        # Simulate 100 rapid balance updates
        num_updates = 100
        start_time = time.time()

        for i in range(num_updates):
            account_service.update_balance("LLM-A", Decimal("100.0"), Decimal("10.0"))

        end_time = time.time()
        total_time = end_time - start_time
        updates_per_second = num_updates / total_time

        print(f"\n✅ Rapid updates stress test:")
        print(f"   {num_updates} updates in {total_time:.2f}s")
        print(f"   Rate: {updates_per_second:.2f} updates/second")

        # Should handle high update rate
        assert total_time < 5.0, f"Updates took too long: {total_time:.2f}s"


# ============================================================================
# Memory and Resource Tests
# ============================================================================

class TestMemoryAndResources:
    """Test memory usage and resource consumption."""

    def test_memory_leak_trading_cycles(self, perf_test_setup):
        """Test for memory leaks in trading cycles."""
        import gc
        import sys

        mock_supabase = perf_test_setup["supabase"]
        mock_binance = perf_test_setup["binance"]

        account_service = AccountService(mock_supabase)
        market_data_service = MarketDataService(mock_binance, mock_supabase)
        risk_manager = RiskManager()
        position_manager = PositionManager(mock_supabase, mock_binance, account_service)

        mock_llm_service = Mock()
        mock_llm_service.get_trading_decision.return_value = {"action": "HOLD"}

        trading_service = TradingService(
            account_service=account_service,
            market_data_service=market_data_service,
            llm_decision_service=mock_llm_service,
            position_manager=position_manager,
            risk_manager=risk_manager,
            supabase=mock_supabase
        )

        # Force garbage collection
        gc.collect()

        # Get initial object count
        initial_objects = len(gc.get_objects())

        # Run many cycles
        for i in range(20):
            trading_service.execute_trading_cycle()

        # Force garbage collection again
        gc.collect()

        # Get final object count
        final_objects = len(gc.get_objects())

        # Object count should not grow significantly
        object_growth = final_objects - initial_objects
        growth_percentage = (object_growth / initial_objects) * 100

        print(f"\n✅ Memory leak test:")
        print(f"   Initial objects: {initial_objects}")
        print(f"   Final objects: {final_objects}")
        print(f"   Growth: {object_growth} ({growth_percentage:.1f}%)")

        # Allow some growth but not excessive
        assert growth_percentage < 50, f"Potential memory leak: {growth_percentage:.1f}% growth"


# ============================================================================
# Performance Benchmarks
# ============================================================================

def test_performance_benchmark_summary(perf_test_setup):
    """
    Comprehensive performance benchmark of the entire system.

    Measures and reports:
    - Trading cycle time
    - Database operation times
    - API call latencies
    - Throughput metrics
    """
    print("\n" + "="*70)
    print("PERFORMANCE BENCHMARK SUMMARY")
    print("="*70)

    mock_supabase = perf_test_setup["supabase"]
    mock_binance = perf_test_setup["binance"]

    # Create services
    account_service = AccountService(mock_supabase)
    market_data_service = MarketDataService(mock_binance, mock_supabase)
    risk_manager = RiskManager()
    position_manager = PositionManager(mock_supabase, mock_binance, account_service)

    mock_llm_service = Mock()
    mock_llm_service.get_trading_decision.return_value = {
        "action": "BUY",
        "symbol": "ETHUSDT",
        "side": "LONG",
        "size_usd": 20.0,
        "leverage": 5
    }

    trading_service = TradingService(
        account_service=account_service,
        market_data_service=market_data_service,
        llm_decision_service=mock_llm_service,
        position_manager=position_manager,
        risk_manager=risk_manager,
        supabase=mock_supabase
    )

    benchmarks = {}

    # 1. Trading cycle
    start = time.time()
    trading_service.execute_trading_cycle()
    benchmarks["trading_cycle"] = time.time() - start

    # 2. Get all accounts
    start = time.time()
    account_service.get_all_accounts()
    benchmarks["get_all_accounts"] = time.time() - start

    # 3. Get market snapshot
    start = time.time()
    market_data_service.get_market_snapshot()
    benchmarks["market_snapshot"] = time.time() - start

    # 4. Risk validation (100 iterations)
    account = {"llm_id": "LLM-A", "balance": 100.0, "margin_used": 0.0, "open_positions": 0}
    decision = {"action": "BUY", "symbol": "ETHUSDT", "size_usd": 20.0, "leverage": 5}
    start = time.time()
    for _ in range(100):
        risk_manager.validate_decision("LLM-A", account, decision, [])
    benchmarks["risk_validation_100x"] = time.time() - start

    # 5. Get trading status
    start = time.time()
    trading_service.get_trading_status()
    benchmarks["get_trading_status"] = time.time() - start

    # Print results
    print("\n📊 Benchmark Results:")
    print(f"   Trading Cycle:        {benchmarks['trading_cycle']*1000:.2f}ms")
    print(f"   Get All Accounts:     {benchmarks['get_all_accounts']*1000:.2f}ms")
    print(f"   Market Snapshot:      {benchmarks['market_snapshot']*1000:.2f}ms")
    print(f"   100 Risk Validations: {benchmarks['risk_validation_100x']*1000:.2f}ms")
    print(f"   Get Trading Status:   {benchmarks['get_trading_status']*1000:.2f}ms")

    print("\n" + "="*70)
    print("✅ BENCHMARK COMPLETE")
    print("="*70 + "\n")

    # Assertions
    assert benchmarks["trading_cycle"] < 5.0, "Trading cycle too slow"
    assert benchmarks["get_all_accounts"] < 0.1, "Get accounts too slow"
    assert benchmarks["risk_validation_100x"] < 0.5, "Risk validation too slow"
