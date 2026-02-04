"""
Protection Manager Example Usage
Demonstrates stop loss and protection mechanisms for trading positions
"""
import sys
import os
from datetime import datetime, timedelta
import random

# Add the backend directory to the Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.data_models import Position, Portfolio, ActionType, OrderStatus
from decision_engine.risk_parameters import RiskParameters
from risk_management.protection_manager import (
    ProtectionManager, ProtectionType, ProtectionStatus, StopLossMethod
)


def create_sample_position(symbol: str = "BTCUSDT", amount: float = 0.5, 
                         entry_price: float = 44000.0, current_price: float = 45000.0) -> Position:
    """Create a sample position for testing"""
    return Position(
        symbol=symbol,
        amount=amount,
        entry_price=entry_price,
        current_price=current_price,
        pnl=(current_price - entry_price) * amount,
        entry_time=datetime.utcnow() - timedelta(hours=6)
    )


def create_sample_portfolio() -> Portfolio:
    """Create a sample portfolio with positions"""
    btc_position = create_sample_position("BTCUSDT", 0.5, 44000.0, 45000.0)
    eth_position = create_sample_position("ETHUSDT", 2.0, 2800.0, 2850.0)
    
    total_value = (0.5 * 45000) + (2.0 * 2850) + 5000  # BTC + ETH + USDT
    unrealized_pnl = btc_position.pnl + eth_position.pnl
    
    return Portfolio(
        btc_balance=0.5,
        usdt_balance=5000.0,
        total_value_usdt=total_value,
        unrealized_pnl=unrealized_pnl,
        positions=[btc_position, eth_position]
    )


def demonstrate_stop_loss_orders():
    """Demonstrate stop loss order creation and management"""
    print("=== Stop Loss Orders Demo ===")
    
    # Create test data
    position = create_sample_position()
    protection_manager = ProtectionManager()
    
    print(f"Position: {position.amount} {position.symbol} at ${position.current_price:,.2f}")
    print(f"Entry Price: ${position.entry_price:,.2f}")
    print(f"Current P&L: ${position.pnl:,.2f}")
    
    # Create stop loss order
    stop_loss_order = protection_manager.create_stop_loss_order(
        position, method=StopLossMethod.FIXED_PERCENTAGE
    )
    
    print(f"\nCreated Stop Loss Order:")
    print(f"  Order ID: {stop_loss_order.id}")
    print(f"  Trigger Price: ${stop_loss_order.trigger_price:,.2f}")
    print(f"  Order Action: {stop_loss_order.order_action.value}")
    print(f"  Quantity: {stop_loss_order.quantity}")
    print(f"  Status: {stop_loss_order.status.value}")
    
    # Test price movement and trigger checking
    print(f"\n--- Price Movement Simulation ---")
    test_prices = [44500, 44000, 43500, 43000, 42500]  # Declining prices
    
    for price in test_prices:
        current_prices = {"BTCUSDT": price}
        triggered_orders = protection_manager.check_protection_triggers(current_prices)
        
        print(f"Price: ${price:,.2f} - ", end="")
        if triggered_orders:
            print(f"TRIGGERED! {len(triggered_orders)} orders")
            for order in triggered_orders:
                # Simulate execution
                execution_result = protection_manager.execute_protection_order(order, price)
                print(f"  Executed: {execution_result.executed_amount} at ${execution_result.executed_price:,.2f}")
            break
        else:
            print("No triggers")
    
    return protection_manager


def demonstrate_trailing_stops():
    """Demonstrate trailing stop functionality"""
    print("\n=== Trailing Stop Orders Demo ===")
    
    # Create test data
    position = create_sample_position()
    protection_manager = ProtectionManager()
    
    print(f"Position: {position.amount} {position.symbol} at ${position.current_price:,.2f}")
    
    # Create trailing stop order
    trailing_stop = protection_manager.create_trailing_stop_order(
        position, trail_percentage=0.05  # 5% trailing stop
    )
    
    print(f"\nCreated Trailing Stop Order:")
    print(f"  Order ID: {trailing_stop.id}")
    print(f"  Initial Trigger: ${trailing_stop.trigger_price:,.2f}")
    print(f"  Trail Percentage: {trailing_stop.trail_percentage:.1%}")
    
    # Simulate price movements
    print(f"\n--- Price Movement and Trailing Updates ---")
    price_sequence = [45000, 46000, 47000, 46500, 46000, 45500, 45000, 44000]
    
    for i, price in enumerate(price_sequence):
        current_prices = {"BTCUSDT": price}
        
        # Update trailing stops
        updates = protection_manager.update_trailing_stops(current_prices)
        
        # Check for triggers
        triggered_orders = protection_manager.check_protection_triggers(current_prices)
        
        print(f"Step {i+1}: Price ${price:,.2f}")
        print(f"  Peak: ${protection_manager.position_peaks.get('BTCUSDT', 0):,.2f}")
        print(f"  Trigger: ${trailing_stop.trigger_price:,.2f}")
        
        if updates > 0:
            print(f"  ✓ Updated {updates} trailing stops")
        
        if triggered_orders:
            print(f"  🚨 TRIGGERED! Executing stop loss")
            for order in triggered_orders:
                execution_result = protection_manager.execute_protection_order(order, price)
                print(f"     Sold {execution_result.executed_amount} at ${execution_result.executed_price:,.2f}")
            break
        
        print()
    
    return protection_manager


def demonstrate_take_profit_orders():
    """Demonstrate take profit order functionality"""
    print("\n=== Take Profit Orders Demo ===")
    
    # Create test data
    position = create_sample_position()
    protection_manager = ProtectionManager()
    
    print(f"Position: {position.amount} {position.symbol}")
    print(f"Entry: ${position.entry_price:,.2f}, Current: ${position.current_price:,.2f}")
    
    # Create take profit order
    take_profit = protection_manager.create_take_profit_order(
        position, profit_percentage=0.10  # 10% profit target
    )
    
    print(f"\nCreated Take Profit Order:")
    print(f"  Order ID: {take_profit.id}")
    print(f"  Trigger Price: ${take_profit.trigger_price:,.2f}")
    print(f"  Profit Target: {((take_profit.trigger_price / position.entry_price) - 1):.1%}")
    
    # Test price movements toward profit target
    print(f"\n--- Price Movement Toward Profit Target ---")
    rising_prices = [45500, 46000, 47000, 48000, 48400, 48800]
    
    for price in rising_prices:
        current_prices = {"BTCUSDT": price}
        triggered_orders = protection_manager.check_protection_triggers(current_prices)
        
        profit_pct = ((price / position.entry_price) - 1) * 100
        print(f"Price: ${price:,.2f} (Profit: {profit_pct:+.1f}%) - ", end="")
        
        if triggered_orders:
            print(f"TAKE PROFIT TRIGGERED!")
            for order in triggered_orders:
                execution_result = protection_manager.execute_protection_order(order, price)
                final_profit = (execution_result.executed_price - position.entry_price) * position.amount
                print(f"  Executed: {execution_result.executed_amount} at ${execution_result.executed_price:,.2f}")
                print(f"  Final Profit: ${final_profit:,.2f}")
            break
        else:
            print("Target not reached")
    
    return protection_manager


def demonstrate_portfolio_protection():
    """Demonstrate portfolio-wide protection management"""
    print("\n=== Portfolio Protection Demo ===")
    
    # Create portfolio with multiple positions
    portfolio = create_sample_portfolio()
    protection_manager = ProtectionManager()
    
    print(f"Portfolio Overview:")
    print(f"  Total Value: ${portfolio.total_value_usdt:,.2f}")
    print(f"  Positions: {len(portfolio.positions)}")
    
    # Create protection for all positions
    protection_orders = []
    for position in portfolio.positions:
        # Stop loss
        stop_loss = protection_manager.create_stop_loss_order(position)
        protection_orders.append(stop_loss)
        
        # Take profit
        take_profit = protection_manager.create_take_profit_order(position)
        protection_orders.append(take_profit)
        
        print(f"\n  {position.symbol}:")
        print(f"    Amount: {position.amount}")
        print(f"    Stop Loss: ${stop_loss.trigger_price:,.2f}")
        print(f"    Take Profit: ${take_profit.trigger_price:,.2f}")
    
    # Get protection summary
    summary = protection_manager.get_protection_summary(portfolio)
    
    print(f"\nProtection Summary:")
    print(f"  Total Positions: {summary.total_positions}")
    print(f"  Protected Positions: {summary.protected_positions}")
    print(f"  Active Stop Losses: {summary.active_stop_losses}")
    print(f"  Active Take Profits: {summary.active_take_profits}")
    print(f"  Protection Coverage: {summary.protection_coverage:.1%}")
    print(f"  Max Potential Loss: ${summary.max_potential_loss:,.2f}")
    
    return protection_manager, portfolio


def demonstrate_auto_adjustments():
    """Demonstrate automatic protection adjustments"""
    print("\n=== Auto Protection Adjustments Demo ===")
    
    portfolio = create_sample_portfolio()
    protection_manager = ProtectionManager()
    
    # Create some protection orders
    for position in portfolio.positions:
        protection_manager.create_stop_loss_order(position)
    
    print(f"Initial protection orders: {len(protection_manager.protection_orders)}")
    
    # Simulate high volatility scenario
    print(f"\n--- High Volatility Adjustment ---")
    high_volatility = 0.08  # 8% volatility
    
    adjustments = protection_manager.auto_adjust_protection_levels(
        portfolio, market_volatility=high_volatility
    )
    
    print(f"Volatility: {high_volatility:.1%}")
    print(f"Adjustments made: {adjustments}")
    
    # Simulate portfolio drawdown scenario
    print(f"\n--- Portfolio Drawdown Adjustment ---")
    # Simulate unrealized losses
    portfolio.unrealized_pnl = -2000.0  # $2000 loss
    
    adjustments = protection_manager.auto_adjust_protection_levels(portfolio)
    
    print(f"Portfolio P&L: ${portfolio.unrealized_pnl:,.2f}")
    print(f"Adjustments made: {adjustments}")
    
    return protection_manager


def demonstrate_continuous_loss_monitoring():
    """Demonstrate continuous loss monitoring"""
    print("\n=== Continuous Loss Monitoring Demo ===")
    
    protection_manager = ProtectionManager()
    
    # Simulate trading history with losses
    recent_trades = [
        {'pnl': -500, 'timestamp': datetime.utcnow() - timedelta(hours=6)},
        {'pnl': -300, 'timestamp': datetime.utcnow() - timedelta(hours=4)},
        {'pnl': -200, 'timestamp': datetime.utcnow() - timedelta(hours=2)},
        {'pnl': -150, 'timestamp': datetime.utcnow() - timedelta(hours=1)},
    ]
    
    print(f"Recent Trading History:")
    for i, trade in enumerate(recent_trades, 1):
        print(f"  Trade {i}: ${trade['pnl']:+,.2f}")
    
    # Check for continuous losses
    should_suspend = protection_manager.monitor_continuous_losses(recent_trades)
    
    print(f"\nContinuous Loss Analysis:")
    print(f"  Should suspend trading: {'YES' if should_suspend else 'NO'}")
    
    if should_suspend:
        total_loss = sum(trade['pnl'] for trade in recent_trades if trade['pnl'] < 0)
        print(f"  Total recent losses: ${total_loss:,.2f}")
        print(f"  Recommendation: Pause trading and review strategy")
    
    return protection_manager


def demonstrate_protection_lifecycle():
    """Demonstrate complete protection order lifecycle"""
    print("\n=== Protection Order Lifecycle Demo ===")
    
    position = create_sample_position()
    protection_manager = ProtectionManager()
    
    # Create protection order
    stop_loss = protection_manager.create_stop_loss_order(position)
    print(f"1. Created: {stop_loss.id} - Status: {stop_loss.status.value}")
    
    # Get position protection
    position_orders = protection_manager.get_position_protection(position.symbol)
    print(f"2. Active orders for {position.symbol}: {len(position_orders)}")
    
    # Cancel order
    cancelled = protection_manager.cancel_protection_order(stop_loss.id, "Manual cancellation")
    print(f"3. Cancelled: {'Success' if cancelled else 'Failed'}")
    print(f"   Status: {stop_loss.status.value}")
    
    # Create new order and trigger it
    new_stop_loss = protection_manager.create_stop_loss_order(position)
    print(f"4. New order: {new_stop_loss.id}")
    
    # Trigger the order
    trigger_price = new_stop_loss.trigger_price - 100  # Price below trigger
    current_prices = {position.symbol: trigger_price}
    triggered = protection_manager.check_protection_triggers(current_prices)
    
    if triggered:
        print(f"5. Triggered at ${trigger_price:,.2f}")
        execution_result = protection_manager.execute_protection_order(triggered[0], trigger_price)
        print(f"6. Executed: {execution_result.order_id}")
    
    # Cleanup expired orders
    expired_count = protection_manager.cleanup_expired_orders()
    print(f"7. Cleaned up {expired_count} expired orders")
    
    # Get manager status
    status = protection_manager.get_protection_manager_status()
    print(f"\nManager Status:")
    print(f"  Total orders: {status['total_protection_orders']}")
    print(f"  Active orders: {status['active_orders']}")
    print(f"  Total triggers: {status['total_triggers']}")
    
    return protection_manager


def main():
    """Run all protection manager demonstrations"""
    print("Protection Manager System Demonstration")
    print("=" * 60)
    
    try:
        # Individual feature demonstrations
        demonstrate_stop_loss_orders()
        demonstrate_trailing_stops()
        demonstrate_take_profit_orders()
        demonstrate_portfolio_protection()
        demonstrate_auto_adjustments()
        demonstrate_continuous_loss_monitoring()
        demonstrate_protection_lifecycle()
        
        print("\n" + "=" * 60)
        print("Protection manager demonstration completed successfully!")
        
    except Exception as e:
        print(f"Error during demonstration: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()