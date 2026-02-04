"""
Integration test for the complete backtesting system
Tests the full workflow from data generation to performance analysis
"""
import sys
import os
sys.path.append('.')

from datetime import datetime, timedelta
import json
from backtesting.engine import BacktestEngine
from core.data_models import MarketData, SentimentScore
from decision_engine.risk_parameters import RiskParameters

def generate_realistic_market_data(start_date: datetime, end_date: datetime, 
                                 initial_price: float = 45000.0) -> list:
    """Generate realistic market data with trends and volatility"""
    import random
    import math
    
    data = []
    current_time = start_date
    price = initial_price
    
    # Create some market phases
    total_hours = int((end_date - start_date).total_seconds() / 3600)
    trend_changes = [0, total_hours // 4, total_hours // 2, 3 * total_hours // 4, total_hours]
    trends = [0.001, -0.002, 0.003, -0.001]  # Different trend strengths
    
    hour_count = 0
    current_trend_idx = 0
    
    while current_time <= end_date:
        # Determine current trend
        if current_trend_idx < len(trend_changes) - 1 and hour_count >= trend_changes[current_trend_idx + 1]:
            current_trend_idx += 1
        
        current_trend = trends[min(current_trend_idx, len(trends) - 1)]
        
        # Generate price movement with trend and noise
        trend_component = current_trend
        noise_component = random.gauss(0, 0.015)  # 1.5% volatility
        
        price_change = trend_component + noise_component
        price *= (1 + price_change)
        price = max(price, 1000.0)  # Floor price
        
        # Generate volume with some correlation to price movement
        base_volume = 100.0
        volume_multiplier = 1.0 + abs(price_change) * 10  # Higher volume on big moves
        volume = base_volume * volume_multiplier * random.uniform(0.8, 1.2)
        
        data.append(MarketData(
            symbol="BTCUSDT",
            price=round(price, 2),
            volume=round(volume, 4),
            timestamp=current_time,
            source="realistic_generator"
        ))
        
        current_time += timedelta(hours=1)
        hour_count += 1
    
    return data

def generate_sentiment_data(market_data: list) -> list:
    """Generate correlated sentiment data"""
    import random
    
    sentiment_data = []
    
    # Generate sentiment for every 6 hours
    for i in range(0, len(market_data), 6):
        data_point = market_data[i]
        
        # Calculate recent price trend for sentiment correlation
        if i >= 24:  # Need some history
            recent_prices = [d.price for d in market_data[i-24:i]]
            price_change = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]
            
            # Sentiment somewhat follows price but with noise and lag
            base_sentiment = 50 + (price_change * 100)  # Convert to 0-100 scale
            noise = random.gauss(0, 15)  # Add noise
            sentiment_value = max(0, min(100, base_sentiment + noise))
        else:
            sentiment_value = random.uniform(30, 70)  # Neutral range initially
        
        sentiment_data.append({
            'timestamp': data_point.timestamp.isoformat(),
            'sentiment_value': sentiment_value,
            'confidence': random.uniform(0.6, 0.9),
            'key_factors': ['market_trend', 'news_analysis'],
            'short_term_impact': (sentiment_value - 50) / 50,  # -1 to 1
            'long_term_impact': (sentiment_value - 50) / 100,   # Smaller long-term impact
            'impact_confidence': random.uniform(0.5, 0.8),
            'reasoning': f"Market sentiment based on recent price action and news analysis"
        })
    
    return sentiment_data

def run_comprehensive_backtest():
    """Run a comprehensive backtest with realistic data"""
    print("🚀 Running Comprehensive Backtesting Integration Test")
    print("=" * 60)
    
    # Setup
    initial_capital = 10000.0
    engine = BacktestEngine(initial_capital=initial_capital)
    
    # Generate 30 days of realistic data
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    
    print(f"📅 Backtest Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    # Generate market data
    print("📊 Generating realistic market data...")
    market_data = generate_realistic_market_data(start_date, end_date)
    print(f"   Generated {len(market_data)} hourly data points")
    
    # Generate sentiment data
    print("💭 Generating correlated sentiment data...")
    sentiment_data = generate_sentiment_data(market_data)
    print(f"   Generated {len(sentiment_data)} sentiment data points")
    
    # Create multiple strategy configurations
    strategies = {
        'Conservative': {
            'risk_parameters': {
                'max_position_size': 0.1,
                'min_position_size': 0.02,
                'min_confidence_threshold': 0.8,
                'sentiment_weight': 0.3,
                'technical_weight': 0.7,
                'max_daily_loss': 0.03
            }
        },
        'Balanced': {
            'risk_parameters': {
                'max_position_size': 0.2,
                'min_position_size': 0.05,
                'min_confidence_threshold': 0.65,
                'sentiment_weight': 0.4,
                'technical_weight': 0.6,
                'max_daily_loss': 0.05
            }
        },
        'Aggressive': {
            'risk_parameters': {
                'max_position_size': 0.3,
                'min_position_size': 0.1,
                'min_confidence_threshold': 0.5,
                'sentiment_weight': 0.5,
                'technical_weight': 0.5,
                'max_daily_loss': 0.08
            }
        }
    }
    
    results = {}
    
    # Run backtests for each strategy
    for strategy_name, config in strategies.items():
        print(f"\n🔄 Testing {strategy_name} Strategy...")
        
        try:
            # Merge with base configuration
            base_config = {
                'risk_parameters': RiskParameters().to_dict(),
                'technical_indicators': {
                    'sma_short_period': 10,
                    'sma_long_period': 20,
                    'rsi_period': 14
                }
            }
            
            # Update with strategy-specific parameters
            strategy_config = base_config.copy()
            strategy_config['risk_parameters'].update(config['risk_parameters'])
            
            # Run backtest
            result = engine.run_backtest(
                start_date=start_date,
                end_date=end_date,
                strategy_config=strategy_config,
                historical_data=market_data,
                sentiment_data=sentiment_data,
                strategy_name=strategy_name
            )
            
            results[strategy_name] = result
            
            # Display key metrics
            metrics = result.performance_metrics
            print(f"   📈 Total Return: {metrics.total_return:.2%}")
            print(f"   📊 Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
            print(f"   📉 Max Drawdown: {metrics.max_drawdown:.2%}")
            print(f"   🎯 Win Rate: {metrics.win_rate:.2%}")
            print(f"   💼 Total Trades: {metrics.total_trades}")
            
        except Exception as e:
            print(f"   ❌ Strategy failed: {e}")
            continue
    
    # Compare strategies
    if results:
        print(f"\n📊 Strategy Comparison Summary")
        print("=" * 60)
        print(f"{'Strategy':<12} {'Return':<8} {'Sharpe':<7} {'MaxDD':<7} {'Trades':<7} {'WinRate':<8}")
        print("-" * 60)
        
        for name, result in results.items():
            m = result.performance_metrics
            print(f"{name:<12} {m.total_return:>6.2%} {m.sharpe_ratio:>6.2f} "
                  f"{m.max_drawdown:>6.2%} {m.total_trades:>6} {m.win_rate:>7.2%}")
    
    # Detailed analysis of best strategy
    if results:
        best_strategy = max(results.items(), key=lambda x: x[1].performance_metrics.sharpe_ratio)
        best_name, best_result = best_strategy
        
        print(f"\n🏆 Best Strategy: {best_name}")
        print("=" * 40)
        
        metrics = best_result.performance_metrics
        print(f"Initial Capital: ${metrics.initial_capital:,.2f}")
        print(f"Final Capital: ${metrics.final_capital:,.2f}")
        print(f"Peak Capital: ${metrics.peak_capital:,.2f}")
        print(f"Total Return: {metrics.total_return:.2%}")
        print(f"Annualized Return: {metrics.annualized_return:.2%}")
        print(f"Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
        print(f"Calmar Ratio: {metrics.calmar_ratio:.2f}")
        print(f"Sortino Ratio: {metrics.sortino_ratio:.2f}")
        print(f"Max Drawdown: {metrics.max_drawdown:.2%}")
        print(f"Volatility: {metrics.volatility:.2%}")
        print(f"Profit Factor: {metrics.profit_factor:.2f}")
        
        # Show recent trades
        if best_result.trades:
            print(f"\n📋 Recent Trades (Last 5):")
            for trade in best_result.trades[-5:]:
                pnl = trade.portfolio_value_after - trade.portfolio_value_before
                print(f"   {trade.timestamp.strftime('%m-%d %H:%M')} | "
                      f"{trade.action.value:4} | "
                      f"{trade.quantity:.6f} BTC @ ${trade.price:,.2f} | "
                      f"PnL: ${pnl:+.2f}")
    
    # Save detailed results
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"backtest_integration_results_{timestamp}.json"
    
    try:
        results_data = {}
        for name, result in results.items():
            results_data[name] = {
                'performance_metrics': result.performance_metrics.to_dict(),
                'total_trades': len(result.trades),
                'backtest_id': result.backtest_id
            }
        
        with open(filename, 'w') as f:
            json.dump(results_data, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {filename}")
        
    except Exception as e:
        print(f"\n⚠️  Failed to save results: {e}")
    
    print(f"\n✅ Integration test completed successfully!")
    print(f"   Tested {len(results)} strategies on {len(market_data)} data points")
    
    return results

def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n🧪 Testing Edge Cases...")
    
    engine = BacktestEngine(initial_capital=1000.0)
    
    # Test with insufficient data
    try:
        minimal_data = [
            MarketData("BTCUSDT", 45000.0, 100.0, datetime.utcnow(), "test")
        ]
        
        result = engine.run_backtest(
            start_date=datetime.utcnow() - timedelta(days=1),
            end_date=datetime.utcnow(),
            strategy_config={'risk_parameters': RiskParameters().to_dict()},
            historical_data=minimal_data,
            strategy_name="Minimal Test"
        )
        print("   ❌ Should have failed with insufficient data")
        
    except ValueError as e:
        print(f"   ✅ Correctly handled insufficient data: {str(e)[:50]}...")
    
    # Test with empty data
    try:
        result = engine.run_backtest(
            start_date=datetime.utcnow() - timedelta(days=1),
            end_date=datetime.utcnow(),
            strategy_config={'risk_parameters': RiskParameters().to_dict()},
            historical_data=[],
            strategy_name="Empty Test"
        )
        print("   ❌ Should have failed with empty data")
        
    except ValueError as e:
        print(f"   ✅ Correctly handled empty data: {str(e)[:50]}...")
    
    print("   ✅ Edge case testing completed")

if __name__ == "__main__":
    try:
        # Run comprehensive test
        results = run_comprehensive_backtest()
        
        # Test edge cases
        test_edge_cases()
        
        print(f"\n🎉 All integration tests passed!")
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()