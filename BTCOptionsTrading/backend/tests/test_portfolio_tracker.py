"""
Tests for Portfolio Tracker.
"""

import pytest
from datetime import datetime, timedelta
from src.portfolio.portfolio_tracker import PortfolioTracker
from src.pricing.options_engine import OptionsEngine
from src.core.models import OptionContract, OptionType


@pytest.fixture
def options_engine():
    """Create options engine."""
    return OptionsEngine()


@pytest.fixture
def portfolio_tracker(options_engine):
    """Create portfolio tracker."""
    return PortfolioTracker(
        initial_cash=100000.0,
        options_engine=options_engine,
        commission_rate=0.0003
    )


@pytest.fixture
def sample_call_option():
    """Create sample call option."""
    from decimal import Decimal
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


@pytest.fixture
def sample_put_option():
    """Create sample put option."""
    from decimal import Decimal
    return OptionContract(
        instrument_name="BTC-31MAR23-28000-P",
        underlying="BTC",
        strike_price=Decimal("28000.0"),
        expiration_date=datetime(2023, 3, 31),
        option_type=OptionType.PUT,
        current_price=Decimal("1200.0"),
        bid_price=Decimal("1190.0"),
        ask_price=Decimal("1210.0"),
        last_price=Decimal("1200.0"),
        implied_volatility=0.8,
        delta=-0.4,
        gamma=0.00001,
        theta=-40.0,
        vega=80.0,
        rho=-40.0,
        open_interest=800,
        volume=80,
        timestamp=datetime(2023, 1, 1)
    )


def test_portfolio_initialization(portfolio_tracker):
    """Test portfolio tracker initialization."""
    assert portfolio_tracker.initial_cash == 100000.0
    assert portfolio_tracker.cash == 100000.0
    assert portfolio_tracker.get_position_count() == 0
    assert len(portfolio_tracker.trade_history) == 0


def test_add_position(portfolio_tracker, sample_call_option):
    """Test adding a position."""
    trade = portfolio_tracker.add_position(
        option=sample_call_option,
        quantity=10,
        price=1500.0,
        timestamp=datetime(2023, 1, 1)
    )
    
    # Check trade record
    assert trade.action == 'BUY'
    assert trade.quantity == 10
    assert trade.price == 1500.0
    assert trade.total_cost == 15000.0
    assert trade.commission == 15000.0 * 0.0003
    
    # Check portfolio state
    assert portfolio_tracker.get_position_count() == 1
    assert portfolio_tracker.cash < 100000.0
    
    # Check position
    positions = portfolio_tracker.get_current_positions()
    assert len(positions) == 1
    option, qty = positions[0]
    assert option.instrument_name == sample_call_option.instrument_name
    assert qty == 10


def test_add_multiple_positions(portfolio_tracker, sample_call_option, sample_put_option):
    """Test adding multiple positions."""
    portfolio_tracker.add_position(sample_call_option, 10, 1500.0)
    portfolio_tracker.add_position(sample_put_option, 5, 1200.0)
    
    assert portfolio_tracker.get_position_count() == 2
    
    positions = portfolio_tracker.get_current_positions()
    assert len(positions) == 2


def test_remove_position(portfolio_tracker, sample_call_option):
    """Test removing a position."""
    # Add position first
    portfolio_tracker.add_position(sample_call_option, 10, 1500.0)
    initial_cash = portfolio_tracker.cash
    
    # Remove partial position
    trade = portfolio_tracker.remove_position(
        option=sample_call_option,
        quantity=5,
        price=1600.0,
        timestamp=datetime(2023, 1, 2)
    )
    
    # Check trade record
    assert trade.action == 'SELL'
    assert trade.quantity == 5
    assert trade.price == 1600.0
    
    # Check portfolio state
    assert portfolio_tracker.get_position_count() == 1
    assert portfolio_tracker.cash > initial_cash  # Made profit
    
    # Check remaining position
    positions = portfolio_tracker.get_current_positions()
    option, qty = positions[0]
    assert qty == 5


def test_remove_full_position(portfolio_tracker, sample_call_option):
    """Test removing full position."""
    portfolio_tracker.add_position(sample_call_option, 10, 1500.0)
    
    # Remove full position
    portfolio_tracker.remove_position(sample_call_option, 10, 1600.0)
    
    # Position should be removed
    assert portfolio_tracker.get_position_count() == 0


def test_insufficient_cash(portfolio_tracker, sample_call_option):
    """Test insufficient cash error."""
    with pytest.raises(ValueError, match="Insufficient cash"):
        portfolio_tracker.add_position(sample_call_option, 1000, 1500.0)


def test_remove_nonexistent_position(portfolio_tracker, sample_call_option):
    """Test removing non-existent position."""
    with pytest.raises(ValueError, match="No position found"):
        portfolio_tracker.remove_position(sample_call_option, 10, 1500.0)


def test_remove_too_many_contracts(portfolio_tracker, sample_call_option):
    """Test removing more contracts than available."""
    portfolio_tracker.add_position(sample_call_option, 10, 1500.0)
    
    with pytest.raises(ValueError, match="Cannot sell"):
        portfolio_tracker.remove_position(sample_call_option, 20, 1500.0)


def test_calculate_portfolio_value(portfolio_tracker, sample_call_option):
    """Test portfolio value calculation."""
    # Add position
    portfolio_tracker.add_position(sample_call_option, 10, 1500.0)
    
    # Calculate value
    value = portfolio_tracker.calculate_portfolio_value(
        spot_price=32000.0,
        volatility=0.8,
        risk_free_rate=0.05,
        timestamp=datetime(2023, 1, 15)
    )
    
    # Value should be cash + options value
    assert value > 0
    assert value != portfolio_tracker.cash


def test_calculate_portfolio_greeks(portfolio_tracker, sample_call_option):
    """Test portfolio Greeks calculation."""
    # Add position
    portfolio_tracker.add_position(sample_call_option, 10, 1500.0)
    
    # Calculate Greeks
    greeks = portfolio_tracker.calculate_portfolio_greeks(
        spot_price=32000.0,
        volatility=0.8,
        risk_free_rate=0.05,
        timestamp=datetime(2023, 1, 15)
    )
    
    # Check Greeks are calculated
    assert greeks.delta != 0
    assert greeks.gamma != 0
    assert greeks.theta != 0
    assert greeks.vega != 0


def test_take_snapshot(portfolio_tracker, sample_call_option):
    """Test taking portfolio snapshot."""
    # Add position
    portfolio_tracker.add_position(sample_call_option, 10, 1500.0)
    
    # Take snapshot
    snapshot = portfolio_tracker.take_snapshot(
        spot_price=32000.0,
        volatility=0.8,
        risk_free_rate=0.05,
        timestamp=datetime(2023, 1, 15)
    )
    
    # Check snapshot
    assert snapshot.total_value > 0
    assert snapshot.cash == portfolio_tracker.cash
    assert snapshot.options_value > 0
    assert snapshot.num_positions == 1
    assert len(portfolio_tracker.snapshots) == 1


def test_multiple_snapshots(portfolio_tracker, sample_call_option):
    """Test taking multiple snapshots."""
    portfolio_tracker.add_position(sample_call_option, 10, 1500.0)
    
    # Take multiple snapshots
    for i in range(5):
        portfolio_tracker.take_snapshot(
            spot_price=30000.0 + i * 1000,
            volatility=0.8,
            timestamp=datetime(2023, 1, 1) + timedelta(days=i)
        )
    
    assert len(portfolio_tracker.snapshots) == 5


def test_get_trade_history(portfolio_tracker, sample_call_option, sample_put_option):
    """Test getting trade history."""
    # Make some trades
    portfolio_tracker.add_position(sample_call_option, 10, 1500.0, datetime(2023, 1, 1))
    portfolio_tracker.add_position(sample_put_option, 5, 1200.0, datetime(2023, 1, 5))
    portfolio_tracker.remove_position(sample_call_option, 5, 1600.0, datetime(2023, 1, 10))
    
    # Get all trades
    all_trades = portfolio_tracker.get_trade_history()
    assert len(all_trades) == 3
    
    # Get trades in date range
    trades = portfolio_tracker.get_trade_history(
        start_date=datetime(2023, 1, 3),
        end_date=datetime(2023, 1, 8)
    )
    assert len(trades) == 1
    assert trades[0].option.instrument_name == sample_put_option.instrument_name


def test_generate_performance_report(portfolio_tracker, sample_call_option):
    """Test generating performance report."""
    # Add position and take snapshots
    portfolio_tracker.add_position(sample_call_option, 10, 1500.0, datetime(2023, 1, 1))
    
    for i in range(10):
        portfolio_tracker.take_snapshot(
            spot_price=30000.0 + i * 500,
            volatility=0.8,
            timestamp=datetime(2023, 1, 1) + timedelta(days=i)
        )
    
    # Sell position
    portfolio_tracker.remove_position(sample_call_option, 10, 1800.0, datetime(2023, 1, 11))
    
    # Generate report
    report = portfolio_tracker.generate_performance_report(
        final_spot_price=35000.0,
        final_volatility=0.8,
        initial_btc_price=30000.0,
        final_btc_price=35000.0
    )
    
    # Check report
    assert report.initial_value == 100000.0
    assert report.final_value > 0
    assert report.num_trades == 2
    assert report.btc_return_pct > 0
    assert -100 <= report.max_drawdown <= 100


def test_performance_report_with_profit(portfolio_tracker, sample_call_option):
    """Test performance report with profitable trades."""
    # Buy low, sell high
    portfolio_tracker.add_position(sample_call_option, 10, 1500.0, datetime(2023, 1, 1))
    portfolio_tracker.take_snapshot(30000.0, 0.8, timestamp=datetime(2023, 1, 1))
    
    portfolio_tracker.remove_position(sample_call_option, 10, 2000.0, datetime(2023, 1, 10))
    portfolio_tracker.take_snapshot(35000.0, 0.8, timestamp=datetime(2023, 1, 10))
    
    report = portfolio_tracker.generate_performance_report(35000.0, 0.8)
    
    # Should have positive return
    assert report.total_return > 0
    assert report.total_return_pct > 0
    assert report.win_rate > 0


def test_performance_report_with_loss(portfolio_tracker, sample_call_option):
    """Test performance report with losing trades."""
    # Buy high, sell low
    portfolio_tracker.add_position(sample_call_option, 10, 2000.0, datetime(2023, 1, 1))
    portfolio_tracker.take_snapshot(35000.0, 0.8, timestamp=datetime(2023, 1, 1))
    
    portfolio_tracker.remove_position(sample_call_option, 10, 1500.0, datetime(2023, 1, 10))
    portfolio_tracker.take_snapshot(30000.0, 0.8, timestamp=datetime(2023, 1, 10))
    
    report = portfolio_tracker.generate_performance_report(30000.0, 0.8)
    
    # Should have negative return
    assert report.total_return < 0
    assert report.total_return_pct < 0
    assert report.win_rate == 0


def test_expired_option_valuation(portfolio_tracker, sample_call_option):
    """Test valuation of expired options."""
    portfolio_tracker.add_position(sample_call_option, 10, 1500.0)
    
    # Value after expiry (ITM)
    value_itm = portfolio_tracker.calculate_portfolio_value(
        spot_price=35000.0,
        volatility=0.8,
        timestamp=datetime(2023, 4, 1)  # After expiry
    )
    
    # Should have intrinsic value only
    intrinsic = (35000.0 - 30000.0) * 10
    assert abs(value_itm - portfolio_tracker.cash - intrinsic) < 1.0
    
    # Value after expiry (OTM)
    value_otm = portfolio_tracker.calculate_portfolio_value(
        spot_price=25000.0,
        volatility=0.8,
        timestamp=datetime(2023, 4, 1)
    )
    
    # Should be worthless
    assert abs(value_otm - portfolio_tracker.cash) < 1.0


def test_empty_portfolio_report(portfolio_tracker):
    """Test generating report with no snapshots."""
    with pytest.raises(ValueError, match="No snapshots available"):
        portfolio_tracker.generate_performance_report(30000.0, 0.8)
