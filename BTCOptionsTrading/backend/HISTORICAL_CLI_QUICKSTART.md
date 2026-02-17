# Historical Data CLI - Quick Start

## Installation

```bash
cd BTCOptionsTrading/backend
pip install click  # If not already installed
```

## Basic Commands

### 1. Download Data
```bash
# Download data for a single expiry date
python historical_cli.py download -e 2024-03-29

# Download multiple dates
python historical_cli.py download -e 2024-03-29 -e 2024-04-26
```

### 2. Import Data
```bash
# Import from directory
python historical_cli.py import-data -d data/downloads

# Import specific files
python historical_cli.py import-data -f data/file1.csv -f data/file2.csv
```

### 3. View Statistics
```bash
# General stats
python historical_cli.py stats

# Stats for date range
python historical_cli.py stats -s 2024-03-01 -e 2024-03-31
```

### 4. Validate Data
```bash
# Validate all data
python historical_cli.py validate

# Validate date range
python historical_cli.py validate -s 2024-03-01 -e 2024-03-31 --detailed
```

### 5. Export Data
```bash
# Export to CSV
python historical_cli.py export -s 2024-03-01 -e 2024-03-31 -o export.csv

# Export to JSON
python historical_cli.py export -s 2024-03-01 -e 2024-03-31 -f json -o export.json

# Export to Parquet (compressed)
python historical_cli.py export -s 2024-03-01 -e 2024-03-31 -f parquet -o export.parquet --compress
```

### 6. Clear Data
```bash
# Clear cache
python historical_cli.py clear --clear-cache

# Clear database (WARNING: deletes all data)
python historical_cli.py clear --clear-database
```

## Complete Workflow

```bash
# 1. Download
python historical_cli.py download -e 2024-03-29 -e 2024-04-26

# 2. Import
python historical_cli.py import-data -d data/downloads

# 3. Check stats
python historical_cli.py stats

# 4. Validate
python historical_cli.py validate -s 2024-03-01 -e 2024-04-30

# 5. Export
python historical_cli.py export -s 2024-03-01 -e 2024-04-30 -o march_april.csv
```

## Help

Get help for any command:
```bash
python historical_cli.py --help
python historical_cli.py download --help
python historical_cli.py import-data --help
```

## Full Documentation

See `HISTORICAL_CLI_GUIDE.md` for complete documentation.
