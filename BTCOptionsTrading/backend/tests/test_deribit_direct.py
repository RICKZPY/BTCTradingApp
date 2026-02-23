#!/usr/bin/env python3
"""
直接测试 Deribit API（不依赖项目代码）
"""

import requests
import json

def test_deribit_api():
    """测试 Deribit API"""
    base_url = "https://test.deribit.com/api/v2"
    
    print("=" * 80)
    print("测试 Deribit API - 获取 BTC 期权数据")
    print("=" * 80)
    
    # 1. 获取期权合约列表
    print("\n步骤 1: 获取期权合约列表...")
    instruments_url = f"{base_url}/public/get_instruments"
    params = {
        "currency": "BTC",
        "kind": "option",
        "expired": "false"  # 使用字符串而不是布尔值
    }
    
    response = requests.get(instruments_url, params=params)
    data = response.json()
    
    if "result" not in data:
        print(f"错误: {data}")
        return
    
    instruments = data["result"]
    print(f"找到 {len(instruments)} 个期权合约")
    
    # 显示第一个合约的信息
    if instruments:
        first = instruments[0]
        print(f"\n第一个合约示例:")
        print(f"  instrument_name: {first.get('instrument_name')}")
        print(f"  strike: {first.get('strike')}")
        print(f"  option_type: {first.get('option_type')}")
        print(f"  expiration_timestamp: {first.get('expiration_timestamp')}")
        
        # 检查是否有市场数据
        print(f"\n检查 get_instruments 返回的字段:")
        print(f"  mark_price: {first.get('mark_price', 'N/A')}")
        print(f"  best_bid_price: {first.get('best_bid_price', 'N/A')}")
        print(f"  best_ask_price: {first.get('best_ask_price', 'N/A')}")
        print(f"  volume: {first.get('stats', {}).get('volume', 'N/A')}")
    
    # 2. 获取单个合约的 ticker 数据
    print("\n" + "=" * 80)
    print("步骤 2: 获取单个合约的 ticker 数据...")
    print("=" * 80)
    
    if instruments:
        instrument_name = instruments[0]["instrument_name"]
        ticker_url = f"{base_url}/public/ticker"
        ticker_params = {"instrument_name": instrument_name}
        
        ticker_response = requests.get(ticker_url, params=ticker_params)
        ticker_data = ticker_response.json()
        
        if "result" in ticker_data:
            ticker = ticker_data["result"]
            print(f"\n合约: {instrument_name}")
            print(f"  mark_price: {ticker.get('mark_price')}")
            print(f"  best_bid_price: {ticker.get('best_bid_price')}")
            print(f"  best_ask_price: {ticker.get('best_ask_price')}")
            print(f"  last_price: {ticker.get('last_price')}")
            print(f"  volume (24h): {ticker.get('stats', {}).get('volume')}")
            print(f"  open_interest: {ticker.get('open_interest')}")
            print(f"  mark_iv: {ticker.get('mark_iv')}")
            
            greeks = ticker.get('greeks', {})
            print(f"\nGreeks:")
            print(f"  delta: {greeks.get('delta')}")
            print(f"  gamma: {greeks.get('gamma')}")
            print(f"  vega: {greeks.get('vega')}")
            print(f"  theta: {greeks.get('theta')}")
    
    # 3. 测试多个合约
    print("\n" + "=" * 80)
    print("步骤 3: 测试前 5 个合约的市场数据...")
    print("=" * 80)
    
    for i, instrument in enumerate(instruments[:5]):
        instrument_name = instrument["instrument_name"]
        ticker_response = requests.get(
            f"{base_url}/public/ticker",
            params={"instrument_name": instrument_name}
        )
        ticker_data = ticker_response.json()
        
        if "result" in ticker_data:
            ticker = ticker_data["result"]
            print(f"\n#{i+1}: {instrument_name}")
            print(f"  Bid: ${ticker.get('best_bid_price', 0)}")
            print(f"  Ask: ${ticker.get('best_ask_price', 0)}")
            print(f"  Volume: {ticker.get('stats', {}).get('volume', 0)}")
            print(f"  Open Interest: {ticker.get('open_interest', 0)}")
    
    print("\n" + "=" * 80)
    print("测试完成！")
    print("=" * 80)
    print("\n结论:")
    print("- get_instruments API: 返回合约基本信息，但不包含实时市场数据")
    print("- ticker API: 返回完整的实时市场数据（bid/ask/volume/OI）")
    print("- 需要对每个合约调用 ticker API 才能获取完整数据")

if __name__ == "__main__":
    test_deribit_api()
