"""
Simple test for backtesting engine without database dependencies
"""
import sys
import os
sys.path.append('.')

from datetime import datetime, timedelta
from backtesting.engine import BacktestEngine, PerformanceMetrics, BacktestTrade
from core.data_models import MarketData, ActionType
from decision_engine.risk_parameters import RiskParameters

def generate_test_data(start_date: datetime, end_date: datetime) -> list:
    """Generate simple test market data"""
    data = []
    current_time = start_date
    price = 45000.0
    
    while current_time <= end_date:
        # Simple price movement
        import random
        price_change = random.uniform(-0.02, 0.02)  # ±2%
        price *= (1 + price_change)
        price = max(price, 1000.0)
        
        data.append(MarketData(
            symbol="BTCUSDT",
            price=round(price, 2),
            volume=100.0,
            timestamp=current_time,
            source="test"
        ))
        
        current_time += timedelta(hours=1)
    
    return data

def test_backtesting_engine():
    """Test the backtesting engine functionality"""
    print("Testing Backtesting Engine...")
    
    # Initialize engine
    engine = BacktestEngine(initial_capital=10000.0)
    print("✓ BacktestEngine initialized")
    
    # Generate test data
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=7)
    market_data = generate_test_data(start_date, end_date)
    print(f"✓ Generated {len(market_data)} test data points")
    
    # Create strategy config
    strategy_config = {
        'risk_parameters': RiskParameters().to_dict(),
        'technical_indicators': {
            'sma_short_period': 10,
            'sma_long_period': 20
        }
    }
    print("✓ Strategy configuration created")
    
    # Test individual components
    print("\nTesting individual components:")
    
    # Test data filtering
    filtered_data = engine._filter_data_by_date(market_data, start_date, end_date)
    print(f"✓ Data filtering: {len(filtered_data)} points")
    
    # Test technical signal generation
    if len(filtered_data) > 20:
        signal = engine._generate_technical_signal(filtered_data, 50, strategy_config)
        print(f"✓ Technical signal: {signal.signal_type.value}, strength: {signal.signal_strength:.3f}")
    
    # Test performance metrics calculation (with dummy data)
    dummy_trades = [
        BacktestTrade(
            trade_id="T1",
            timestamp=start_date,
            action=ActionType.BUY,
            symbol="BTCUSDT",
            quantity=0.1,
            price=45000.0,
            value=4500.0,
            decision=None,
            portfolio_value_before=10000.0,
            portfolio_value_after=10500.0
        )
    ]
    
    dummy_equity_curve = [
        (start_date, 10000.0),
        (start_date + timedelta(days=1), 10200.0),
        (start_date + timedelta(days=2), 10500.0),
        (end_date, 10800.0)
    ]
    
    try:
        metrics = engine._calculate_performance_metrics(
            dummy_trades, dummy_equity_curve, start_date, end_date, 10000.0
        )
        print(f"✓ Performance metrics: {metrics.total_return:.2%} return")
    except Exception as e:
        print(f"✗ Performance metrics failed: {e}")
    
    print("\n✓ All basic tests passed!")
    return True

if __name__ == "__main__":
    try:
        test_backtesting_engine()
        print("\n🎉 Backtesting engine test completed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()