#!/usr/bin/env python3
"""
测试新API端点
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

# 测试导入
try:
    from src.api.routes import smart_strategy, scheduled_trading
    print("✓ 路由导入成功")
    print(f"  smart_strategy router: {smart_strategy.router}")
    print(f"  scheduled_trading router: {scheduled_trading.router}")
except Exception as e:
    print(f"✗ 路由导入失败: {e}")
    import traceback
    traceback.print_exc()

# 测试智能策略构建器
try:
    from src.strategy.smart_strategy_builder import (
        SmartStrategyBuilder,
        RelativeExpiry,
        RelativeStrike,
        PREDEFINED_TEMPLATES
    )
    print("\n✓ 智能策略构建器导入成功")
    print(f"  预定义模板数量: {len(PREDEFINED_TEMPLATES)}")
    print(f"  相对到期日选项: {[e.value for e in RelativeExpiry]}")
    print(f"  相对行权价选项: {[s.value for s in RelativeStrike]}")
except Exception as e:
    print(f"\n✗ 智能策略构建器导入失败: {e}")
    import traceback
    traceback.print_exc()

# 测试定时交易
try:
    from src.trading.deribit_trader import DeribitTrader
    from src.trading.scheduled_trading import ScheduledTradingManager
    print("\n✓ 定时交易模块导入成功")
except Exception as e:
    print(f"\n✗ 定时交易模块导入失败: {e}")
    import traceback
    traceback.print_exc()

print("\n所有测试完成！")
