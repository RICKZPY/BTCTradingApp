"""
Tests for Risk Calculator.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
import numpy as np

from src.core.models import OptionContract, Portfolio, Position, OptionType
from src.pricing.options_engine import OptionsEngine
from src.risk.risk_calculator import RiskCalculator


@pytest.fixture
def options_engine():
    """Create options engine for testing."""
    return OptionsEngine()


@pytest.fixture
def risk_calculator(options_engine):
    """Create risk calculator for testing."""
    return RiskCalculator(options_engine)


@pytest.fixture
def sample_portfolio():
    """Create a sample portfolio for testing."""
    expiry = datetime.now() + timedelta(days=30)
    now = datetime.now()
    
    # Long call position
    call_contract = OptionContract(
        instrument_name="BTC-30000-C",
        underlying="BTC",
        option_type=OptionType.CALL,
        strike_price=Decimal("30000"),
        expiration_date=expiry,
        current_price=Decimal("2000"),
        bid_price=Decimal("1950"),
        ask_price=Decimal("2050"),
        last_price=Decimal("2000"),
        implied_volatility=0.8,
        delta=0.5,
        gamma=0.001,
        theta=-50,
        vega=100,
        rho=25,
        open_interest=1000,
        volume=50,
        timestamp=now
    )
    
    # Short put position
    put_contract = OptionContract(
        instrument_name="BTC-28000-P",
        underlying="BTC",
        option_type=OptionType.PUT,
        strike_price=Decimal("28000"),
        expiration_date=expiry,
        current_price=Decimal("1500"),
        bid_price=Decimal("1450"),
        ask_price=Decimal("1550"),
        last_price=Decimal("1500"),
        implied_volatility=0.8,
        delta=-0.4,
        gamma=0.001,
        theta=-45,
        vega=100,
        rho=-20,
        open_interest=800,
        volume=30,
        timestamp=now
    )
    
    # Create positions
    call_position = Position(
        option_contract=call_contract,
        quantity=10,
        entry_price=Decimal("2000"),
        entry_date=now,
        current_value=Decimal("2000"),
        unrealized_pnl=Decimal("0")
    )
    
    put_position = Position(
        option_contract=put_contract,
        quantity=-5,
        entry_price=Decimal("1500"),
        entry_date=now,
        current_value=Decimal("1500"),
        unrealized_pnl=Decimal("0")
    )
    
    portfolio = Portfolio(
        positions=[call_position, put_position],
        cash_balance=Decimal("100000"),
        total_value=Decimal("100000")
    )
    
    return portfolio


def test_calculate_portfolio_greeks(risk_calculator, sample_portfolio):
    """Test portfolio Greeks calculation."""
    spot_price = 29000.0
    
    greeks = risk_calculator.calculate_portfolio_greeks(
        portfolio=sample_portfolio,
        spot_price=spot_price
    )
    
    # Check that all Greeks are present
    assert 'delta' in greeks
    assert 'gamma' in greeks
    assert 'theta' in greeks
    assert 'vega' in greeks
    assert 'rho' in greeks
    
    # Check that Greeks are reasonable values
    assert -100 < greeks['delta'] < 100  # Delta should be reasonable
    assert greeks['gamma'] >= 0  # Gamma is always positive
    assert greeks['theta'] <= 0  # Theta is typically negative
    assert greeks['vega'] >= 0  # Vega is always positive


def test_calculate_var(risk_calculator, sample_portfolio):
    """Test VaR calculation."""
    spot_price = 29000.0
    volatility = 0.8
    
    var_result = risk_calculator.calculate_var(
        portfolio=sample_portfolio,
        spot_price=spot_price,
        volatility=volatility,
        confidence_level=0.95,
        time_horizon_days=1
    )
    
    # Check that all fields are present
    assert 'var' in var_result
    assert 'cvar' in var_result
    assert 'portfolio_value' in var_result
    assert 'var_percentage' in var_result
    assert 'confidence_level' in var_result
    assert 'time_horizon_days' in var_result
    
    # Check that values are reasonable
    assert var_result['var'] >= 0
    assert var_result['cvar'] >= var_result['var']  # CVaR should be >= VaR
    assert var_result['portfolio_value'] > 0
    assert var_result['var_percentage'] >= 0  # VaR percentage can exceed 100% for high-risk portfolios
    assert var_result['confidence_level'] == 0.95
    assert var_result['time_horizon_days'] == 1


def test_calculate_var_different_confidence_levels(risk_calculator, sample_portfolio):
    """Test VaR with different confidence levels."""
    spot_price = 29000.0
    volatility = 0.8
    
    var_95 = risk_calculator.calculate_var(
        portfolio=sample_portfolio,
        spot_price=spot_price,
        volatility=volatility,
        confidence_level=0.95
    )
    
    var_99 = risk_calculator.calculate_var(
        portfolio=sample_portfolio,
        spot_price=spot_price,
        volatility=volatility,
        confidence_level=0.99
    )
    
    # Higher confidence level should result in higher VaR
    assert var_99['var'] > var_95['var']


def test_calculate_margin_requirement(risk_calculator, sample_portfolio):
    """Test margin requirement calculation."""
    spot_price = 29000.0
    
    margin = risk_calculator.calculate_margin_requirement(
        portfolio=sample_portfolio,
        spot_price=spot_price
    )
    
    # Check that all fields are present
    assert 'initial_margin' in margin
    assert 'maintenance_margin' in margin
    assert 'premium_paid' in margin
    assert 'premium_received' in margin
    assert 'total_margin_required' in margin
    
    # Check that values are reasonable
    assert margin['initial_margin'] >= 0
    assert margin['maintenance_margin'] >= 0
    assert margin['maintenance_margin'] <= margin['initial_margin']
    assert margin['premium_paid'] >= 0
    assert margin['premium_received'] >= 0
    assert margin['total_margin_required'] >= 0


def test_margin_long_vs_short(risk_calculator, options_engine):
    """Test that short positions require more margin than long positions."""
    expiry = datetime.now() + timedelta(days=30)
    now = datetime.now()
    
    call_contract = OptionContract(
        instrument_name="BTC-30000-C",
        underlying="BTC",
        option_type=OptionType.CALL,
        strike_price=Decimal("30000"),
        expiration_date=expiry,
        current_price=Decimal("2000"),
        bid_price=Decimal("1950"),
        ask_price=Decimal("2050"),
        last_price=Decimal("2000"),
        implied_volatility=0.8,
        delta=0.5,
        gamma=0.001,
        theta=-50,
        vega=100,
        rho=25,
        open_interest=1000,
        volume=50,
        timestamp=now
    )
    
    # Long portfolio
    long_position = Position(
        option_contract=call_contract,
        quantity=10,
        entry_price=Decimal("2000"),
        entry_date=now,
        current_value=Decimal("2000"),
        unrealized_pnl=Decimal("0")
    )
    long_portfolio = Portfolio(
        positions=[long_position],
        cash_balance=Decimal("100000"),
        total_value=Decimal("100000")
    )
    
    # Short portfolio
    short_position = Position(
        option_contract=call_contract,
        quantity=-10,
        entry_price=Decimal("2000"),
        entry_date=now,
        current_value=Decimal("2000"),
        unrealized_pnl=Decimal("0")
    )
    short_portfolio = Portfolio(
        positions=[short_position],
        cash_balance=Decimal("100000"),
        total_value=Decimal("100000")
    )
    
    spot_price = 29000.0
    
    long_margin = risk_calculator.calculate_margin_requirement(long_portfolio, spot_price)
    short_margin = risk_calculator.calculate_margin_requirement(short_portfolio, spot_price)
    
    # Short position should require more margin
    assert short_margin['initial_margin'] > long_margin['initial_margin']


def test_check_risk_limits_no_violations(risk_calculator, sample_portfolio):
    """Test risk limit checking with no violations."""
    spot_price = 29000.0
    
    result = risk_calculator.check_risk_limits(
        portfolio=sample_portfolio,
        spot_price=spot_price,
        max_delta=100.0,
        max_gamma=1.0,
        max_vega=1000.0
    )
    
    assert 'has_violations' in result
    assert 'violations' in result
    assert 'warnings' in result
    assert 'greeks' in result
    
    # Should have no violations with high limits
    assert result['has_violations'] == False
    assert len(result['violations']) == 0


def test_check_risk_limits_with_violations(risk_calculator, sample_portfolio):
    """Test risk limit checking with violations."""
    spot_price = 29000.0
    
    result = risk_calculator.check_risk_limits(
        portfolio=sample_portfolio,
        spot_price=spot_price,
        max_delta=0.1,  # Very low limit to trigger violation
        max_gamma=0.0001,
        max_vega=1.0
    )
    
    # Should have violations with very low limits
    assert result['has_violations'] == True
    assert len(result['violations']) > 0
    
    # Check violation structure
    for violation in result['violations']:
        assert 'type' in violation
        assert 'current' in violation
        assert 'limit' in violation
        assert 'message' in violation


def test_stress_test_price_shocks(risk_calculator, sample_portfolio):
    """Test stress testing with price shocks."""
    spot_price = 29000.0
    
    result = risk_calculator.stress_test(
        portfolio=sample_portfolio,
        spot_price=spot_price,
        price_shocks=[-0.2, -0.1, 0.1, 0.2]
    )
    
    # Check result structure
    assert 'base_portfolio_value' in result
    assert 'price_scenarios' in result
    assert 'volatility_scenarios' in result
    assert 'worst_price_scenario' in result
    assert 'worst_volatility_scenario' in result
    assert 'max_loss' in result
    
    # Check that we have the right number of scenarios
    assert len(result['price_scenarios']) == 4
    
    # Check scenario structure
    for scenario in result['price_scenarios']:
        assert 'shock_percentage' in scenario
        assert 'shocked_price' in scenario
        assert 'portfolio_value' in scenario
        assert 'pnl' in scenario
        assert 'pnl_percentage' in scenario


def test_stress_test_volatility_shocks(risk_calculator, sample_portfolio):
    """Test stress testing with volatility shocks."""
    spot_price = 29000.0
    
    result = risk_calculator.stress_test(
        portfolio=sample_portfolio,
        spot_price=spot_price,
        volatility_shocks=[-0.5, 0.5, 1.0]
    )
    
    # Check that we have the right number of scenarios
    assert len(result['volatility_scenarios']) == 3
    
    # Check scenario structure
    for scenario in result['volatility_scenarios']:
        assert 'shock_percentage' in scenario
        assert 'portfolio_value' in scenario
        assert 'pnl' in scenario
        assert 'pnl_percentage' in scenario


def test_stress_test_worst_case(risk_calculator, sample_portfolio):
    """Test that stress test identifies worst case scenario."""
    spot_price = 29000.0
    
    result = risk_calculator.stress_test(
        portfolio=sample_portfolio,
        spot_price=spot_price
    )
    
    # Worst case should have negative P&L
    assert result['worst_price_scenario']['pnl'] <= 0
    
    # Max loss should be the minimum of all scenarios
    all_pnls = [s['pnl'] for s in result['price_scenarios']] + \
               [s['pnl'] for s in result['volatility_scenarios']]
    assert result['max_loss'] == min(all_pnls)


def test_empty_portfolio(risk_calculator, options_engine):
    """Test risk calculations with empty portfolio."""
    empty_portfolio = Portfolio(
        positions=[],
        cash_balance=Decimal("100000"),
        total_value=Decimal("100000")
    )
    spot_price = 29000.0
    
    # Greeks should all be zero
    greeks = risk_calculator.calculate_portfolio_greeks(empty_portfolio, spot_price)
    assert greeks['delta'] == 0
    assert greeks['gamma'] == 0
    assert greeks['theta'] == 0
    assert greeks['vega'] == 0
    assert greeks['rho'] == 0
    
    # VaR should be zero
    var_result = risk_calculator.calculate_var(empty_portfolio, spot_price, 0.8)
    assert var_result['var'] == 0
    assert var_result['portfolio_value'] == 0
    
    # Margin should be zero
    margin = risk_calculator.calculate_margin_requirement(empty_portfolio, spot_price)
    assert margin['initial_margin'] == 0
    assert margin['total_margin_required'] == 0


def test_var_time_horizon_scaling(risk_calculator, sample_portfolio):
    """Test that VaR scales with time horizon."""
    spot_price = 29000.0
    volatility = 0.8
    
    var_1day = risk_calculator.calculate_var(
        portfolio=sample_portfolio,
        spot_price=spot_price,
        volatility=volatility,
        time_horizon_days=1
    )
    
    var_10day = risk_calculator.calculate_var(
        portfolio=sample_portfolio,
        spot_price=spot_price,
        volatility=volatility,
        time_horizon_days=10
    )
    
    # VaR should increase with time horizon (approximately sqrt(10) times)
    # Allow some tolerance due to rounding
    expected_ratio = np.sqrt(10)
    actual_ratio = var_10day['var'] / var_1day['var']
    assert 2.5 < actual_ratio < 4.0  # sqrt(10) ≈ 3.16
