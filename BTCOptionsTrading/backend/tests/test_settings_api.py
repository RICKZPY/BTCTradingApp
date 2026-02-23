"""
Test script for settings API endpoints.
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_get_system_info():
    """Test getting system information"""
    print("\n=== Testing System Info ===")
    response = requests.get(f"{BASE_URL}/api/settings/system-info")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_get_deribit_config():
    """Test getting Deribit configuration"""
    print("\n=== Testing Get Deribit Config ===")
    response = requests.get(f"{BASE_URL}/api/settings/deribit")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_update_deribit_config():
    """Test updating Deribit configuration"""
    print("\n=== Testing Update Deribit Config ===")
    config = {
        "api_key": "test_api_key_12345",
        "api_secret": "test_api_secret_67890",
        "test_mode": True
    }
    response = requests.post(f"{BASE_URL}/api/settings/deribit", json=config)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Verify the config was saved
    if response.status_code == 200:
        print("\n--- Verifying saved config ---")
        verify_response = requests.get(f"{BASE_URL}/api/settings/deribit")
        print(f"Verification: {json.dumps(verify_response.json(), indent=2)}")
    
    return response.status_code == 200

def test_get_trading_config():
    """Test getting trading configuration"""
    print("\n=== Testing Get Trading Config ===")
    response = requests.get(f"{BASE_URL}/api/settings/trading")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_update_trading_config():
    """Test updating trading configuration"""
    print("\n=== Testing Update Trading Config ===")
    config = {
        "risk_free_rate": 0.06,
        "default_initial_capital": 150000.0,
        "commission_rate": 0.0005
    }
    response = requests.post(f"{BASE_URL}/api/settings/trading", json=config)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Verify the config was saved
    if response.status_code == 200:
        print("\n--- Verifying saved config ---")
        verify_response = requests.get(f"{BASE_URL}/api/settings/trading")
        print(f"Verification: {json.dumps(verify_response.json(), indent=2)}")
    
    return response.status_code == 200

if __name__ == "__main__":
    print("=" * 60)
    print("Settings API Test Suite")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("System Info", test_get_system_info()))
    results.append(("Get Deribit Config", test_get_deribit_config()))
    results.append(("Update Deribit Config", test_update_deribit_config()))
    results.append(("Get Trading Config", test_get_trading_config()))
    results.append(("Update Trading Config", test_update_trading_config()))
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\nTotal: {passed}/{total} tests passed")
