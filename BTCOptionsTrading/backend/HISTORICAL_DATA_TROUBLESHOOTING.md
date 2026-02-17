# Historical Data System - Troubleshooting Guide

## Table of Contents

1. [Download Issues](#download-issues)
2. [Import Issues](#import-issues)
3. [Validation Issues](#validation-issues)
4. [Performance Issues](#performance-issues)
5. [Storage Issues](#storage-issues)
6. [Database Issues](#database-issues)
7. [API Issues](#api-issues)
8. [Data Quality Issues](#data-quality-issues)
9. [Backtest Integration Issues](#backtest-integration-issues)
10. [Common Error Messages](#common-error-messages)

## Download Issues

### Problem: Downloads Fail with Network Errors

**Symptoms**:
- Connection timeout errors
- "Failed to download" messages
- Incomplete downloads

**Possible Causes**:
1. Internet connection issues
2. CryptoDataDownload server unavailable
3. Firewall blocking connections
4. Rate limiting

**Solutions**:

1. **Check internet connection**:
   ```bash
   ping www.cryptodatadownload.com
   ```

2. **Retry with force flag**:
   ```bash
   python historical_cli.py download -e 2024-03-29 --force
   ```

3. **Reduce concurrency**:
   ```bash
   python historical_cli.py download -e 2024-03-29 -c 1
   ```

4. **Check firewall settings**:
   - Ensure outbound HTTPS connections are allowed
   - Check corporate proxy settings

5. **Wait and retry**:
   - CryptoDataDownload may be temporarily unavailable
   - Try again in a few minutes

6. **Check logs**:
   ```bash
   tail -f logs/app.log | grep ERROR
   ```

### Problem: Downloaded Files Are Corrupted

**Symptoms**:
- ZIP extraction fails
- "Invalid ZIP file" errors
- Incomplete CSV files

**Solutions**:

1. **Re-download with force flag**:
   ```bash
   python historical_cli.py download -e 2024-03-29 --force
   ```

2. **Verify file integrity**:
   ```bash
   unzip -t data/downloads/Deribit_BTCUSD_20240329.zip
   ```

3. **Check disk space**:
   ```bash
   df -h
   ```

4. **Clear partial downloads**:
   ```bash
   rm -rf data/downloads/*
   python historical_cli.py download -e 2024-03-29
   ```

### Problem: Expiry Date Not Found

**Symptoms**:
- "No data available for expiry date" error
- Empty file list

**Solutions**:

1. **Check available dates**:
   ```bash
   python historical_cli.py download --list-available
   ```

2. **Verify date format**:
   - Must be YYYY-MM-DD
   - Example: 2024-03-29 (not 2024-3-29 or 03/29/2024)

3. **Check CryptoDataDownload website**:
   - Visit https://www.cryptodatadownload.com/data/deribit/
   - Verify the expiry date exists

## Import Issues

### Problem: CSV Files Fail to Import

**Symptoms**:
- "Failed to parse CSV" errors
- Import completes with 0 records
- "Invalid file format" errors

**Solutions**:

1. **Verify CSV format**:
   ```bash
   head -n 5 data/downloads/Deribit_BTCUSD_20240329_50000_C.csv
   ```

2. **Check file permissions**:
   ```bash
   ls -la data/downloads/
   chmod 644 data/downloads/*.csv
   ```

3. **Import without validation**:
   ```bash
   python historical_cli.py import -d data/downloads --no-validate
   ```

4. **Import specific files**:
   ```bash
   python historical_cli.py import -f data/downloads/file1.csv
   ```

5. **Check for encoding issues**:
   ```bash
   file data/downloads/*.csv
   ```

### Problem: Database Write Errors

**Symptoms**:
- "Database is locked" errors
- "Permission denied" errors
- Import fails partway through

**Solutions**:

1. **Check database permissions**:
   ```bash
   ls -la data/btc_options.db
   chmod 644 data/btc_options.db
   ```

2. **Ensure no other processes are using the database**:
   ```bash
   lsof data/btc_options.db
   ```

3. **Close other connections**:
   - Stop the API server if running
   - Close any database browsers

4. **Use a different database path**:
   ```bash
   python historical_cli.py import -d data/downloads --db-path /tmp/test.db
   ```

5. **Check disk space**:
   ```bash
   df -h
   ```

### Problem: Import Is Very Slow

**Symptoms**:
- Import takes hours for small datasets
- Progress bar barely moves

**Solutions**:

1. **Disable validation during import**:
   ```bash
   python historical_cli.py import -d data/downloads --no-validate --no-report
   ```

2. **Validate separately after import**:
   ```bash
   python historical_cli.py validate
   ```

3. **Check system resources**:
   ```bash
   top
   iostat
   ```

4. **Import in smaller batches**:
   ```bash
   python historical_cli.py import -f data/downloads/file1.csv
   python historical_cli.py import -f data/downloads/file2.csv
   ```

5. **Optimize database**:
   ```bash
   sqlite3 data/btc_options.db "VACUUM;"
   ```

## Validation Issues

### Problem: Validation Reports Many Issues

**Symptoms**:
- Quality score below 70
- Many "missing data" warnings
- Numerous anomaly detections

**Solutions**:

1. **Get detailed report**:
   ```bash
   python historical_cli.py validate --detailed
   ```

2. **Check specific issues**:
   - Review the detailed issue list
   - Determine if issues are acceptable

3. **Validate specific date range**:
   ```bash
   python historical_cli.py validate -s 2024-03-01 -e 2024-03-31 --detailed
   ```

4. **Re-download problematic data**:
   ```bash
   python historical_cli.py download -e 2024-03-29 --force
   python historical_cli.py import -d data/downloads
   ```

5. **Filter out problematic records during export**:
   ```bash
   python historical_cli.py export -s 2024-03-01 -e 2024-03-31 -o clean_data.csv
   ```

### Problem: False Positive Anomalies

**Symptoms**:
- Valid data flagged as anomalous
- Reasonable price movements flagged as extreme

**Solutions**:

1. **Review validation thresholds**:
   - Check `config/historical_data_config.py`
   - Adjust `max_price_change_pct` if needed

2. **Manually review flagged data**:
   ```bash
   python historical_cli.py validate --detailed
   ```

3. **Compare with source data**:
   - Check original CSV files
   - Verify against CryptoDataDownload

4. **Use data despite warnings**:
   - If anomalies are acceptable, proceed with backtest
   - Document known issues

## Performance Issues

### Problem: Queries Are Slow

**Symptoms**:
- Long wait times for data queries
- API timeouts
- CLI commands hang

**Solutions**:

1. **Check database indexes**:
   ```sql
   sqlite3 data/btc_options.db ".indexes"
   ```

2. **Rebuild indexes**:
   ```sql
   sqlite3 data/btc_options.db "REINDEX;"
   ```

3. **Optimize database**:
   ```bash
   sqlite3 data/btc_options.db "VACUUM; ANALYZE;"
   ```

4. **Use Parquet cache**:
   - Parquet files are 10-100x faster than database queries
   - Export frequently used data to Parquet

5. **Limit query scope**:
   ```bash
   # Instead of querying all data
   python historical_cli.py export -s 2024-03-01 -e 2024-03-31 -o data.csv
   
   # Query specific instruments
   python historical_cli.py export -s 2024-03-01 -e 2024-03-31 -i BTC-29MAR24-50000-C -o data.csv
   ```

### Problem: Exports Take Too Long

**Symptoms**:
- Export commands run for hours
- Large file generation is slow

**Solutions**:

1. **Use Parquet format**:
   ```bash
   # Parquet is much faster than CSV
   python historical_cli.py export -s 2024-03-01 -e 2024-03-31 -f parquet -o data.parquet
   ```

2. **Export in smaller chunks**:
   ```bash
   python historical_cli.py export -s 2024-03-01 -e 2024-03-15 -o part1.csv
   python historical_cli.py export -s 2024-03-16 -e 2024-03-31 -o part2.csv
   ```

3. **Export specific instruments**:
   ```bash
   python historical_cli.py export -s 2024-03-01 -e 2024-03-31 -i BTC-29MAR24-50000-C -o data.csv
   ```

4. **Use compression**:
   ```bash
   python historical_cli.py export -s 2024-03-01 -e 2024-03-31 -f parquet -o data.parquet --compress
   ```

## Storage Issues

### Problem: Running Out of Disk Space

**Symptoms**:
- "No space left on device" errors
- Import fails
- Database write errors

**Solutions**:

1. **Check current usage**:
   ```bash
   python historical_cli.py stats
   df -h
   ```

2. **Clear cache**:
   ```bash
   python historical_cli.py clear --clear-cache
   ```

3. **Export and compress old data**:
   ```bash
   python historical_cli.py export -s 2024-01-01 -e 2024-02-29 -f parquet -o archive.parquet --compress
   ```

4. **Delete old data from database**:
   ```bash
   python historical_cli.py clear --clear-database
   # Then re-import only needed data
   ```

5. **Move data to larger disk**:
   ```bash
   mv data /path/to/larger/disk/
   ln -s /path/to/larger/disk/data data
   ```

### Problem: Cache Growing Too Large

**Symptoms**:
- Cache directory is very large
- Slow file operations

**Solutions**:

1. **Check cache size**:
   ```bash
   du -sh data/cache
   ```

2. **Clear old cache files**:
   ```bash
   python historical_cli.py clear --clear-cache
   ```

3. **Adjust cache size limit**:
   - Edit `config/historical_data_config.py`
   - Set `max_size_gb` to appropriate value

4. **Use Parquet compression**:
   - Parquet files with compression are much smaller
   - Re-export data with compression

## Database Issues

### Problem: Database Is Corrupted

**Symptoms**:
- "Database disk image is malformed" errors
- Queries return unexpected results
- Import fails with database errors

**Solutions**:

1. **Check database integrity**:
   ```bash
   sqlite3 data/btc_options.db "PRAGMA integrity_check;"
   ```

2. **Backup current database**:
   ```bash
   cp data/btc_options.db data/btc_options.db.backup
   ```

3. **Try to repair**:
   ```bash
   sqlite3 data/btc_options.db ".recover" | sqlite3 data/btc_options_recovered.db
   ```

4. **Rebuild from scratch**:
   ```bash
   # Export data first
   python historical_cli.py export -s 2024-01-01 -e 2024-12-31 -f parquet -o backup.parquet
   
   # Clear database
   python historical_cli.py clear --clear-database
   
   # Re-import
   python historical_cli.py import -d data/downloads
   ```

### Problem: Database Locked

**Symptoms**:
- "Database is locked" errors
- Operations timeout

**Solutions**:

1. **Check for other processes**:
   ```bash
   lsof data/btc_options.db
   ```

2. **Stop API server**:
   ```bash
   pkill -f "python.*run_api.py"
   ```

3. **Close database browsers**:
   - Close any SQLite browser applications
   - Close any Python scripts accessing the database

4. **Wait and retry**:
   - Sometimes locks are temporary
   - Wait 30 seconds and try again

5. **Use WAL mode** (Write-Ahead Logging):
   ```bash
   sqlite3 data/btc_options.db "PRAGMA journal_mode=WAL;"
   ```

## API Issues

### Problem: API Returns 500 Errors

**Symptoms**:
- Internal server errors
- API requests fail
- No response from server

**Solutions**:

1. **Check API logs**:
   ```bash
   tail -f logs/app.log
   ```

2. **Restart API server**:
   ```bash
   pkill -f "python.*run_api.py"
   python run_api.py
   ```

3. **Check database connection**:
   ```bash
   sqlite3 data/btc_options.db "SELECT COUNT(*) FROM historical_option_data;"
   ```

4. **Verify API is running**:
   ```bash
   curl http://localhost:8000/api/historical-data/stats
   ```

5. **Check for port conflicts**:
   ```bash
   lsof -i :8000
   ```

### Problem: API Requests Timeout

**Symptoms**:
- Requests take too long
- Connection timeout errors
- No response

**Solutions**:

1. **Increase timeout**:
   ```python
   import requests
   response = requests.get(url, timeout=300)  # 5 minutes
   ```

2. **Use smaller date ranges**:
   ```python
   # Instead of querying entire year
   response = requests.get(url, params={"start_date": "2024-03-01", "end_date": "2024-03-31"})
   ```

3. **Use pagination**:
   ```python
   response = requests.get(url, params={"limit": 1000, "offset": 0})
   ```

4. **Check server resources**:
   ```bash
   top
   free -h
   ```

## Data Quality Issues

### Problem: Missing Data for Backtest Period

**Symptoms**:
- Backtest fails with "insufficient data" error
- Coverage percentage is low
- Missing dates reported

**Solutions**:

1. **Check coverage**:
   ```bash
   python historical_cli.py stats -s 2024-03-01 -e 2024-03-31
   ```

2. **Download missing data**:
   ```bash
   python historical_cli.py download -e 2024-03-29
   python historical_cli.py import -d data/downloads
   ```

3. **Adjust backtest period**:
   - Use a period with better coverage
   - Check available dates first

4. **Use hybrid data source**:
   - Combine historical and live data
   - Fill gaps with live API data

### Problem: Inconsistent Data Between Instruments

**Symptoms**:
- Some instruments have data, others don't
- Uneven coverage across strikes
- Missing call or put data

**Solutions**:

1. **Check available instruments**:
   ```bash
   python historical_cli.py stats
   ```

2. **Download complete expiry date**:
   ```bash
   python historical_cli.py download -e 2024-03-29 --force
   python historical_cli.py import -d data/downloads
   ```

3. **Validate specific instruments**:
   ```bash
   python historical_cli.py validate -i BTC-29MAR24-50000-C --detailed
   ```

4. **Check source data**:
   - Visit CryptoDataDownload
   - Verify all instruments are available

## Backtest Integration Issues

### Problem: Backtest Not Using Historical Data

**Symptoms**:
- Backtest uses live API despite configuration
- Results don't match historical data
- "No historical data found" warnings

**Solutions**:

1. **Verify data source configuration**:
   ```python
   engine = BacktestEngine(data_source='historical')
   ```

2. **Check data availability**:
   ```bash
   python historical_cli.py stats -s 2024-03-01 -e 2024-03-31
   ```

3. **Explicitly provide historical data**:
   ```python
   backtest_data = manager.get_data_for_backtest(
       start_date=datetime(2024, 3, 1),
       end_date=datetime(2024, 3, 31)
   )
   engine = BacktestEngine(
       data_source='historical',
       historical_data=backtest_data
   )
   ```

4. **Check logs**:
   ```bash
   grep "data_source" logs/app.log
   ```

### Problem: Backtest Results Don't Match Expectations

**Symptoms**:
- Unexpected returns
- Strange price movements
- Inconsistent results

**Solutions**:

1. **Validate data quality**:
   ```bash
   python historical_cli.py validate -s 2024-03-01 -e 2024-03-31 --detailed
   ```

2. **Check for data gaps**:
   ```bash
   python historical_cli.py stats -s 2024-03-01 -e 2024-03-31
   ```

3. **Compare with source data**:
   - Export data and review manually
   - Compare with original CSV files

4. **Verify backtest configuration**:
   - Check strategy parameters
   - Verify date ranges
   - Review execution logic

## Common Error Messages

### "Failed to download: Connection timeout"

**Cause**: Network connectivity issues or server unavailable

**Solution**:
```bash
# Check connection
ping www.cryptodatadownload.com

# Retry with reduced concurrency
python historical_cli.py download -e 2024-03-29 -c 1
```

### "Database is locked"

**Cause**: Another process is using the database

**Solution**:
```bash
# Find processes using database
lsof data/btc_options.db

# Stop API server
pkill -f "python.*run_api.py"

# Retry operation
python historical_cli.py import -d data/downloads
```

### "Invalid CSV format"

**Cause**: Corrupted or incorrectly formatted CSV file

**Solution**:
```bash
# Re-download file
python historical_cli.py download -e 2024-03-29 --force

# Verify file
head -n 5 data/downloads/Deribit_BTCUSD_20240329_50000_C.csv
```

### "No space left on device"

**Cause**: Disk is full

**Solution**:
```bash
# Check space
df -h

# Clear cache
python historical_cli.py clear --clear-cache

# Export and compress old data
python historical_cli.py export -s 2024-01-01 -e 2024-02-29 -f parquet -o archive.parquet --compress
```

### "Permission denied"

**Cause**: Insufficient file permissions

**Solution**:
```bash
# Fix permissions
chmod 644 data/btc_options.db
chmod 755 data/downloads

# Run with appropriate user
sudo chown $USER:$USER data/btc_options.db
```

### "Validation failed: Quality score below threshold"

**Cause**: Data quality issues detected

**Solution**:
```bash
# Get detailed report
python historical_cli.py validate --detailed

# Review issues and decide if acceptable
# Re-download if needed
python historical_cli.py download -e 2024-03-29 --force
```

## Getting Help

If you're still experiencing issues:

1. **Check logs**:
   ```bash
   tail -n 100 logs/app.log
   ```

2. **Review documentation**:
   - User Guide: `HISTORICAL_DATA_GUIDE.md`
   - CLI Guide: `backend/HISTORICAL_CLI_GUIDE.md`
   - API Documentation: `backend/HISTORICAL_DATA_API.md`

3. **Check system requirements**:
   - Python 3.8+
   - SQLite 3
   - Sufficient disk space (1GB+ recommended)
   - Internet connection

4. **Verify installation**:
   ```bash
   python historical_cli.py --help
   pip list | grep -E "click|pandas|pyarrow"
   ```

5. **Test with minimal example**:
   ```bash
   # Try downloading just one expiry date
   python historical_cli.py download -e 2024-03-29
   python historical_cli.py import -d data/downloads
   python historical_cli.py stats
   ```

## Preventive Measures

To avoid common issues:

1. **Regular validation**:
   ```bash
   python historical_cli.py validate
   ```

2. **Monitor storage**:
   ```bash
   python historical_cli.py stats
   df -h
   ```

3. **Regular backups**:
   ```bash
   python historical_cli.py export -s 2024-01-01 -e 2024-12-31 -f parquet -o backup.parquet --compress
   ```

4. **Keep logs clean**:
   ```bash
   # Rotate logs periodically
   mv logs/app.log logs/app.log.old
   ```

5. **Update regularly**:
   ```bash
   git pull
   pip install -r requirements.txt --upgrade
   ```
