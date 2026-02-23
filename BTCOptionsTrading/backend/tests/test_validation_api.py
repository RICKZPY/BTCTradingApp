"""
测试策略验证API
"""

import requests
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/strategies"


def test_valid_strangle():
    """测试有效的宽跨式策略"""
    print("\n=== 测试有效的宽跨式策略 ===")
    
    expiry = (datetime.now() + timedelta(days=30)).isoformat()
    
    payload = {
        "name": "BTC宽跨式",
        "strategy_type": "strangle",
        "initial_capital": 100000.0,
        "legs": [
            {
                "option_contract": {
                    "instrument_name": "BTC-30000-C",
                    "underlying": "BTC",
                    "option_type": "call",
                    "strike_price": 30000.0,
                    "expiration_date": expiry
                },
                "action": "buy",
                "quantity": 1
            },
            {
                "option_contract": {
                    "instrument_name": "BTC-28000-P",
                    "underlying": "BTC",
                    "option_type": "put",
                    "strike_price": 28000.0,
                    "expiration_date": expiry
                },
                "action": "buy",
                "quantity": 1
            }
        ]
    }
    
    response = requests.post(f"{BASE_URL}/validate", json=payload)
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    
    result = response.json()
    assert result["is_valid"] == True, "策略应该是有效的"
    assert len(result["errors"]) == 0, "不应该有错误"
    print("✓ 测试通过")


def test_invalid_strangle_strike_order():
    """测试无效的宽跨式策略（执行价顺序错误）"""
    print("\n=== 测试无效的宽跨式策略（执行价顺序错误） ===")
    
    expiry = (datetime.now() + timedelta(days=30)).isoformat()
    
    payload = {
        "name": "错误的宽跨式",
        "strategy_type": "strangle",
        "initial_capital": 100000.0,
        "legs": [
            {
                "option_contract": {
                    "instrument_name": "BTC-28000-C",
                    "underlying": "BTC",
                    "option_type": "call",
                    "strike_price": 28000.0,
                    "expiration_date": expiry
                },
                "action": "buy",
                "quantity": 1
            },
            {
                "option_contract": {
                    "instrument_name": "BTC-30000-P",
                    "underlying": "BTC",
                    "option_type": "put",
                    "strike_price": 30000.0,
                    "expiration_date": expiry
                },
                "action": "buy",
                "quantity": 1
            }
        ]
    }
    
    response = requests.post(f"{BASE_URL}/validate", json=payload)
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    
    result = response.json()
    assert result["is_valid"] == False, "策略应该是无效的"
    assert len(result["errors"]) > 0, "应该有错误"
    print("✓ 测试通过")


def test_invalid_leg_count():
    """测试无效的腿数量"""
    print("\n=== 测试无效的腿数量 ===")
    
    expiry = (datetime.now() + timedelta(days=30)).isoformat()
    
    payload = {
        "name": "错误的跨式",
        "strategy_type": "straddle",
        "initial_capital": 100000.0,
        "legs": [
            {
                "option_contract": {
                    "instrument_name": "BTC-29000-C",
                    "underlying": "BTC",
                    "option_type": "call",
                    "strike_price": 29000.0,
                    "expiration_date": expiry
                },
                "action": "buy",
                "quantity": 1
            }
        ]
    }
    
    response = requests.post(f"{BASE_URL}/validate", json=payload)
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    
    result = response.json()
    assert result["is_valid"] == False, "策略应该是无效的"
    assert len(result["errors"]) > 0, "应该有错误"
    print("✓ 测试通过")


def test_expired_option():
    """测试过期的期权"""
    print("\n=== 测试过期的期权 ===")
    
    expiry = (datetime.now() - timedelta(days=1)).isoformat()
    
    payload = {
        "name": "过期期权",
        "strategy_type": "single_leg",
        "initial_capital": 100000.0,
        "legs": [
            {
                "option_contract": {
                    "instrument_name": "BTC-29000-C",
                    "underlying": "BTC",
                    "option_type": "call",
                    "strike_price": 29000.0,
                    "expiration_date": expiry
                },
                "action": "buy",
                "quantity": 1
            }
        ]
    }
    
    response = requests.post(f"{BASE_URL}/validate", json=payload)
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    
    result = response.json()
    assert result["is_valid"] == False, "策略应该是无效的"
    assert len(result["errors"]) > 0, "应该有错误"
    print("✓ 测试通过")


def test_valid_iron_condor():
    """测试有效的铁鹰策略"""
    print("\n=== 测试有效的铁鹰策略 ===")
    
    expiry = (datetime.now() + timedelta(days=30)).isoformat()
    
    payload = {
        "name": "BTC铁鹰",
        "strategy_type": "iron_condor",
        "initial_capital": 100000.0,
        "legs": [
            {
                "option_contract": {
                    "instrument_name": "BTC-27000-P",
                    "underlying": "BTC",
                    "option_type": "put",
                    "strike_price": 27000.0,
                    "expiration_date": expiry
                },
                "action": "buy",
                "quantity": 1
            },
            {
                "option_contract": {
                    "instrument_name": "BTC-28000-P",
                    "underlying": "BTC",
                    "option_type": "put",
                    "strike_price": 28000.0,
                    "expiration_date": expiry
                },
                "action": "sell",
                "quantity": 1
            },
            {
                "option_contract": {
                    "instrument_name": "BTC-30000-C",
                    "underlying": "BTC",
                    "option_type": "call",
                    "strike_price": 30000.0,
                    "expiration_date": expiry
                },
                "action": "sell",
                "quantity": 1
            },
            {
                "option_contract": {
                    "instrument_name": "BTC-31000-C",
                    "underlying": "BTC",
                    "option_type": "call",
                    "strike_price": 31000.0,
                    "expiration_date": expiry
                },
                "action": "buy",
                "quantity": 1
            }
        ]
    }
    
    response = requests.post(f"{BASE_URL}/validate", json=payload)
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    
    result = response.json()
    assert result["is_valid"] == True, "策略应该是有效的"
    print("✓ 测试通过")


if __name__ == "__main__":
    print("开始测试策略验证API...")
    print("确保后端服务正在运行: http://localhost:8000")
    
    try:
        test_valid_strangle()
        test_invalid_strangle_strike_order()
        test_invalid_leg_count()
        test_expired_option()
        test_valid_iron_condor()
        
        print("\n" + "="*50)
        print("所有测试通过！✓")
        print("="*50)
        
    except AssertionError as e:
        print(f"\n✗ 测试失败: {e}")
    except requests.exceptions.ConnectionError:
        print("\n✗ 无法连接到后端服务，请确保服务正在运行")
    except Exception as e:
        print(f"\n✗ 测试出错: {e}")
