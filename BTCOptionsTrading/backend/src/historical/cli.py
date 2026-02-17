"""
Command-line interface for historical data management
"""
import click
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from decimal import Decimal

from src.historical.manager import HistoricalDataManager
from src.historical.downloader import CryptoDataDownloader
from src.config.logging_config import get_logger

logger = get_logger(__name__)


@click.group()
def historical_cli():
    """Historical Options Data Management CLI"""
    pass


@historical_cli.command()
@click.option('--expiry-date', '-e', multiple=True, help='Expiry date in YYYY-MM-DD format (can specify multiple)')
@click.option('--symbol', '-s', default='BTC', help='Underlying symbol (default: BTC)')
@click.option('--download-dir', '-d', default='data/downloads', help='Download directory')
@click.option('--force', '-f', is_flag=True, help='Force re-download even if files exist')
@click.option('--max-concurrent', '-c', default=3, help='Maximum concurrent downloads')
def download(expiry_date, symbol, download_dir, force, max_concurrent):
    """
    Download historical options data from CryptoDataDownload
    
    Example:
        historical-cli download -e 2024-03-29 -e 2024-04-26 -s BTC
    """
    try:
        if not expiry_date:
            click.echo("Error: At least one expiry date must be specified", err=True)
            click.echo("Example: historical-cli download -e 2024-03-29", err=True)
            return
        
        # Parse expiry dates
        expiry_dates = []
        for date_str in expiry_date:
            try:
                parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
                expiry_dates.append(parsed_date)
            except ValueError:
                click.echo(f"Error: Invalid date format '{date_str}'. Use YYYY-MM-DD", err=True)
                return
        
        click.echo(f"Downloading data for {len(expiry_dates)} expiry date(s)...")
        click.echo(f"Symbol: {symbol}")
        click.echo(f"Download directory: {download_dir}")
        click.echo(f"Force re-download: {force}")
        click.echo("-" * 60)
        
        # Initialize downloader
        downloader = CryptoDataDownloader(cache_dir=download_dir)
        
        # Download data
        async def run_download():
            if len(expiry_dates) == 1:
                # Single download
                path = await downloader.download_data(
                    expiry_dates[0],
                    symbol=symbol,
                    force_redownload=force
                )
                click.echo(f"✓ Downloaded to: {path}")
                
                # Show extracted files
                files = downloader.get_extracted_files(expiry_dates[0], symbol)
                click.echo(f"✓ Extracted {len(files)} CSV files")
                
            else:
                # Batch download
                results = await downloader.batch_download(
                    expiry_dates,
                    symbol=symbol,
                    max_concurrent=max_concurrent
                )
                
                # Show results
                success_count = sum(1 for path in results.values() if path is not None)
                failure_count = len(results) - success_count
                
                click.echo("-" * 60)
                click.echo(f"Download complete:")
                click.echo(f"  Success: {success_count}/{len(results)}")
                click.echo(f"  Failed: {failure_count}/{len(results)}")
                
                if failure_count > 0:
                    click.echo("\nFailed downloads:")
                    for date, path in results.items():
                        if path is None:
                            click.echo(f"  ✗ {date.date()}")
        
        # Run async download
        asyncio.run(run_download())
        
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        logger.error(f"Download command failed: {e}", exc_info=True)


@historical_cli.command()
@click.option('--file', '-f', multiple=True, help='CSV file path (can specify multiple)')
@click.option('--directory', '-d', help='Directory containing CSV files')
@click.option('--validate/--no-validate', default=True, help='Validate data quality')
@click.option('--report/--no-report', default=True, help='Generate quality report')
@click.option('--db-path', default='data/btc_options.db', help='Database path')
def import_data(file, directory, validate, report, db_path):
    """
    Import historical data into the system
    
    Example:
        historical-cli import -d data/downloads/BTC_20240329
        historical-cli import -f data/file1.csv -f data/file2.csv
    """
    try:
        # Determine files to import
        file_paths = []
        
        if directory:
            dir_path = Path(directory)
            if not dir_path.exists():
                click.echo(f"Error: Directory not found: {directory}", err=True)
                return
            file_paths = list(dir_path.glob("**/*.csv"))
            click.echo(f"Found {len(file_paths)} CSV files in {directory}")
        
        if file:
            for f in file:
                path = Path(f)
                if not path.exists():
                    click.echo(f"Warning: File not found: {f}", err=True)
                else:
                    file_paths.append(path)
        
        if not file_paths:
            click.echo("Error: No files to import. Specify --file or --directory", err=True)
            return
        
        click.echo(f"Importing {len(file_paths)} file(s)...")
        click.echo(f"Validation: {'enabled' if validate else 'disabled'}")
        click.echo(f"Quality report: {'enabled' if report else 'disabled'}")
        click.echo("-" * 60)
        
        # Initialize manager
        manager = HistoricalDataManager(db_path=db_path)
        
        # Import data
        result = manager.import_historical_data(
            file_paths=file_paths,
            validate=validate,
            generate_report=report
        )
        
        # Display results
        click.echo("-" * 60)
        click.echo("Import complete:")
        click.echo(f"  Files processed: {result.total_count}")
        click.echo(f"  Success: {result.success_count}")
        click.echo(f"  Failed: {result.failure_count}")
        click.echo(f"  Records imported: {result.records_imported}")
        click.echo(f"  Duration: {result.import_duration_seconds:.1f}s")
        
        if result.failed_files:
            click.echo("\nFailed files:")
            for failed_file in result.failed_files:
                click.echo(f"  ✗ {failed_file}")
        
        # Display quality report
        if result.quality_report:
            report_data = result.quality_report
            click.echo("\nData Quality Report:")
            click.echo(f"  Quality score: {report_data.quality_score:.1f}/100")
            click.echo(f"  Total records: {report_data.total_records}")
            click.echo(f"  Coverage: {report_data.coverage_percentage:.1%}")
            click.echo(f"  Anomalies: {report_data.anomaly_records}")
            click.echo(f"  Issues: {len(report_data.issues)}")
            
            if report_data.issues:
                click.echo("\nTop issues:")
                for issue in report_data.issues[:5]:
                    click.echo(f"  [{issue.severity}] {issue.message}")
        
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        logger.error(f"Import command failed: {e}", exc_info=True)


@historical_cli.command()
@click.option('--start-date', '-s', help='Start date (YYYY-MM-DD)')
@click.option('--end-date', '-e', help='End date (YYYY-MM-DD)')
@click.option('--instrument', '-i', help='Instrument name (e.g., BTC-29MAR24-50000-C)')
@click.option('--db-path', default='data/btc_options.db', help='Database path')
@click.option('--detailed', is_flag=True, help='Show detailed validation results')
def validate(start_date, end_date, instrument, db_path, detailed):
    """
    Validate data quality
    
    Example:
        historical-cli validate --start-date 2024-03-01 --end-date 2024-03-31
        historical-cli validate --instrument BTC-29MAR24-50000-C
    """
    try:
        # Parse dates
        start_dt = None
        end_dt = None
        
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            except ValueError:
                click.echo(f"Error: Invalid start date format. Use YYYY-MM-DD", err=True)
                return
        
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                # Include the entire end day by setting time to 23:59:59
                from datetime import timedelta
                end_dt = end_dt + timedelta(days=1) - timedelta(seconds=1)
            except ValueError:
                click.echo(f"Error: Invalid end date format. Use YYYY-MM-DD", err=True)
                return
        
        click.echo("Validating data quality...")
        if start_dt:
            click.echo(f"Start date: {start_dt.date()}")
        if end_dt:
            click.echo(f"End date: {end_dt.date()}")
        if instrument:
            click.echo(f"Instrument: {instrument}")
        click.echo("-" * 60)
        
        # Initialize manager
        manager = HistoricalDataManager(db_path=db_path)
        
        # Validate data
        report = manager.validate_data_quality(
            start_date=start_dt,
            end_date=end_dt,
            instrument_name=instrument
        )
        
        # Display results
        click.echo("Validation Results:")
        click.echo("-" * 60)
        click.echo(f"Quality score: {report.quality_score:.1f}/100")
        click.echo(f"Total records: {report.total_records}")
        click.echo(f"Missing records: {report.missing_records}")
        click.echo(f"Anomaly records: {report.anomaly_records}")
        click.echo(f"Coverage: {report.coverage_percentage:.1%}")
        click.echo(f"Time range: {report.time_range[0].date()} to {report.time_range[1].date()}")
        
        if report.issues:
            click.echo(f"\nIssues found: {len(report.issues)}")
            
            # Group by severity
            from collections import Counter
            severity_counts = Counter(issue.severity for issue in report.issues)
            
            for severity, count in severity_counts.items():
                click.echo(f"  {severity}: {count}")
            
            if detailed:
                click.echo("\nDetailed issues:")
                for i, issue in enumerate(report.issues[:20], 1):  # Show first 20
                    click.echo(f"\n{i}. [{issue.severity}] {issue.message}")
                    if issue.timestamp:
                        click.echo(f"   Time: {issue.timestamp}")
                    if issue.field_name:
                        click.echo(f"   Field: {issue.field_name}")
                
                if len(report.issues) > 20:
                    click.echo(f"\n... and {len(report.issues) - 20} more issues")
        else:
            click.echo("\n✓ No issues found")
        
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        logger.error(f"Validate command failed: {e}", exc_info=True)


@historical_cli.command()
@click.option('--start-date', '-s', required=True, help='Start date (YYYY-MM-DD)')
@click.option('--end-date', '-e', required=True, help='End date (YYYY-MM-DD)')
@click.option('--instrument', '-i', multiple=True, help='Instrument name (can specify multiple)')
@click.option('--format', '-f', type=click.Choice(['csv', 'json', 'parquet']), default='csv', help='Export format')
@click.option('--output', '-o', required=True, help='Output file path')
@click.option('--compress', is_flag=True, help='Compress output file')
@click.option('--db-path', default='data/btc_options.db', help='Database path')
def export(start_date, end_date, instrument, format, output, compress, db_path):
    """
    Export historical data
    
    Example:
        historical-cli export -s 2024-03-01 -e 2024-03-31 -f csv -o data/export.csv
        historical-cli export -s 2024-03-01 -e 2024-03-31 -i BTC-29MAR24-50000-C -f json -o data/export.json
    """
    try:
        # Parse dates
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            # Include the entire end day by setting time to 23:59:59
            from datetime import timedelta
            end_dt = end_dt + timedelta(days=1) - timedelta(seconds=1)
        except ValueError:
            click.echo(f"Error: Invalid date format. Use YYYY-MM-DD", err=True)
            return
        
        click.echo("Exporting data...")
        click.echo(f"Date range: {start_dt.date()} to {end_dt.date()}")
        click.echo(f"Format: {format}")
        click.echo(f"Output: {output}")
        if instrument:
            click.echo(f"Instruments: {len(instrument)}")
        click.echo("-" * 60)
        
        # Initialize manager
        manager = HistoricalDataManager(db_path=db_path)
        
        # Query data
        data = []
        if instrument:
            # Query each instrument separately
            for inst in instrument:
                inst_data = manager.cache.query_option_data(
                    instrument_name=inst,
                    start_date=start_dt,
                    end_date=end_dt
                )
                data.extend(inst_data)
        else:
            # Query all instruments in date range
            data = manager.cache.query_option_data(
                start_date=start_dt,
                end_date=end_dt
            )
        
        if not data:
            click.echo("No data found for the specified criteria", err=True)
            return
        
        click.echo(f"Found {len(data)} records")
        
        # Export data
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == 'csv':
            import csv
            with open(output_path, 'w', newline='') as f:
                writer = csv.writer(f)
                # Write header
                writer.writerow([
                    'instrument_name', 'timestamp', 'open_price', 'high_price',
                    'low_price', 'close_price', 'volume', 'strike_price',
                    'expiry_date', 'option_type', 'underlying_symbol'
                ])
                # Write data
                for d in data:
                    writer.writerow([
                        d.instrument_name, d.timestamp, d.open_price, d.high_price,
                        d.low_price, d.close_price, d.volume, d.strike_price,
                        d.expiry_date, d.option_type.value, d.underlying_symbol
                    ])
        
        elif format == 'json':
            import json
            json_data = []
            for d in data:
                json_data.append({
                    'instrument_name': d.instrument_name,
                    'timestamp': d.timestamp.isoformat(),
                    'open_price': str(d.open_price),
                    'high_price': str(d.high_price),
                    'low_price': str(d.low_price),
                    'close_price': str(d.close_price),
                    'volume': str(d.volume),
                    'strike_price': str(d.strike_price),
                    'expiry_date': d.expiry_date.isoformat(),
                    'option_type': d.option_type.value,
                    'underlying_symbol': d.underlying_symbol
                })
            
            with open(output_path, 'w') as f:
                json.dump(json_data, f, indent=2)
        
        elif format == 'parquet':
            try:
                import pandas as pd
                import pyarrow.parquet as pq
                
                # Convert to DataFrame
                df_data = []
                for d in data:
                    df_data.append({
                        'instrument_name': d.instrument_name,
                        'timestamp': d.timestamp,
                        'open_price': float(d.open_price),
                        'high_price': float(d.high_price),
                        'low_price': float(d.low_price),
                        'close_price': float(d.close_price),
                        'volume': float(d.volume),
                        'strike_price': float(d.strike_price),
                        'expiry_date': d.expiry_date,
                        'option_type': d.option_type.value,
                        'underlying_symbol': d.underlying_symbol
                    })
                
                df = pd.DataFrame(df_data)
                df.to_parquet(output_path, compression='snappy' if compress else None)
                
            except ImportError:
                click.echo("Error: pandas and pyarrow are required for parquet export", err=True)
                return
        
        # Compress if requested
        if compress and format != 'parquet':
            import gzip
            import shutil
            
            compressed_path = Path(str(output_path) + '.gz')
            with open(output_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            output_path.unlink()  # Remove uncompressed file
            output_path = compressed_path
        
        # Get file size
        file_size = output_path.stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        
        click.echo("-" * 60)
        click.echo("Export complete:")
        click.echo(f"  Records exported: {len(data)}")
        click.echo(f"  File: {output_path}")
        click.echo(f"  Size: {file_size_mb:.2f} MB")
        
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        logger.error(f"Export command failed: {e}", exc_info=True)


@historical_cli.command()
@click.option('--start-date', '-s', help='Start date (YYYY-MM-DD)')
@click.option('--end-date', '-e', help='End date (YYYY-MM-DD)')
@click.option('--symbol', default='BTC', help='Underlying symbol')
@click.option('--db-path', default='data/btc_options.db', help='Database path')
def stats(start_date, end_date, symbol, db_path):
    """
    Display statistics about stored historical data
    
    Example:
        historical-cli stats
        historical-cli stats --start-date 2024-03-01 --end-date 2024-03-31
    """
    try:
        # Parse dates
        start_dt = None
        end_dt = None
        
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            except ValueError:
                click.echo(f"Error: Invalid start date format. Use YYYY-MM-DD", err=True)
                return
        
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                # Include the entire end day by setting time to 23:59:59
                from datetime import timedelta
                end_dt = end_dt + timedelta(days=1) - timedelta(seconds=1)
            except ValueError:
                click.echo(f"Error: Invalid end date format. Use YYYY-MM-DD", err=True)
                return
        
        # Initialize manager
        manager = HistoricalDataManager(db_path=db_path)
        
        click.echo("Historical Data Statistics")
        click.echo("=" * 60)
        
        # Get general stats
        general_stats = manager.get_stats()
        
        click.echo("\nGeneral:")
        click.echo(f"  Download directory: {general_stats['download_dir']}")
        click.echo(f"  CSV files: {general_stats['csv_files']}")
        
        cache_stats = general_stats['cache']
        click.echo(f"\nCache:")
        click.echo(f"  Total records: {cache_stats.get('total_records', 0)}")
        click.echo(f"  Cache size: {cache_stats.get('cache_size_mb', 0):.2f} MB")
        click.echo(f"  Database size: {cache_stats.get('db_size_mb', 0):.2f} MB")
        
        # Get available instruments
        instruments = manager.get_available_instruments(
            start_date=start_dt,
            end_date=end_dt,
            underlying_symbol=symbol
        )
        
        click.echo(f"\nInstruments:")
        click.echo(f"  Total: {len(instruments)}")
        if instruments:
            click.echo(f"  Sample: {', '.join(instruments[:5])}")
            if len(instruments) > 5:
                click.echo(f"  ... and {len(instruments) - 5} more")
        
        # Get available dates
        dates = manager.get_available_dates(underlying_symbol=symbol)
        
        click.echo(f"\nDate Coverage:")
        click.echo(f"  Total days: {len(dates)}")
        if dates:
            click.echo(f"  First date: {min(dates).date()}")
            click.echo(f"  Last date: {max(dates).date()}")
        
        # Get coverage stats if date range specified
        if start_dt and end_dt:
            coverage = manager.get_coverage_stats(
                start_date=start_dt,
                end_date=end_dt,
                underlying_symbol=symbol
            )
            
            click.echo(f"\nCoverage ({start_dt.date()} to {end_dt.date()}):")
            click.echo(f"  Days with data: {coverage.days_with_data}/{coverage.total_days}")
            click.echo(f"  Coverage: {coverage.coverage_percentage:.1%}")
            click.echo(f"  Strikes covered: {len(coverage.strikes_covered)}")
            click.echo(f"  Expiries covered: {len(coverage.expiries_covered)}")
            
            if coverage.missing_dates:
                missing_count = len(coverage.missing_dates)
                click.echo(f"  Missing dates: {missing_count}")
                if missing_count <= 10:
                    for missing_date in coverage.missing_dates:
                        click.echo(f"    - {missing_date.date()}")
                else:
                    click.echo(f"    First: {coverage.missing_dates[0].date()}")
                    click.echo(f"    Last: {coverage.missing_dates[-1].date()}")
        
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        logger.error(f"Stats command failed: {e}", exc_info=True)


@historical_cli.command()
@click.option('--clear-cache', is_flag=True, help='Clear file cache')
@click.option('--clear-database', is_flag=True, help='Clear database (WARNING: deletes all data)')
@click.option('--db-path', default='data/btc_options.db', help='Database path')
@click.confirmation_option(prompt='Are you sure you want to clear data?')
def clear(clear_cache, clear_database, db_path):
    """
    Clear cached data (requires confirmation)
    
    Example:
        historical-cli clear --clear-cache
        historical-cli clear --clear-database
    """
    try:
        if not clear_cache and not clear_database:
            click.echo("Error: Specify --clear-cache or --clear-database", err=True)
            return
        
        # Initialize manager
        manager = HistoricalDataManager(db_path=db_path)
        
        if clear_cache:
            click.echo("Clearing file cache...")
            manager.cache.clear_cache(clear_database=False)
            click.echo("✓ File cache cleared")
        
        if clear_database:
            click.echo("Clearing database...")
            manager.cache.clear_cache(clear_database=True)
            click.echo("✓ Database cleared")
        
        click.echo("Clear operation complete")
        
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        logger.error(f"Clear command failed: {e}", exc_info=True)


if __name__ == '__main__':
    historical_cli()
