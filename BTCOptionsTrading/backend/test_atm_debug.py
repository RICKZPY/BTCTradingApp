#!/usr/bin/env python
"""Debug ATM endpoint issue"""

import asyncio
import sys
from datetime import datetime
from decimal import Decimal

# Add backend to path
sys.path.insert(0, '/Users/kiro/workspace/BTCOptionsTrading/backend')

from src.connectors.deribit_connector import DeribitConnector

async def test():
    connector = DeribitConnector()
    try:
        # Get options chain
        print("Fetching options chain...")
        options = await connector.get_options_chain('BTC')
        print(f'Total options: {len(options)}')
        
        # Group by expiry date
        expiry_map = {}
        for opt in options:
            expiry_str = opt.expiration_date.strftime('%Y-%m-%d')
            if expiry_str not in expiry_map:
                expiry_map[expiry_str] = {
                    'timestamp': int(opt.expiration_date.timestamp()),
                    'options': []
                }
            expiry_map[expiry_str]['options'].append(opt)
        
        print(f'Available expiry dates: {sorted(expiry_map.keys())}')
        
        # Check first option structure
        if options:
            opt = options[0]
            print(f'\nSample option: {opt.instrument_name}')
            print(f'  Strike: {opt.strike_price} (type: {type(opt.strike_price).__name__})')
            print(f'  Expiration: {opt.expiration_date} (type: {type(opt.expiration_date).__name__})')
            print(f'  Current price: {opt.current_price}')
        
        # Test ATM logic
        print("\n--- Testing ATM Logic ---")
        selected_expiry = sorted(expiry_map.keys())[0]
        print(f"Selected expiry: {selected_expiry}")
        
        selected_options = expiry_map[selected_expiry]['options']
        print(f"Options for this expiry: {len(selected_options)}")
        
        # Get underlying price
        underlying_price = await connector.get_index_price('BTC')
        print(f"Underlying price: {underlying_price}")
        
        # Extract strikes
        print("\nExtracting strikes...")
        available_strikes = []
        for opt in selected_options:
            strike = float(opt.strike_price)
            available_strikes.append(strike)
            if len(available_strikes) <= 5:
                print(f"  Strike: {strike} (type: {type(strike).__name__})")
        
        available_strikes = sorted(set(available_strikes))
        print(f"Total unique strikes: {len(available_strikes)}")
        print(f"Strike range: {available_strikes[0]} - {available_strikes[-1]}")
        
        # Find ATM
        atm_strike = min(available_strikes, key=lambda x: abs(x - underlying_price))
        print(f"ATM strike: {atm_strike}")
        
        # Get strike range
        num_strikes = 5
        interval = 1000
        min_strike = atm_strike - (num_strikes * interval)
        max_strike = atm_strike + (num_strikes * interval)
        print(f"Strike range: {min_strike} - {max_strike}")
        
        # Filter options
        print("\nFiltering options...")
        filtered_count = 0
        for option in selected_options:
            strike = float(option.strike_price)
            if min_strike <= strike <= max_strike:
                filtered_count += 1
        
        print(f"Filtered options: {filtered_count}")
        
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()
    finally:
        await connector.close()

if __name__ == '__main__':
    asyncio.run(test())
