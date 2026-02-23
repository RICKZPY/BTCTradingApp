#!/usr/bin/env python
"""
Download and process CSV files from the server's daily_snapshots directory
"""

import os
import csv
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Server data directory
SERVER_DATA_DIR = "/root/BTCTradingApp/BTCOptionsTrading/backend/data/daily_snapshots"
LOCAL_DATA_DIR = "./downloaded_csv_data"

def ensure_local_dir():
    """Create local directory if it doesn't exist"""
    Path(LOCAL_DATA_DIR).mkdir(parents=True, exist_ok=True)

def list_csv_files():
    """List all CSV files in the server directory"""
    if not os.path.exists(SERVER_DATA_DIR):
        print(f"Server directory not found: {SERVER_DATA_DIR}")
        return []
    
    csv_files = []
    for file in os.listdir(SERVER_DATA_DIR):
        if file.endswith('.csv'):
            csv_files.append(file)
    
    return sorted(csv_files)

def process_csv_file(csv_path):
    """Process a single CSV file and extract contract data"""
    data = []
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
        return data
    except Exception as e:
        print(f"Error processing {csv_path}: {e}")
        return []

def organize_by_contract(all_data):
    """Organize data by contract name"""
    contracts = defaultdict(list)
    
    for row in all_data:
        instrument_name = row.get('instrument_name', 'unknown')
        contracts[instrument_name].append(row)
    
    return contracts

def download_and_organize():
    """Download CSV files and organize them"""
    ensure_local_dir()
    
    print("=" * 70)
    print("CSV Data Download and Organization")
    print("=" * 70)
    
    # List CSV files
    csv_files = list_csv_files()
    print(f"\nFound {len(csv_files)} CSV files in {SERVER_DATA_DIR}")
    
    if not csv_files:
        print("No CSV files found!")
        return
    
    # Show first few files
    print("\nFirst 10 files:")
    for i, file in enumerate(csv_files[:10], 1):
        file_path = os.path.join(SERVER_DATA_DIR, file)
        file_size = os.path.getsize(file_path) / 1024  # KB
        print(f"  {i}. {file} ({file_size:.1f} KB)")
    
    if len(csv_files) > 10:
        print(f"  ... and {len(csv_files) - 10} more files")
    
    # Process all CSV files
    print("\nProcessing CSV files...")
    all_data = []
    for i, csv_file in enumerate(csv_files, 1):
        csv_path = os.path.join(SERVER_DATA_DIR, csv_file)
        data = process_csv_file(csv_path)
        all_data.extend(data)
        
        if i % 10 == 0:
            print(f"  Processed {i}/{len(csv_files)} files ({len(all_data)} records)")
    
    print(f"\nTotal records processed: {len(all_data)}")
    
    # Organize by contract
    print("\nOrganizing data by contract...")
    contracts = organize_by_contract(all_data)
    
    print(f"Found {len(contracts)} unique contracts:")
    for contract_name in sorted(contracts.keys())[:20]:
        count = len(contracts[contract_name])
        print(f"  - {contract_name}: {count} records")
    
    if len(contracts) > 20:
        print(f"  ... and {len(contracts) - 20} more contracts")
    
    # Save organized data
    print("\nSaving organized data...")
    
    # Save summary
    summary = {
        'total_files': len(csv_files),
        'total_records': len(all_data),
        'total_contracts': len(contracts),
        'contracts': {
            name: {
                'record_count': len(data),
                'date_range': {
                    'start': min(row.get('timestamp', '') for row in data),
                    'end': max(row.get('timestamp', '') for row in data)
                }
            }
            for name, data in contracts.items()
        },
        'download_date': datetime.now().isoformat()
    }
    
    summary_path = os.path.join(LOCAL_DATA_DIR, 'summary.json')
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"Summary saved to: {summary_path}")
    
    # Save contract data
    for contract_name, data in contracts.items():
        # Sanitize filename
        safe_name = contract_name.replace('/', '_').replace('\\', '_')
        contract_file = os.path.join(LOCAL_DATA_DIR, f"{safe_name}.json")
        
        with open(contract_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Contract data saved to: {LOCAL_DATA_DIR}/")
    
    print("\n" + "=" * 70)
    print("Download and organization complete!")
    print("=" * 70)
    
    return summary, contracts

if __name__ == '__main__':
    download_and_organize()
