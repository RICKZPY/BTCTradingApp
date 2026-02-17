# Historical Data CLI Guide

This guide explains how to use the command-line interface (CLI) for managing historical options data.

## Installation

The CLI requires the following dependencies:
```bash
pip install click
```

All other dependencies should already be installed as part of the main project.

## Quick Start

The CLI is accessible via the `historical_cli.py` script in the backend directory:

```bash
cd BTCOptionsTrading/backend
python historical_cli.py --help
```

Or make it executable and run directly:
```bash
chmod +x historical_cli.py
./historical_cli.py --help
```

## Available Commands

### 1. Download Historical Data

Download historical options data from CryptoDataDownload.

**Usage:**
```bash
python historical_cli.py download [OPTIONS]
```

**Options:**
- `-e, --expiry-date TEXT`: Expiry date in YYYY-MM-DD format (can specify multiple)
- `-s, --symbol TEXT`: Underlying symbol (default: BTC)
- `-d, --download-dir TEXT`: Download directory (default: data/downloads)
- `-f, --force`: Force re-download even if files exist
- `-c, --max-concurrent INTEGER`: Maximum concurrent downloads (default: 3)

**Examples:**
```bash
# Download data for a single expiry date
python historical_cli.py download -e 2024-03-29

# Download data for multiple expiry dates
python historical_cli.py download -e 2024-03-29 -e 2024-04-26 -e 2024-05-31

# Download with custom settings
python historical_cli.py download -e 2024-03-29 -s BTC -d /custom/path --force

# Batch download with higher concurrency
python historical_cli.py download -e 2024-03-29 -e 2024-04-26 -c 5
```

**Output:**
- Downloads ZIP files from CryptoDataDownload
- Automatically extracts CSV files
- Shows progress and results
- Implements retry logic with exponential backoff

### 2. Import Data into System

Import downloaded CSV files into the database.

**Usage:**
```bash
python historical_cli.py import [OPTIONS]
```

**Options:**
- `-f, --file TEXT`: CSV file path (can specify multiple)
- `-d, --directory TEXT`: Directory containing CSV files
- `--validate/--no-validate`: Validate data quality (default: validate)
- `--report/--no-report`: Generate quality report (default: report)
- `--db-path TEXT`: Database path (default: data/btc_options.db)

**Examples:**
```bash
# Import all CSV files from a directory
python historical_cli.py import -d data/downloads/BTC_20240329

# Import specific files
python historical_cli.py import -f data/file1.csv -f data/file2.csv

# Import without validation (faster)
python historical_cli.py import -d data/downloads --no-validate --no-report

# Import to custom database
python historical_cli.py import -d data/downloads --db-path /custom/db.db
```

**Output:**
- Number of files processed
- Success/failure counts
- Records imported
- Duration
- Quality report (if enabled)

### 3. Validate Data Quality

Validate the quality and completeness of stored data.

**Usage:**
```bash
python historical_cli.py validate [OPTIONS]
```

**Options:**
- `-s, --start-date TEXT`: Start date (YYYY-MM-DD)
- `-e, --end-date TEXT`: End date (YYYY-MM-DD)
- `-i, --instrument TEXT`: Instrument name (e.g., BTC-29MAR24-50000-C)
- `--db-path TEXT`: Database path (default: data/btc_options.db)
- `--detailed`: Show detailed validation results

**Examples:**
```bash
# Validate all data
python historical_cli.py validate

# Validate data for a date range
python historical_cli.py validate --start-date 2024-03-01 --end-date 2024-03-31

# Validate specific instrument
python historical_cli.py validate --instrument BTC-29MAR24-50000-C

# Get detailed validation report
python historical_cli.py validate --start-date 2024-03-01 --end-date 2024-03-31 --detailed
```

**Output:**
- Quality score (0-100)
- Total records
- Missing/anomaly records
- Coverage percentage
- List of issues by severity
- Detailed issue descriptions (with --detailed flag)

### 4. Export Data

Export historical data to various formats.

**Usage:**
```bash
python historical_cli.py export [OPTIONS]
```

**Options:**
- `-s, --start-date TEXT`: Start date (YYYY-MM-DD) [required]
- `-e, --end-date TEXT`: End date (YYYY-MM-DD) [required]
- `-i, --instrument TEXT`: Instrument name (can specify multiple)
- `-f, --format [csv|json|parquet]`: Export format (default: csv)
- `-o, --output TEXT`: Output file path [required]
- `--compress`: Compress output file
- `--db-path TEXT`: Database path (default: data/btc_options.db)

**Examples:**
```bash
# Export to CSV
python historical_cli.py export -s 2024-03-01 -e 2024-03-31 -f csv -o data/export.csv

# Export to JSON with compression
python historical_cli.py export -s 2024-03-01 -e 2024-03-31 -f json -o data/export.json --compress

# Export specific instruments to Parquet
python historical_cli.py export -s 2024-03-01 -e 2024-03-31 \
  -i BTC-29MAR24-50000-C -i BTC-29MAR24-51000-C \
  -f parquet -o data/export.parquet

# Export all data for a month
python historical_cli.py export -s 2024-03-01 -e 2024-03-31 -f csv -o data/march_2024.csv
```

**Output:**
- Records exported
- File path
- File size

**Supported Formats:**
- **CSV**: Human-readable, widely compatible
- **JSON**: Structured data, easy to parse
- **Parquet**: Columnar format, efficient for large datasets (requires pandas and pyarrow)

### 5. Display Statistics

Show statistics about stored historical data.

**Usage:**
```bash
python historical_cli.py stats [OPTIONS]
```

**Options:**
- `-s, --start-date TEXT`: Start date (YYYY-MM-DD)
- `-e, --end-date TEXT`: End date (YYYY-MM-DD)
- `--symbol TEXT`: Underlying symbol (default: BTC)
- `--db-path TEXT`: Database path (default: data/btc_options.db)

**Examples:**
```bash
# Show general statistics
python historical_cli.py stats

# Show statistics for a date range
python historical_cli.py stats --start-date 2024-03-01 --end-date 2024-03-31

# Show statistics for ETH options
python historical_cli.py stats --symbol ETH
```

**Output:**
- Download directory info
- CSV files count
- Cache statistics
- Total records
- Available instruments
- Date coverage
- Coverage percentage (if date range specified)
- Missing dates

### 6. Clear Data

Clear cached data or database (requires confirmation).

**Usage:**
```bash
python historical_cli.py clear [OPTIONS]
```

**Options:**
- `--clear-cache`: Clear file cache
- `--clear-database`: Clear database (WARNING: deletes all data)
- `--db-path TEXT`: Database path (default: data/btc_options.db)

**Examples:**
```bash
# Clear file cache only
python historical_cli.py clear --clear-cache

# Clear database (requires confirmation)
python historical_cli.py clear --clear-database

# Clear both
python historical_cli.py clear --clear-cache --clear-database
```

**Warning:** The `--clear-database` option will delete all historical data from the database. This action cannot be undone.

## Complete Workflow Example

Here's a complete workflow from downloading to using historical data:

```bash
# 1. Download data for multiple expiry dates
python historical_cli.py download \
  -e 2024-03-29 \
  -e 2024-04-26 \
  -e 2024-05-31 \
  -s BTC

# 2. Import the downloaded data
python historical_cli.py import \
  -d data/downloads \
  --validate \
  --report

# 3. Check statistics
python historical_cli.py stats

# 4. Validate data quality for a specific period
python historical_cli.py validate \
  --start-date 2024-03-01 \
  --end-date 2024-05-31 \
  --detailed

# 5. Export data for analysis
python historical_cli.py export \
  -s 2024-03-01 \
  -e 2024-05-31 \
  -f parquet \
  -o data/q1_2024.parquet \
  --compress

# 6. Get coverage statistics
python historical_cli.py stats \
  --start-date 2024-03-01 \
  --end-date 2024-05-31
```

## Tips and Best Practices

### 1. Batch Downloads
When downloading multiple expiry dates, use batch mode for efficiency:
```bash
python historical_cli.py download -e 2024-03-29 -e 2024-04-26 -e 2024-05-31 -c 3
```

### 2. Validation
Always validate data after import to ensure quality:
```bash
python historical_cli.py import -d data/downloads --validate --report
```

### 3. Regular Updates
Set up a cron job or scheduled task to regularly check for new data:
```bash
# Example cron job (runs weekly on Sunday at 2 AM)
0 2 * * 0 cd /path/to/BTCOptionsTrading/backend && python historical_cli.py download -e $(date -d "next friday" +\%Y-\%m-\%d)
```

### 4. Storage Management
Monitor storage usage and clear old data when needed:
```bash
# Check current usage
python historical_cli.py stats

# Clear cache if needed
python historical_cli.py clear --clear-cache
```

### 5. Export for Backup
Regularly export data for backup purposes:
```bash
# Monthly backup
python historical_cli.py export \
  -s 2024-03-01 \
  -e 2024-03-31 \
  -f parquet \
  -o backups/march_2024.parquet \
  --compress
```

## Troubleshooting

### Download Fails
If downloads fail:
1. Check your internet connection
2. Verify the expiry date is valid and data exists on CryptoDataDownload
3. Use the `--force` flag to retry
4. Check logs in `logs/app.log`

### Import Errors
If import fails:
1. Verify CSV files are in the correct format
2. Check file permissions
3. Ensure database path is writable
4. Use `--no-validate` to skip validation if data has known issues

### Validation Issues
If validation reports many issues:
1. Use `--detailed` flag to see specific problems
2. Check if data source has known quality issues
3. Consider filtering out problematic records during export

### Performance
For large datasets:
1. Use Parquet format for exports (much faster than CSV)
2. Increase `--max-concurrent` for downloads (but not too high)
3. Use `--no-validate` during import if validation is slow
4. Consider splitting large date ranges into smaller chunks

## Integration with Python Code

You can also use the CLI commands programmatically:

```python
import subprocess

# Download data
subprocess.run([
    'python', 'historical_cli.py', 'download',
    '-e', '2024-03-29',
    '-s', 'BTC'
])

# Import data
subprocess.run([
    'python', 'historical_cli.py', 'import',
    '-d', 'data/downloads'
])
```

Or use the underlying classes directly:

```python
from src.historical.manager import HistoricalDataManager

manager = HistoricalDataManager()
result = manager.import_historical_data(
    file_paths=['data/file1.csv'],
    validate=True
)
print(f"Imported {result.records_imported} records")
```

## Requirements Validation

This CLI implementation satisfies the following requirements:

- **Requirement 1.1**: Download command connects to CryptoDataDownload
- **Requirement 2.4**: Import command validates data completeness
- **Requirement 5.5**: Stats command provides coverage statistics
- **Requirement 9.1**: Export command supports multiple formats

## Support

For issues or questions:
1. Check the logs in `logs/app.log`
2. Review the design document at `.kiro/specs/historical-data-integration/design.md`
3. Consult the requirements document at `.kiro/specs/historical-data-integration/requirements.md`
