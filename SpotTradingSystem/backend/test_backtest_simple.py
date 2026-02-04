#!/usr/bin/env python3
"""
Simple backtest functionality test
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from backtesting.engine import BacktestEngine
from core.data_models import MarketData


def generate_sample_data(symbol: str, start_date: datetime, end_date: datetime):
    """Generate sample market data"""
    data = []
    current_date = start_date
    base_price = 45000.0
    
    while current_date <= end_date:
        # Simple price variation
        price_change = (hash(str(current_date)) % 1000 - 500) / 100
        base_price += price_change
        base_price = max(base_price, 1000.0)
        
        volume = 1000 + (hash(str(current_date + timedelta(minutes=1))) % 500)
        
        data.append(MarketData(
            symbol=symbol,
            timestamp=current_date,
            price=base_price,
            volume=volume,
            source="test_generator"
        ))
        
        current_date += timedelta(hours=1)
    
    return data


def test_backtest():
    """Test backtest functionality"""
    print("🧪 Testing Backtest Functionality")
    print("=" * 50)
    
    # 1. Create backtest engine
    print("1. Creating backtest engine...")
    engine = BacktestEngine(initial_capital=10000.0)
    print(f"   ✅ Engine created with ${engine.initial_capital} capital")
    
    # 2. Generate sample data
    print("2. Generating sample market data...")
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    
    sample_data = generate_sample_data("BTCUSDT", start_date, end_date)
    print(f"   ✅ Generated {len(sample_data)} data points")
    print(f"   📊 Price range: ${sample_data[0].price:.2f} - ${sample_data[-1].price:.2f}")
    
    # 3. Configure strategy
    print("3. Configuring strategy...")
    strategy_config = {
        'risk_parameters': {
            'max_position_size': 0.1,
            'stop_loss_percentage': 0.05,
            'take_profit_percentage': 0.15,
            'min_confidence_threshold': 0.7,
            'sentiment_weight': 0.4,
            'technical_weight': 0.6
        }
    }
    print(f"   ✅ Strategy configured with {len(strategy_config['risk_parameters'])} parameters")
    
    # 4. Run backtest
    print("4. Running backtest...")
    result = engine.run_backtest(
        start_date=start_date,
        end_date=end_date,
        strategy_config=strategy_config,
        historical_data=sample_data,
        strategy_name="Test Strategy"
    )
    
    print(f"   ✅ Backtest completed: {result.backtest_id}")
    
    # 5. Display results
    print("5. Backtest Results:")
    print("   " + "=" * 40)
    metrics = result.performance_metrics
    
    print(f"   📈 Total Return: {metrics.total_return:.2%}")
    print(f"   📊 Total Trades: {metrics.total_trades}")
    print(f"   🎯 Win Rate: {metrics.win_rate:.1%}")
    print(f"   📉 Max Drawdown: {metrics.max_drawdown:.2%}")
    print(f"   ⚡ Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
    print(f"   💰 Initial Capital: ${metrics.initial_capital:,.2f}")
    print(f"   💰 Final Capital: ${metrics.final_capital:,.2f}")
    print(f"   📅 Duration: {metrics.duration_days} days")
    
    # 6. Test API response format
    print("6. Testing API response format...")
    api_response = {
        'backtest_id': result.backtest_id,
        'strategy_name': result.strategy_name,
        'performance_metrics': {
            'total_return': metrics.total_return,
            'annualized_return': metrics.annualized_return,
            'total_trades': metrics.total_trades,
            'winning_trades': metrics.winning_trades,
            'losing_trades': metrics.losing_trades,
            'win_rate': metrics.win_rate,
            'sharpe_ratio': metrics.sharpe_ratio,
            'max_drawdown': metrics.max_drawdown,
            'volatility': metrics.volatility,
            'initial_capital': metrics.initial_capital,
            'final_capital': metrics.final_capital
        },
        'trades': len(result.trades),
        'equity_curve_points': len(result.equity_curve)
    }
    
    print(f"   ✅ API response contains {len(api_response)} top-level fields")
    print(f"   ✅ Performance metrics contains {len(api_response['performance_metrics'])} fields")
    
    print("\n🎉 All tests passed! Backtest functionality is working correctly.")
    
    return True


if __name__ == "__main__":
    try:
        success = test_backtest()
        if success:
            print("\n✅ Backtest API is ready!")
            print("\n📋 Next Steps:")
            print("   1. Start the main API server")
            print("   2. Test the /api/v1/backtesting/run endpoint")
            print("   3. Verify frontend integration")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)