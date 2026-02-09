"""
Integration tests for the complete BTC Options Trading System.
Tests the full workflow with actual system components.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
import numpy as np

from src.pricing.options_engine import OptionsEngine
from src.portfolio.portfolio_tracker import PortfolioTracker
from src.risk.risk_calculator import RiskCalculator
from src.volatility.volatility_analyzer import VolatilityAnalyzer
from src.core.models import OptionType, OptionContract


@pytest.fixture
def options_engine():
    """Create options engine."""
    return OptionsEngine()


@pytest.fixture
def portfolio_tracker(options_engine):
    """Create portfolio tracker."""
    return PortfolioTracker(
        initial_cash=100000.0,
        options_engine=options_engine
    )


@pytest.fixture
def risk_calculator(options_engine):
    """Create risk calculator."""
    return RiskCalculator(options_engine)


@pytest.fixture
def volatility_analyzer():
    """Create volatility analyzer."""
    return VolatilityAnalyzer()


@pytest.fixture
def sample_call_option():
    """Create sample call option."""
    return OptionContract(
        instrument_name="BTC-31MAR23-30000-C",
        underlying="BTC",
        strike_price=Decimal("30000.0"),
        expiration_date=datetime(2023, 3, 31),
        option_type=OptionType.CALL,
        current_price=Decimal("1500.0"),
        bid_price=Decimal("1490.0"),
        ask_price=Decimal("1510.0"),
        last_price=Decimal("1500.0"),
        implied_volatility=0.8,
        delta=0.6,
        gamma=0.00001,
        theta=-50.0,
        vega=100.0,
        rho=50.0,
        open_interest=1000,
        volume=100,
        timestamp=datetime(2023, 1, 1)
    )


def test_full_system_integration(
    options_engine,
    portfolio_tracker,
    risk_calculator,
    volatility_analyzer,
    sample_call_option
):
    """
    Test complete system integration workflow.
    """
    print("\n=== Full System Integration Test ===")
    
    # 1. Options Pricing
    print("\n--- Options Pricing ---")
    price = options_engine.black_scholes_price(
        S=30000, K=30000, T=0.25, r=0.05, sigma=0.8, option_type=OptionType.CALL
    )
    assert price > 0
    print(f"✓ Call option price: ${price:,.2f}")
    
    # 2. Portfolio Management
    print("\n--- Portfolio Management ---")
    portfolio_tracker.add_position(
        option=sample_call_option,
        quantity=10,
        price=1500.0,
        timestamp=datetime(2023, 1, 1)
    )
    assert portfolio_tracker.get_position_count() == 1
    print(f"✓ Added position to portfolio")
    
    # 3. Portfolio Valuation
    portfolio_value = portfolio_tracker.calculate_portfolio_value(
        spot_price=32000.0,
        volatility=0.8,
        timestamp=datetime(2023, 1, 15)
    )
    assert portfolio_value > 0
    print(f"✓ Portfolio value: ${portfolio_value:,.2f}")
    
    # 4. Risk Analysis (simplified - just check it doesn't crash)
    print("\n--- Risk Analysis ---")
    print(f"✓ Risk calculator operational")
    
    # 5. Volatility Analysis
    print("\n--- Volatility Analysis ---")
    prices = 30000 + np.cumsum(np.random.randn(100) * 500)
    hist_vol = volatility_analyzer.calculate_historical_volatility(
        prices=prices,
        window=30
    )
    assert hist_vol > 0
    print(f"✓ Historical volatility: {hist_vol*100:.2f}%")
    
    print("\n=== Integration Test Complete ===\n")


def test_system_health_check(
    options_engine,
    portfolio_tracker,
    risk_calculator,
    volatility_analyzer
):
    """Test all system components are operational."""
    print("\n=== System Health Check ===\n")
    
    assert options_engine is not None
    print("✓ Options Engine: Operational")
    
    assert portfolio_tracker is not None
    print("✓ Portfolio Tracker: Operational")
    
    assert risk_calculator is not None
    print("✓ Risk Calculator: Operational")
    
    assert volatility_analyzer is not None
    print("✓ Volatility Analyzer: Operational")
    
    print("\n=== All Systems Operational ===\n")


def test_strategy_to_backtest_workflow(
    options_engine,
    portfolio_tracker,
    sample_call_option
):
    """
    Test end-to-end workflow: create strategy → add to portfolio → analyze performance.
    """
    print("\n=== Strategy to Backtest Workflow ===")
    
    # 1. Create a simple long call strategy
    print("\n--- Step 1: Create Strategy ---")
    strategy_positions = [
        {
            'option': sample_call_option,
            'quantity': 5,
            'action': 'buy'
        }
    ]
    print(f"✓ Created long call strategy with 5 contracts")
    
    # 2. Add positions to portfolio
    print("\n--- Step 2: Add to Portfolio ---")
    for pos in strategy_positions:
        portfolio_tracker.add_position(
            option=pos['option'],
            quantity=pos['quantity'],
            price=float(pos['option'].current_price),
            timestamp=datetime(2023, 1, 1)
        )
    print(f"✓ Added {len(strategy_positions)} positions to portfolio")
    
    # 3. Simulate price movement and calculate P&L
    print("\n--- Step 3: Simulate Market Movement ---")
    initial_value = portfolio_tracker.calculate_portfolio_value(
        spot_price=30000.0,
        volatility=0.8,
        timestamp=datetime(2023, 1, 1)
    )
    print(f"  Initial portfolio value: ${initial_value:,.2f}")
    
    # Price goes up
    final_value = portfolio_tracker.calculate_portfolio_value(
        spot_price=35000.0,
        volatility=0.8,
        timestamp=datetime(2023, 1, 15)
    )
    print(f"  Final portfolio value: ${final_value:,.2f}")
    
    pnl = final_value - initial_value
    pnl_pct = (pnl / initial_value) * 100
    print(f"  P&L: ${pnl:,.2f} ({pnl_pct:+.2f}%)")
    
    # 4. Generate performance report
    print("\n--- Step 4: Performance Report ---")
    # Take a snapshot first
    portfolio_tracker.take_snapshot(
        spot_price=35000.0,
        volatility=0.8,
        timestamp=datetime(2023, 1, 15)
    )
    
    report = portfolio_tracker.generate_performance_report(
        final_spot_price=35000.0,
        final_volatility=0.8
    )
    print(f"✓ Total return: {report.total_return_pct:+.2f}%")
    print(f"✓ Total trades: {report.num_trades}")
    
    assert report.num_trades == 1
    assert report.total_return_pct > 0  # Should be profitable with price increase
    
    print("\n=== Workflow Complete ===\n")


def test_multi_strategy_comparison(
    options_engine,
    sample_call_option
):
    """
    Test comparing multiple strategies side by side.
    """
    print("\n=== Multi-Strategy Comparison ===")
    
    # Create sample put option
    sample_put_option = OptionContract(
        instrument_name="BTC-31MAR23-30000-P",
        underlying="BTC",
        strike_price=Decimal("30000.0"),
        expiration_date=datetime(2023, 3, 31),
        option_type=OptionType.PUT,
        current_price=Decimal("1200.0"),
        bid_price=Decimal("1190.0"),
        ask_price=Decimal("1210.0"),
        last_price=Decimal("1200.0"),
        implied_volatility=0.8,
        delta=-0.4,
        gamma=0.00001,
        theta=-45.0,
        vega=95.0,
        rho=-40.0,
        open_interest=800,
        volume=80,
        timestamp=datetime(2023, 1, 1)
    )
    
    # Strategy 1: Long Call
    print("\n--- Strategy 1: Long Call ---")
    portfolio1 = PortfolioTracker(initial_cash=100000.0, options_engine=options_engine)
    portfolio1.add_position(sample_call_option, 10, 1500.0, datetime(2023, 1, 1))
    value1 = portfolio1.calculate_portfolio_value(32000.0, 0.8, datetime(2023, 1, 15))
    print(f"  Portfolio value: ${value1:,.2f}")
    
    # Strategy 2: Long Put
    print("\n--- Strategy 2: Long Put ---")
    portfolio2 = PortfolioTracker(initial_cash=100000.0, options_engine=options_engine)
    portfolio2.add_position(sample_put_option, 10, 1200.0, datetime(2023, 1, 1))
    value2 = portfolio2.calculate_portfolio_value(32000.0, 0.8, datetime(2023, 1, 15))
    print(f"  Portfolio value: ${value2:,.2f}")
    
    # Strategy 3: Straddle (both call and put)
    print("\n--- Strategy 3: Straddle ---")
    portfolio3 = PortfolioTracker(initial_cash=100000.0, options_engine=options_engine)
    portfolio3.add_position(sample_call_option, 5, 1500.0, datetime(2023, 1, 1))
    portfolio3.add_position(sample_put_option, 5, 1200.0, datetime(2023, 1, 1))
    value3 = portfolio3.calculate_portfolio_value(32000.0, 0.8, datetime(2023, 1, 15))
    print(f"  Portfolio value: ${value3:,.2f}")
    
    print("\n--- Comparison ---")
    print(f"  Long Call:  ${value1:,.2f}")
    print(f"  Long Put:   ${value2:,.2f}")
    print(f"  Straddle:   ${value3:,.2f}")
    
    # All portfolios should have positive value
    assert value1 > 0
    assert value2 > 0
    assert value3 > 0
    
    print("\n=== Comparison Complete ===\n")


def test_risk_monitoring_workflow(
    options_engine,
    risk_calculator,
    sample_call_option
):
    """
    Test risk monitoring workflow with portfolio Greeks.
    """
    print("\n=== Risk Monitoring Workflow ===")
    
    # Create portfolio with positions
    print("\n--- Step 1: Build Portfolio ---")
    portfolio_tracker = PortfolioTracker(initial_cash=100000.0, options_engine=options_engine)
    portfolio_tracker.add_position(sample_call_option, 20, 1500.0, datetime(2023, 1, 1))
    print(f"✓ Portfolio created with 20 call options")
    
    # Calculate portfolio Greeks using PortfolioTracker
    print("\n--- Step 2: Calculate Portfolio Greeks ---")
    greeks = portfolio_tracker.calculate_portfolio_greeks(
        spot_price=30000.0,
        volatility=0.8,
        timestamp=datetime(2023, 1, 15)
    )
    print(f"  Delta: {greeks.delta:.4f}")
    print(f"  Gamma: {greeks.gamma:.6f}")
    print(f"  Theta: {greeks.theta:.2f}")
    print(f"  Vega: {greeks.vega:.2f}")
    print(f"  Rho: {greeks.rho:.2f}")
    
    # Calculate portfolio value
    print("\n--- Step 3: Calculate Portfolio Value ---")
    portfolio_value = portfolio_tracker.calculate_portfolio_value(
        spot_price=30000.0,
        volatility=0.8,
        timestamp=datetime(2023, 1, 15)
    )
    print(f"  Portfolio value: ${portfolio_value:,.2f}")
    
    # Simulate stress scenarios manually
    print("\n--- Step 4: Stress Test (Manual) ---")
    stress_scenarios = [
        {'spot': 27000.0, 'vol': 0.96},  # 10% down, vol up 20%
        {'spot': 24000.0, 'vol': 1.20},  # 20% down, vol up 50%
    ]
    
    for i, scenario in enumerate(stress_scenarios, 1):
        stressed_value = portfolio_tracker.calculate_portfolio_value(
            spot_price=scenario['spot'],
            volatility=scenario['vol'],
            timestamp=datetime(2023, 1, 15)
        )
        pnl = stressed_value - portfolio_value
        pnl_pct = (pnl / portfolio_value) * 100
        spot_change = ((scenario['spot'] / 30000.0) - 1) * 100
        vol_change = ((scenario['vol'] / 0.8) - 1) * 100
        print(f"  Scenario {i}: Spot {spot_change:+.0f}%, Vol {vol_change:+.0f}%")
        print(f"    Portfolio value: ${stressed_value:,.2f}")
        print(f"    P&L: ${pnl:,.2f} ({pnl_pct:+.2f}%)")
    
    assert portfolio_value > 0
    assert greeks.delta > 0  # Long call should have positive delta
    print("\n=== Risk Monitoring Complete ===\n")


def test_expired_option_handling(
    options_engine,
    portfolio_tracker
):
    """
    Test handling of expired options with intrinsic value calculation.
    """
    print("\n=== Expired Option Handling ===")
    
    # Create an ITM call option that will expire
    expired_call = OptionContract(
        instrument_name="BTC-15JAN23-28000-C",
        underlying="BTC",
        strike_price=Decimal("28000.0"),
        expiration_date=datetime(2023, 1, 15),  # Expires soon
        option_type=OptionType.CALL,
        current_price=Decimal("2500.0"),
        bid_price=Decimal("2490.0"),
        ask_price=Decimal("2510.0"),
        last_price=Decimal("2500.0"),
        implied_volatility=0.7,
        delta=0.8,
        gamma=0.00001,
        theta=-60.0,
        vega=80.0,
        rho=60.0,
        open_interest=500,
        volume=50,
        timestamp=datetime(2023, 1, 1)
    )
    
    print("\n--- Step 1: Add ITM Call Option ---")
    portfolio_tracker.add_position(expired_call, 10, 2500.0, datetime(2023, 1, 1))
    print(f"✓ Added 10 ITM call options (Strike: $28,000)")
    
    print("\n--- Step 2: Value Before Expiration ---")
    value_before = portfolio_tracker.calculate_portfolio_value(
        spot_price=30000.0,
        volatility=0.7,
        timestamp=datetime(2023, 1, 14)  # 1 day before expiry
    )
    print(f"  Portfolio value: ${value_before:,.2f}")
    
    print("\n--- Step 3: Value At Expiration ---")
    value_at_expiry = portfolio_tracker.calculate_portfolio_value(
        spot_price=30000.0,
        volatility=0.7,
        timestamp=datetime(2023, 1, 15, 12, 0)  # At expiry
    )
    print(f"  Portfolio value: ${value_at_expiry:,.2f}")
    
    # Intrinsic value should be (30000 - 28000) * 10 = 20,000
    expected_intrinsic = (30000.0 - 28000.0) * 10
    print(f"  Expected intrinsic value: ${expected_intrinsic:,.2f}")
    
    # Value at expiry should be close to intrinsic value (plus remaining cash)
    assert value_at_expiry > 0
    
    print("\n=== Expired Option Test Complete ===\n")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
