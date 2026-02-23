"""
测试 Order Book API
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_orderbook_api():
    """测试 Order Book API"""
    print("\n" + "="*80)
    print("Order Book API 测试")
    print("="*80 + "\n")
    
    # 测试 1: 获取摘要
    print("测试 1: 获取 Order Book 摘要")
    print("-" * 80)
    try:
        response = requests.get(f"{BASE_URL}/api/orderbook/summary")
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应数据:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        print()
    except Exception as e:
        print(f"✗ 错误: {e}\n")
        return
    
    # 测试 2: 手动收集 Order Book
    print("测试 2: 手动收集 Order Book")
    print("-" * 80)
    try:
        payload = {
            "underlying": "BTC",
            "num_strikes": 4
        }
        response = requests.post(
            f"{BASE_URL}/api/orderbook/collect",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应数据:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        print()
    except Exception as e:
        print(f"✗ 错误: {e}\n")
        return
    
    # 测试 3: 获取最新 Order Book
    print("测试 3: 获取最新 Order Book")
    print("-" * 80)
    try:
        response = requests.get(f"{BASE_URL}/api/orderbook/latest?limit=10")
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应数据:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        print()
    except Exception as e:
        print(f"✗ 错误: {e}\n")
        return
    
    # 测试 4: 获取历史数据
    print("测试 4: 获取历史 Order Book")
    print("-" * 80)
    try:
        response = requests.get(f"{BASE_URL}/api/orderbook/history?days=7")
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应数据:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        print()
    except Exception as e:
        print(f"✗ 错误: {e}\n")
        return
    
    # 测试 5: 配置定时收集
    print("测试 5: 配置定时 Order Book 收集")
    print("-" * 80)
    try:
        payload = {
            "underlying": "BTC",
            "num_strikes": 4,
            "hour": 5,
            "minute": 0
        }
        response = requests.post(
            f"{BASE_URL}/api/orderbook/schedule",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应数据:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        print()
    except Exception as e:
        print(f"✗ 错误: {e}\n")
        return
    
    # 测试 6: 查看定时配置
    print("测试 6: 查看定时 Order Book 收集配置")
    print("-" * 80)
    try:
        response = requests.get(f"{BASE_URL}/api/orderbook/schedule")
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应数据:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        print()
    except Exception as e:
        print(f"✗ 错误: {e}\n")
        return
    
    print("="*80)
    print("✓ 所有 API 测试完成")
    print("="*80 + "\n")

if __name__ == "__main__":
    test_orderbook_api()
