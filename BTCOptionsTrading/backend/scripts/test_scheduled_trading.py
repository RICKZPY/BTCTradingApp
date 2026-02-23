#!/usr/bin/env python3
"""
测试定时交易功能
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.trading.deribit_trader import DeribitTrader
from src.trading.scheduled_trading import ScheduledTradingManager
from src.core.models import (
    Strategy, StrategyLeg, StrategyType, OptionContract,
    ActionType, OptionType
)
from decimal import Decimal
from datetime import datetime, timedelta


async def main():
    """主函数"""
    print("=== 定时交易功能测试 ===\n")
    
    # 1. 初始化交易客户端（使用测试网络）
    print("1. 初始化Deribit测试客户端...")
    api_key = input("请输入Deribit测试网API Key: ").strip()
    api_secret = input("请输入Deribit测试网API Secret: ").strip()
    
    trader = DeribitTrader(
        api_key=api_key,
        api_secret=api_secret,
        testnet=True
    )
    
    # 2. 认证
    print("\n2. 进行认证...")
    auth_success = await trader.authenticate()
    if not auth_success:
        print("❌ 认证失败")
        return
    print("✓ 认证成功")
    
    # 3. 获取账户信息
    print("\n3. 获取账户信息...")
    account = await trader.get_account_summary()
    if account:
        print(f"✓ 账户余额: {account.get('balance', 0)} BTC")
        print(f"  可用余额: {account.get('available_funds', 0)} BTC")
    
    # 4. 创建测试策略
    print("\n4. 创建测试策略...")
    
    # 创建一个简单的看涨期权策略
    expiry = datetime.now() + timedelta(days=7)
    
    option_contract = OptionContract(
        instrument_name="BTC-28FEB26-100000-C",  # 示例合约名
        underlying="BTC",
        option_type=OptionType.CALL,
        strike_price=Decimal("100000"),
        expiration_date=expiry,
        current_price=Decimal("0.05"),
        bid_price=Decimal("0.048"),
        ask_price=Decimal("0.052"),
        last_price=Decimal("0.05"),
        implied_volatility=0.8,
        delta=0.3,
        gamma=0.001,
        theta=-0.01,
        vega=0.1,
        rho=0.01,
        open_interest=100,
        volume=50,
        timestamp=datetime.now()
    )
    
    leg = StrategyLeg(
        option_contract=option_contract,
        action=ActionType.BUY,
        quantity=1
    )
    
    strategy = Strategy(
        name="测试看涨策略",
        description="用于测试定时交易的简单看涨策略",
        strategy_type=StrategyType.SINGLE_LEG,
        legs=[leg]
    )
    
    print(f"✓ 创建策略: {strategy.name}")
    print(f"  策略ID: {strategy.id}")
    
    # 5. 初始化定时交易管理器
    print("\n5. 初始化定时交易管理器...")
    manager = ScheduledTradingManager(trader)
    
    # 6. 添加定时策略（设置为1分钟后执行，用于测试）
    print("\n6. 添加定时策略...")
    now = datetime.now()
    test_time = (now + timedelta(minutes=1)).strftime("%H:%M")
    
    strategy_id = manager.add_scheduled_strategy(
        strategy=strategy,
        schedule_time=test_time,
        timezone="Asia/Shanghai",
        use_market_order=False,
        auto_close=False
    )
    
    print(f"✓ 已添加定时策略")
    print(f"  执行时间: {test_time} (北京时间)")
    print(f"  策略ID: {strategy_id}")
    
    # 7. 启动调度器
    print("\n7. 启动调度器...")
    manager.start()
    print("✓ 调度器已启动")
    
    # 8. 显示所有定时策略
    print("\n8. 当前定时策略:")
    scheduled = manager.get_scheduled_strategies()
    for s in scheduled:
        print(f"  - {s['strategy_name']}")
        print(f"    执行时间: {s['schedule_time']}")
        print(f"    状态: {'启用' if s['enabled'] else '禁用'}")
    
    # 9. 等待执行（或按Ctrl+C退出）
    print("\n9. 等待定时执行...")
    print("   按 Ctrl+C 停止")
    
    try:
        # 保持运行
        while True:
            await asyncio.sleep(10)
            
            # 检查执行日志
            log = manager.get_execution_log()
            if log:
                print(f"\n执行日志更新: {len(log)} 条记录")
                for entry in log[-1:]:  # 显示最新一条
                    print(f"  策略: {entry['strategy_name']}")
                    print(f"  时间: {entry['execution_time']}")
                    print(f"  成功: {entry['success']}")
                    
    except KeyboardInterrupt:
        print("\n\n停止调度器...")
        manager.stop()
        print("✓ 已停止")


if __name__ == "__main__":
    asyncio.run(main())
