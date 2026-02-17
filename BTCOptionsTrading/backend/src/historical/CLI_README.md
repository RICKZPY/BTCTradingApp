# Historical Data CLI

A command-line interface for managing historical options data in the BTC Options Trading system.

## Overview

The Historical Data CLI provides a comprehensive set of commands for:
- Downloading historical options data from CryptoDataDownload
- Importing data into the system database
- Validating data quality and completeness
- Exporting data in multiple formats
- Viewing statistics and coverage information
- Managing cached data

## Features

### ✓ Download Command
- Download historical options data from CryptoDataDownload
- Support for single or batch downloads
- Automatic retry with exponential backoff
- Progress tracking
- Idempotent operations (skip existing files)

### ✓ Import Command
- Import CSV files into the database
- Automatic data validation
- Quality report generation
- Batch processing support
- Error handling and recovery

### ✓ Validate Command
- Comprehensive data quality validation
- Check for missing data, anomalies, and errors
- Generate detailed quality reports
- Support for date range and instrument filtering

### ✓ Export Command
- Export data in CSV, JSON, or Parquet formats
- Support for date range filtering
- Instrument-specific exports
- Optional compression
- Efficient batch processing

### ✓ Stats Command
- View database statistics
- Check data coverage
- List available instruments and dates
- Monitor storage usage

### ✓ Clear Command
- Clear file cache
- Clear database (with confirmation)
- Storage management

## Installation

```bash
cd BTCOptionsTrading/backend
pip install click
```

## Quick Start

```bash
# View available commands
python historical_cli.py --help

# Download data
python historical_cli.py download -e 2024-03-29

# Import data
python historical_cli.py import-data -d data/downloads

# View statistics
python historical_cli.py stats

# Validate data
python historical_cli.py validate -s 2024-03-01 -e 2024-03-31

# Export data
python historical_cli.py export -s 2024-03-01 -e 2024-03-31 -o export.csv
```

## Documentation

- **Quick Start Guide**: `HISTORICAL_CLI_QUICKSTART.md`
- **Complete Guide**: `HISTORICAL_CLI_GUIDE.md`
- **Design Document**: `.kiro/specs/historical-data-integration/design.md`
- **Requirements**: `.kiro/specs/historical-data-integration/requirements.md`

## Architecture

The CLI is built on top of the historical data management system:

```
CLI (cli.py)
    ↓
HistoricalDataManager (manager.py)
    ↓
├── CryptoDataDownloader (downloader.py)
├── HistoricalDataConverter (converter.py)
├── HistoricalDataValidator (validator.py)
└── HistoricalDataCache (cache.py)
```

## Requirements Satisfied

This CLI implementation satisfies the following requirements from the spec:

- **Requirement 1.1**: Download historical data from CryptoDataDownload
- **Requirement 2.4**: Validate data completeness and quality
- **Requirement 5.5**: Provide data coverage statistics
- **Requirement 9.1**: Export data in multiple formats

## Command Reference

| Command | Description | Example |
|---------|-------------|---------|
| `download` | Download historical data | `python historical_cli.py download -e 2024-03-29` |
| `import-data` | Import CSV files | `python historical_cli.py import-data -d data/downloads` |
| `validate` | Validate data quality | `python historical_cli.py validate -s 2024-03-01 -e 2024-03-31` |
| `export` | Export data | `python historical_cli.py export -s 2024-03-01 -e 2024-03-31 -o export.csv` |
| `stats` | View statistics | `python historical_cli.py stats` |
| `clear` | Clear cached data | `python historical_cli.py clear --clear-cache` |

## Examples

### Complete Workflow

```bash
# 1. Download data for multiple expiry dates
python historical_cli.py download \
  -e 2024-03-29 \
  -e 2024-04-26 \
  -e 2024-05-31

# 2. Import all downloaded data
python historical_cli.py import-data \
  -d data/downloads \
  --validate \
  --report

# 3. Check statistics
python historical_cli.py stats

# 4. Validate data quality
python historical_cli.py validate \
  --start-date 2024-03-01 \
  --end-date 2024-05-31 \
  --detailed

# 5. Export for analysis
python historical_cli.py export \
  -s 2024-03-01 \
  -e 2024-05-31 \
  -f parquet \
  -o q1_2024.parquet \
  --compress
```

### Batch Operations

```bash
# Download multiple dates with concurrency control
python historical_cli.py download \
  -e 2024-03-29 \
  -e 2024-04-26 \
  -e 2024-05-31 \
  -c 5

# Import multiple files
python historical_cli.py import-data \
  -f data/file1.csv \
  -f data/file2.csv \
  -f data/file3.csv
```

### Data Quality

```bash
# Validate all data
python historical_cli.py validate

# Validate specific date range with details
python historical_cli.py validate \
  --start-date 2024-03-01 \
  --end-date 2024-03-31 \
  --detailed

# Validate specific instrument
python historical_cli.py validate \
  --instrument BTC-29MAR24-50000-C
```

### Export Formats

```bash
# Export to CSV
python historical_cli.py export \
  -s 2024-03-01 -e 2024-03-31 \
  -f csv -o march.csv

# Export to JSON with compression
python historical_cli.py export \
  -s 2024-03-01 -e 2024-03-31 \
  -f json -o march.json --compress

# Export to Parquet (most efficient)
python historical_cli.py export \
  -s 2024-03-01 -e 2024-03-31 \
  -f parquet -o march.parquet
```

## Error Handling

The CLI includes comprehensive error handling:
- Network errors with retry logic
- File parsing errors with recovery
- Database errors with rollback
- User-friendly error messages
- Detailed logging to `logs/app.log`

## Performance

- Concurrent downloads for batch operations
- Efficient database queries with indexes
- Parquet format for fast exports
- Progress tracking for long operations
- Memory-efficient streaming for large files

## Testing

The CLI has been tested with:
- Valid and invalid command-line arguments
- Various date ranges and formats
- Different export formats
- Error conditions and edge cases
- Large datasets

## Future Enhancements

Potential improvements for future versions:
- Interactive mode for guided workflows
- Configuration file support
- Scheduled/automated downloads
- Email notifications for errors
- Web dashboard integration
- More export formats (Excel, HDF5)

## Support

For issues or questions:
1. Check the documentation in `HISTORICAL_CLI_GUIDE.md`
2. Review logs in `logs/app.log`
3. Consult the design document
4. Check the requirements document

## License

Part of the BTC Options Trading system.
