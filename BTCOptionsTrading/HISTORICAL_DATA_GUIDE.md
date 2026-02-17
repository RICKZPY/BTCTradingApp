# Historical Options Data Integration - User Guide

## Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Data Sources](#data-sources)
4. [Installation](#installation)
5. [Quick Start](#quick-start)
6. [Using the CLI](#using-the-cli)
7. [Using the API](#using-the-api)
8. [Using the Python SDK](#using-the-python-sdk)
9. [Data Quality and Validation](#data-quality-and-validation)
10. [Backtest Integration](#backtest-integration)
11. [Troubleshooting](#troubleshooting)
12. [Best Practices](#best-practices)
13. [FAQ](#faq)

## Overview

The Historical Options Data Integration system allows you to download, store, and use real historical Bitcoin options data from CryptoDataDownload in your backtesting workflows. This enables more accurate strategy testing using actual market data instead of simulated prices.

### Key Features

- **Free Data Access**: Download historical Deribit BTC options data from CryptoDataDownload
- **Automated Processing**: Automatic download, parsing, validation, and storage
- **Data Quality Validation**: Comprehensive checks for completeness and accuracy
- **Multiple Interfaces**: CLI, REST API, and Python SDK
- **Flexible Export**: Export data in CSV, JSON, or Parquet formats
- **Backtest Integration**: Seamlessly use historical data in your backtests
- **Efficient Caching**: Fast access to frequently used data

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interfaces                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │     CLI      │  │   REST API   │  │  Python SDK  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Historical Data Manager                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Downloader  │  │  Converter   │  │  Validator   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data Storage                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  SQLite DB   │  │  File Cache  │  │    Parquet   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backtest Engine                           │
└─────────────────────────────────────────────────────────────┘
```

## Getting Started

### Prerequisites

- Python 3.8 or higher
- SQLite 3
- Internet connection for downloading data
- At least 1GB free disk space (more for extensive historical data)

### What You'll Need

1. **Backend Installation**: The BTC Options Trading backend must be installed
2. **Dependencies**: All Python dependencies from `requirements.txt`
3. **Database**: SQLite database (automatically created)
4. **Storage**: Directory for downloaded files and cache

## Data Sources

### CryptoDataDownload

The system uses free historical data from [CryptoDataDownload](https://www.cryptodatadownload.com/data/deribit/), which provides:

- **Exchange**: Deribit
- **Asset**: Bitcoin (BTC) options
- **Format**: CSV files with OHLCV data
- **Frequency**: Varies by file (typically hourly or daily)
- **Coverage**: Multiple expiry dates
- **Cost**: Free

### Data Format

Each CSV file contains:
- **Timestamp**: Date and time of the data point
- **Open**: Opening price
- **High**: Highest price in the period
- **Low**: Lowest price in the period
- **Close**: Closing price
- **Volume**: Trading volume

File naming convention: `Deribit_BTCUSD_YYYYMMDD_STRIKE_TYPE.csv`
- Example: `Deribit_BTCUSD_20240329_50000_C.csv` (Call option, $50,000 strike, March 29, 2024 expiry)

## Installation

### 1. Install Dependencies

```bash
cd BTCOptionsTrading/backend
pip install -r requirements.txt
```

### 2. Verify Installation

```bash
python historical_cli.py --help
```

You should see the CLI help message with available commands.

### 3. Initialize Database

The database is automatically created on first use, but you can verify:

```bash
python historical_cli.py stats
```

## Quick Start

### Complete Workflow in 5 Steps

```bash
# 1. Download historical data for a specific expiry date
python historical_cli.py download -e 2024-03-29

# 2. Import the downloaded data into the database
python historical_cli.py import -d data/downloads

# 3. Validate data quality
python historical_cli.py validate -s 2024-03-01 -e 2024-03-31

# 4. View statistics
python historical_cli.py stats

# 5. Use in backtest (see Backtest Integration section)
```

### Your First Download

Let's download and import data for one expiry date:

```bash
# Download data for March 29, 2024 expiry
python historical_cli.py download -e 2024-03-29

# Import all downloaded files
python historical_cli.py import -d data/downloads

# Check what we have
python historical_cli.py stats
```

Expected output:
```
✓ Downloaded 15 files for expiry 2024-03-29
✓ Imported 15 files successfully
✓ Total records: 12,450
✓ Date range: 2024-01-01 to 2024-03-29
```

## Using the CLI

The Command-Line Interface (CLI) is the primary way to manage historical data.

### Download Command

Download historical options data from CryptoDataDownload.

```bash
# Basic usage
python historical_cli.py download -e 2024-03-29

# Multiple expiry dates
python historical_cli.py download -e 2024-03-29 -e 2024-04-26 -e 2024-05-31

# With custom settings
python historical_cli.py download -e 2024-03-29 -s BTC -d /custom/path --force

# Batch download with higher concurrency
python historical_cli.py download -e 2024-03-29 -e 2024-04-26 -c 5
```

**Options:**
- `-e, --expiry-date`: Expiry date in YYYY-MM-DD format (can specify multiple)
- `-s, --symbol`: Underlying symbol (default: BTC)
- `-d, --download-dir`: Download directory (default: data/downloads)
- `-f, --force`: Force re-download even if files exist
- `-c, --max-concurrent`: Maximum concurrent downloads (default: 3)

### Import Command

Import downloaded CSV files into the database.

```bash
# Import from directory
python historical_cli.py import -d data/downloads

# Import specific files
python historical_cli.py import -f data/file1.csv -f data/file2.csv

# Import without validation (faster)
python historical_cli.py import -d data/downloads --no-validate --no-report

# Import to custom database
python historical_cli.py import -d data/downloads --db-path /custom/db.db
```

**Options:**
- `-f, --file`: CSV file path (can specify multiple)
- `-d, --directory`: Directory containing CSV files
- `--validate/--no-validate`: Validate data quality (default: validate)
- `--report/--no-report`: Generate quality report (default: report)
- `--db-path`: Database path (default: data/btc_options.db)

### Validate Command

Validate the quality and completeness of stored data.

```bash
# Validate all data
python historical_cli.py validate

# Validate date range
python historical_cli.py validate --start-date 2024-03-01 --end-date 2024-03-31

# Validate specific instrument
python historical_cli.py validate --instrument BTC-29MAR24-50000-C

# Get detailed validation report
python historical_cli.py validate --start-date 2024-03-01 --end-date 2024-03-31 --detailed
```

**Options:**
- `-s, --start-date`: Start date (YYYY-MM-DD)
- `-e, --end-date`: End date (YYYY-MM-DD)
- `-i, --instrument`: Instrument name
- `--db-path`: Database path
- `--detailed`: Show detailed validation results

### Export Command

Export historical data to various formats.

```bash
# Export to CSV
python historical_cli.py export -s 2024-03-01 -e 2024-03-31 -f csv -o data/export.csv

# Export to JSON with compression
python historical_cli.py export -s 2024-03-01 -e 2024-03-31 -f json -o data/export.json --compress

# Export specific instruments to Parquet
python historical_cli.py export -s 2024-03-01 -e 2024-03-31 \
  -i BTC-29MAR24-50000-C -i BTC-29MAR24-51000-C \
  -f parquet -o data/export.parquet
```

**Options:**
- `-s, --start-date`: Start date (YYYY-MM-DD) [required]
- `-e, --end-date`: End date (YYYY-MM-DD) [required]
- `-i, --instrument`: Instrument name (can specify multiple)
- `-f, --format`: Export format (csv, json, parquet)
- `-o, --output`: Output file path [required]
- `--compress`: Compress output file
- `--db-path`: Database path

### Stats Command

Show statistics about stored historical data.

```bash
# General statistics
python historical_cli.py stats

# Statistics for date range
python historical_cli.py stats --start-date 2024-03-01 --end-date 2024-03-31

# Statistics for specific symbol
python historical_cli.py stats --symbol ETH
```

**Options:**
- `-s, --start-date`: Start date (YYYY-MM-DD)
- `-e, --end-date`: End date (YYYY-MM-DD)
- `--symbol`: Underlying symbol (default: BTC)
- `--db-path`: Database path

### Clear Command

Clear cached data or database.

```bash
# Clear file cache only
python historical_cli.py clear --clear-cache

# Clear database (requires confirmation)
python historical_cli.py clear --clear-database

# Clear both
python historical_cli.py clear --clear-cache --clear-database
```

**Warning:** The `--clear-database` option will delete all historical data. This action cannot be undone.

## Using the API

The REST API provides programmatic access to historical data management.

### Base URL

```
http://localhost:8000/api/historical-data
```

### Endpoints

#### 1. Import Historical Data

```http
POST /api/historical-data/import
Content-Type: application/json

{
  "expiry_dates": ["2024-03-29", "2024-04-26"],
  "validate": true
}
```

Response:
```json
{
  "success": true,
  "files_processed": 30,
  "records_imported": 25000,
  "records_failed": 0,
  "duration_seconds": 45.2,
  "quality_report": {
    "total_records": 25000,
    "missing_records": 0,
    "anomaly_records": 5,
    "coverage_percentage": 99.8
  }
}
```

#### 2. List Available Data

```http
GET /api/historical-data/available?symbol=BTC
```

Response:
```json
{
  "files": [
    {
      "expiry_date": "2024-03-29",
      "url": "https://...",
      "filename": "Deribit_BTCUSD_20240329.zip",
      "estimated_size": 5242880,
      "last_modified": "2024-03-30T00:00:00Z"
    }
  ]
}
```

#### 3. Get Coverage Statistics

```http
GET /api/historical-data/coverage?start_date=2024-03-01&end_date=2024-03-31
```

Response:
```json
{
  "start_date": "2024-03-01",
  "end_date": "2024-03-31",
  "total_records": 25000,
  "coverage_percentage": 95.5,
  "available_instruments": 150,
  "missing_dates": ["2024-03-15", "2024-03-16"]
}
```

#### 4. Export Data

```http
POST /api/historical-data/export
Content-Type: application/json

{
  "start_date": "2024-03-01",
  "end_date": "2024-03-31",
  "format": "csv",
  "instruments": ["BTC-29MAR24-50000-C"],
  "compress": true
}
```

Response:
```json
{
  "success": true,
  "file_path": "data/exports/historical_data_20240315_120000.csv.gz",
  "records_exported": 5000,
  "file_size_bytes": 524288
}
```

#### 5. Clear Cache

```http
DELETE /api/historical-data/cache?before_date=2024-01-01
```

Response:
```json
{
  "success": true,
  "records_deleted": 10000
}
```

### API Examples

#### Python with requests

```python
import requests

# Import data
response = requests.post(
    'http://localhost:8000/api/historical-data/import',
    json={
        'expiry_dates': ['2024-03-29'],
        'validate': True
    }
)
result = response.json()
print(f"Imported {result['records_imported']} records")

# Get coverage stats
response = requests.get(
    'http://localhost:8000/api/historical-data/coverage',
    params={
        'start_date': '2024-03-01',
        'end_date': '2024-03-31'
    }
)
stats = response.json()
print(f"Coverage: {stats['coverage_percentage']}%")
```

#### JavaScript/TypeScript

```typescript
// Import data
const response = await fetch('http://localhost:8000/api/historical-data/import', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    expiry_dates: ['2024-03-29'],
    validate: true
  })
});
const result = await response.json();
console.log(`Imported ${result.records_imported} records`);

// Get coverage stats
const statsResponse = await fetch(
  'http://localhost:8000/api/historical-data/coverage?' +
  'start_date=2024-03-01&end_date=2024-03-31'
);
const stats = await statsResponse.json();
console.log(`Coverage: ${stats.coverage_percentage}%`);
```

## Using the Python SDK

For Python applications, you can use the historical data classes directly.

### Basic Usage

```python
from src.historical.manager import HistoricalDataManager
from datetime import datetime

# Initialize manager
manager = HistoricalDataManager()

# Import historical data
result = await manager.import_historical_data(
    expiry_dates=[datetime(2024, 3, 29)],
    validate=True
)

print(f"Imported {result.records_imported} records")
print(f"Quality score: {result.quality_report.quality_score}")

# Get data for backtest
backtest_data = manager.get_data_for_backtest(
    start_date=datetime(2024, 3, 1),
    end_date=datetime(2024, 3, 31),
    strikes=[50000, 51000, 52000]
)

print(f"Loaded {len(backtest_data.options_data)} instruments")
```

### Advanced Usage

```python
from src.historical.downloader import CryptoDataDownloader
from src.historical.converter import HistoricalDataConverter
from src.historical.validator import HistoricalDataValidator
from src.historical.cache import HistoricalDataCache

# Initialize components
downloader = CryptoDataDownloader(cache_dir="data/historical")
converter = HistoricalDataConverter()
validator = HistoricalDataValidator()
cache = HistoricalDataCache(db_manager=db_manager)

# Download data
files = await downloader.batch_download(
    expiry_dates=[datetime(2024, 3, 29), datetime(2024, 4, 26)],
    max_concurrent=3
)

# Parse and convert
for file_path in files.values():
    ohlcv_data = converter.parse_csv_file(file_path)
    option_info = converter.extract_option_info(file_path.name)
    internal_data = converter.convert_to_internal_format(ohlcv_data, option_info)
    
    # Validate
    validation_result = validator.validate_data_completeness(internal_data)
    if validation_result.is_valid:
        # Store in cache
        cache.store_historical_data(internal_data)

# Query data
data = cache.query_option_data(
    instrument_name="BTC-29MAR24-50000-C",
    start_date=datetime(2024, 3, 1),
    end_date=datetime(2024, 3, 31)
)
```

## Data Quality and Validation

### Validation Checks

The system performs comprehensive validation:

1. **Completeness Checks**
   - Time series continuity
   - Missing values detection
   - Data point count verification

2. **Price Sanity Checks**
   - Negative price detection
   - Extreme volatility detection
   - OHLC relationship validation (Low ≤ Open ≤ High, Low ≤ Close ≤ High)

3. **Option-Specific Checks**
   - Put-call parity validation
   - Strike price consistency
   - Expiry date validation

### Quality Reports

Quality reports include:

```json
{
  "quality_score": 95.5,
  "total_records": 25000,
  "missing_records": 100,
  "anomaly_records": 50,
  "coverage_percentage": 99.4,
  "time_range": ["2024-03-01", "2024-03-31"],
  "issues": [
    {
      "severity": "warning",
      "type": "missing_data",
      "description": "Missing data for 2024-03-15",
      "count": 50
    },
    {
      "severity": "error",
      "type": "price_anomaly",
      "description": "Negative prices detected",
      "count": 5
    }
  ]
}
```

### Interpreting Quality Scores

- **95-100**: Excellent quality, safe to use
- **85-95**: Good quality, minor issues
- **70-85**: Acceptable quality, review issues
- **Below 70**: Poor quality, investigate before use

## Backtest Integration

### Using Historical Data in Backtests

```python
from src.backtest.backtest_engine import BacktestEngine
from src.historical.manager import HistoricalDataManager
from datetime import datetime

# Get historical data
manager = HistoricalDataManager()
backtest_data = manager.get_data_for_backtest(
    start_date=datetime(2024, 3, 1),
    end_date=datetime(2024, 3, 31)
)

# Configure backtest engine
engine = BacktestEngine(
    data_source='historical',  # Use historical data
    historical_data=backtest_data
)

# Run backtest
strategy = YourStrategy()
results = engine.run_backtest(
    strategy=strategy,
    start_date=datetime(2024, 3, 1),
    end_date=datetime(2024, 3, 31)
)

print(f"Total return: {results.total_return}%")
print(f"Sharpe ratio: {results.sharpe_ratio}")
```

### Data Source Selection

The backtest engine supports multiple data sources:

```python
# Use historical data
engine = BacktestEngine(data_source='historical')

# Use live API data
engine = BacktestEngine(data_source='live')

# Hybrid: historical for past, live for recent
engine = BacktestEngine(
    data_source='hybrid',
    historical_cutoff=datetime(2024, 3, 1)
)
```

### Handling Missing Data

```python
# Check data coverage before backtest
coverage = manager.get_coverage_stats(
    start_date=datetime(2024, 3, 1),
    end_date=datetime(2024, 3, 31)
)

if coverage.coverage_percentage < 90:
    print(f"Warning: Only {coverage.coverage_percentage}% coverage")
    print(f"Missing dates: {coverage.missing_dates}")
    
    # Download missing data
    for missing_date in coverage.missing_dates:
        await manager.import_historical_data(
            expiry_dates=[missing_date],
            validate=True
        )
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Download Fails

**Problem**: Downloads fail with network errors

**Solutions**:
- Check internet connection
- Verify the expiry date exists on CryptoDataDownload
- Use `--force` flag to retry
- Check logs in `logs/app.log`
- Try reducing `--max-concurrent` value

```bash
# Retry with force flag
python historical_cli.py download -e 2024-03-29 --force

# Reduce concurrency
python historical_cli.py download -e 2024-03-29 -c 1
```

#### 2. Import Errors

**Problem**: CSV files fail to import

**Solutions**:
- Verify CSV files are in correct format
- Check file permissions
- Ensure database path is writable
- Use `--no-validate` to skip validation
- Check for corrupted files

```bash
# Import without validation
python historical_cli.py import -d data/downloads --no-validate

# Check file permissions
ls -la data/downloads/

# Verify database is writable
touch data/btc_options.db
```

#### 3. Validation Issues

**Problem**: Validation reports many issues

**Solutions**:
- Use `--detailed` flag to see specific problems
- Check if data source has known quality issues
- Filter out problematic records during export
- Review validation thresholds in config

```bash
# Get detailed validation report
python historical_cli.py validate -s 2024-03-01 -e 2024-03-31 --detailed

# Export only valid data
python historical_cli.py export -s 2024-03-01 -e 2024-03-31 -o clean_data.csv
```

#### 4. Performance Issues

**Problem**: Operations are slow

**Solutions**:
- Use Parquet format for exports (10-100x faster than CSV)
- Increase `--max-concurrent` for downloads
- Use `--no-validate` during import if validation is slow
- Split large date ranges into smaller chunks
- Check disk I/O performance

```bash
# Use Parquet for better performance
python historical_cli.py export -s 2024-03-01 -e 2024-03-31 -f parquet -o data.parquet

# Increase concurrency
python historical_cli.py download -e 2024-03-29 -e 2024-04-26 -c 5
```

#### 5. Storage Issues

**Problem**: Running out of disk space

**Solutions**:
- Clear old cache files
- Export and compress data
- Use Parquet format (more space-efficient)
- Delete unnecessary expiry dates

```bash
# Check current usage
python historical_cli.py stats

# Clear cache
python historical_cli.py clear --clear-cache

# Export and compress
python historical_cli.py export -s 2024-03-01 -e 2024-03-31 -f parquet -o backup.parquet --compress
```

### Checking Logs

Detailed logs are stored in `logs/app.log`:

```bash
# View recent logs
tail -f logs/app.log

# Search for errors
grep ERROR logs/app.log

# Search for specific operation
grep "import" logs/app.log
```

### Database Issues

If the database becomes corrupted:

```bash
# Backup current database
cp data/btc_options.db data/btc_options.db.backup

# Clear and rebuild
python historical_cli.py clear --clear-database
python historical_cli.py import -d data/downloads
```

## Best Practices

### 1. Regular Data Updates

Set up a schedule to check for new data:

```bash
# Weekly cron job (Sunday at 2 AM)
0 2 * * 0 cd /path/to/BTCOptionsTrading/backend && python historical_cli.py download -e $(date -d "next friday" +\%Y-\%m-\%d)
```

### 2. Data Validation

Always validate data after import:

```bash
python historical_cli.py import -d data/downloads --validate --report
```

### 3. Backup Strategy

Regular backups of your data:

```bash
# Monthly backup script
#!/bin/bash
DATE=$(date +%Y%m)
python historical_cli.py export \
  -s 2024-01-01 \
  -e 2024-12-31 \
  -f parquet \
  -o backups/historical_${DATE}.parquet \
  --compress
```

### 4. Storage Management

Monitor and manage storage:

```bash
# Check usage regularly
python historical_cli.py stats

# Clear old data
python historical_cli.py clear --clear-cache

# Export before clearing
python historical_cli.py export -s 2024-01-01 -e 2024-12-31 -o archive.parquet --compress
```

### 5. Batch Operations

Use batch operations for efficiency:

```bash
# Download multiple dates at once
python historical_cli.py download \
  -e 2024-03-29 \
  -e 2024-04-26 \
  -e 2024-05-31 \
  -c 3
```

### 6. Data Quality Monitoring

Regularly check data quality:

```bash
# Weekly quality check
python historical_cli.py validate -s $(date -d "7 days ago" +%Y-%m-%d) -e $(date +%Y-%m-%d) --detailed
```

### 7. Performance Optimization

- Use Parquet format for large datasets
- Limit concurrent downloads to avoid rate limiting
- Use `--no-validate` for large imports (validate separately)
- Cache frequently accessed data

## FAQ

### General Questions

**Q: Is the historical data free?**
A: Yes, CryptoDataDownload provides free historical Deribit options data.

**Q: How far back does the data go?**
A: It varies by expiry date. Check CryptoDataDownload for available dates.

**Q: How often is new data added?**
A: CryptoDataDownload typically updates after options expire.

**Q: Can I use this for live trading?**
A: No, this is historical data for backtesting only. Use the live API for trading.

### Technical Questions

**Q: What database does it use?**
A: SQLite by default, but the system can be adapted for PostgreSQL.

**Q: How much disk space do I need?**
A: Approximately 100MB per expiry date, depending on the number of strikes.

**Q: Can I run multiple imports simultaneously?**
A: No, imports should be run sequentially to avoid database conflicts.

**Q: What's the difference between CSV, JSON, and Parquet exports?**
A: 
- CSV: Human-readable, widely compatible, larger file size
- JSON: Structured, easy to parse, moderate file size
- Parquet: Columnar, very efficient, smallest file size, fastest to read

### Data Quality Questions

**Q: What if validation fails?**
A: Review the detailed report, check the data source, and decide whether to use the data or re-download.

**Q: Can I fix data quality issues?**
A: The system can filter out problematic records during export, but cannot fix source data issues.

**Q: What's a good quality score?**
A: Above 95 is excellent, 85-95 is good, below 85 requires investigation.

### Backtest Questions

**Q: Can I mix historical and live data?**
A: Yes, the backtest engine supports hybrid mode.

**Q: What if I'm missing data for my backtest period?**
A: The system will warn you and suggest downloading the missing data.

**Q: How do I know if my backtest is using historical data?**
A: Check the backtest configuration or logs for the data source.

## Additional Resources

### Documentation

- **CLI Guide**: `backend/HISTORICAL_CLI_GUIDE.md`
- **Quick Start**: `backend/HISTORICAL_CLI_QUICKSTART.md`
- **Design Document**: `.kiro/specs/historical-data-integration/design.md`
- **Requirements**: `.kiro/specs/historical-data-integration/requirements.md`
- **API Documentation**: See API section above

### Example Code

- **CLI Examples**: `backend/examples/historical_cli_example.py`
- **Python SDK Examples**: See "Using the Python SDK" section
- **API Examples**: See "Using the API" section

### Support

For issues or questions:
1. Check this guide and the troubleshooting section
2. Review logs in `logs/app.log`
3. Consult the design and requirements documents
4. Check the GitHub issues (if applicable)

## Conclusion

The Historical Options Data Integration system provides a comprehensive solution for managing historical Bitcoin options data. Whether you're using the CLI, REST API, or Python SDK, you have powerful tools to download, validate, store, and use real market data in your backtesting workflows.

Start with the Quick Start section, explore the examples, and refer back to this guide as needed. Happy backtesting!
