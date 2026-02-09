"""
Example usage of Portfolio Tracker.

This script demonstrates:
1. Creating a portfolio tracker
2. Adding and removing positions
3. Taking snapshots
4. Calculating portfolio value and Greeks
5. Generating performance reports
"""

from datetime import datetime, timedelta
from src.portfolio.portfolio_tracker import PortfolioTracker
from src.pricing.options_engine import OptionsEngine
from src.core.models import OptionContract, OptionType


def print_separator(title=""):
    """Print a separator line."""
    if title:
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
    else:
        print(f"{'='*60}")


def main():
    """Run portfolio tracker examples."""
    print_separator("Portfolio Tracker Example")
    
    # Initialize
    options_engine = OptionsEngine()
    tracker = PortfolioTracker(
        initial_cash=100000.0,
        options_engine=options_engine,
        commission_rate=0.0003
    )
    
    print(f"\nInitial Cash: ${tracker.initial_cash:,.2f}")
    
    # Create some options
    from decimal import Decimal
    call_option = OptionContract(
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
    
    put_option = OptionContract(
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
    
    # Example 1: Add positions
    print_separator("1. Adding Positions")
    
    trade1 = tracker.add_position(
        option=call_option,
        quantity=10,
        price=1500.0,
        timestamp=datetime(2023, 1, 1)
    )
    print(f"\nTrade 1: {trade1.action} {trade1.quantity} {trade1.option.instrument_name}")
    print(f"  Price: ${trade1.price:,.2f}")
    print(f"  Total Cost: ${trade1.total_cost:,.2f}")
    print(f"  Commission: ${trade1.commission:,.2f}")
    print(f"  Cash Remaining: ${tracker.cash:,.2f}")
    
    trade2 = tracker.add_position(
        option=put_option,
        quantity=5,
        price=1200.0,
        timestamp=datetime(2023, 1, 1)
    )
    print(f"\nTrade 2: {trade2.action} {trade2.quantity} {trade2.option.instrument_name}")
    print(f"  Price: ${trade2.price:,.2f}")
    print(f"  Total Cost: ${trade2.total_cost:,.2f}")
    print(f"  Commission: ${trade2.commission:,.2f}")
    print(f"  Cash Remaining: ${tracker.cash:,.2f}")
    
    # Example 2: Portfolio valuation
    print_separator("2. Portfolio Valuation")
    
    spot_price = 32000.0
    volatility = 0.8
    timestamp = datetime(2023, 1, 15)
    
    value = tracker.calculate_portfolio_value(
        spot_price=spot_price,
        volatility=volatility,
        timestamp=timestamp
    )
    
    print(f"\nSpot Price: ${spot_price:,.2f}")
    print(f"Volatility: {volatility*100:.1f}%")
    print(f"Date: {timestamp.strftime('%Y-%m-%d')}")
    print(f"\nPortfolio Value: ${value:,.2f}")
    print(f"  Cash: ${tracker.cash:,.2f}")
    print(f"  Options Value: ${value - tracker.cash:,.2f}")
    print(f"  Total P&L: ${value - tracker.initial_cash:,.2f}")
    print(f"  P&L %: {((value - tracker.initial_cash) / tracker.initial_cash) * 100:.2f}%")
    
    # Example 3: Portfolio Greeks
    print_separator("3. Portfolio Greeks")
    
    greeks = tracker.calculate_portfolio_greeks(
        spot_price=spot_price,
        volatility=volatility,
        timestamp=timestamp
    )
    
    print(f"\nPortfolio Greeks:")
    print(f"  Delta: {greeks.delta:,.4f}")
    print(f"  Gamma: {greeks.gamma:,.6f}")
    print(f"  Theta: {greeks.theta:,.4f}")
    print(f"  Vega: {greeks.vega:,.4f}")
    print(f"  Rho: {greeks.rho:,.4f}")
    
    # Example 4: Take snapshots over time
    print_separator("4. Portfolio Snapshots Over Time")
    
    print("\nTaking daily snapshots for 10 days...")
    for i in range(10):
        day = datetime(2023, 1, 1) + timedelta(days=i)
        price = 30000.0 + i * 500  # Price increases
        vol = 0.8 - i * 0.02  # Volatility decreases
        
        snapshot = tracker.take_snapshot(
            spot_price=price,
            volatility=vol,
            timestamp=day
        )
        
        print(f"\nDay {i+1} ({day.strftime('%Y-%m-%d')})")
        print(f"  Spot: ${price:,.2f}, Vol: {vol*100:.1f}%")
        print(f"  Portfolio Value: ${snapshot.total_value:,.2f}")
        print(f"  P&L: ${snapshot.total_pnl:,.2f} ({snapshot.pnl_percent:.2f}%)")
        print(f"  Delta: {snapshot.greeks.delta:,.2f}")
    
    # Example 5: Close positions
    print_separator("5. Closing Positions")
    
    trade3 = tracker.remove_position(
        option=call_option,
        quantity=5,
        price=2000.0,
        timestamp=datetime(2023, 1, 15)
    )
    print(f"\nTrade 3: {trade3.action} {trade3.quantity} {trade3.option.instrument_name}")
    print(f"  Price: ${trade3.price:,.2f}")
    print(f"  Total Proceeds: ${trade3.total_cost:,.2f}")
    print(f"  Commission: ${trade3.commission:,.2f}")
    print(f"  Cash After Sale: ${tracker.cash:,.2f}")
    
    # Example 6: Trade history
    print_separator("6. Trade History")
    
    trades = tracker.get_trade_history()
    print(f"\nTotal Trades: {len(trades)}")
    for trade in trades:
        print(f"\n{trade.trade_id}: {trade.action} {trade.quantity} {trade.option.instrument_name}")
        print(f"  Date: {trade.timestamp.strftime('%Y-%m-%d')}")
        print(f"  Price: ${trade.price:,.2f}")
        print(f"  Total: ${trade.total_cost:,.2f}")
    
    # Example 7: Performance report
    print_separator("7. Performance Report")
    
    # Close remaining positions
    tracker.remove_position(call_option, 5, 2100.0, datetime(2023, 1, 20))
    tracker.remove_position(put_option, 5, 1000.0, datetime(2023, 1, 20))
    
    # Take final snapshot
    tracker.take_snapshot(
        spot_price=35000.0,
        volatility=0.7,
        timestamp=datetime(2023, 1, 20)
    )
    
    report = tracker.generate_performance_report(
        final_spot_price=35000.0,
        final_volatility=0.7,
        initial_btc_price=30000.0,
        final_btc_price=35000.0
    )
    
    print(f"\nPerformance Report")
    print(f"  Period: {report.start_date.strftime('%Y-%m-%d')} to {report.end_date.strftime('%Y-%m-%d')}")
    print(f"\n  Initial Value: ${report.initial_value:,.2f}")
    print(f"  Final Value: ${report.final_value:,.2f}")
    print(f"  Total Return: ${report.total_return:,.2f} ({report.total_return_pct:.2f}%)")
    print(f"\n  BTC Return: {report.btc_return_pct:.2f}%")
    print(f"  Excess Return: {report.excess_return_pct:.2f}%")
    print(f"\n  Sharpe Ratio: {report.sharpe_ratio:.4f}")
    print(f"  Max Drawdown: {report.max_drawdown:.2f}%")
    print(f"\n  Number of Trades: {report.num_trades}")
    print(f"  Win Rate: {report.win_rate:.2f}%")
    print(f"  Avg Trade P&L: ${report.avg_trade_pnl:,.2f}")
    print(f"  Best Trade: ${report.best_trade:,.2f}")
    print(f"  Worst Trade: ${report.worst_trade:,.2f}")
    
    # Example 8: Current positions
    print_separator("8. Current Positions")
    
    positions = tracker.get_current_positions()
    print(f"\nNumber of Positions: {len(positions)}")
    if len(positions) == 0:
        print("  (All positions closed)")
    else:
        for option, qty in positions:
            print(f"\n  {option.instrument_name}")
            print(f"    Quantity: {qty}")
            print(f"    Strike: ${option.strike_price:,.2f}")
            print(f"    Expiry: {option.expiration_date.strftime('%Y-%m-%d')}")
    
    print(f"\nFinal Cash Balance: ${tracker.cash:,.2f}")
    
    print_separator()


if __name__ == "__main__":
    main()
