#!/bin/bash
# Example script demonstrating Historical Data CLI usage

echo "=========================================="
echo "Historical Data CLI - Example Workflow"
echo "=========================================="
echo ""

# Set the backend directory
BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$BACKEND_DIR"

echo "Step 1: View CLI help"
echo "----------------------------------------"
python historical_cli.py --help
echo ""

echo "Step 2: Check current statistics"
echo "----------------------------------------"
python historical_cli.py stats
echo ""

echo "Step 3: Download sample data (example - will fail if date doesn't exist)"
echo "----------------------------------------"
echo "Command: python historical_cli.py download -e 2024-03-29"
echo "Note: This will download from CryptoDataDownload if the data exists"
echo ""

echo "Step 4: Import data (if you have CSV files)"
echo "----------------------------------------"
echo "Command: python historical_cli.py import-data -d data/downloads"
echo "Note: This will import all CSV files from the downloads directory"
echo ""

echo "Step 5: Validate data quality"
echo "----------------------------------------"
echo "Command: python historical_cli.py validate --start-date 2024-03-01 --end-date 2024-03-31"
echo "Note: This will validate data for the specified date range"
echo ""

echo "Step 6: Export data"
echo "----------------------------------------"
echo "Command: python historical_cli.py export -s 2024-03-01 -e 2024-03-31 -f csv -o export.csv"
echo "Note: This will export data to CSV format"
echo ""

echo "=========================================="
echo "Example workflow complete!"
echo "=========================================="
echo ""
echo "For more information, see:"
echo "  - HISTORICAL_CLI_QUICKSTART.md"
echo "  - HISTORICAL_CLI_GUIDE.md"
echo "  - src/historical/CLI_README.md"
