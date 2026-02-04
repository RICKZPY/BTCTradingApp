#!/usr/bin/env python3
"""
Test backtest API endpoint using requests
"""
import requests
import json
import time


def test_backtest_endpoint():
    """Test the backtest API endpoint"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Backtest API Endpoint")
    print("=" * 50)
    
    # Test 1: Check if API is running
    print("1. Checking if API server is running...")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("   ✅ API server is running")
        else:
            print(f"   ❌ API server returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Cannot connect to API server: {e}")
        print("   💡 Please start the API server first:")
        print("      cd backend && python api/main.py")
        return False
    
    # Test 2: Check backtest status
    print("2. Checking backtest engine status...")
    try:
        response = requests.get(f"{base_url}/api/v1/backtesting/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Status endpoint working: {data.get('message', 'OK')}")
            if data.get('data', {}).get('available', False):
                print("   ✅ Backtest engine is available")
            else:
                print("   ⚠️  Backtest engine not available")
        else:
            print(f"   ❌ Status endpoint returned {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error checking status: {e}")
    
    # Test 3: Run a simple backtest
    print("3. Running a simple backtest...")
    backtest_request = {
        "symbol": "BTCUSDT",
        "days": 7,
        "initial_capital": 10000.0,
        "max_position_size": 0.1,
        "strategy_name": "Test Strategy"
    }
    
    try:
        print(f"   📤 Sending request: {json.dumps(backtest_request, indent=2)}")
        response = requests.post(
            f"{base_url}/api/v1/backtesting/run",
            json=backtest_request,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Backtest completed successfully!")
            
            if 'data' in data and data['data']:
                result_data = data['data']
                print(f"   📊 Backtest ID: {result_data.get('backtest_id', 'N/A')}")
                print(f"   📈 Strategy: {result_data.get('strategy_name', 'N/A')}")
                
                metrics = result_data.get('performance_metrics', {})
                print(f"   💰 Total Return: {metrics.get('total_return', 0):.2%}")
                print(f"   📊 Total Trades: {metrics.get('total_trades', 0)}")
                print(f"   🎯 Win Rate: {metrics.get('win_rate', 0):.1%}")
                print(f"   📉 Max Drawdown: {metrics.get('max_drawdown', 0):.2%}")
                print(f"   📅 Duration: {metrics.get('duration_days', 0)} days")
                
                print(f"   📈 Equity Curve Points: {len(result_data.get('equity_curve', []))}")
                print(f"   📊 Data Points Used: {result_data.get('data_points', 0)}")
            
        elif response.status_code == 503:
            print("   ⚠️  Backtest service unavailable (missing dependencies)")
            data = response.json()
            print(f"   📝 Details: {data.get('detail', 'Unknown error')}")
        else:
            print(f"   ❌ Backtest failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"   📝 Error: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"   📝 Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("   ⏰ Request timed out (backtest may be taking too long)")
    except Exception as e:
        print(f"   ❌ Error running backtest: {e}")
    
    # Test 4: Check API documentation
    print("4. Checking API documentation...")
    try:
        response = requests.get(f"{base_url}/docs", timeout=5)
        if response.status_code == 200:
            print("   ✅ API documentation is accessible at /docs")
        else:
            print(f"   ⚠️  API docs returned status {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error accessing docs: {e}")
    
    print("\n🎉 Backtest endpoint testing completed!")
    return True


if __name__ == "__main__":
    print("Starting backtest endpoint test...")
    print("Make sure the API server is running on http://localhost:8000")
    print()
    
    success = test_backtest_endpoint()
    
    if success:
        print("\n✅ Test completed! Check the results above.")
        print("\n📋 Next Steps:")
        print("   1. If backtest engine is available, test the frontend")
        print("   2. If not available, check dependencies")
        print("   3. Verify the frontend can call the API correctly")
    else:
        print("\n❌ Test failed. Please check the API server.")
    
    exit(0 if success else 1)