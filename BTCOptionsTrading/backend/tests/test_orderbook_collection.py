"""
测试 Order Book 收集功能
"""

import sys
import json
sys.path.insert(0, '/Users/rickzhong/BTCTradingApp/BTCOptionsTrading/backend')

from src.collectors.orderbook_collector import OrderBookCollector
from src.config.logging_config import get_logger

logger = get_logger(__name__)

def test_orderbook_collection():
    """测试 Order Book 收集"""
    print("\n" + "="*80)
    print("Order Book 收集测试")
    print("="*80 + "\n")
    
    # 初始化收集器
    collector = OrderBookCollector()
    print(f"✓ 收集器初始化成功")
    print(f"  数据目录: {collector.data_dir}\n")
    
    # 测试 1: 获取 ATM 价位
    print("测试 1: 获取 ATM 价位")
    print("-" * 80)
    try:
        atm_strikes = collector.get_atm_strikes("BTC", num_strikes=4)
        print(f"✓ 获取 ATM 价位成功")
        print(f"  ATM 价位: {atm_strikes}\n")
    except Exception as e:
        print(f"✗ 获取 ATM 价位失败: {e}\n")
        return
    
    # 测试 2: 获取 Option 链
    print("测试 2: 获取 Option 链")
    print("-" * 80)
    try:
        options_chain = collector.get_options_chain("BTC", days_ahead=30)
        print(f"✓ 获取 Option 链成功")
        print(f"  总共获取 {len(options_chain)} 个 option")
        if options_chain:
            print(f"  示例 option:")
            for opt in options_chain[:3]:
                print(f"    - {opt['instrument_name']}: strike={opt['strike_price']}, type={opt['option_type']}")
        print()
    except Exception as e:
        print(f"✗ 获取 Option 链失败: {e}\n")
        return
    
    # 测试 3: 收集 Order Book
    print("测试 3: 收集 Order Book 数据")
    print("-" * 80)
    try:
        orderbook_data = collector.collect_orderbook("BTC", num_strikes=4)
        print(f"✓ 收集 Order Book 成功")
        print(f"  总共收集 {len(orderbook_data)} 条数据")
        if orderbook_data:
            print(f"  示例数据:")
            for data in orderbook_data[:3]:
                print(f"    - {data['instrument_name']}")
                print(f"      Bid: {data['bid_price']} x {data['bid_size']}")
                print(f"      Ask: {data['ask_price']} x {data['ask_size']}")
        print()
    except Exception as e:
        print(f"✗ 收集 Order Book 失败: {e}\n")
        return
    
    # 测试 4: 保存到 CSV
    print("测试 4: 保存到 CSV")
    print("-" * 80)
    try:
        csv_file = collector.save_to_csv(orderbook_data)
        print(f"✓ 保存到 CSV 成功")
        print(f"  文件路径: {csv_file}\n")
    except Exception as e:
        print(f"✗ 保存到 CSV 失败: {e}\n")
        return
    
    # 测试 5: 完整流程
    print("测试 5: 完整的收集和保存流程")
    print("-" * 80)
    try:
        result_file = collector.collect_and_save("BTC", num_strikes=4)
        print(f"✓ 完整流程执行成功")
        print(f"  结果文件: {result_file}\n")
    except Exception as e:
        print(f"✗ 完整流程失败: {e}\n")
        return
    
    print("="*80)
    print("✓ 所有测试完成")
    print("="*80 + "\n")

if __name__ == "__main__":
    test_orderbook_collection()
