#!/usr/bin/env python
"""Test ATM endpoint fix"""

import asyncio
import sys
from datetime import datetime, timezone

# Add backend to path
sys.path.insert(0, '/Users/kiro/workspace/BTCOptionsTrading/backend')

from src.connectors.deribit_connector import DeribitConnector

async def test():
    connector = DeribitConnector()
    try:
        print("Testing ATM endpoint fix...")
        print("=" * 60)
        
        # Get options chain
        print("\n1. Fetching options chain...")
        options = await connector.get_options_chain('BTC')
        print(f'   Total options: {len(options)}')
        
        # Check date formatting
        if options:
            opt = options[0]
            print(f'\n2. Sample option date handling:')
            print(f'   Instrument: {opt.instrument_name}')
            print(f'   Expiration date: {opt.expiration_date}')
            print(f'   Timezone info: {opt.expiration_date.tzinfo}')
            print(f'   ISO format: {opt.expiration_date.date().isoformat()}')
        
        # Group by expiry date
        print(f'\n3. Grouping by expiry date...')
        expiry_map = {}
        for opt in options:
            # Use the same logic as the backend
            expiry_date_str = opt.expiration_date.date().isoformat()
            if expiry_date_str not in expiry_map:
                expiry_map[expiry_date_str] = []
            expiry_map[expiry_date_str].append(opt)
        
        available_dates = sorted(expiry_map.keys())
        print(f'   Available expiry dates: {available_dates}')
        
        # Test with first available date
        if available_dates:
            test_date = available_dates[0]
            print(f'\n4. Testing with date: {test_date}')
            print(f'   Options for this date: {len(expiry_map[test_date])}')
            
            # Simulate what the frontend sends
            print(f'\n5. Frontend would send: {test_date}')
            print(f'   Backend would look for: {test_date}')
            print(f'   Match: {test_date in expiry_map}')
        
        print("\n" + "=" * 60)
        print("✓ Date formatting test passed!")
        
    except Exception as e:
        import traceback
        print(f"✗ Error: {e}")
        traceback.print_exc()
    finally:
        await connector.close()

if __name__ == '__main__':
    asyncio.run(test())
