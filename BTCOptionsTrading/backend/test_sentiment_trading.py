#!/usr/bin/env python3
"""
测试情绪交易服务
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sentiment_trading_service import SentimentTradingService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_sentiment_fetch():
    """测试获取情绪数据"""
    print("\n=== 测试1: 获取情绪数据 ===")
    service = SentimentTradingService()
    
    data = await service.fetch_sentiment_data()
    if data:
        print(f"✓ 成功获取情绪数据: {data}")
        return data
    else:
        print("✗ 获取情绪数据失败")
        return None


async def test_sentiment_analysis(sentiment_data):
    """测试情绪分析"""
    print("\n=== 测试2: 情绪分析 ===")
    service = SentimentTradingService()
    
    if not sentiment_data:
        print("跳过测试（无情绪数据）")
        return
    
    strategy = service.analyze_sentiment(sentiment_data)
    print(f"✓ 选择的策略: {strategy}")
    
    # 测试不同情况
    test_cases = [
        {"data": {"negative_count": 20, "positive_count": 10}},
        {"data": {"negative_count": 10, "positive_count": 20}},
        {"data": {"negative_count": 15, "positive_count": 15}},
    ]
    
    for i, case in enumerate(test_cases, 1):
        strategy = service.analyze_sentiment(case)
        neg = case["data"]["negative_count"]
        pos = case["data"]["positive_count"]
        print(f"  案例{i}: 负面={neg}, 正面={pos} -> 策略={strategy}")


async def test_positions_and_orders():
    """测试获取持仓和订单"""
    print("\n=== 测试3: 获取持仓和订单 ===")
    service = SentimentTradingService()
    
    try:
        # 先认证
        authenticated = await service.trader.authenticate()
        if not authenticated:
            print("✗ Deribit认证失败")
            return
        print("✓ Deribit认证成功")
        
        # 获取持仓和订单
        result = await service.get_positions_and_orders()
        print(f"✓ 持仓数量: {result.get('position_count', 0)}")
        print(f"✓ 订单数量: {result.get('order_count', 0)}")
        
        if result.get('errors'):
            print(f"  警告: {result['errors']}")
        
        return result
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return None


async def test_strategy_execution():
    """测试策略执行（模拟）"""
    print("\n=== 测试4: 策略执行（仅验证构建） ===")
    service = SentimentTradingService()
    
    strategies = ["bearish_news", "bullish_news", "mixed_news"]
    
    for strategy_type in strategies:
        try:
            strategy = service.strategy_builder.build_from_template(
                template_id=strategy_type,
                capital=1000,
                expiry_days=7
            )
            if strategy:
                print(f"✓ {strategy_type} 策略构建成功")
            else:
                print(f"✗ {strategy_type} 策略构建失败")
        except Exception as e:
            print(f"✗ {strategy_type} 策略构建出错: {e}")


async def main():
    """运行所有测试"""
    print("=" * 50)
    print("情绪交易服务测试")
    print("=" * 50)
    
    # 测试1: 获取情绪数据
    sentiment_data = await test_sentiment_fetch()
    
    # 测试2: 情绪分析
    await test_sentiment_analysis(sentiment_data)
    
    # 测试3: 获取持仓和订单
    await test_positions_and_orders()
    
    # 测试4: 策略构建
    await test_strategy_execution()
    
    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
