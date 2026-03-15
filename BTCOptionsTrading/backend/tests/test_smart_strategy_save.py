"""
测试智能策略构建和保存功能
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.connectors.deribit_connector import DeribitConnector
from src.strategy.smart_strategy_builder import (
    SmartStrategyBuilder,
    SmartStrategyTemplate,
    SmartStrategyLeg,
    RelativeExpiry,
    RelativeStrike,
    PREDEFINED_TEMPLATES
)
from src.core.models import StrategyType, OptionType, ActionType
from src.storage.database import get_db
from src.storage.dao import StrategyDAO


async def test_build_and_save():
    """测试构建和保存策略"""
    print("=" * 60)
    print("测试智能策略构建和保存")
    print("=" * 60)
    
    # 1. 使用预定义模板构建策略
    print("\n1. 从模板构建策略...")
    template = PREDEFINED_TEMPLATES['atm_call_weekly']
    
    connector = DeribitConnector()
    builder = SmartStrategyBuilder(connector)
    
    strategy = await builder.build_strategy(template, 'BTC')
    
    print(f"✓ 策略构建成功:")
    print(f"  名称: {strategy.name}")
    print(f"  类型: {strategy.strategy_type.value}")
    print(f"  腿数: {len(strategy.legs)}")
    
    for i, leg in enumerate(strategy.legs):
        print(f"\n  腿 #{i+1}:")
        print(f"    合约: {leg.option_contract.instrument_name}")
        print(f"    操作: {leg.action.value}")
        print(f"    数量: {leg.quantity}")
        print(f"    行权价: ${leg.option_contract.strike_price}")
        print(f"    当前价: {leg.option_contract.current_price} BTC")
    
    # 2. 保存到数据库
    print("\n2. 保存策略到数据库...")
    db = next(get_db())
    try:
        db_strategy = StrategyDAO.create(db, strategy)
        print(f"✓ 策略保存成功，ID: {db_strategy.id}")
        
        # 3. 验证保存
        print("\n3. 验证保存的策略...")
        saved_strategy = StrategyDAO.get_by_id(db, db_strategy.id)
        
        if saved_strategy:
            print(f"✓ 策略验证成功:")
            print(f"  ID: {saved_strategy.id}")
            print(f"  名称: {saved_strategy.name}")
            print(f"  类型: {saved_strategy.strategy_type}")
            print(f"  腿数: {len(saved_strategy.legs)}")
            
            # 4. 列出所有策略
            print("\n4. 当前数据库中的所有策略:")
            all_strategies = StrategyDAO.get_all(db)
            for s in all_strategies:
                print(f"  - {s.name} ({s.strategy_type}) - {s.created_at}")
            
            print(f"\n✓ 测试完成！共有 {len(all_strategies)} 个策略")
        else:
            print("✗ 策略验证失败：未找到保存的策略")
            
    except Exception as e:
        print(f"✗ 保存失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(test_build_and_save())
