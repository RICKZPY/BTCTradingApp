# Historical Data API Documentation

## Overview

The Historical Data API provides RESTful endpoints for managing historical Bitcoin options data. This API allows you to programmatically download, import, validate, export, and query historical options data.

## Base URL

```
http://localhost:8000/api/historical-data
```

## Authentication

Currently, the API does not require authentication. In production, implement appropriate authentication mechanisms.

## Endpoints

### 1. Import Historical Data

Import historical options data from CryptoDataDownload.

**Endpoint**: `POST /api/historical-data/import`

**Request Body**:
```json
{
  "expiry_dates": ["2024-03-29", "2024-04-26"],
  "validate": true,
  "generate_report": true
}
```

**Parameters**:
- `expiry_dates` (array of strings, required): List of expiry dates in YYYY-MM-DD format
- `validate` (boolean, optional): Whether to validate data quality (default: true)
- `generate_report` (boolean, optional): Whether to generate quality report (default: true)

**Response** (200 OK):
```json
{
  "success": true,
  "files_processed": 30,
  "records_imported": 25000,
  "records_failed": 0,
  "duration_seconds": 45.2,
  "quality_report": {
    "quality_score": 95.5,
    "total_records": 25000,
    "missing_records": 100,
    "anomaly_records": 50,
    "coverage_percentage": 99.4,
    "issues": [
      {
        "severity": "warning",
        "type": "missing_data",
        "description": "Missing data for 2024-03-15",
        "count": 50
      }
    ]
  }
}
```

**Error Response** (400 Bad Request):
```json
{
  "success": false,
  "error": "Invalid expiry date format",
  "details": "Date must be in YYYY-MM-DD format"
}
```

**Error Response** (500 Internal Server Error):
```json
{
  "success": false,
  "error": "Import failed",
  "details": "Network error: Connection timeout"
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/historical-data/import \
  -H "Content-Type: application/json" \
  -d '{
    "expiry_dates": ["2024-03-29"],
    "validate": true
  }'
```

---

### 2. List Available Data

List available historical data files from CryptoDataDownload.

**Endpoint**: `GET /api/historical-data/available`

**Query Parameters**:
- `symbol` (string, optional): Underlying symbol (default: BTC)

**Response** (200 OK):
```json
{
  "symbol": "BTC",
  "files": [
    {
      "expiry_date": "2024-03-29",
      "url": "https://www.cryptodatadownload.com/data/deribit/Deribit_BTCUSD_20240329.zip",
      "filename": "Deribit_BTCUSD_20240329.zip",
      "estimated_size": 5242880,
      "last_modified": "2024-03-30T00:00:00Z"
    },
    {
      "expiry_date": "2024-04-26",
      "url": "https://www.cryptodatadownload.com/data/deribit/Deribit_BTCUSD_20240426.zip",
      "filename": "Deribit_BTCUSD_20240426.zip",
      "estimated_size": 6291456,
      "last_modified": "2024-04-27T00:00:00Z"
    }
  ],
  "total_files": 2
}
```

**Example**:
```bash
curl http://localhost:8000/api/historical-data/available?symbol=BTC
```

---

### 3. Get Coverage Statistics

Get statistics about data coverage for a specific date range.

**Endpoint**: `GET /api/historical-data/coverage`

**Query Parameters**:
- `start_date` (string, required): Start date in YYYY-MM-DD format
- `end_date` (string, required): End date in YYYY-MM-DD format
- `symbol` (string, optional): Underlying symbol (default: BTC)

**Response** (200 OK):
```json
{
  "symbol": "BTC",
  "start_date": "2024-03-01",
  "end_date": "2024-03-31",
  "total_records": 25000,
  "coverage_percentage": 95.5,
  "available_instruments": 150,
  "available_dates": [
    "2024-03-01",
    "2024-03-02",
    "2024-03-03"
  ],
  "missing_dates": [
    "2024-03-15",
    "2024-03-16"
  ],
  "expiry_dates": [
    "2024-03-29",
    "2024-04-26"
  ]
}
```

**Error Response** (400 Bad Request):
```json
{
  "error": "Invalid date range",
  "details": "start_date must be before end_date"
}
```

**Example**:
```bash
curl "http://localhost:8000/api/historical-data/coverage?start_date=2024-03-01&end_date=2024-03-31"
```

---

### 4. Export Data

Export historical data in various formats.

**Endpoint**: `POST /api/historical-data/export`

**Request Body**:
```json
{
  "start_date": "2024-03-01",
  "end_date": "2024-03-31",
  "format": "csv",
  "instruments": ["BTC-29MAR24-50000-C", "BTC-29MAR24-51000-C"],
  "compress": true
}
```

**Parameters**:
- `start_date` (string, required): Start date in YYYY-MM-DD format
- `end_date` (string, required): End date in YYYY-MM-DD format
- `format` (string, optional): Export format - "csv", "json", or "parquet" (default: "csv")
- `instruments` (array of strings, optional): List of instrument names to export (default: all)
- `compress` (boolean, optional): Whether to compress the output file (default: false)

**Response** (200 OK):
```json
{
  "success": true,
  "file_path": "data/exports/historical_data_20240315_120000.csv.gz",
  "records_exported": 5000,
  "file_size_bytes": 524288,
  "format": "csv",
  "compressed": true
}
```

**Error Response** (400 Bad Request):
```json
{
  "success": false,
  "error": "Invalid format",
  "details": "Format must be one of: csv, json, parquet"
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/historical-data/export \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-03-01",
    "end_date": "2024-03-31",
    "format": "parquet",
    "compress": true
  }'
```

---

### 5. Query Historical Data

Query historical options data for specific instruments and date range.

**Endpoint**: `GET /api/historical-data/query`

**Query Parameters**:
- `instrument_name` (string, required): Instrument name (e.g., BTC-29MAR24-50000-C)
- `start_date` (string, required): Start date in YYYY-MM-DD format
- `end_date` (string, required): End date in YYYY-MM-DD format
- `limit` (integer, optional): Maximum number of records to return (default: 1000)
- `offset` (integer, optional): Number of records to skip (default: 0)

**Response** (200 OK):
```json
{
  "instrument_name": "BTC-29MAR24-50000-C",
  "start_date": "2024-03-01",
  "end_date": "2024-03-31",
  "total_records": 720,
  "returned_records": 100,
  "data": [
    {
      "timestamp": "2024-03-01T00:00:00Z",
      "open_price": 1250.50,
      "high_price": 1275.00,
      "low_price": 1240.00,
      "close_price": 1260.75,
      "volume": 15.5,
      "strike_price": 50000,
      "expiry_date": "2024-03-29",
      "option_type": "call",
      "underlying_symbol": "BTC"
    }
  ]
}
```

**Example**:
```bash
curl "http://localhost:8000/api/historical-data/query?instrument_name=BTC-29MAR24-50000-C&start_date=2024-03-01&end_date=2024-03-31&limit=100"
```

---

### 6. Validate Data

Validate the quality of stored historical data.

**Endpoint**: `POST /api/historical-data/validate`

**Request Body**:
```json
{
  "start_date": "2024-03-01",
  "end_date": "2024-03-31",
  "instrument_name": "BTC-29MAR24-50000-C",
  "detailed": true
}
```

**Parameters**:
- `start_date` (string, optional): Start date in YYYY-MM-DD format
- `end_date` (string, optional): End date in YYYY-MM-DD format
- `instrument_name` (string, optional): Specific instrument to validate
- `detailed` (boolean, optional): Include detailed issue descriptions (default: false)

**Response** (200 OK):
```json
{
  "is_valid": true,
  "quality_score": 95.5,
  "total_records": 25000,
  "missing_records": 100,
  "anomaly_records": 50,
  "coverage_percentage": 99.4,
  "issues": [
    {
      "severity": "warning",
      "type": "missing_data",
      "description": "Missing data for 2024-03-15",
      "count": 50,
      "affected_instruments": ["BTC-29MAR24-50000-C"]
    },
    {
      "severity": "error",
      "type": "price_anomaly",
      "description": "Negative prices detected",
      "count": 5,
      "affected_records": [
        {
          "instrument": "BTC-29MAR24-51000-C",
          "timestamp": "2024-03-10T12:00:00Z",
          "issue": "Negative close price: -10.5"
        }
      ]
    }
  ]
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/historical-data/validate \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-03-01",
    "end_date": "2024-03-31",
    "detailed": true
  }'
```

---

### 7. Get Statistics

Get general statistics about stored historical data.

**Endpoint**: `GET /api/historical-data/stats`

**Query Parameters**:
- `start_date` (string, optional): Start date in YYYY-MM-DD format
- `end_date` (string, optional): End date in YYYY-MM-DD format
- `symbol` (string, optional): Underlying symbol (default: BTC)

**Response** (200 OK):
```json
{
  "symbol": "BTC",
  "total_records": 50000,
  "total_instruments": 300,
  "date_range": {
    "earliest": "2024-01-01",
    "latest": "2024-03-31"
  },
  "expiry_dates": [
    "2024-03-29",
    "2024-04-26",
    "2024-05-31"
  ],
  "storage": {
    "database_size_bytes": 52428800,
    "cache_size_bytes": 104857600,
    "total_size_bytes": 157286400
  },
  "coverage": {
    "percentage": 95.5,
    "missing_dates": 5,
    "total_dates": 90
  }
}
```

**Example**:
```bash
curl "http://localhost:8000/api/historical-data/stats?symbol=BTC"
```

---

### 8. Clear Cache

Clear cached historical data.

**Endpoint**: `DELETE /api/historical-data/cache`

**Query Parameters**:
- `before_date` (string, optional): Clear data before this date in YYYY-MM-DD format (default: clear all)

**Response** (200 OK):
```json
{
  "success": true,
  "records_deleted": 10000,
  "cache_cleared": true,
  "space_freed_bytes": 52428800
}
```

**Example**:
```bash
# Clear all cache
curl -X DELETE http://localhost:8000/api/historical-data/cache

# Clear cache before specific date
curl -X DELETE "http://localhost:8000/api/historical-data/cache?before_date=2024-01-01"
```

---

### 9. Get Available Instruments

Get list of available instruments in the database.

**Endpoint**: `GET /api/historical-data/instruments`

**Query Parameters**:
- `expiry_date` (string, optional): Filter by expiry date in YYYY-MM-DD format
- `option_type` (string, optional): Filter by option type - "call" or "put"
- `min_strike` (number, optional): Minimum strike price
- `max_strike` (number, optional): Maximum strike price

**Response** (200 OK):
```json
{
  "instruments": [
    {
      "instrument_name": "BTC-29MAR24-50000-C",
      "strike_price": 50000,
      "expiry_date": "2024-03-29",
      "option_type": "call",
      "underlying_symbol": "BTC",
      "record_count": 720,
      "date_range": {
        "earliest": "2024-01-01",
        "latest": "2024-03-29"
      }
    }
  ],
  "total_instruments": 150
}
```

**Example**:
```bash
curl "http://localhost:8000/api/historical-data/instruments?expiry_date=2024-03-29&option_type=call"
```

---

## Error Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid parameters |
| 404 | Not Found - Resource not found |
| 500 | Internal Server Error - Server error |
| 503 | Service Unavailable - External service unavailable |

## Rate Limiting

Currently, no rate limiting is implemented. In production, consider implementing rate limiting to prevent abuse.

## Data Formats

### Date Format

All dates must be in ISO 8601 format: `YYYY-MM-DD`

Examples:
- `2024-03-29`
- `2024-04-26`

### Timestamp Format

All timestamps are in ISO 8601 format with UTC timezone: `YYYY-MM-DDTHH:MM:SSZ`

Examples:
- `2024-03-29T12:00:00Z`
- `2024-04-26T15:30:45Z`

### Instrument Name Format

Instrument names follow the format: `{SYMBOL}-{EXPIRY}-{STRIKE}-{TYPE}`

Examples:
- `BTC-29MAR24-50000-C` (Call option)
- `BTC-29MAR24-50000-P` (Put option)

Where:
- `SYMBOL`: Underlying asset (BTC, ETH)
- `EXPIRY`: Expiry date in DDMMMYY format
- `STRIKE`: Strike price
- `TYPE`: C for Call, P for Put

## Usage Examples

### Python

```python
import requests
from datetime import datetime

BASE_URL = "http://localhost:8000/api/historical-data"

# Import data
response = requests.post(
    f"{BASE_URL}/import",
    json={
        "expiry_dates": ["2024-03-29"],
        "validate": True
    }
)
result = response.json()
print(f"Imported {result['records_imported']} records")

# Get coverage stats
response = requests.get(
    f"{BASE_URL}/coverage",
    params={
        "start_date": "2024-03-01",
        "end_date": "2024-03-31"
    }
)
stats = response.json()
print(f"Coverage: {stats['coverage_percentage']}%")

# Query data
response = requests.get(
    f"{BASE_URL}/query",
    params={
        "instrument_name": "BTC-29MAR24-50000-C",
        "start_date": "2024-03-01",
        "end_date": "2024-03-31",
        "limit": 100
    }
)
data = response.json()
print(f"Retrieved {len(data['data'])} records")

# Export data
response = requests.post(
    f"{BASE_URL}/export",
    json={
        "start_date": "2024-03-01",
        "end_date": "2024-03-31",
        "format": "parquet",
        "compress": True
    }
)
export_result = response.json()
print(f"Exported to {export_result['file_path']}")
```

### JavaScript/TypeScript

```typescript
const BASE_URL = 'http://localhost:8000/api/historical-data';

// Import data
const importData = async () => {
  const response = await fetch(`${BASE_URL}/import`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      expiry_dates: ['2024-03-29'],
      validate: true
    })
  });
  const result = await response.json();
  console.log(`Imported ${result.records_imported} records`);
};

// Get coverage stats
const getCoverage = async () => {
  const params = new URLSearchParams({
    start_date: '2024-03-01',
    end_date: '2024-03-31'
  });
  const response = await fetch(`${BASE_URL}/coverage?${params}`);
  const stats = await response.json();
  console.log(`Coverage: ${stats.coverage_percentage}%`);
};

// Query data
const queryData = async () => {
  const params = new URLSearchParams({
    instrument_name: 'BTC-29MAR24-50000-C',
    start_date: '2024-03-01',
    end_date: '2024-03-31',
    limit: '100'
  });
  const response = await fetch(`${BASE_URL}/query?${params}`);
  const data = await response.json();
  console.log(`Retrieved ${data.data.length} records`);
};

// Export data
const exportData = async () => {
  const response = await fetch(`${BASE_URL}/export`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      start_date: '2024-03-01',
      end_date: '2024-03-31',
      format: 'parquet',
      compress: true
    })
  });
  const result = await response.json();
  console.log(`Exported to ${result.file_path}`);
};
```

### cURL

```bash
# Import data
curl -X POST http://localhost:8000/api/historical-data/import \
  -H "Content-Type: application/json" \
  -d '{"expiry_dates": ["2024-03-29"], "validate": true}'

# Get coverage stats
curl "http://localhost:8000/api/historical-data/coverage?start_date=2024-03-01&end_date=2024-03-31"

# Query data
curl "http://localhost:8000/api/historical-data/query?instrument_name=BTC-29MAR24-50000-C&start_date=2024-03-01&end_date=2024-03-31&limit=100"

# Export data
curl -X POST http://localhost:8000/api/historical-data/export \
  -H "Content-Type: application/json" \
  -d '{"start_date": "2024-03-01", "end_date": "2024-03-31", "format": "parquet", "compress": true}'

# Get statistics
curl "http://localhost:8000/api/historical-data/stats?symbol=BTC"

# Clear cache
curl -X DELETE "http://localhost:8000/api/historical-data/cache?before_date=2024-01-01"
```

## Best Practices

1. **Always validate data after import**
   ```python
   # Import with validation
   response = requests.post(f"{BASE_URL}/import", json={"expiry_dates": ["2024-03-29"], "validate": True})
   ```

2. **Check coverage before backtesting**
   ```python
   # Check coverage first
   coverage = requests.get(f"{BASE_URL}/coverage", params={"start_date": "2024-03-01", "end_date": "2024-03-31"}).json()
   if coverage['coverage_percentage'] < 90:
       print("Warning: Low data coverage")
   ```

3. **Use Parquet format for large exports**
   ```python
   # Parquet is 10-100x faster than CSV
   response = requests.post(f"{BASE_URL}/export", json={"start_date": "2024-03-01", "end_date": "2024-03-31", "format": "parquet"})
   ```

4. **Handle errors gracefully**
   ```python
   try:
       response = requests.post(f"{BASE_URL}/import", json={"expiry_dates": ["2024-03-29"]})
       response.raise_for_status()
       result = response.json()
   except requests.exceptions.RequestException as e:
       print(f"Error: {e}")
   ```

5. **Use pagination for large queries**
   ```python
   # Query in batches
   offset = 0
   limit = 1000
   while True:
       response = requests.get(f"{BASE_URL}/query", params={"instrument_name": "BTC-29MAR24-50000-C", "start_date": "2024-03-01", "end_date": "2024-03-31", "limit": limit, "offset": offset})
       data = response.json()
       if not data['data']:
           break
       # Process data
       offset += limit
   ```

## Support

For issues or questions:
- Check the main user guide: `HISTORICAL_DATA_GUIDE.md`
- Review the CLI documentation: `backend/HISTORICAL_CLI_GUIDE.md`
- Consult the design document: `.kiro/specs/historical-data-integration/design.md`

## Changelog

### Version 1.0.0
- Initial API release
- All core endpoints implemented
- Support for CSV, JSON, and Parquet exports
- Comprehensive validation and quality reporting
