#!/usr/bin/env python3
"""
简单的数据采集脚本（不依赖项目代码）
直接调用 Deribit API 并保存到 CSV
"""

import requests
import csv
from datetime import datetime
from pathlib import Path

def collect_btc_options():
    """采集 BTC 期权数据"""
    base_url = "https://www.deribit.com/api/v2"
    
    print("=" * 80)
    print("开始采集 BTC 期权数据")
    print("=" * 80)
    
    # 1. 获取期权合约列表
    print("\n正在获取期权合约列表...")
    instruments_url = f"{base_url}/public/get_instruments"
    params = {
        "currency": "BTC",
        "kind": "option",
        "expired": "false"
    }
    
    response = requests.get(instruments_url, params=params)
    data = response.json()
    
    if "result" not in data:
        print(f"错误: {data}")
        return
    
    instruments = data["result"]
    print(f"找到 {len(instruments)} 个期权合约")
    
    # 2. 获取每个合约的市场数据
    print("\n正在获取市场数据...")
    options_data = []
    
    for i, instrument in enumerate(instruments):
        if i % 50 == 0:
            print(f"进度: {i}/{len(instruments)}")
        
        instrument_name = instrument["instrument_name"]
        
        try:
            # 获取 ticker 数据
            ticker_response = requests.get(
                f"{base_url}/public/ticker",
                params={"instrument_name": instrument_name}
            )
            ticker_data = ticker_response.json()
            
            if "result" in ticker_data:
                ticker = ticker_data["result"]
                
                # 合并数据
                option_data = {
                    "timestamp": datetime.now().isoformat(),
                    "instrument_name": instrument_name,
                    "underlying_symbol": "BTC",
                    "strike_price": instrument.get("strike", 0),
                    "expiry_date": datetime.fromtimestamp(
                        instrument.get("expiration_timestamp", 0) / 1000
                    ).isoformat() if instrument.get("expiration_timestamp") else "",
                    "option_type": instrument.get("option_type", ""),
                    "mark_price": ticker.get("mark_price", 0),
                    "bid_price": ticker.get("best_bid_price", 0),
                    "ask_price": ticker.get("best_ask_price", 0),
                    "last_price": ticker.get("last_price", 0),
                    "volume": ticker.get("stats", {}).get("volume", 0),
                    "open_interest": ticker.get("open_interest", 0),
                    "implied_volatility": ticker.get("mark_iv", 0),
                    "delta": ticker.get("greeks", {}).get("delta", 0),
                    "gamma": ticker.get("greeks", {}).get("gamma", 0),
                    "theta": ticker.get("greeks", {}).get("theta", 0),
                    "vega": ticker.get("greeks", {}).get("vega", 0),
                    "rho": ticker.get("greeks", {}).get("rho", 0)
                }
                options_data.append(option_data)
        except Exception as e:
            print(f"警告: 获取 {instrument_name} 数据失败: {e}")
            continue
    
    print(f"\n成功获取 {len(options_data)} 个合约的数据")
    
    # 3. 保存到 CSV
    output_dir = Path("data/downloads")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_file = output_dir / f"BTC_options_{timestamp_str}.csv"
    
    print(f"\n正在保存到: {csv_file}")
    
    fieldnames = [
        'timestamp', 'instrument_name', 'underlying_symbol', 'strike_price',
        'expiry_date', 'option_type', 'mark_price', 'bid_price', 'ask_price',
        'last_price', 'volume', 'open_interest', 'implied_volatility',
        'delta', 'gamma', 'theta', 'vega', 'rho'
    ]
    
    with open(csv_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(options_data)
    
    print(f"✅ 数据已保存到: {csv_file}")
    print(f"文件大小: {csv_file.stat().st_size / 1024:.2f} KB")
    
    # 4. 统计信息
    print("\n" + "=" * 80)
    print("数据统计:")
    print("=" * 80)
    
    total = len(options_data)
    has_bid = sum(1 for o in options_data if o['bid_price'] > 0)
    has_ask = sum(1 for o in options_data if o['ask_price'] > 0)
    has_volume = sum(1 for o in options_data if o['volume'] > 0)
    has_oi = sum(1 for o in options_data if o['open_interest'] > 0)
    
    print(f"\n总合约数: {total}")
    print(f"有买价的合约: {has_bid} ({has_bid/total*100:.1f}%)")
    print(f"有卖价的合约: {has_ask} ({has_ask/total*100:.1f}%)")
    print(f"有成交量的合约: {has_volume} ({has_volume/total*100:.1f}%)")
    print(f"有持仓量的合约: {has_oi} ({has_oi/total*100:.1f}%)")
    
    print("\n" + "=" * 80)
    print("采集完成！")
    print("=" * 80)

if __name__ == "__main__":
    collect_btc_options()
