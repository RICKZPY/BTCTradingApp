#!/usr/bin/env python
"""
Test ATM endpoint with actual API calls
"""

import asyncio
import sys
import httpx
from datetime import datetime

# Add backend to path
sys.path.insert(0, '/Users/kiro/workspace/BTCOptionsTrading/backend')

async def test_atm_endpoint():
    """Test the ATM endpoint"""
    
    print("=" * 70)
    print("Testing ATM Endpoint Fix")
    print("=" * 70)
    
    # First, get available dates from the options chain endpoint
    print("\n1. Getting available expiry dates from /api/data/options-chain...")
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.get(
                "http://localhost:8000/api/data/options-chain",
                params={"currency": "BTC"}
            )
            response.raise_for_status()
            options_data = response.json()
            
            # Extract unique expiry dates
            expiry_dates = set()
            for option in options_data:
                if 'expiration_timestamp' in option:
                    date = datetime.fromtimestamp(option['expiration_timestamp']).date().isoformat()
                    expiry_dates.add(date)
            
            available_dates = sorted(list(expiry_dates))
            print(f"   ✓ Found {len(available_dates)} available expiry dates")
            print(f"   Available dates: {available_dates[:5]}...")  # Show first 5
            
            if not available_dates:
                print("   ✗ No expiry dates found!")
                return
            
            # Test ATM endpoint without expiry_date
            print("\n2. Testing /api/options/atm without expiry_date parameter...")
            response = await client.get(
                "http://localhost:8000/api/options/atm",
                params={"currency": "BTC", "num_strikes": 5}
            )
            response.raise_for_status()
            atm_data = response.json()
            print(f"   ✓ Success!")
            print(f"   Expiration date: {atm_data['expiration_date']}")
            print(f"   ATM strike: {atm_data['atm_strike']}")
            print(f"   Call options: {len(atm_data['call_options'])}")
            print(f"   Put options: {len(atm_data['put_options'])}")
            
            # Test ATM endpoint with specific expiry_date
            test_date = available_dates[0]
            print(f"\n3. Testing /api/options/atm with expiry_date={test_date}...")
            response = await client.get(
                "http://localhost:8000/api/options/atm",
                params={
                    "currency": "BTC",
                    "expiry_date": test_date,
                    "num_strikes": 5
                }
            )
            
            if response.status_code == 200:
                atm_data = response.json()
                print(f"   ✓ Success!")
                print(f"   Expiration date: {atm_data['expiration_date']}")
                print(f"   ATM strike: {atm_data['atm_strike']}")
                print(f"   Call options: {len(atm_data['call_options'])}")
                print(f"   Put options: {len(atm_data['put_options'])}")
                
                # Verify data
                if len(atm_data['call_options']) > 0 and len(atm_data['put_options']) > 0:
                    print(f"   ✓ Both call and put options returned")
                else:
                    print(f"   ⚠ Warning: Missing call or put options")
            else:
                print(f"   ✗ Error: {response.status_code}")
                print(f"   Response: {response.text}")
            
            # Test with another date
            if len(available_dates) > 1:
                test_date2 = available_dates[1]
                print(f"\n4. Testing with another date: {test_date2}...")
                response = await client.get(
                    "http://localhost:8000/api/options/atm",
                    params={
                        "currency": "BTC",
                        "expiry_date": test_date2,
                        "num_strikes": 5
                    }
                )
                
                if response.status_code == 200:
                    atm_data = response.json()
                    print(f"   ✓ Success!")
                    print(f"   Expiration date: {atm_data['expiration_date']}")
                    print(f"   Options: {len(atm_data['call_options']) + len(atm_data['put_options'])}")
                else:
                    print(f"   ✗ Error: {response.status_code}")
            
            print("\n" + "=" * 70)
            print("✓ ATM endpoint test completed successfully!")
            print("=" * 70)
            
        except httpx.ConnectError:
            print("   ✗ Could not connect to API server")
            print("   Make sure the API is running on http://localhost:8000")
        except Exception as e:
            print(f"   ✗ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_atm_endpoint())
