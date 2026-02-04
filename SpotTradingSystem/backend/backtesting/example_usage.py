"""
Backtesting Engine Example Usage
Demonstrates how to use the backtesting engine for strategy validation
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
import json

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backtesting.engine import BacktestEngine, BacktestResult
from backtesting.data_provider import HistoricalDataProvider
from decision_engine.risk_parameters import RiskParameters

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_sample_strategy_config() -> Dict[str, Any]:
    """Create sample strategy configuration"""
    return {
        'strategy_name': 'SMA Crossover with Sentiment',
        'risk_parameters': {
            'max_position_size': 0.2,  # 20% of portfolio
            'min_position_size': 0.05,  # 5% of portfolio
            'max_daily_loss': 0.05,    # 5% daily loss limit
            'max_portfolio_risk': 0.3,  # 30% portfolio risk limit
            'min_confidence_threshold': 0.6,  # 60% minimum confidence
            'high_confidence_threshold': 0.8,  # 80% high confidence
            'sentiment_weight': 0.3,    # 30% weight for sentiment
            'technical_weight': 0.7,    # 70% weight for technical
            'trade_cooldown_minutes': 60,  # 1 hour cooldown
            'max_volatility_threshold': 0.05  # 5% volatility threshold
        },
        'technical_indicators': {
            'sma_short_period': 10,
            'sma_long_period': 20,
            'rsi_period': 14,
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9
        }
    }


def run_sample_backtest():
    """Run a sample backtest with generated data"""
    logger.info("Starting sample backtest demonstration")
    
    # Initialize components
    data_provider = HistoricalDataProvider()
    backtest_engine = BacktestEngine(initial_capital=10000.0)
    
    # Set date range (last 30 days)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    
    logger.info(f"Backtest period: {start_date} to {end_date}")
    
    # Try to get real data first, fallback to sample data
    market_data = data_provider.get_market_data("BTCUSDT", start_date, end_date)
    
    if len(market_data) < 100:
        logger.info("Insufficient real data, generating sample data")
        market_data = data_provider.generate_sample_data(
            start_date, end_date, interval_minutes=60
        )
    
    # Validate data quality
    validation = data_provider.validate_data_quality(market_data)
    logger.info(f"Data validation: {validation['valid']}, {validation['data_points']} points")
    
    if validation['issues']:
        logger.warning(f"Data issues: {validation['issues']}")
    
    # Get sentiment data (if available)
    sentiment_data = data_provider.get_sentiment_data(start_date, end_date)
    
    # Create strategy configuration
    strategy_config = create_sample_strategy_config()
    
    try:
        # Run backtest
        result = backtest_engine.run_backtest(
            start_date=start_date,
            end_date=end_date,
            strategy_config=strategy_config,
            historical_data=market_data,
            sentiment_data=sentiment_data if sentiment_data else None,
            strategy_name="Sample SMA Strategy"
        )
        
        # Display results
        display_backtest_results(result)
        
        return result
        
    except Exception as e:
        logger.error(f"Backtest failed: {e}")
        return None


def display_backtest_results(result: BacktestResult):
    """Display backtest results in a formatted way"""
    print("\n" + "="*60)
    print(f"BACKTEST RESULTS: {result.strategy_name}")
    print("="*60)
    
    metrics = result.performance_metrics
    
    print(f"Backtest ID: {result.backtest_id}")
    print(f"Period: {metrics.start_date.strftime('%Y-%m-%d')} to {metrics.end_date.strftime('%Y-%m-%d')}")
    print(f"Duration: {metrics.duration_days} days")
    print()
    
    print("PERFORMANCE METRICS:")
    print("-" * 30)
    print(f"Initial Capital: ${metrics.initial_capital:,.2f}")
    print(f"Final Capital: ${metrics.final_capital:,.2f}")
    print(f"Total Return: {metrics.total_return:.2%}")
    print(f"Annualized Return: {metrics.annualized_return:.2%}")
    print(f"Peak Capital: ${metrics.peak_capital:,.2f}")
    print()
    
    print("RISK METRICS:")
    print("-" * 30)
    print(f"Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
    print(f"Max Drawdown: {metrics.max_drawdown:.2%}")
    print(f"Max Drawdown Duration: {metrics.max_drawdown_duration} days")
    print(f"Volatility: {metrics.volatility:.2%}")
    print(f"Calmar Ratio: {metrics.calmar_ratio:.2f}")
    print(f"Sortino Ratio: {metrics.sortino_ratio:.2f}")
    print()
    
    print("TRADE METRICS:")
    print("-" * 30)
    print(f"Total Trades: {metrics.total_trades}")
    print(f"Winning Trades: {metrics.winning_trades}")
    print(f"Losing Trades: {metrics.losing_trades}")
    print(f"Win Rate: {metrics.win_rate:.2%}")
    print(f"Profit Factor: {metrics.profit_factor:.2f}")
    print(f"Average Win: ${metrics.average_win:.2f}")
    print(f"Average Loss: ${metrics.average_loss:.2f}")
    print(f"Largest Win: ${metrics.largest_win:.2f}")
    print(f"Largest Loss: ${metrics.largest_loss:.2f}")
    print()
    
    if result.trades:
        print("RECENT TRADES:")
        print("-" * 30)
        for trade in result.trades[-5:]:  # Show last 5 trades
            print(f"{trade.timestamp.strftime('%Y-%m-%d %H:%M')} | "
                  f"{trade.action.value:4} | "
                  f"{trade.quantity:.6f} BTC @ ${trade.price:.2f} | "
                  f"Value: ${trade.value:.2f}")
    
    print("\n" + "="*60)


def run_strategy_comparison():
    """Compare multiple strategy configurations"""
    logger.info("Running strategy comparison")
    
    data_provider = HistoricalDataProvider()
    
    # Generate sample data for consistent comparison
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    market_data = data_provider.generate_sample_data(start_date, end_date)
    
    # Define different strategies
    strategies = [
        {
            'name': 'Conservative',
            'config': {
                'risk_parameters': {
                    'max_position_size': 0.1,
                    'min_confidence_threshold': 0.8,
                    'sentiment_weight': 0.5,
                    'technical_weight': 0.5
                }
            }
        },
        {
            'name': 'Aggressive',
            'config': {
                'risk_parameters': {
                    'max_position_size': 0.3,
                    'min_confidence_threshold': 0.5,
                    'sentiment_weight': 0.3,
                    'technical_weight': 0.7
                }
            }
        },
        {
            'name': 'Sentiment-Focused',
            'config': {
                'risk_parameters': {
                    'max_position_size': 0.2,
                    'min_confidence_threshold': 0.6,
                    'sentiment_weight': 0.7,
                    'technical_weight': 0.3
                }
            }
        }
    ]
    
    results = []
    
    for strategy in strategies:
        logger.info(f"Testing {strategy['name']} strategy")
        
        # Merge with base config
        base_config = create_sample_strategy_config()
        strategy_config = {**base_config, **strategy['config']}
        strategy_config['risk_parameters'] = {
            **base_config['risk_parameters'],
            **strategy['config']['risk_parameters']
        }
        
        backtest_engine = BacktestEngine(initial_capital=10000.0)
        
        try:
            result = backtest_engine.run_backtest(
                start_date=start_date,
                end_date=end_date,
                strategy_config=strategy_config,
                historical_data=market_data,
                strategy_name=strategy['name']
            )
            
            results.append({
                'name': strategy['name'],
                'result': result,
                'return': result.performance_metrics.total_return,
                'sharpe': result.performance_metrics.sharpe_ratio,
                'max_drawdown': result.performance_metrics.max_drawdown,
                'trades': result.performance_metrics.total_trades
            })
            
        except Exception as e:
            logger.error(f"Strategy {strategy['name']} failed: {e}")
    
    # Display comparison
    print("\n" + "="*80)
    print("STRATEGY COMPARISON")
    print("="*80)
    print(f"{'Strategy':<15} {'Return':<10} {'Sharpe':<8} {'Max DD':<8} {'Trades':<8}")
    print("-" * 80)
    
    for result in sorted(results, key=lambda x: x['return'], reverse=True):
        print(f"{result['name']:<15} "
              f"{result['return']:>8.2%} "
              f"{result['sharpe']:>7.2f} "
              f"{result['max_drawdown']:>7.2%} "
              f"{result['trades']:>7}")
    
    print("="*80)
    
    return results


def save_backtest_results(result: BacktestResult, filename: str = None):
    """Save backtest results to JSON file"""
    if not filename:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"backtest_result_{timestamp}.json"
    
    # Convert result to dictionary
    result_dict = {
        'backtest_info': result.to_dict(),
        'performance_metrics': result.performance_metrics.to_dict(),
        'trades': [trade.to_dict() for trade in result.trades],
        'equity_curve': [
            {'timestamp': ts.isoformat(), 'value': value}
            for ts, value in result.equity_curve
        ],
        'drawdown_curve': [
            {'timestamp': ts.isoformat(), 'drawdown': dd}
            for ts, dd in result.drawdown_curve
        ]
    }
    
    try:
        with open(filename, 'w') as f:
            json.dump(result_dict, f, indent=2, default=str)
        
        logger.info(f"Backtest results saved to {filename}")
        return filename
        
    except Exception as e:
        logger.error(f"Failed to save results: {e}")
        return None


def main():
    """Main demonstration function"""
    print("Bitcoin Trading System - Backtesting Engine Demo")
    print("=" * 50)
    
    # Run sample backtest
    result = run_sample_backtest()
    
    if result:
        # Save results
        filename = save_backtest_results(result)
        
        # Run strategy comparison
        print("\n")
        comparison_results = run_strategy_comparison()
        
        print(f"\nDemo completed successfully!")
        if filename:
            print(f"Results saved to: {filename}")
    else:
        print("Demo failed - check logs for details")


if __name__ == "__main__":
    main()