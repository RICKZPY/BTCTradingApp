#!/usr/bin/env python3
"""
Example script demonstrating how to use the Historical Data CLI programmatically
"""
import subprocess
import sys
from pathlib import Path
from datetime import datetime

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


def run_cli_command(command_args):
    """
    Run a CLI command and return the result
    
    Args:
        command_args: List of command arguments
        
    Returns:
        Tuple of (stdout, stderr, return_code)
    """
    cmd = ['python', 'historical_cli.py'] + command_args
    print(f"\n{'='*60}")
    print(f"Running: {' '.join(cmd)}")
    print('='*60)
    
    result = subprocess.run(
        cmd,
        cwd=backend_dir,
        capture_output=True,
        text=True
    )
    
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr, file=sys.stderr)
    
    return result.stdout, result.stderr, result.returncode


def example_workflow():
    """
    Demonstrate a complete workflow using the CLI
    """
    print("\n" + "="*60)
    print("Historical Data CLI - Example Workflow")
    print("="*60)
    
    # 1. View help
    print("\n1. Viewing CLI help...")
    run_cli_command(['--help'])
    
    # 2. Check statistics
    print("\n2. Checking current statistics...")
    run_cli_command(['stats'])
    
    # 3. Example download command (commented out to avoid actual download)
    print("\n3. Example download command:")
    print("   python historical_cli.py download -e 2024-03-29")
    print("   (Skipped in this example)")
    
    # 4. Example import command
    print("\n4. Example import command:")
    print("   python historical_cli.py import-data -d data/downloads")
    print("   (Skipped - no data to import)")
    
    # 5. Example validate command
    print("\n5. Example validate command:")
    print("   python historical_cli.py validate --start-date 2024-03-01 --end-date 2024-03-31")
    print("   (Skipped - no data to validate)")
    
    # 6. Example export command
    print("\n6. Example export command:")
    print("   python historical_cli.py export -s 2024-03-01 -e 2024-03-31 -o export.csv")
    print("   (Skipped - no data to export)")
    
    print("\n" + "="*60)
    print("Example workflow complete!")
    print("="*60)


def example_direct_usage():
    """
    Demonstrate using the underlying classes directly (alternative to CLI)
    """
    print("\n" + "="*60)
    print("Direct Usage Example (Alternative to CLI)")
    print("="*60)
    
    from src.historical.manager import HistoricalDataManager
    
    # Initialize manager
    print("\nInitializing HistoricalDataManager...")
    manager = HistoricalDataManager(
        download_dir="data/downloads",
        db_path="data/btc_options.db"
    )
    
    # Get statistics
    print("\nGetting statistics...")
    stats = manager.get_stats()
    print(f"Download directory: {stats['download_dir']}")
    print(f"CSV files: {stats['csv_files']}")
    print(f"Total records: {stats['cache'].get('total_records', 0)}")
    
    # Get available instruments
    print("\nGetting available instruments...")
    instruments = manager.get_available_instruments()
    print(f"Total instruments: {len(instruments)}")
    if instruments:
        print(f"Sample: {', '.join(instruments[:5])}")
    
    # Get available dates
    print("\nGetting available dates...")
    dates = manager.get_available_dates()
    print(f"Total days with data: {len(dates)}")
    if dates:
        print(f"First date: {min(dates).date()}")
        print(f"Last date: {max(dates).date()}")
    
    print("\n" + "="*60)
    print("Direct usage example complete!")
    print("="*60)


def example_batch_operations():
    """
    Demonstrate batch operations
    """
    print("\n" + "="*60)
    print("Batch Operations Example")
    print("="*60)
    
    # Example: Download multiple dates
    print("\nExample: Batch download")
    print("Command:")
    print("  python historical_cli.py download \\")
    print("    -e 2024-03-29 \\")
    print("    -e 2024-04-26 \\")
    print("    -e 2024-05-31 \\")
    print("    -c 3")
    
    # Example: Import multiple files
    print("\nExample: Import multiple files")
    print("Command:")
    print("  python historical_cli.py import-data \\")
    print("    -f data/file1.csv \\")
    print("    -f data/file2.csv \\")
    print("    -f data/file3.csv")
    
    # Example: Export with filtering
    print("\nExample: Export with filtering")
    print("Command:")
    print("  python historical_cli.py export \\")
    print("    -s 2024-03-01 \\")
    print("    -e 2024-03-31 \\")
    print("    -i BTC-29MAR24-50000-C \\")
    print("    -i BTC-29MAR24-51000-C \\")
    print("    -f parquet \\")
    print("    -o filtered_export.parquet \\")
    print("    --compress")
    
    print("\n" + "="*60)
    print("Batch operations examples complete!")
    print("="*60)


def main():
    """
    Main function - run all examples
    """
    print("\n" + "="*80)
    print(" "*20 + "Historical Data CLI Examples")
    print("="*80)
    
    # Run workflow example
    example_workflow()
    
    # Run direct usage example
    try:
        example_direct_usage()
    except Exception as e:
        print(f"\nNote: Direct usage example failed (expected if no data): {e}")
    
    # Show batch operations examples
    example_batch_operations()
    
    print("\n" + "="*80)
    print("All examples complete!")
    print("="*80)
    print("\nFor more information, see:")
    print("  - HISTORICAL_CLI_QUICKSTART.md")
    print("  - HISTORICAL_CLI_GUIDE.md")
    print("  - src/historical/CLI_README.md")
    print()


if __name__ == '__main__':
    main()
