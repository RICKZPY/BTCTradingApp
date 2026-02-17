# Historical Data Integration - Quick Start

Get started with historical Bitcoin options data in 5 minutes!

## What You'll Need

- Python 3.8+
- Internet connection
- 1GB free disk space

## Installation

```bash
cd BTCOptionsTrading/backend
pip install -r requirements.txt
```

## Quick Start (3 Steps)

### Step 1: Download Data

```bash
python historical_cli.py download -e 2024-03-29
```

This downloads historical options data for the March 29, 2024 expiry date from CryptoDataDownload.

### Step 2: Import Data

```bash
python historical_cli.py import -d data/downloads
```

This imports the downloaded CSV files into your local database.

### Step 3: Verify

```bash
python historical_cli.py stats
```

This shows statistics about your imported data.

## What's Next?

### Use in Backtests

```python
from src.historical.manager import HistoricalDataManager
from datetime import datetime

manager = HistoricalDataManager()
backtest_data = manager.get_data_for_backtest(
    start_date=datetime(2024, 3, 1),
    end_date=datetime(2024, 3, 31)
)

# Use backtest_data in your backtest engine
```

### Export Data

```bash
# Export to CSV
python historical_cli.py export -s 2024-03-01 -e 2024-03-31 -o march.csv

# Export to Parquet (faster, smaller)
python historical_cli.py export -s 2024-03-01 -e 2024-03-31 -f parquet -o march.parquet
```

### Validate Quality

```bash
python historical_cli.py validate -s 2024-03-01 -e 2024-03-31
```

## Common Commands

```bash
# Download multiple dates
python historical_cli.py download -e 2024-03-29 -e 2024-04-26 -e 2024-05-31

# Import with validation
python historical_cli.py import -d data/downloads --validate

# Get detailed statistics
python historical_cli.py stats -s 2024-03-01 -e 2024-03-31

# Clear cache
python historical_cli.py clear --clear-cache
```

## Documentation

- **Complete Guide**: [HISTORICAL_DATA_GUIDE.md](HISTORICAL_DATA_GUIDE.md)
- **CLI Reference**: [backend/HISTORICAL_CLI_GUIDE.md](backend/HISTORICAL_CLI_GUIDE.md)
- **API Documentation**: [backend/HISTORICAL_DATA_API.md](backend/HISTORICAL_DATA_API.md)
- **Troubleshooting**: [backend/HISTORICAL_DATA_TROUBLESHOOTING.md](backend/HISTORICAL_DATA_TROUBLESHOOTING.md)

## Examples

Check out the example scripts in `backend/examples/`:

- `historical_data_import_example.py` - Data import examples
- `historical_backtest_example.py` - Using data in backtests
- `historical_data_export_example.py` - Data export examples
- `historical_cli_example.py` - CLI usage examples

Run an example:

```bash
cd backend/examples
python historical_data_import_example.py
```

## Need Help?

1. Check the [Troubleshooting Guide](backend/HISTORICAL_DATA_TROUBLESHOOTING.md)
2. Review the [Complete Guide](HISTORICAL_DATA_GUIDE.md)
3. Look at the [Examples](backend/examples/)
4. Check logs: `tail -f backend/logs/app.log`

## Tips

- Use Parquet format for better performance (10-100x faster than CSV)
- Always validate data after import
- Check coverage before running backtests
- Regular backups: `python historical_cli.py export -s 2024-01-01 -e 2024-12-31 -f parquet -o backup.parquet --compress`

Happy backtesting! 🚀
