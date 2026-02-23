#!/usr/bin/env python3
"""
简单的订单簿收集脚本
每天北京时间早上5点收集ATM附近期权的orderbook数据
"""
import asyncio
import aiohttp
import csv
from datetime import datetime, timedelta
from pathlib import Path
import pytz

# 配置
DERIBIT_API = "https://www.deribit.com/api/v2"
DATA_DIR = Path(__file__).parent / "data" / "orderbook"
COLLECTION_DURATION = 120  # 收集2分钟（5点前后1分钟）
COLLECTION_INTERVAL = 1  # 每秒收集一次

async def get_btc_price(session):
    """获取BTC当前价格"""
    url = f"{DERIBIT_API}/public/get_index_price"
    params = {"index_name": "btc_usd"}
    async with session.get(url, params=params) as resp:
        data = await resp.json()
        return data['result']['index_price']

async def get_instruments(session):
    """获取所有BTC期权合约"""
    url = f"{DERIBIT_API}/public/get_instruments"
    params = {
        "currency": "BTC",
        "kind": "option",
        "expired": "false"
    }
    async with session.get(url, params=params) as resp:
        data = await resp.json()
        return data['result']

def filter_atm_options(instruments, btc_price, days_limit=30):
    """筛选ATM附近4个价位、一个月内到期的期权"""
    now = datetime.now(pytz.UTC)
    one_month_later = now + timedelta(days=days_limit)
    
    # 找到最接近ATM的strike价格
    strikes = sorted(set(inst['strike'] for inst in instruments))
    atm_strike = min(strikes, key=lambda x: abs(x - btc_price))
    atm_index = strikes.index(atm_strike)
    
    # 选择ATM附近4个价位（ATM上下各2个）
    selected_strikes = strikes[max(0, atm_index-2):atm_index+3]
    
    # 筛选符合条件的期权
    filtered = []
    for inst in instruments:
        expiry = datetime.fromtimestamp(inst['expiration_timestamp'] / 1000, tz=pytz.UTC)
        if (inst['strike'] in selected_strikes and 
            expiry <= one_month_later):
            filtered.append(inst)
    
    return filtered

async def get_orderbook(session, instrument_name):
    """获取单个合约的orderbook"""
    url = f"{DERIBIT_API}/public/get_order_book"
    params = {"instrument_name": instrument_name, "depth": 10}
    
    try:
        async with session.get(url, params=params) as resp:
            data = await resp.json()
            if 'result' in data:
                return data['result']
    except Exception as e:
        print(f"获取 {instrument_name} orderbook失败: {e}")
    return None

async def collect_orderbooks(instruments):
    """收集所有选定合约的orderbook"""
    timestamp = datetime.now(pytz.timezone('Asia/Shanghai'))
    results = []
    
    async with aiohttp.ClientSession() as session:
        for inst in instruments:
            orderbook = await get_orderbook(session, inst['instrument_name'])
            if orderbook:
                # 记录每个bid
                for bid in orderbook.get('bids', []):
                    results.append({
                        'timestamp': timestamp.isoformat(),
                        'instrument': inst['instrument_name'],
                        'strike': inst['strike'],
                        'option_type': inst['option_type'],
                        'expiry': datetime.fromtimestamp(inst['expiration_timestamp']/1000).strftime('%Y-%m-%d'),
                        'side': 'bid',
                        'price': bid[0],
                        'amount': bid[1]
                    })
                
                # 记录每个ask
                for ask in orderbook.get('asks', []):
                    results.append({
                        'timestamp': timestamp.isoformat(),
                        'instrument': inst['instrument_name'],
                        'strike': inst['strike'],
                        'option_type': inst['option_type'],
                        'expiry': datetime.fromtimestamp(inst['expiration_timestamp']/1000).strftime('%Y-%m-%d'),
                        'side': 'ask',
                        'price': ask[0],
                        'amount': ask[1]
                    })
    
    return results

async def main():
    """主函数"""
    print("开始收集orderbook数据...")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # 生成CSV文件名
    beijing_time = datetime.now(pytz.timezone('Asia/Shanghai'))
    csv_filename = DATA_DIR / f"orderbook_{beijing_time.strftime('%Y%m%d_%H%M%S')}.csv"
    
    # 获取要监控的合约
    async with aiohttp.ClientSession() as session:
        btc_price = await get_btc_price(session)
        print(f"BTC价格: ${btc_price:,.2f}")
        
        instruments = await get_instruments(session)
        selected = filter_atm_options(instruments, btc_price)
        print(f"选中 {len(selected)} 个期权合约")
        for inst in selected:
            print(f"  - {inst['instrument_name']}")
    
    # 收集数据
    all_data = []
    start_time = datetime.now()
    iteration = 0
    
    while (datetime.now() - start_time).total_seconds() < COLLECTION_DURATION:
        iteration += 1
        print(f"\n第 {iteration} 次收集 ({datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%H:%M:%S')})")
        
        data = await collect_orderbooks(selected)
        all_data.extend(data)
        print(f"收集了 {len(data)} 条记录")
        
        await asyncio.sleep(COLLECTION_INTERVAL)
    
    # 保存到CSV
    if all_data:
        with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'timestamp', 'instrument', 'strike', 'option_type', 
                'expiry', 'side', 'price', 'amount'
            ])
            writer.writeheader()
            writer.writerows(all_data)
        
        print(f"\n数据已保存到: {csv_filename}")
        print(f"总共收集了 {len(all_data)} 条orderbook记录")
    else:
        print("没有收集到数据")

if __name__ == "__main__":
    asyncio.run(main())
