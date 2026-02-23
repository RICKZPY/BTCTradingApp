#!/usr/bin/env python3
"""
简化的 Order Book 收集测试 - 诊断问题
"""

import sys
import asyncio
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

async def main():
    print("=" * 80)
    print("Order Book 收集 - 诊断测试")
    print("=" * 80)
    print()
    
    # 步骤 1: 导入模块
    print("[1/5] 导入模块...")
    try:
        from src.connectors.deribit_connector import DeribitConnector
        from src.config.logging_config import get_logger
        print("  ✓ 导入成功")
    except Exception as e:
        print(f"  ✗ 导入失败: {e}")
        return 1
    
    logger = get_logger(__name__)
    
    # 步骤 2: 初始化连接器
    print("\n[2/5] 初始化 Deribit 连接器...")
    try:
        connector = DeribitConnector()
        print("  ✓ 连接器初始化成功")
    except Exception as e:
        print(f"  ✗ 初始化失败: {e}")
        return 1
    
    # 步骤 3: 获取 BTC 价格
    print("\n[3/5] 获取 BTC 价格...")
    try:
        price = await connector.get_index_price("BTC")
        print(f"  ✓ BTC 价格: {price}")
    except Exception as e:
        print(f"  ✗ 获取价格失败: {e}")
        await connector.close()
        return 1
    
    # 步骤 4: 获取 Option 链
    print("\n[4/5] 获取 Option 链...")
    try:
        contracts = await connector.get_options_chain("BTC")
        print(f"  ✓ 获取到 {len(contracts)} 个 Option 合约")
        
        if contracts:
            first = contracts[0]
            print(f"    示例: {first.instrument_name}")
            print(f"    执行价: {first.strike_price}")
            print(f"    类型: {first.option_type}")
    except Exception as e:
        print(f"  ✗ 获取 Option 链失败: {e}")
        await connector.close()
        return 1
    
    # 步骤 5: 获取 Order Book
    print("\n[5/5] 获取 Order Book...")
    try:
        if contracts:
            instrument = contracts[0].instrument_name
            print(f"  获取 {instrument} 的 Order Book...")
            
            orderbook = await connector.get_orderbook(instrument)
            
            if orderbook:
                bids = orderbook.get('bids', [])
                asks = orderbook.get('asks', [])
                print(f"  ✓ 获取成功")
                print(f"    Bids: {len(bids)} 条")
                print(f"    Asks: {len(asks)} 条")
                
                if bids:
                    print(f"    最优买价: {bids[0][0]} (数量: {bids[0][1]})")
                if asks:
                    print(f"    最优卖价: {asks[0][0]} (数量: {asks[0][1]})")
            else:
                print(f"  ✗ 没有获取到 Order Book 数据")
    except Exception as e:
        print(f"  ✗ 获取 Order Book 失败: {e}")
        import traceback
        traceback.print_exc()
        await connector.close()
        return 1
    
    # 关闭连接
    await connector.close()
    
    print("\n" + "=" * 80)
    print("✓ 诊断完成 - 所有步骤成功")
    print("=" * 80)
    print()
    print("现在可以运行完整的收集脚本:")
    print("  python collect_orderbook.py")
    print()
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
