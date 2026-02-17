#!/usr/bin/env python3
"""
Example: Historical Data Import

This example demonstrates how to import historical options data from CryptoDataDownload
into the system. It covers:
- Downloading data
- Importing CSV files
- Validating data quality
- Checking import results

Requirements: 1.1, 2.1, 2.4, 3.1
"""
import sys
import asyncio
from pathlib import Path
from datetime import datetime

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from src.historical.manager import HistoricalDataManager
from src.historical.downloader import CryptoDataDownloader
from src.historical.converter import HistoricalDataConverter
from src.historical.validator import HistoricalDataValidator
from src.historical.cache import HistoricalDataCache
from src.storage.database import DatabaseManager


async def example_1_simple_import():
    """
    Example 1: Simple import using the manager
    
    This is the easiest way to import data - just specify expiry dates
    and let the manager handle everything.
    """
    print("\n" + "="*80)
    print("Example 1: Simple Import Using Manager")
    print("="*80)
    
    # Initialize manager
    manager = HistoricalDataManager(
        download_dir="data/downloads",
        db_path="data/btc_options.db"
    )
    
    # Import data for specific expiry dates
    expiry_dates = [
        datetime(2024, 3, 29),  # March 29, 2024
        datetime(2024, 4, 26),  # April 26, 2024
    ]
    
    print(f"\nImporting data for {len(expiry_dates)} expiry dates...")
    print(f"Expiry dates: {[d.strftime('%Y-%m-%d') for d in expiry_dates]}")
    
    result = await manager.import_historical_data(
        expiry_dates=expiry_dates,
        validate=True  # Validate data quality during import
    )
    
    # Print results
    print("\n" + "-"*80)
    print("Import Results:")
    print("-"*80)
    print(f"Files processed: {result.files_processed}")
    print(f"Records imported: {result.records_imported}")
    print(f"Records failed: {result.records_failed}")
    print(f"Duration: {result.duration_seconds:.2f} seconds")
    
    if result.quality_report:
        print(f"\nQuality Score: {result.quality_report.quality_score:.1f}/100")
        print(f"Total records: {result.quality_report.total_records}")
        print(f"Missing records: {result.quality_report.missing_records}")
        print(f"Anomaly records: {result.quality_report.anomaly_records}")
        print(f"Coverage: {result.quality_report.coverage_percentage:.1f}%")
        
        if result.quality_report.issues:
            print(f"\nIssues found: {len(result.quality_report.issues)}")
            for issue in result.quality_report.issues[:5]:  # Show first 5
                print(f"  - [{issue.severity}] {issue.type}: {issue.description}")
    
    print("\n✓ Simple import complete!")


async def example_2_step_by_step_import():
    """
    Example 2: Step-by-step import with full control
    
    This example shows how to use individual components for more control
    over the import process.
    """
    print("\n" + "="*80)
    print("Example 2: Step-by-Step Import with Full Control")
    print("="*80)
    
    # Initialize components
    downloader = CryptoDataDownloader(cache_dir="data/downloads")
    converter = HistoricalDataConverter()
    validator = HistoricalDataValidator()
    
    db_manager = DatabaseManager(db_path="data/btc_options.db")
    cache = HistoricalDataCache(
        db_manager=db_manager,
        file_cache_dir="data/cache"
    )
    
    # Step 1: Download data
    print("\nStep 1: Downloading data...")
    expiry_date = datetime(2024, 3, 29)
    
    try:
        file_path = await downloader.download_data(
            expiry_date=expiry_date,
            force_redownload=False  # Skip if already downloaded
        )
        print(f"✓ Downloaded to: {file_path}")
    except Exception as e:
        print(f"✗ Download failed: {e}")
        return
    
    # Step 2: List CSV files in the downloaded directory
    print("\nStep 2: Finding CSV files...")
    csv_files = list(Path(file_path).parent.glob("*.csv"))
    print(f"✓ Found {len(csv_files)} CSV files")
    
    # Step 3: Parse and convert each file
    print("\nStep 3: Parsing and converting CSV files...")
    all_data = []
    
    for csv_file in csv_files[:3]:  # Process first 3 files as example
        print(f"\n  Processing: {csv_file.name}")
        
        # Parse CSV
        ohlcv_data = converter.parse_csv_file(csv_file)
        print(f"    ✓ Parsed {len(ohlcv_data)} records")
        
        # Extract option info from filename
        option_info = converter.extract_option_info(csv_file.name)
        print(f"    ✓ Extracted info: {option_info.symbol} "
              f"{option_info.strike_price} {option_info.option_type.value}")
        
        # Convert to internal format
        internal_data = converter.convert_to_internal_format(
            ohlcv_data=ohlcv_data,
            option_info=option_info
        )
        print(f"    ✓ Converted to internal format")
        
        all_data.extend(internal_data)
    
    print(f"\n✓ Total records to import: {len(all_data)}")
    
    # Step 4: Validate data
    print("\nStep 4: Validating data quality...")
    
    # Completeness check
    completeness_result = validator.validate_data_completeness(all_data)
    print(f"  Completeness: {'✓ Valid' if completeness_result.is_valid else '✗ Invalid'}")
    if completeness_result.errors:
        print(f"    Errors: {len(completeness_result.errors)}")
    if completeness_result.warnings:
        print(f"    Warnings: {len(completeness_result.warnings)}")
    
    # Price sanity check
    sanity_result = validator.validate_price_sanity(all_data)
    print(f"  Price sanity: {'✓ Valid' if sanity_result.is_valid else '✗ Invalid'}")
    if sanity_result.errors:
        print(f"    Errors: {len(sanity_result.errors)}")
    
    # Step 5: Store in cache
    print("\nStep 5: Storing data in cache...")
    cache.store_historical_data(all_data)
    print(f"✓ Stored {len(all_data)} records")
    
    # Step 6: Verify storage
    print("\nStep 6: Verifying storage...")
    if all_data:
        sample_instrument = all_data[0].instrument_name
        stored_data = cache.query_option_data(
            instrument_name=sample_instrument,
            start_date=all_data[0].timestamp,
            end_date=all_data[-1].timestamp
        )
        print(f"✓ Verified: Retrieved {len(stored_data)} records for {sample_instrument}")
    
    print("\n✓ Step-by-step import complete!")


async def example_3_batch_import():
    """
    Example 3: Batch import multiple expiry dates
    
    This example shows how to efficiently import data for multiple
    expiry dates using concurrent downloads.
    """
    print("\n" + "="*80)
    print("Example 3: Batch Import Multiple Expiry Dates")
    print("="*80)
    
    manager = HistoricalDataManager(
        download_dir="data/downloads",
        db_path="data/btc_options.db"
    )
    
    # Define multiple expiry dates
    expiry_dates = [
        datetime(2024, 3, 29),
        datetime(2024, 4, 26),
        datetime(2024, 5, 31),
        datetime(2024, 6, 28),
    ]
    
    print(f"\nBatch importing {len(expiry_dates)} expiry dates...")
    for date in expiry_dates:
        print(f"  - {date.strftime('%Y-%m-%d')}")
    
    # Import with progress tracking
    start_time = datetime.now()
    
    result = await manager.import_historical_data(
        expiry_dates=expiry_dates,
        validate=True
    )
    
    duration = (datetime.now() - start_time).total_seconds()
    
    # Print summary
    print("\n" + "-"*80)
    print("Batch Import Summary:")
    print("-"*80)
    print(f"Expiry dates processed: {len(expiry_dates)}")
    print(f"Files processed: {result.files_processed}")
    print(f"Records imported: {result.records_imported:,}")
    print(f"Records failed: {result.records_failed}")
    print(f"Total duration: {duration:.2f} seconds")
    print(f"Average per expiry: {duration/len(expiry_dates):.2f} seconds")
    print(f"Records per second: {result.records_imported/duration:.0f}")
    
    if result.quality_report:
        print(f"\nOverall Quality Score: {result.quality_report.quality_score:.1f}/100")
    
    print("\n✓ Batch import complete!")


async def example_4_import_with_error_handling():
    """
    Example 4: Import with comprehensive error handling
    
    This example shows how to handle various errors that might occur
    during the import process.
    """
    print("\n" + "="*80)
    print("Example 4: Import with Error Handling")
    print("="*80)
    
    manager = HistoricalDataManager(
        download_dir="data/downloads",
        db_path="data/btc_options.db"
    )
    
    expiry_dates = [
        datetime(2024, 3, 29),
        datetime(2024, 4, 26),
    ]
    
    print(f"\nImporting with error handling...")
    
    try:
        result = await manager.import_historical_data(
            expiry_dates=expiry_dates,
            validate=True
        )
        
        # Check for partial failures
        if result.records_failed > 0:
            print(f"\n⚠ Warning: {result.records_failed} records failed to import")
            print("Check logs for details")
        
        # Check quality score
        if result.quality_report:
            if result.quality_report.quality_score < 70:
                print(f"\n⚠ Warning: Low quality score: "
                      f"{result.quality_report.quality_score:.1f}/100")
                print("Consider re-downloading the data")
            elif result.quality_report.quality_score < 85:
                print(f"\n⚠ Notice: Acceptable quality score: "
                      f"{result.quality_report.quality_score:.1f}/100")
                print("Review quality report for details")
            else:
                print(f"\n✓ Good quality score: "
                      f"{result.quality_report.quality_score:.1f}/100")
        
        # Check coverage
        if result.quality_report and result.quality_report.coverage_percentage < 90:
            print(f"\n⚠ Warning: Low coverage: "
                  f"{result.quality_report.coverage_percentage:.1f}%")
            print("Some data may be missing")
        
        print("\n✓ Import completed with error handling")
        
    except ConnectionError as e:
        print(f"\n✗ Network error: {e}")
        print("Check your internet connection and try again")
    except PermissionError as e:
        print(f"\n✗ Permission error: {e}")
        print("Check file and directory permissions")
    except ValueError as e:
        print(f"\n✗ Invalid data: {e}")
        print("Check the expiry dates and data format")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        print("Check logs for more details")


async def example_5_import_from_local_files():
    """
    Example 5: Import from local CSV files
    
    This example shows how to import data from CSV files that you've
    already downloaded manually.
    """
    print("\n" + "="*80)
    print("Example 5: Import from Local CSV Files")
    print("="*80)
    
    manager = HistoricalDataManager(
        download_dir="data/downloads",
        db_path="data/btc_options.db"
    )
    
    # Specify local CSV files
    csv_directory = Path("data/test_csv")
    
    if not csv_directory.exists():
        print(f"\n⚠ Directory not found: {csv_directory}")
        print("This example requires CSV files in data/test_csv/")
        return
    
    csv_files = list(csv_directory.glob("*.csv"))
    
    if not csv_files:
        print(f"\n⚠ No CSV files found in {csv_directory}")
        return
    
    print(f"\nFound {len(csv_files)} CSV files:")
    for csv_file in csv_files:
        print(f"  - {csv_file.name}")
    
    # Import files
    print(f"\nImporting files...")
    
    result = await manager.import_from_files(
        file_paths=csv_files,
        validate=True
    )
    
    print("\n" + "-"*80)
    print("Import Results:")
    print("-"*80)
    print(f"Files processed: {result.files_processed}")
    print(f"Records imported: {result.records_imported}")
    print(f"Records failed: {result.records_failed}")
    
    print("\n✓ Local file import complete!")


async def main():
    """
    Run all examples
    """
    print("\n" + "="*80)
    print(" "*20 + "Historical Data Import Examples")
    print("="*80)
    print("\nThese examples demonstrate various ways to import historical options data.")
    print("Choose which examples to run, or run all of them.")
    print("\nNote: Some examples may be skipped if required data is not available.")
    
    # Run examples
    examples = [
        ("Simple Import", example_1_simple_import),
        ("Step-by-Step Import", example_2_step_by_step_import),
        ("Batch Import", example_3_batch_import),
        ("Import with Error Handling", example_4_import_with_error_handling),
        ("Import from Local Files", example_5_import_from_local_files),
    ]
    
    for name, example_func in examples:
        try:
            await example_func()
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
    asyncio.run(main())
