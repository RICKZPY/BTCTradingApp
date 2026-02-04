"""
Trading Execution Example Usage
Demonstrates Binance API integration, order execution, and position management
"""
import sys
import os
from datetime import datetime, timedelta
import time

# Add the backend directory to the Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.data_models import TradingDecision, ActionType, RiskLevel, PriceRange, Portfolio, Position
from trading_execution.binance_client import BinanceClient, OrderSide, OrderType
from trading_execution.order_manager import OrderManager, OrderExecutionStrategy
from trading_execution.position_manager import PositionManager


def create_sample_trading_decision(action: ActionType = ActionType.BUY,
                                 confidence: float = 0.8,
                                 suggested_amount: float = 0.05) -> TradingDecision:
    """Create a sample trading decision for testing"""
    return TradingDecision(
        action=action,
        confidence=confidence,
        suggested_amount=suggested_amount,
        price_range=PriceRange(
            min_price=44000.0,
            max_price=46000.0
        ),
        reasoning="Sample trading decision for execution testing",
        risk_level=RiskLevel.MEDIUM
    )


def create_sample_portfolio() -> Portfolio:
    """Create a sample portfolio for testing"""
    btc_position = Position(
        symbol="BTCUSDT",
        amount=0.1,
        entry_price=44000.0,
        current_price=45000.0,
        pnl=100.0,
        entry_time=datetime.utcnow() - timedelta(hours=2)
    )
    
    return Portfolio(
        btc_balance=0.1,
        usdt_balance=5000.0,
        total_value_usdt=9500.0,
        unrealized_pnl=100.0,
        positions=[btc_position]
    )


def demonstrate_binance_client():
    """Demonstrate Binance API client functionality"""
    print("=== Binance Client Demo ===")
    
    # Note: Using demo credentials - replace with real testnet credentials for actual testing
    api_key = "demo_api_key"
    api_secret = "demo_api_secret"
    
    # Initialize client (testnet mode)
    client = BinanceClient(api_key, api_secret, testnet=True)
    
    print(f"Client initialized (testnet: {client.testnet})")
    print(f"Base URL: {client.base_url}")
    
    # Note: The following would work with real credentials
    try:
        # Test connectivity (this would work with real API)
        print("\nTesting connectivity...")
        print("Note: This demo uses placeholder credentials")
        print("With real testnet credentials, you would see:")
        print("  ✓ Connectivity test successful")
        
        # Get server time (this would work with real API)
        print("\nServer time check...")
        print("  Server time: 2026-02-01 16:59:58 (example)")
        
        # Get exchange info (this would work with real API)
        print("\nExchange info...")
        print("  Symbol: BTCUSDT")
        print("  Status: TRADING")
        print("  Base asset: BTC")
        print("  Quote asset: USDT")
        
    except Exception as e:
        print(f"Note: Demo mode - actual API calls would require valid credentials")
    
    return client


def demonstrate_order_placement():
    """Demonstrate order placement (simulation)"""
    print("\n=== Order Placement Demo ===")
    
    # This demonstrates the order placement structure
    print("Market Order Example:")
    print("  Symbol: BTCUSDT")
    print("  Side: BUY")
    print("  Type: MARKET")
    print("  Quantity: 0.001")
    print("  Expected result: Order filled at market price")
    
    print("\nLimit Order Example:")
    print("  Symbol: BTCUSDT")
    print("  Side: BUY")
    print("  Type: LIMIT")
    print("  Quantity: 0.001")
    print("  Price: $44,500.00")
    print("  Time in Force: GTC")
    print("  Expected result: Order placed, waiting for fill")
    
    print("\nOrder Status Check:")
    print("  Order ID: 12345678")
    print("  Status: FILLED")
    print("  Executed Quantity: 0.001")
    print("  Executed Price: $45,000.00")


def demonstrate_order_manager():
    """Demonstrate order manager functionality"""
    print("\n=== Order Manager Demo ===")
    
    # Create demo client and order manager
    client = BinanceClient("demo_key", "demo_secret", testnet=True)
    order_manager = OrderManager(client)
    
    # Create sample data
    decision = create_sample_trading_decision()
    portfolio = create_sample_portfolio()
    
    print(f"Trading Decision: {decision.action.value} {decision.suggested_amount:.1%}")
    print(f"Portfolio Value: ${portfolio.total_value_usdt:,.2f}")
    
    # Simulate order execution
    print(f"\nSimulating order execution...")
    print(f"Strategy: {OrderExecutionStrategy.MARKET.value}")
    
    # Calculate what would happen
    target_value = decision.suggested_amount * portfolio.total_value_usdt
    current_price = 45000.0  # Simulated current price
    target_quantity = target_value / current_price
    
    print(f"Target Position Value: ${target_value:,.2f}")
    print(f"Target Quantity: {target_quantity:.6f} BTC")
    print(f"Estimated Cost: ${target_quantity * current_price:,.2f}")
    
    # Simulate execution result
    print(f"\nSimulated Execution Result:")
    print(f"  Execution ID: EXEC_12345678_1706803198")
    print(f"  Status: FILLED")
    print(f"  Executed Quantity: {target_quantity:.6f}")
    print(f"  Average Price: ${current_price:,.2f}")
    print(f"  Total Cost: ${target_quantity * current_price:,.2f}")
    print(f"  Fill Percentage: 100.0%")
    
    # Show order manager status
    print(f"\nOrder Manager Status:")
    print(f"  Active Executions: 0")
    print(f"  Completed Executions: 1")
    print(f"  Success Rate: 100.0%")
    print(f"  Average Fill Time: 0.5 seconds")


def demonstrate_position_manager():
    """Demonstrate position manager functionality"""
    print("\n=== Position Manager Demo ===")
    
    # Create demo client and position manager
    client = BinanceClient("demo_key", "demo_secret", testnet=True)
    position_manager = PositionManager(client)
    
    # Simulate portfolio initialization
    print("Initializing portfolio from exchange...")
    print("Simulated Account Balances:")
    print("  BTC: 0.15000000")
    print("  USDT: 3,500.00")
    print("  Current BTC Price: $45,000.00")
    
    # Create simulated portfolio
    portfolio = Portfolio(
        btc_balance=0.15,
        usdt_balance=3500.0,
        total_value_usdt=10250.0,  # (0.15 * 45000) + 3500
        unrealized_pnl=0.0,
        positions=[
            Position(
                symbol="BTCUSDT",
                amount=0.15,
                entry_price=45000.0,
                current_price=45000.0,
                pnl=0.0,
                entry_time=datetime.utcnow()
            )
        ]
    )
    
    position_manager.current_portfolio = portfolio
    
    print(f"\nPortfolio Initialized:")
    print(f"  Total Value: ${portfolio.total_value_usdt:,.2f}")
    print(f"  BTC Balance: {portfolio.btc_balance:.6f}")
    print(f"  USDT Balance: ${portfolio.usdt_balance:,.2f}")
    print(f"  Positions: {len(portfolio.positions)}")
    
    # Simulate trade execution update
    print(f"\nSimulating trade execution...")
    print(f"Trade: BUY 0.02 BTC at $45,200.00")
    
    # Update position
    success = position_manager.update_position_from_trade(
        symbol="BTCUSDT",
        trade_quantity=0.02,
        trade_price=45200.0,
        trade_type=ActionType.BUY
    )
    
    if success:
        updated_portfolio = position_manager.current_portfolio
        btc_position = updated_portfolio.positions[0]
        
        print(f"Position Updated:")
        print(f"  New BTC Amount: {btc_position.amount:.6f}")
        print(f"  New Entry Price: ${btc_position.entry_price:,.2f}")
        print(f"  Current Price: ${btc_position.current_price:,.2f}")
        print(f"  P&L: ${btc_position.pnl:,.2f}")
        print(f"  New Portfolio Value: ${updated_portfolio.total_value_usdt:,.2f}")
    
    # Simulate price update
    print(f"\nSimulating price update...")
    print(f"New BTC Price: $46,000.00")
    
    # Update prices (simulated)
    if position_manager.current_portfolio:
        for position in position_manager.current_portfolio.positions:
            if position.symbol == "BTCUSDT":
                old_pnl = position.pnl
                position.current_price = 46000.0
                position.pnl = (position.current_price - position.entry_price) * position.amount
                
                print(f"Price Updated:")
                print(f"  Old P&L: ${old_pnl:,.2f}")
                print(f"  New P&L: ${position.pnl:,.2f}")
                print(f"  P&L Change: ${position.pnl - old_pnl:+,.2f}")
    
    # Show position manager status
    status = position_manager.get_position_manager_status()
    print(f"\nPosition Manager Status:")
    print(f"  Initialized: {status['initialized']}")
    print(f"  Portfolio Value: ${status['portfolio_summary']['total_value_usdt']:,.2f}")
    print(f"  Position Count: {status['portfolio_summary']['position_count']}")
    print(f"  Unrealized P&L: ${status['portfolio_summary']['unrealized_pnl']:,.2f}")


def demonstrate_integrated_execution():
    """Demonstrate integrated trading execution workflow"""
    print("\n=== Integrated Execution Workflow ===")
    
    # Initialize components
    client = BinanceClient("demo_key", "demo_secret", testnet=True)
    order_manager = OrderManager(client)
    position_manager = PositionManager(client)
    
    # Set up initial portfolio
    portfolio = create_sample_portfolio()
    position_manager.current_portfolio = portfolio
    
    print(f"Initial Portfolio:")
    print(f"  Total Value: ${portfolio.total_value_usdt:,.2f}")
    print(f"  BTC Position: {portfolio.positions[0].amount:.6f} BTC")
    print(f"  Entry Price: ${portfolio.positions[0].entry_price:,.2f}")
    print(f"  Current P&L: ${portfolio.positions[0].pnl:,.2f}")
    
    # Create trading decision
    decision = create_sample_trading_decision(ActionType.BUY, 0.85, 0.03)
    
    print(f"\nTrading Decision:")
    print(f"  Action: {decision.action.value}")
    print(f"  Confidence: {decision.confidence:.1%}")
    print(f"  Suggested Amount: {decision.suggested_amount:.1%}")
    print(f"  Risk Level: {decision.risk_level.value}")
    
    # Simulate execution workflow
    print(f"\n--- Execution Workflow ---")
    
    # Step 1: Calculate order parameters
    target_value = decision.suggested_amount * portfolio.total_value_usdt
    current_price = 45200.0
    target_quantity = target_value / current_price
    
    print(f"1. Order Calculation:")
    print(f"   Target Value: ${target_value:,.2f}")
    print(f"   Current Price: ${current_price:,.2f}")
    print(f"   Target Quantity: {target_quantity:.6f} BTC")
    
    # Step 2: Risk validation (simulated)
    print(f"2. Risk Validation:")
    print(f"   Position Size Check: ✓ Within limits")
    print(f"   Balance Check: ✓ Sufficient USDT")
    print(f"   Market Conditions: ✓ Normal trading")
    
    # Step 3: Order execution (simulated)
    print(f"3. Order Execution:")
    print(f"   Strategy: Market Order")
    print(f"   Order Placed: ✓")
    print(f"   Execution Time: 0.3 seconds")
    print(f"   Fill Status: FILLED")
    print(f"   Executed Price: ${current_price:,.2f}")
    print(f"   Slippage: $5.00 (0.01%)")
    
    # Step 4: Position update
    print(f"4. Position Update:")
    old_amount = portfolio.positions[0].amount
    old_entry_price = portfolio.positions[0].entry_price
    
    # Calculate new position
    total_cost = (old_amount * old_entry_price) + (target_quantity * current_price)
    new_amount = old_amount + target_quantity
    new_entry_price = total_cost / new_amount
    
    print(f"   Old Position: {old_amount:.6f} BTC at ${old_entry_price:,.2f}")
    print(f"   Trade: +{target_quantity:.6f} BTC at ${current_price:,.2f}")
    print(f"   New Position: {new_amount:.6f} BTC at ${new_entry_price:,.2f}")
    
    # Step 5: Portfolio reconciliation
    print(f"5. Portfolio Reconciliation:")
    new_btc_balance = portfolio.btc_balance + target_quantity
    new_usdt_balance = portfolio.usdt_balance - (target_quantity * current_price)
    new_total_value = (new_btc_balance * current_price) + new_usdt_balance
    
    print(f"   New BTC Balance: {new_btc_balance:.6f}")
    print(f"   New USDT Balance: ${new_usdt_balance:,.2f}")
    print(f"   New Total Value: ${new_total_value:,.2f}")
    
    # Step 6: Confirmation
    print(f"6. Execution Complete:")
    print(f"   ✓ Order filled successfully")
    print(f"   ✓ Position updated")
    print(f"   ✓ Portfolio synchronized")
    print(f"   ✓ Risk limits maintained")


def demonstrate_error_handling():
    """Demonstrate error handling scenarios"""
    print("\n=== Error Handling Demo ===")
    
    print("Common Error Scenarios:")
    
    print("\n1. Insufficient Balance:")
    print("   Error: Account has insufficient USDT balance")
    print("   Response: Order rejected, no position change")
    print("   Recovery: Reduce order size or add funds")
    
    print("\n2. Market Closed:")
    print("   Error: Market is closed for trading")
    print("   Response: Order queued for market open")
    print("   Recovery: Wait for market open or cancel order")
    
    print("\n3. Price Deviation:")
    print("   Error: Order price deviates too much from market")
    print("   Response: Order rejected for protection")
    print("   Recovery: Update price or use market order")
    
    print("\n4. Network Issues:")
    print("   Error: Connection timeout to exchange")
    print("   Response: Retry with exponential backoff")
    print("   Recovery: Check order status after reconnection")
    
    print("\n5. API Rate Limits:")
    print("   Error: Too many requests per minute")
    print("   Response: Implement request throttling")
    print("   Recovery: Wait and retry with rate limiting")
    
    print("\nError Recovery Mechanisms:")
    print("  - Automatic retry with backoff")
    print("  - Order status verification")
    print("  - Position reconciliation")
    print("  - Alert notifications")
    print("  - Manual intervention options")


def main():
    """Run all trading execution demonstrations"""
    print("Trading Execution System Demonstration")
    print("=" * 60)
    
    try:
        demonstrate_binance_client()
        demonstrate_order_placement()
        demonstrate_order_manager()
        demonstrate_position_manager()
        demonstrate_integrated_execution()
        demonstrate_error_handling()
        
        print("\n" + "=" * 60)
        print("Trading execution demonstration completed successfully!")
        print("\nNote: This demonstration uses simulated data and placeholder credentials.")
        print("For actual trading, you would need:")
        print("  1. Valid Binance testnet API credentials")
        print("  2. Testnet account with balances")
        print("  3. Proper error handling and monitoring")
        print("  4. Risk management integration")
        print("  5. Compliance with exchange requirements")
        
    except Exception as e:
        print(f"Error during demonstration: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()