#!/usr/bin/env python3
"""
Test script for network toggle functionality.
Tests switching between testnet and mainnet.
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_network_toggle():
    """Test network toggle between testnet and mainnet"""
    print("=" * 60)
    print("Testing Network Toggle Functionality")
    print("=" * 60)
    
    # Test 1: Get initial Deribit config
    print("\n1. Getting initial Deribit configuration...")
    response = requests.get(f"{BASE_URL}/api/settings/deribit")
    if response.status_code == 200:
        config = response.json()
        print(f"   ✓ Current mode: {'Testnet' if config['test_mode'] else 'Mainnet'}")
        print(f"   ✓ Has credentials: {config['has_credentials']}")
    else:
        print(f"   ✗ Failed: {response.status_code}")
        return False
    
    # Test 2: Switch to testnet
    print("\n2. Switching to testnet...")
    test_config = {
        "api_key": "test_api_key_12345",
        "api_secret": "test_api_secret_67890",
        "test_mode": True
    }
    response = requests.post(
        f"{BASE_URL}/api/settings/deribit",
        json=test_config
    )
    if response.status_code == 200:
        result = response.json()
        print(f"   ✓ {result['message']}")
        print(f"   ✓ Test mode: {result['test_mode']}")
    else:
        print(f"   ✗ Failed: {response.status_code} - {response.text}")
        return False
    
    # Test 3: Verify testnet configuration
    print("\n3. Verifying testnet configuration...")
    response = requests.get(f"{BASE_URL}/api/settings/system-info")
    if response.status_code == 200:
        info = response.json()
        if info['deribit_mode'] == 'test':
            print(f"   ✓ Deribit mode: {info['deribit_mode']}")
            print(f"   ✓ Status: {info['deribit_status']}")
        else:
            print(f"   ✗ Expected 'test' mode, got '{info['deribit_mode']}'")
            return False
    else:
        print(f"   ✗ Failed: {response.status_code}")
        return False
    
    # Test 4: Switch to mainnet
    print("\n4. Switching to mainnet...")
    mainnet_config = {
        "api_key": "prod_api_key_12345",
        "api_secret": "prod_api_secret_67890",
        "test_mode": False
    }
    response = requests.post(
        f"{BASE_URL}/api/settings/deribit",
        json=mainnet_config
    )
    if response.status_code == 200:
        result = response.json()
        print(f"   ✓ {result['message']}")
        print(f"   ✓ Test mode: {result['test_mode']}")
    else:
        print(f"   ✗ Failed: {response.status_code} - {response.text}")
        return False
    
    # Test 5: Verify mainnet configuration
    print("\n5. Verifying mainnet configuration...")
    response = requests.get(f"{BASE_URL}/api/settings/system-info")
    if response.status_code == 200:
        info = response.json()
        if info['deribit_mode'] == 'production':
            print(f"   ✓ Deribit mode: {info['deribit_mode']}")
            print(f"   ✓ Status: {info['deribit_status']}")
        else:
            print(f"   ✗ Expected 'production' mode, got '{info['deribit_mode']}'")
            return False
    else:
        print(f"   ✗ Failed: {response.status_code}")
        return False
    
    # Test 6: Switch back to testnet
    print("\n6. Switching back to testnet...")
    response = requests.post(
        f"{BASE_URL}/api/settings/deribit",
        json=test_config
    )
    if response.status_code == 200:
        result = response.json()
        print(f"   ✓ {result['message']}")
        print(f"   ✓ Test mode: {result['test_mode']}")
    else:
        print(f"   ✗ Failed: {response.status_code}")
        return False
    
    return True


if __name__ == "__main__":
    try:
        success = test_network_toggle()
        print("\n" + "=" * 60)
        if success:
            print("✓ All network toggle tests passed!")
        else:
            print("✗ Some tests failed")
        print("=" * 60)
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Cannot connect to API server")
        print("  Make sure the API server is running on http://localhost:8000")
    except Exception as e:
        print(f"\n✗ Error: {e}")
