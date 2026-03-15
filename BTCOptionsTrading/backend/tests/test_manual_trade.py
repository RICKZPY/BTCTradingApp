#!/usr/bin/env python3
"""
手动测试交易脚本
立即读取sentiment API并执行一次交易
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from sentiment_trading_service import SentimentTradingService
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_trade():
    """测试交易流程"""
    print("="*60)
    print("手动测试交易")
    print("="*60)
    print()
    
    # 初始化服务
    print("1. 初始化交易服务...")
    try:
        service = SentimentTradingService()
    except Exception as e:
        print(f"✗ 初始化失败: {e}")
        return
    
    print("✓ 服务初始化成功")
    print()
    
    # 认证
    print("2. 连接Deribit测试网...")
    try:
        authenticated = await service.trader.authenticate()
        if not authenticated:
            print("✗ Deribit认证失败")
            return
        print("✓ Deribit认证成功")
    except Exception as e:
        print(f"✗ 认证失败: {e}")
        return
    
    print()
    
    # 获取情绪数据
    print("3. 获取情绪数据...")
    sentiment_data = await service.fetch_sentiment_data()
    
    if not sentiment_data:
        print("✗ 无法获取情绪数据")
        return
    
    print("✓ 成功获取情绪数据:")
    data = sentiment_data.get('data', {})
    print(f"  - 负面消息: {data.get('negative_count', 0)}")
    print(f"  - 正面消息: {data.get('positive_count', 0)}")
    print(f"  - 中性消息: {data.get('neutral_count', 0)}")
    print(f"  - 总消息数: {data.get('total_count', 0)}")
    print()
    
    # 分析情绪
    print("4. 分析情绪并选择策略...")
    strategy_type = service.analyze_sentiment(sentiment_data)
    
    strategy_names = {
        "bearish_news": "负面消息策略（看跌）",
        "bullish_news": "利好消息策略（看涨）",
        "mixed_news": "消息混杂策略（中性）"
    }
    
    print(f"✓ 选择策略: {strategy_names.get(strategy_type, strategy_type)}")
    print()
    
    # 确认执行
    print("="*60)
    print("准备执行交易")
    print("="*60)
    print(f"策略类型: {strategy_names.get(strategy_type, strategy_type)}")
    print(f"交易网络: 测试网 (Testnet)")
    print(f"资金规模: $1000 USD")
    print()
    
    response = input("确认执行交易？(yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("取消交易")
        return
    
    print()
    
    # 执行交易
    print("5. 执行交易策略...")
    result = await service.execute_sentiment_strategy(strategy_type, sentiment_data)
    
    print()
    print("="*60)
    print("交易结果")
    print("="*60)
    
    if result.get("success"):
        print("✓ 交易执行成功！")
        print()
        print("执行详情:")
        
        # 显示订单信息
        if "orders" in result:
            orders = result["orders"]
            print(f"  下单数量: {len(orders)}")
            for i, order in enumerate(orders, 1):
                print(f"\n  订单 {i}:")
                print(f"    合约: {order.get('instrument_name', 'N/A')}")
                print(f"    方向: {order.get('direction', 'N/A')}")
                print(f"    数量: {order.get('amount', 'N/A')}")
                print(f"    价格: {order.get('price', 'N/A')}")
                print(f"    状态: {order.get('order_state', 'N/A')}")
        
        # 显示策略信息
        if "strategy" in result:
            strategy = result["strategy"]
            print(f"\n  策略信息:")
            print(f"    类型: {strategy.get('type', 'N/A')}")
            print(f"    资金: ${strategy.get('capital', 'N/A')}")
    else:
        print("✗ 交易执行失败")
        print(f"错误: {result.get('error', '未知错误')}")
    
    print()
    
    # 获取最新持仓
    print("6. 获取最新持仓信息...")
    positions_data = await service.get_positions_and_orders()
    
    print(f"✓ 当前持仓数量: {positions_data.get('position_count', 0)}")
    print(f"✓ 未完成订单: {positions_data.get('order_count', 0)}")
    
    if positions_data.get('errors'):
        print(f"⚠ 警告: {positions_data['errors']}")
    
    print()
    print("="*60)
    print("测试完成！")
    print("="*60)
    print()
    print("查看详细信息:")
    print(f"  - 交易历史: cat data/sentiment_trading_history.json")
    print(f"  - 持仓信息: cat data/current_positions.json")
    print(f"  - API查看: curl http://localhost:5002/api/status")
    print()


if __name__ == "__main__":
    try:
        asyncio.run(test_trade())
    except KeyboardInterrupt:
        print("\n\n操作已取消")
    except Exception as e:
        print(f"\n✗ 发生错误: {e}")
        import traceback
        traceback.print_exc()
