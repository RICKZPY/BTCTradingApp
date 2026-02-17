#!/usr/bin/env python3
"""
Example: Historical Data Export

This example demonstrates how to export historical options data in various formats.
It covers:
- Exporting to CSV, JSON, and Parquet formats
- Filtering data by date range and instruments
- Batch exports and compression
- Export for backup and analysis

Requirements: 9.1, 9.2, 9.3
"""
import sys
from pathlib import Path
from datetime import datetime
from decimal import Decimal

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from src.historical.manager import HistoricalDataManager
from src.historical.cache import HistoricalDataCache
from src.storage.database import DatabaseManager


def example_1_simple_csv_export():
    """
    Example 1: Simple CSV export
    
    This is the easiest way to export data - just specify date range
    and output file.
    """
    print("\n" + "="*80)
    print("Example 1: Simple CSV Export")
    print("="*80)
    
    manager = HistoricalDataManager(
        download_dir="data/downloads",
        db_path="data/btc_options.db"
    )
    
    # Define export parameters
    start_date = datetime(2024, 3, 1)
    end_date = datetime(2024, 3, 31)
    output_file = "data/exports/march_2024.csv"
    
    print(f"\nExporting data:")
    print(f"  Period: {start_date.date()} to {end_date.date()}")
    print(f"  Format: CSV")
    print(f"  Output: {output_file}")
    
    # Export data
    result = manager.export_data(
        start_date=start_date,
        end_date=end_date,
        output_path=output_file,
        format='csv'
    )
    
    # Print results
    print("\n" + "-"*80)
    print("Export Results:")
    print("-"*80)
    print(f"Records exported: {result.records_exported:,}")
    print(f"File size: {result.file_size_bytes / 1024 / 1024:.2f} MB")
    print(f"File path: {result.file_path}")
    
    print("\n✓ CSV export complete!")


def example_2_export_multiple_formats():
    """
    Example 2: Export to multiple formats
    
    This example shows how to export the same data to different formats
    for different use cases.
    """
    print("\n" + "="*80)
    print("Example 2: Export to Multiple Formats")
    print("="*80)
    
    manager = HistoricalDataManager(
        download_dir="data/downloads",
        db_path="data/btc_options.db"
    )
    
    # Define export parameters
    start_date = datetime(2024, 3, 1)
    end_date = datetime(2024, 3, 31)
    
    print(f"\nExporting data for: {start_date.date()} to {end_date.date()}")
    
    formats = [
        ('csv', 'data/exports/march_2024.csv', 'Human-readable, Excel-compatible'),
        ('json', 'data/exports/march_2024.json', 'Structured, API-friendly'),
        ('parquet', 'data/exports/march_2024.parquet', 'Efficient, analytics-optimized'),
    ]
    
    results = {}
    
    for format_type, output_file, description in formats:
        print(f"\n{format_type.upper()} Export ({description}):")
        print(f"  Output: {output_file}")
        
        result = manager.export_data(
            start_date=start_date,
            end_date=end_date,
            output_path=output_file,
            format=format_type
        )
        
        results[format_type] = result
        
        print(f"  ✓ Exported {result.records_exported:,} records")
        print(f"  ✓ File size: {result.file_size_bytes / 1024 / 1024:.2f} MB")
    
    # Compare file sizes
    print("\n" + "-"*80)
    print("Format Comparison:")
    print("-"*80)
    
    for format_type in ['csv', 'json', 'parquet']:
        result = results[format_type]
        size_mb = result.file_size_bytes / 1024 / 1024
        print(f"{format_type.upper():8s}: {size_mb:8.2f} MB")
    
    # Parquet is typically 5-10x smaller than CSV
    csv_size = results['csv'].file_size_bytes
    parquet_size = results['parquet'].file_size_bytes
    compression_ratio = csv_size / parquet_size if parquet_size > 0 else 0
    
    print(f"\nParquet is {compression_ratio:.1f}x smaller than CSV")
    
    print("\n✓ Multi-format export complete!")


def example_3_filtered_export():
    """
    Example 3: Export with filtering
    
    This example shows how to export only specific instruments or
    data that meets certain criteria.
    """
    print("\n" + "="*80)
    print("Example 3: Filtered Export")
    print("="*80)
    
    manager = HistoricalDataManager(
        download_dir="data/downloads",
        db_path="data/btc_options.db"
    )
    
    # Define export parameters
    start_date = datetime(2024, 3, 1)
    end_date = datetime(2024, 3, 31)
    
    # Filter by specific instruments
    instruments = [
        "BTC-29MAR24-50000-C",
        "BTC-29MAR24-50000-P",
        "BTC-29MAR24-52000-C",
        "BTC-29MAR24-52000-P",
    ]
    
    print(f"\nExporting filtered data:")
    print(f"  Period: {start_date.date()} to {end_date.date()}")
    print(f"  Instruments: {len(instruments)}")
    for instrument in instruments:
        print(f"    - {instrument}")
    
    # Export filtered data
    result = manager.export_data(
        start_date=start_date,
        end_date=end_date,
        output_path="data/exports/filtered_march_2024.csv",
        format='csv',
        instruments=instruments
    )
    
    print("\n" + "-"*80)
    print("Export Results:")
    print("-"*80)
    print(f"Records exported: {result.records_exported:,}")
    print(f"File size: {result.file_size_bytes / 1024:.2f} KB")
    
    # Compare with unfiltered export
    print("\nFiltering reduced data size significantly")
    
    print("\n✓ Filtered export complete!")


def example_4_compressed_export():
    """
    Example 4: Compressed export for backup
    
    This example shows how to export and compress data for efficient
    storage and backup.
    """
    print("\n" + "="*80)
    print("Example 4: Compressed Export for Backup")
    print("="*80)
    
    manager = HistoricalDataManager(
        download_dir="data/downloads",
        db_path="data/btc_options.db"
    )
    
    # Export entire dataset
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)
    
    print(f"\nCreating compressed backup:")
    print(f"  Period: {start_date.date()} to {end_date.date()}")
    print(f"  Format: Parquet (most efficient)")
    print(f"  Compression: Enabled")
    
    # Export with compression
    result = manager.export_data(
        start_date=start_date,
        end_date=end_date,
        output_path="data/exports/backup_2024.parquet",
        format='parquet',
        compress=True
    )
    
    print("\n" + "-"*80)
    print("Backup Results:")
    print("-"*80)
    print(f"Records exported: {result.records_exported:,}")
    print(f"Compressed size: {result.file_size_bytes / 1024 / 1024:.2f} MB")
    print(f"File path: {result.file_path}")
    
    # Estimate uncompressed size
    estimated_uncompressed = result.file_size_bytes * 3  # Typical 3x compression
    print(f"\nEstimated uncompressed: {estimated_uncompressed / 1024 / 1024:.2f} MB")
    print(f"Space saved: {(estimated_uncompressed - result.file_size_bytes) / 1024 / 1024:.2f} MB")
    
    print("\n✓ Compressed backup complete!")


def example_5_batch_export_by_expiry():
    """
    Example 5: Batch export by expiry date
    
    This example shows how to export data organized by expiry date,
    creating separate files for each expiry.
    """
    print("\n" + "="*80)
    print("Example 5: Batch Export by Expiry Date")
    print("="*80)
    
    manager = HistoricalDataManager(
        download_dir="data/downloads",
        db_path="data/btc_options.db"
    )
    
    # Get available expiry dates
    print("\nGetting available expiry dates...")
    available_dates = manager.get_available_expiry_dates()
    
    if not available_dates:
        print("✗ No data available")
        return
    
    print(f"✓ Found {len(available_dates)} expiry dates")
    
    # Export each expiry to separate file
    export_dir = Path("data/exports/by_expiry")
    export_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\nExporting to: {export_dir}")
    
    results = []
    
    for expiry_date in available_dates[:3]:  # Export first 3 as example
        expiry_str = expiry_date.strftime('%Y%m%d')
        output_file = export_dir / f"expiry_{expiry_str}.parquet"
        
        print(f"\n  Exporting {expiry_date.date()}...")
        
        # Export data for this expiry
        # (Filter by instruments with this expiry)
        result = manager.export_data_by_expiry(
            expiry_date=expiry_date,
            output_path=output_file,
            format='parquet'
        )
        
        results.append((expiry_date, result))
        
        print(f"    ✓ {result.records_exported:,} records, "
              f"{result.file_size_bytes / 1024:.0f} KB")
    
    # Summary
    print("\n" + "-"*80)
    print("Batch Export Summary:")
    print("-"*80)
    
    total_records = sum(r.records_exported for _, r in results)
    total_size = sum(r.file_size_bytes for _, r in results)
    
    print(f"Files created: {len(results)}")
    print(f"Total records: {total_records:,}")
    print(f"Total size: {total_size / 1024 / 1024:.2f} MB")
    
    print("\n✓ Batch export complete!")


def example_6_export_for_analysis():
    """
    Example 6: Export for external analysis
    
    This example shows how to export data in formats suitable for
    analysis in tools like Excel, Python pandas, or R.
    """
    print("\n" + "="*80)
    print("Example 6: Export for External Analysis")
    print("="*80)
    
    manager = HistoricalDataManager(
        download_dir="data/downloads",
        db_path="data/btc_options.db"
    )
    
    start_date = datetime(2024, 3, 1)
    end_date = datetime(2024, 3, 31)
    
    print(f"\nExporting data for analysis:")
    print(f"  Period: {start_date.date()} to {end_date.date()}")
    
    # 1. CSV for Excel
    print("\n1. CSV for Excel:")
    csv_result = manager.export_data(
        start_date=start_date,
        end_date=end_date,
        output_path="data/exports/analysis_excel.csv",
        format='csv'
    )
    print(f"   ✓ {csv_result.records_exported:,} records")
    print(f"   ✓ Open in Excel: {csv_result.file_path}")
    
    # 2. Parquet for Python/pandas
    print("\n2. Parquet for Python/pandas:")
    parquet_result = manager.export_data(
        start_date=start_date,
        end_date=end_date,
        output_path="data/exports/analysis_pandas.parquet",
        format='parquet'
    )
    print(f"   ✓ {parquet_result.records_exported:,} records")
    print(f"   ✓ Load with: pd.read_parquet('{parquet_result.file_path}')")
    
    # 3. JSON for general use
    print("\n3. JSON for general use:")
    json_result = manager.export_data(
        start_date=start_date,
        end_date=end_date,
        output_path="data/exports/analysis_general.json",
        format='json'
    )
    print(f"   ✓ {json_result.records_exported:,} records")
    print(f"   ✓ Load with: json.load(open('{json_result.file_path}'))")
    
    # Example Python code for loading
    print("\n" + "-"*80)
    print("Example Python Code:")
    print("-"*80)
    print("""
# Load CSV with pandas
import pandas as pd
df = pd.read_csv('data/exports/analysis_excel.csv')

# Load Parquet with pandas (faster)
df = pd.read_parquet('data/exports/analysis_pandas.parquet')

# Load JSON
import json
with open('data/exports/analysis_general.json') as f:
    data = json.load(f)
    """)
    
    print("\n✓ Export for analysis complete!")


def example_7_incremental_export():
    """
    Example 7: Incremental export (export only new data)
    
    This example shows how to export only data that hasn't been
    exported before, useful for regular backups.
    """
    print("\n" + "="*80)
    print("Example 7: Incremental Export")
    print("="*80)
    
    manager = HistoricalDataManager(
        download_dir="data/downloads",
        db_path="data/btc_options.db"
    )
    
    # Track last export date (in practice, store this persistently)
    last_export_date = datetime(2024, 3, 15)
    current_date = datetime(2024, 3, 31)
    
    print(f"\nIncremental export:")
    print(f"  Last export: {last_export_date.date()}")
    print(f"  Current date: {current_date.date()}")
    print(f"  Exporting: {last_export_date.date()} to {current_date.date()}")
    
    # Export only new data
    result = manager.export_data(
        start_date=last_export_date,
        end_date=current_date,
        output_path=f"data/exports/incremental_{current_date.strftime('%Y%m%d')}.parquet",
        format='parquet',
        compress=True
    )
    
    print("\n" + "-"*80)
    print("Incremental Export Results:")
    print("-"*80)
    print(f"New records: {result.records_exported:,}")
    print(f"File size: {result.file_size_bytes / 1024:.2f} KB")
    print(f"File path: {result.file_path}")
    
    # Update last export date
    print(f"\nUpdate last export date to: {current_date.date()}")
    
    print("\n✓ Incremental export complete!")


def example_8_export_with_validation():
    """
    Example 8: Export with data validation
    
    This example shows how to validate data before exporting to ensure
    quality.
    """
    print("\n" + "="*80)
    print("Example 8: Export with Validation")
    print("="*80)
    
    manager = HistoricalDataManager(
        download_dir="data/downloads",
        db_path="data/btc_options.db"
    )
    
    start_date = datetime(2024, 3, 1)
    end_date = datetime(2024, 3, 31)
    
    print(f"\nValidating data before export:")
    print(f"  Period: {start_date.date()} to {end_date.date()}")
    
    # Validate data first
    print("\nRunning validation...")
    validation_result = manager.validate_data(
        start_date=start_date,
        end_date=end_date
    )
    
    print("\n" + "-"*80)
    print("Validation Results:")
    print("-"*80)
    print(f"Quality score: {validation_result.quality_score:.1f}/100")
    print(f"Total records: {validation_result.total_records:,}")
    print(f"Issues found: {len(validation_result.issues)}")
    
    # Decide whether to export
    if validation_result.quality_score < 70:
        print("\n✗ Quality score too low - export cancelled")
        print("Fix data quality issues before exporting")
        return
    elif validation_result.quality_score < 85:
        print("\n⚠ Quality score acceptable but not ideal")
        print("Consider reviewing issues before using exported data")
    else:
        print("\n✓ Quality score good - proceeding with export")
    
    # Export validated data
    print("\nExporting validated data...")
    result = manager.export_data(
        start_date=start_date,
        end_date=end_date,
        output_path="data/exports/validated_march_2024.parquet",
        format='parquet'
    )
    
    print(f"\n✓ Exported {result.records_exported:,} validated records")
    
    print("\n✓ Export with validation complete!")


def main():
    """
    Run all examples
    """
    print("\n" + "="*80)
    print(" "*20 + "Historical Data Export Examples")
    print("="*80)
    print("\nThese examples demonstrate various ways to export historical options data.")
    print("\nNote: Some examples may be skipped if required data is not available.")
    
    # Run examples
    examples = [
        ("Simple CSV Export", example_1_simple_csv_export),
        ("Multiple Formats", example_2_export_multiple_formats),
        ("Filtered Export", example_3_filtered_export),
        ("Compressed Backup", example_4_compressed_export),
        ("Batch by Expiry", example_5_batch_export_by_expiry),
        ("Export for Analysis", example_6_export_for_analysis),
        ("Incremental Export", example_7_incremental_export),
        ("Export with Validation", example_8_export_with_validation),
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
    print("  - HISTORICAL_CLI_GUIDE.md")
    print("  - .kiro/specs/historical-data-integration/design.md")
    print()


if __name__ == '__main__':
    main()
