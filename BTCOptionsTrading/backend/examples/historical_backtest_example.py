#!/usr/bin/env python3
"""
Example: Using Historical Data in Backtests

This example demonstrates how to use historical options data in backtesting.
It covers:
- Loading historical data for backtests
- Configuring backtest engine with historical data
- Running backtests with different data sources
- Handling missing data

Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
from decimal import Decimal

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from src.historical.manager import HistoricalDataManager
from src.backtest.backtest_engine import BacktestEngine
from src.strategy.strategy_manager import StrategyManager


def example_1_simple_backtest_with_historical_data():
    """
    Example 1: Simple backtest using historical data
    
    This is the easiest way to run a backtest with historical data.
    """
    print("\n" + "="*80)
    print("Example 1: Simple Backtest with Historical Data")
    print("="*80)
    
    # Initialize historical data manager
    manager = HistoricalDataManager(
        download_dir="data/downloads",
        db_path="data/btc_options.db"
    )
    
    # Define backtest period
    start_date = datetime(2024, 3, 1)
    end_date = datetime(2024, 3, 31)
    
    print(f"\nBacktest period: {start_date.date()} to {end_date.date()}")
    
    # Get historical data for backtest
    print("\nLoading historical data...")
    backtest_data = manager.get_data_for_backtest(
        start_date=start_date,
        end_date=end_date,
        strikes=None  # Load all strikes
    )
    
    print(f"✓ Loaded data for {len(backtest_data.options_data)} instruments")
    print(f"  Coverage: {backtest_data.coverage_stats.coverage_percentage:.1f}%")
    
    # Configure backtest engine with historical data
    print("\nConfiguring backtest engine...")
    engine = BacktestEngine(
        data_source='historical',
        historical_data=backtest_data
    )
    
    # Define a simple strategy (example)
    strategy_config = {
        'name': 'Simple Call Spread',
        'type': 'vertical_spread',
        'direction': 'bullish',
        'entry_rules': {
            'min_dte': 7,
            'max_dte': 30,
            'strike_selection': 'atm'
        },
        'exit_rules': {
            'profit_target': 0.5,
            'stop_loss': 0.3,
            'max_hold_days': 7
        }
    }
    
    # Run backtest
    print("\nRunning backtest...")
    results = engine.run_backtest(
        strategy=strategy_config,
        start_date=start_date,
        end_date=end_date,
        initial_capital=10000
    )
    
    # Print results
    print("\n" + "-"*80)
    print("Backtest Results:")
    print("-"*80)
    print(f"Total trades: {results.total_trades}")
    print(f"Winning trades: {results.winning_trades}")
    print(f"Losing trades: {results.losing_trades}")
    print(f"Win rate: {results.win_rate:.1f}%")
    print(f"Total return: {results.total_return:.2f}%")
    print(f"Max drawdown: {results.max_drawdown:.2f}%")
    print(f"Sharpe ratio: {results.sharpe_ratio:.2f}")
    print(f"Final capital: ${results.final_capital:,.2f}")
    
    print("\n✓ Simple backtest complete!")


def example_2_backtest_with_specific_strikes():
    """
    Example 2: Backtest with specific strike prices
    
    This example shows how to load data for specific strikes only,
    which is more efficient for strategies that use limited strikes.
    """
    print("\n" + "="*80)
    print("Example 2: Backtest with Specific Strikes")
    print("="*80)
    
    manager = HistoricalDataManager(
        download_dir="data/downloads",
        db_path="data/btc_options.db"
    )
    
    # Define backtest parameters
    start_date = datetime(2024, 3, 1)
    end_date = datetime(2024, 3, 31)
    
    # Specify strikes to load (more efficient)
    strikes = [
        Decimal('48000'),
        Decimal('50000'),
        Decimal('52000'),
        Decimal('54000'),
        Decimal('56000'),
    ]
    
    print(f"\nBacktest period: {start_date.date()} to {end_date.date()}")
    print(f"Loading data for {len(strikes)} strikes:")
    for strike in strikes:
        print(f"  - ${strike:,.0f}")
    
    # Load data for specific strikes
    backtest_data = manager.get_data_for_backtest(
        start_date=start_date,
        end_date=end_date,
        strikes=strikes
    )
    
    print(f"\n✓ Loaded data for {len(backtest_data.options_data)} instruments")
    
    # Configure and run backtest
    engine = BacktestEngine(
        data_source='historical',
        historical_data=backtest_data
    )
    
    strategy_config = {
        'name': 'Iron Condor',
        'type': 'iron_condor',
        'strikes': strikes,
        'entry_rules': {
            'min_dte': 14,
            'max_dte': 21,
        },
        'exit_rules': {
            'profit_target': 0.5,
            'stop_loss': 0.5,
        }
    }
    
    print("\nRunning backtest with specific strikes...")
    results = engine.run_backtest(
        strategy=strategy_config,
        start_date=start_date,
        end_date=end_date,
        initial_capital=10000
    )
    
    print(f"\n✓ Backtest complete: {results.total_trades} trades executed")


def example_3_check_data_coverage_before_backtest():
    """
    Example 3: Check data coverage before running backtest
    
    This example shows how to verify data availability and coverage
    before running a backtest to avoid issues.
    """
    print("\n" + "="*80)
    print("Example 3: Check Data Coverage Before Backtest")
    print("="*80)
    
    manager = HistoricalDataManager(
        download_dir="data/downloads",
        db_path="data/btc_options.db"
    )
    
    # Define desired backtest period
    start_date = datetime(2024, 3, 1)
    end_date = datetime(2024, 3, 31)
    
    print(f"\nDesired backtest period: {start_date.date()} to {end_date.date()}")
    
    # Check coverage first
    print("\nChecking data coverage...")
    coverage_stats = manager.get_coverage_stats(
        start_date=start_date,
        end_date=end_date
    )
    
    print("\n" + "-"*80)
    print("Coverage Statistics:")
    print("-"*80)
    print(f"Total records: {coverage_stats.total_records:,}")
    print(f"Coverage percentage: {coverage_stats.coverage_percentage:.1f}%")
    print(f"Available instruments: {coverage_stats.available_instruments}")
    print(f"Date range: {coverage_stats.date_range[0].date()} to {coverage_stats.date_range[1].date()}")
    
    if coverage_stats.missing_dates:
        print(f"\nMissing dates: {len(coverage_stats.missing_dates)}")
        for date in coverage_stats.missing_dates[:5]:  # Show first 5
            print(f"  - {date.date()}")
        if len(coverage_stats.missing_dates) > 5:
            print(f"  ... and {len(coverage_stats.missing_dates) - 5} more")
    
    # Decide whether to proceed
    if coverage_stats.coverage_percentage < 80:
        print("\n⚠ Warning: Coverage is below 80%")
        print("Consider downloading more data or adjusting the backtest period")
        return
    elif coverage_stats.coverage_percentage < 95:
        print("\n⚠ Notice: Coverage is acceptable but not ideal")
        print("Results may be affected by missing data")
    else:
        print("\n✓ Coverage is good - proceeding with backtest")
    
    # Load data and run backtest
    backtest_data = manager.get_data_for_backtest(
        start_date=start_date,
        end_date=end_date
    )
    
    engine = BacktestEngine(
        data_source='historical',
        historical_data=backtest_data
    )
    
    print("\nRunning backtest...")
    # ... run backtest ...
    
    print("\n✓ Coverage check and backtest complete!")


def example_4_hybrid_data_source():
    """
    Example 4: Hybrid data source (historical + live)
    
    This example shows how to use historical data for the past and
    live API data for recent periods.
    """
    print("\n" + "="*80)
    print("Example 4: Hybrid Data Source (Historical + Live)")
    print("="*80)
    
    manager = HistoricalDataManager(
        download_dir="data/downloads",
        db_path="data/btc_options.db"
    )
    
    # Define backtest period
    # Use historical data up to 7 days ago, live data for recent days
    cutoff_date = datetime.now() - timedelta(days=7)
    start_date = datetime.now() - timedelta(days=30)
    end_date = datetime.now()
    
    print(f"\nBacktest period: {start_date.date()} to {end_date.date()}")
    print(f"Historical data cutoff: {cutoff_date.date()}")
    print(f"  - Historical: {start_date.date()} to {cutoff_date.date()}")
    print(f"  - Live API: {cutoff_date.date()} to {end_date.date()}")
    
    # Load historical data
    print("\nLoading historical data...")
    historical_data = manager.get_data_for_backtest(
        start_date=start_date,
        end_date=cutoff_date
    )
    
    print(f"✓ Loaded historical data: {len(historical_data.options_data)} instruments")
    
    # Configure backtest engine with hybrid mode
    print("\nConfiguring hybrid backtest engine...")
    engine = BacktestEngine(
        data_source='hybrid',
        historical_data=historical_data,
        historical_cutoff=cutoff_date
    )
    
    print("\nRunning hybrid backtest...")
    print("  - Using historical data for past period")
    print("  - Using live API for recent period")
    
    # ... run backtest ...
    
    print("\n✓ Hybrid backtest complete!")


def example_5_handle_missing_data():
    """
    Example 5: Handle missing data gracefully
    
    This example shows how to handle situations where historical data
    is incomplete or missing for the backtest period.
    """
    print("\n" + "="*80)
    print("Example 5: Handle Missing Data")
    print("="*80)
    
    manager = HistoricalDataManager(
        download_dir="data/downloads",
        db_path="data/btc_options.db"
    )
    
    # Try to load data for a period that might have gaps
    start_date = datetime(2024, 3, 1)
    end_date = datetime(2024, 3, 31)
    
    print(f"\nAttempting to load data for: {start_date.date()} to {end_date.date()}")
    
    try:
        # Check coverage first
        coverage_stats = manager.get_coverage_stats(
            start_date=start_date,
            end_date=end_date
        )
        
        if coverage_stats.coverage_percentage < 50:
            print(f"\n✗ Insufficient data: {coverage_stats.coverage_percentage:.1f}% coverage")
            print("\nOptions:")
            print("1. Download missing data:")
            if coverage_stats.missing_dates:
                print(f"   Missing dates: {len(coverage_stats.missing_dates)}")
                # Suggest expiry dates to download
                print("   Suggested downloads:")
                print("   python historical_cli.py download -e 2024-03-29")
            
            print("\n2. Adjust backtest period to available data:")
            if coverage_stats.date_range:
                print(f"   Available: {coverage_stats.date_range[0].date()} "
                      f"to {coverage_stats.date_range[1].date()}")
            
            print("\n3. Use hybrid mode with live API data")
            return
        
        # Load data
        backtest_data = manager.get_data_for_backtest(
            start_date=start_date,
            end_date=end_date
        )
        
        # Check for gaps in loaded data
        if backtest_data.coverage_stats.missing_dates:
            print(f"\n⚠ Warning: Data has {len(backtest_data.coverage_stats.missing_dates)} "
                  f"missing dates")
            print("Backtest will skip these dates")
        
        # Configure backtest with gap handling
        engine = BacktestEngine(
            data_source='historical',
            historical_data=backtest_data,
            handle_missing_data='skip'  # Options: 'skip', 'interpolate', 'error'
        )
        
        print("\nRunning backtest with gap handling...")
        # ... run backtest ...
        
        print("\n✓ Backtest complete despite data gaps")
        
    except ValueError as e:
        print(f"\n✗ Error: {e}")
        print("Unable to proceed with backtest")


def example_6_compare_data_sources():
    """
    Example 6: Compare results from different data sources
    
    This example shows how to run the same backtest with different
    data sources to compare results.
    """
    print("\n" + "="*80)
    print("Example 6: Compare Data Sources")
    print("="*80)
    
    manager = HistoricalDataManager(
        download_dir="data/downloads",
        db_path="data/btc_options.db"
    )
    
    # Define backtest parameters
    start_date = datetime(2024, 3, 1)
    end_date = datetime(2024, 3, 31)
    
    strategy_config = {
        'name': 'Test Strategy',
        'type': 'simple',
        'entry_rules': {'min_dte': 7},
        'exit_rules': {'profit_target': 0.5}
    }
    
    print(f"\nBacktest period: {start_date.date()} to {end_date.date()}")
    print("Running same strategy with different data sources...\n")
    
    # 1. Historical data
    print("1. Using historical data...")
    historical_data = manager.get_data_for_backtest(
        start_date=start_date,
        end_date=end_date
    )
    
    engine_historical = BacktestEngine(
        data_source='historical',
        historical_data=historical_data
    )
    
    results_historical = engine_historical.run_backtest(
        strategy=strategy_config,
        start_date=start_date,
        end_date=end_date,
        initial_capital=10000
    )
    
    print(f"   Total return: {results_historical.total_return:.2f}%")
    print(f"   Sharpe ratio: {results_historical.sharpe_ratio:.2f}")
    
    # 2. Live API data (if available)
    print("\n2. Using live API data...")
    engine_live = BacktestEngine(
        data_source='live'
    )
    
    try:
        results_live = engine_live.run_backtest(
            strategy=strategy_config,
            start_date=start_date,
            end_date=end_date,
            initial_capital=10000
        )
        
        print(f"   Total return: {results_live.total_return:.2f}%")
        print(f"   Sharpe ratio: {results_live.sharpe_ratio:.2f}")
        
        # Compare results
        print("\n" + "-"*80)
        print("Comparison:")
        print("-"*80)
        print(f"Return difference: {abs(results_historical.total_return - results_live.total_return):.2f}%")
        print(f"Sharpe difference: {abs(results_historical.sharpe_ratio - results_live.sharpe_ratio):.2f}")
        
    except Exception as e:
        print(f"   ✗ Live API not available: {e}")
    
    print("\n✓ Data source comparison complete!")


def main():
    """
    Run all examples
    """
    print("\n" + "="*80)
    print(" "*20 + "Historical Backtest Examples")
    print("="*80)
    print("\nThese examples demonstrate how to use historical data in backtests.")
    print("\nNote: Some examples may be skipped if required data is not available.")
    
    # Run examples
    examples = [
        ("Simple Backtest", example_1_simple_backtest_with_historical_data),
        ("Specific Strikes", example_2_backtest_with_specific_strikes),
        ("Coverage Check", example_3_check_data_coverage_before_backtest),
        ("Hybrid Data Source", example_4_hybrid_data_source),
        ("Handle Missing Data", example_5_handle_missing_data),
        ("Compare Data Sources", example_6_compare_data_sources),
    ]
    
    for name, example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"\n✗ Example '{name}' failed: {e}")
            print("This is expected if data is not available")
    
    print("\n" + "="*80)
    print("All examples complete!")
    print("="*80)
    print("\nFor more information, see:")
    print("  - HISTORICAL_DATA_GUIDE.md")
    print("  - BACKTEST_GUIDE.md")
    print("  - .kiro/specs/historical-data-integration/design.md")
    print()


if __name__ == '__main__':
    main()
