"""
测试事件驱动型策略模板
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.connectors.deribit_connector import DeribitConnector
from src.strategy.smart_strategy_builder import (
    SmartStrategyBuilder,
    PREDEFINED_TEMPLATES
)


async def test_event_driven_templates():
    """测试三个事件驱动型模板"""
    print("=" * 60)
    print("测试事件驱动型策略模板")
    print("=" * 60)
    
    connector = DeribitConnector()
    builder = SmartStrategyBuilder(connector)
    
    # 测试模板列表
    test_templates = [
        ('bullish_news', '利好消息策略'),
        ('bearish_news', '负面消息策略'),
        ('mixed_news', '消息混杂策略')
    ]
    
    for template_id, template_name in test_templates:
        print(f"\n{'=' * 60}")
        print(f"测试模板: {template_name}")
        print('=' * 60)
        
        if template_id not in PREDEFINED_TEMPLATES:
            print(f"✗ 模板 {template_id} 不存在")
            continue
        
        template = PREDEFINED_TEMPLATES[template_id]
        
        print(f"\n模板信息:")
        print(f"  名称: {template.name}")
        print(f"  描述: {template.description}")
        print(f"  类型: {template.strategy_type.value}")
        print(f"  腿数: {len(template.legs)}")
        
        # 构建策略
        try:
            strategy = await builder.build_strategy(template, 'BTC')
            
            print(f"\n✓ 策略构建成功:")
            print(f"  策略名称: {strategy.name}")
            print(f"  总成本: {strategy.total_cost} BTC")
            print(f"  净Delta: {strategy.net_delta:.4f}")
            
            for i, leg in enumerate(strategy.legs):
                print(f"\n  腿 #{i+1}:")
                print(f"    合约: {leg.option_contract.instrument_name}")
                print(f"    类型: {leg.option_contract.option_type.value}")
                print(f"    操作: {leg.action.value}")
                print(f"    数量: {leg.quantity}")
                print(f"    行权价: ${leg.option_contract.strike_price}")
                print(f"    到期日: {leg.option_contract.expiration_date.strftime('%Y-%m-%d')}")
                print(f"    当前价: {leg.option_contract.current_price} BTC")
                print(f"    Delta: {leg.option_contract.delta:.4f}")
                
        except Exception as e:
            print(f"\n✗ 构建失败: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_event_driven_templates())
