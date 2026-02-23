"""
Order Book 收集 - Mock 测试 (不需要真实 API 调用)
"""

import os
import csv
from datetime import datetime, timezone
from pathlib import Path

def test_orderbook_mock():
    """Mock 测试 Order Book 收集"""
    print("\n" + "="*80)
    print("Order Book 收集 - Mock 测试")
    print("="*80 + "\n")
    
    # 创建数据目录
    data_dir = "BTCOptionsTrading/backend/data/orderbook"
    Path(data_dir).mkdir(parents=True, exist_ok=True)
    print(f"✓ 数据目录: {data_dir}\n")
    
    # 模拟 Order Book 数据
    print("生成模拟 Order Book 数据...")
    print("-" * 80)
    
    # ATM 价位 (假设 BTC 当前价格 68000)
    atm_strikes = [66000, 67000, 68000, 69000]
    
    # 模拟 option 数据
    options = [
        {"instrument": "BTC-27FEB26-66000-C", "strike": 66000, "type": "call", "expiry": "2026-02-27"},
        {"instrument": "BTC-27FEB26-66000-P", "strike": 66000, "type": "put", "expiry": "2026-02-27"},
        {"instrument": "BTC-27FEB26-67000-C", "strike": 67000, "type": "call", "expiry": "2026-02-27"},
        {"instrument": "BTC-27FEB26-67000-P", "strike": 67000, "type": "put", "expiry": "2026-02-27"},
        {"instrument": "BTC-27FEB26-68000-C", "strike": 68000, "type": "call", "expiry": "2026-02-27"},
        {"instrument": "BTC-27FEB26-68000-P", "strike": 68000, "type": "put", "expiry": "2026-02-27"},
        {"instrument": "BTC-27FEB26-69000-C", "strike": 69000, "type": "call", "expiry": "2026-02-27"},
        {"instrument": "BTC-27FEB26-69000-P", "strike": 69000, "type": "put", "expiry": "2026-02-27"},
    ]
    
    print(f"ATM 价位: {atm_strikes}")
    print(f"Option 数量: {len(options)}\n")
    
    # 生成 Order Book 数据
    print("生成 Order Book 数据...")
    print("-" * 80)
    
    orderbook_data = []
    timestamp = datetime.now(timezone.utc).isoformat()
    
    for opt in options:
        # 模拟 bid/ask 数据
        bid_price = opt['strike'] - 10
        ask_price = opt['strike'] - 5
        bid_size = 0.5
        ask_size = 0.3
        
        orderbook_data.append({
            'timestamp': timestamp,
            'instrument_name': opt['instrument'],
            'strike_price': opt['strike'],
            'option_type': opt['type'],
            'expiry_date': opt['expiry'],
            'bid_price': bid_price,
            'bid_size': bid_size,
            'ask_price': ask_price,
            'ask_size': ask_size
        })
        
        print(f"  {opt['instrument']}")
        print(f"    Bid: {bid_price} x {bid_size}")
        print(f"    Ask: {ask_price} x {ask_size}")
    
    print(f"\n✓ 生成了 {len(orderbook_data)} 条 Order Book 数据\n")
    
    # 保存到 CSV
    print("保存到 CSV...")
    print("-" * 80)
    
    now = datetime.now()
    filename = f"orderbook_{now.strftime('%Y%m%d_%H%M%S')}.csv"
    filepath = os.path.join(data_dir, filename)
    
    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [
                'timestamp', 'instrument_name', 'strike_price', 'option_type',
                'expiry_date', 'bid_price', 'bid_size', 'ask_price', 'ask_size'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(orderbook_data)
        
        print(f"✓ 文件已保存: {filepath}\n")
    except Exception as e:
        print(f"✗ 保存失败: {e}\n")
        return
    
    # 验证文件
    print("验证文件...")
    print("-" * 80)
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            print(f"✓ 文件包含 {len(rows)} 条记录\n")
            
            # 显示前 3 条记录
            print("前 3 条记录:")
            for i, row in enumerate(rows[:3]):
                print(f"\n  记录 {i+1}:")
                for key, value in row.items():
                    print(f"    {key}: {value}")
    except Exception as e:
        print(f"✗ 验证失败: {e}\n")
        return
    
    # 显示文件信息
    print("\n\n文件信息:")
    print("-" * 80)
    
    file_size = os.path.getsize(filepath)
    file_mtime = os.path.getmtime(filepath)
    file_mtime_str = datetime.fromtimestamp(file_mtime).isoformat()
    
    print(f"文件名: {filename}")
    print(f"文件大小: {file_size} 字节")
    print(f"最后修改: {file_mtime_str}")
    print(f"完整路径: {filepath}\n")
    
    # 显示目录内容
    print("目录内容:")
    print("-" * 80)
    
    files = os.listdir(data_dir)
    for f in files:
        fpath = os.path.join(data_dir, f)
        fsize = os.path.getsize(fpath)
        print(f"  {f} ({fsize} 字节)")
    
    print("\n" + "="*80)
    print("✓ Mock 测试完成")
    print("="*80 + "\n")

if __name__ == "__main__":
    test_orderbook_mock()
