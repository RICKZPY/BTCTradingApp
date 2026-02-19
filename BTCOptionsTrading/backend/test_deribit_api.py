#!/usr/bin/env python3
"""
测试 Deribit API 数据获取
验证 bid/ask/volume 等市场数据是否正确获取
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.connectors.deribit_connector import DeribitConnector


async def test_api():
    """测试 API 数据获取"""
    connector = DeribitConnector()
    
    try:
        print("=" * 80)
        print("测试 Deribit API 数据获取")
        print("=" * 80)
        
        # 获取 BTC 期权链
        print("\n正在获取 BTC 期权数据...")
        options = await connector.get_options_chain("BTC")
        
        print(f"\n总共获取到 {len(options)} 个期权合约")
        
        # 显示前 5 个合约的详细信息
        print("\n" + "=" * 80)
        print("前 5 个合约的详细信息：")
        print("=" * 80)
        
        for i, option in enumerate(options[:5]):
            print(f"\n合约 #{i+1}:")
            print(f"  名称: {option.instrument_name}")
            print(f"  类型: {option.option_type.value}")
            print(f"  执行价: ${option.strike_price}")
            print(f"  到期日: {option.expiration_date.strftime('%Y-%m-%d')}")
            print(f"  当前价格: ${option.current_price}")
            print(f"  买价 (bid): ${option.bid_price}")
            print(f"  卖价 (ask): ${option.ask_price}")
            print(f"  最后成交价: ${option.last_price}")
            print(f"  成交量: {option.volume}")
            print(f"  持仓量: {option.open_interest}")
            print(f"  隐含波动率: {option.implied_volatility:.2%}")
            print(f"  Delta: {option.delta:.4f}")
            print(f"  Gamma: {option.gamma:.4f}")
            print(f"  Vega: {option.vega:.4f}")
        
        # 统计有效数据
        print("\n" + "=" * 80)
        print("数据质量统计：")
        print("=" * 80)
        
        total = len(options)
        has_bid = sum(1 for o in options if o.bid_price > 0)
        has_ask = sum(1 for o in options if o.ask_price > 0)
        has_volume = sum(1 for o in options if o.volume > 0)
        has_oi = sum(1 for o in options if o.open_interest > 0)
        
        print(f"\n总合约数: {total}")
        print(f"有买价的合约: {has_bid} ({has_bid/total*100:.1f}%)")
        print(f"有卖价的合约: {has_ask} ({has_ask/total*100:.1f}%)")
        print(f"有成交量的合约: {has_volume} ({has_volume/total*100:.1f}%)")
        print(f"有持仓量的合约: {has_oi} ({has_oi/total*100:.1f}%)")
        
        # 找出成交量最大的 5 个合约
        print("\n" + "=" * 80)
        print("成交量最大的 5 个合约：")
        print("=" * 80)
        
        sorted_by_volume = sorted(options, key=lambda x: x.volume, reverse=True)[:5]
        for i, option in enumerate(sorted_by_volume):
            print(f"\n#{i+1}: {option.instrument_name}")
            print(f"  成交量: {option.volume}")
            print(f"  买价: ${option.bid_price}")
            print(f"  卖价: ${option.ask_price}")
            print(f"  持仓量: {option.open_interest}")
        
        print("\n" + "=" * 80)
        print("测试完成！")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n错误: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        await connector.close()


if __name__ == "__main__":
    asyncio.run(test_api())
