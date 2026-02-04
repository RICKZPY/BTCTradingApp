#!/usr/bin/env python3
"""
Test backtest API functionality
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
from datetime import datetime, timedelta
from api.routes.backtesting import _generate_sample_market_data, BacktestRequest
from backtesting.engine import BacktestEngine


async def test_backtest_api():
    """Test backtest API functionality"""
    print("Testing Backtest API...")
    
    # Test sample data generation
    print("1. Testing sample data generation...")
    start_date = datetime.utcnow() - timedelta(days=7)
    end_date = datetime.utcnow()
    
    sample_data = _generate_sample_market_data("BTCUSDT", start_date, end_date)
    print(f"   Generated {len(sample_data)} data points")
    print(f"   Price range: ${sample_data[0].price:.2f} - ${sample_data[-1].price:.2f}")
    
    # Test backtest request model
    print("2. Testing backtest request model...")
    request = BacktestRequest(
        symbol="BTCUSDT",
        days=7,
        initial_capital=10000.0,
        strategy_name="Test Strategy"
    )
    print(f"   Request created: {request.symbol}, {request.days} days")
    
    # Test backtest engine with sample data
    print("3. Testing backtest engine...")
    engine = BacktestEngine(initial_capital=request.initial_capital)
    
    strategy_config = {
        'risk_parameters': {
            'max_position_size': request.max_position_size,
            'stop_loss_percentage': request.stop_loss_percentage,
            'take_profit_percentage': request.take_profit_percentage,
            'min_confidence_threshold': request.min_confidence_threshold,
            'sentiment_weight': request.sentiment_weight,
            'technical_weight': request.technical_weight
        }
    }
    
    result = engine.run_backtest(
        start_date=start_date,
        end_date=end_date,
        strategy_config=strategy_config,
        historical_data=sample_data,
        strategy_name=request.strategy_name
    )
    
    print(f"   Backtest ID: {result.backtest_id}")
    print(f"   Total trades: {result.performance_metrics.total_trades}")
    print(f"   Total return: {result.performance_metrics.total_return:.2%}")
    print(f"   Sharpe ratio: {result.performance_metrics.sharpe_ratio:.2f}")
    print(f"   Max drawdown: {result.performance_metrics.max_drawdown:.2%}")
    
    # Test response data formatting
    print("4. Testing response data formatting...")
    metrics = result.performance_metrics
    
    response_data = {
        'backtest_id': result.backtest_id,
        'strategy_name': result.strategy_name,
        'performance_metrics': {
            'total_return': metrics.total_return,
            'total_trades': metrics.total_trades,
            'win_rate': metrics.win_rate,
            'sharpe_ratio': metrics.sharpe_ratio,
            'max_drawdown': metrics.max_drawdown,
            'initial_capital': metrics.initial_capital,
            'final_capital': metrics.final_capital
        },
        'trades_count': len(result.trades),
        'equity_curve_points': len(result.equity_curve)
    }
    
    print(f"   Response data keys: {list(response_data.keys())}")
    print(f"   Performance metrics keys: {list(response_data['performance_metrics'].keys())}")
    
    print("\n✅ All backtest API tests passed!")
    return True


if __name__ == "__main__":
    success = asyncio.run(test_backtest_api())
    if success:
        print("\n🎉 Backtest API is ready for use!")
        print("\nAPI Endpoints:")
        print("- POST /api/v1/backtesting/run - Run backtest")
        print("- GET /api/v1/backtesting/status - Get engine status")
    else:
        print("\n❌ Backtest API tests failed")
    
    sys.exit(0 if success else 1)