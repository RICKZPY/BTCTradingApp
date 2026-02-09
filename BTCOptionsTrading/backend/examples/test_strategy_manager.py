"""
策略管理器使用示例
演示如何创建和管理各种期权策略
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime, timedelta
from decimal import Decimal

from src.strategy.strategy_manager import StrategyManager
from src.core.models import OptionType


def print_strategy_info(strategy):
    """打印策略信息"""
    print(f"\n策略名称: {strategy.name}")
    print(f"策略类型: {strategy.strategy_type.value}")
    print(f"策略描述: {strategy.description}")
    print(f"创建时间: {strategy.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"策略腿数: {len(strategy.legs)}")
    print("\n策略腿详情:")
    for i, leg in enumerate(strategy.legs, 1):
        contract = leg.option_contract
        print(f"  腿 {i}:")
        print(f"    合约: {contract.instrument_name}")
        print(f"    类型: {contract.option_type.value}")
        print(f"    执行价: ${contract.strike_price}")
        print(f"    到期日: {contract.expiration_date.strftime('%Y-%m-%d')}")
        print(f"    操作: {leg.action.value}")
        print(f"    数量: {leg.quantity}")


def main():
    print("=" * 70)
    print("策略管理器使用示例")
    print("=" * 70)
    
    # 创建策略管理器
    manager = StrategyManager()
    
    # 测试参数
    current_price = Decimal('45000')
    expiry = datetime.now() + timedelta(days=30)
    quantity = 1
    
    print(f"\n当前BTC价格: ${current_price}")
    print(f"期权到期日: {expiry.strftime('%Y-%m-%d')}")
    
    # 1. 单腿策略
    print("\n" + "=" * 70)
    print("1. 单腿期权策略")
    print("=" * 70)
    
    # 买入看涨期权
    long_call = manager.create_single_leg_strategy(
        option_type=OptionType.CALL,
        action='buy',
        strike=current_price,
        expiry=expiry,
        quantity=quantity
    )
    print_strategy_info(long_call)
    
    # 卖出看跌期权
    short_put = manager.create_single_leg_strategy(
        option_type=OptionType.PUT,
        action='sell',
        strike=current_price - Decimal('1000'),
        expiry=expiry,
        quantity=quantity
    )
    print_strategy_info(short_put)
    
    # 2. 跨式策略
    print("\n" + "=" * 70)
    print("2. 跨式策略（Straddle）")
    print("=" * 70)
    
    # 买入跨式
    long_straddle = manager.create_straddle(
        strike=current_price,
        expiry=expiry,
        quantity=quantity,
        long=True
    )
    print_strategy_info(long_straddle)
    print("\n策略说明: 同时买入相同执行价的看涨和看跌期权")
    print("适用场景: 预期市场将有大幅波动，但方向不确定")
    
    # 卖出跨式
    short_straddle = manager.create_straddle(
        strike=current_price,
        expiry=expiry,
        quantity=quantity,
        long=False
    )
    print_strategy_info(short_straddle)
    print("\n策略说明: 同时卖出相同执行价的看涨和看跌期权")
    print("适用场景: 预期市场将保持平稳，波动率较低")
    
    # 3. 宽跨式策略
    print("\n" + "=" * 70)
    print("3. 宽跨式策略（Strangle）")
    print("=" * 70)
    
    strangle = manager.create_strangle(
        call_strike=current_price + Decimal('2000'),
        put_strike=current_price - Decimal('2000'),
        expiry=expiry,
        quantity=quantity,
        long=True
    )
    print_strategy_info(strangle)
    print("\n策略说明: 买入不同执行价的看涨和看跌期权")
    print("适用场景: 预期市场将有较大波动，成本比跨式策略低")
    
    # 4. 铁鹰策略
    print("\n" + "=" * 70)
    print("4. 铁鹰策略（Iron Condor）")
    print("=" * 70)
    
    iron_condor = manager.create_iron_condor(
        strikes=[
            current_price - Decimal('3000'),  # 买入看跌
            current_price - Decimal('1500'),  # 卖出看跌
            current_price + Decimal('1500'),  # 卖出看涨
            current_price + Decimal('3000')   # 买入看涨
        ],
        expiry=expiry,
        quantity=quantity
    )
    print_strategy_info(iron_condor)
    print("\n策略说明: 4腿复合策略，在两侧设置价差")
    print("适用场景: 预期市场在一定区间内波动，收取权利金")
    
    # 5. 蝶式策略
    print("\n" + "=" * 70)
    print("5. 蝶式策略（Butterfly）")
    print("=" * 70)
    
    butterfly = manager.create_butterfly(
        center_strike=current_price,
        wing_width=Decimal('2000'),
        expiry=expiry,
        quantity=quantity
    )
    print_strategy_info(butterfly)
    print("\n策略说明: 3腿策略，中间执行价卖出2倍数量")
    print("适用场景: 预期市场价格将停留在中间执行价附近")
    
    # 6. 策略验证
    print("\n" + "=" * 70)
    print("6. 策略验证")
    print("=" * 70)
    
    strategies = [
        ("买入跨式", long_straddle),
        ("铁鹰策略", iron_condor),
        ("蝶式策略", butterfly)
    ]
    
    for name, strategy in strategies:
        result = manager.validate_strategy(strategy)
        print(f"\n{name}:")
        print(f"  有效性: {'✓ 有效' if result.is_valid else '✗ 无效'}")
        if result.errors:
            print(f"  错误: {', '.join(result.errors)}")
        if result.warnings:
            print(f"  警告: {', '.join(result.warnings)}")
        if result.is_valid and not result.warnings:
            print(f"  状态: 策略配置正确，可以执行")
    
    # 7. 策略统计
    print("\n" + "=" * 70)
    print("7. 策略统计")
    print("=" * 70)
    
    all_strategies = [
        long_call, short_put, long_straddle, short_straddle,
        strangle, iron_condor, butterfly
    ]
    
    print(f"\n总共创建策略数: {len(all_strategies)}")
    print(f"单腿策略: 2")
    print(f"双腿策略: 3 (跨式 x2, 宽跨式 x1)")
    print(f"三腿策略: 1 (蝶式)")
    print(f"四腿策略: 1 (铁鹰)")
    
    total_legs = sum(len(s.legs) for s in all_strategies)
    print(f"\n总期权腿数: {total_legs}")
    
    print("\n" + "=" * 70)
    print("示例完成！")
    print("=" * 70)


if __name__ == "__main__":
    main()
