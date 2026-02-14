"""
测试增强的策略验证功能
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from decimal import Decimal
from datetime import datetime, timedelta
from strategy.strategy_validator import StrategyValidator


def test_strangle_validation():
    """测试宽跨式策略验证"""
    print("\n=== 测试宽跨式策略验证 ===")
    
    validator = StrategyValidator(initial_capital=Decimal("100000"))
    
    # 测试1：正确的宽跨式配置
    print("\n1. 正确的宽跨式配置:")
    legs = [
        {
            "option_contract": {
                "strike_price": 46000,
                "option_type": "call",
                "expiration_date": (datetime.now() + timedelta(days=30)).isoformat(),
                "underlying": "BTC"
            },
            "action": "buy",
            "quantity": 1
        },
        {
            "option_contract": {
                "strike_price": 44000,
                "option_type": "put",
                "expiration_date": (datetime.now() + timedelta(days=30)).isoformat(),
                "underlying": "BTC"
            },
            "action": "buy",
            "quantity": 1
        }
    ]
    
    is_valid, errors, warnings = validator.validate_strategy("strangle", legs, "测试宽跨式")
    print(f"验证结果: {'通过' if is_valid else '失败'}")
    if errors:
        print("错误:")
        for error in errors:
            print(f"  - {error['message']}")
    if warnings:
        print("警告:")
        for warning in warnings:
            print(f"  - {warning['message']}")
    
    # 测试2：错误的宽跨式配置（看涨执行价低于看跌）
    print("\n2. 错误的宽跨式配置（看涨执行价低于看跌）:")
    legs[0]["option_contract"]["strike_price"] = 43000  # 看涨执行价低于看跌
    
    is_valid, errors, warnings = validator.validate_strategy("strangle", legs, "错误宽跨式")
    print(f"验证结果: {'通过' if is_valid else '失败'}")
    if errors:
        print("错误:")
        for error in errors:
            print(f"  - {error['message']}")


def test_iron_condor_validation():
    """测试铁鹰策略验证"""
    print("\n=== 测试铁鹰策略验证 ===")
    
    validator = StrategyValidator(initial_capital=Decimal("100000"))
    
    # 正确的铁鹰配置
    print("\n1. 正确的铁鹰配置:")
    legs = [
        {
            "option_contract": {
                "strike_price": 42000,
                "option_type": "put",
                "expiration_date": (datetime.now() + timedelta(days=30)).isoformat(),
                "underlying": "BTC"
            },
            "action": "buy",
            "quantity": 1
        },
        {
            "option_contract": {
                "strike_price": 43000,
                "option_type": "put",
                "expiration_date": (datetime.now() + timedelta(days=30)).isoformat(),
                "underlying": "BTC"
            },
            "action": "sell",
            "quantity": 1
        },
        {
            "option_contract": {
                "strike_price": 47000,
                "option_type": "call",
                "expiration_date": (datetime.now() + timedelta(days=30)).isoformat(),
                "underlying": "BTC"
            },
            "action": "sell",
            "quantity": 1
        },
        {
            "option_contract": {
                "strike_price": 48000,
                "option_type": "call",
                "expiration_date": (datetime.now() + timedelta(days=30)).isoformat(),
                "underlying": "BTC"
            },
            "action": "buy",
            "quantity": 1
        }
    ]
    
    is_valid, errors, warnings = validator.validate_strategy("iron_condor", legs, "测试铁鹰")
    print(f"验证结果: {'通过' if is_valid else '失败'}")
    if errors:
        print("错误:")
        for error in errors:
            print(f"  - {error['message']}")
    if warnings:
        print("警告:")
        for warning in warnings:
            print(f"  - {warning['message']}")


def test_butterfly_validation():
    """测试蝶式策略验证"""
    print("\n=== 测试蝶式策略验证 ===")
    
    validator = StrategyValidator(initial_capital=Decimal("100000"))
    
    # 正确的蝶式配置
    print("\n1. 正确的蝶式配置:")
    legs = [
        {
            "option_contract": {
                "strike_price": 43000,
                "option_type": "call",
                "expiration_date": (datetime.now() + timedelta(days=30)).isoformat(),
                "underlying": "BTC"
            },
            "action": "buy",
            "quantity": 1
        },
        {
            "option_contract": {
                "strike_price": 45000,
                "option_type": "call",
                "expiration_date": (datetime.now() + timedelta(days=30)).isoformat(),
                "underlying": "BTC"
            },
            "action": "sell",
            "quantity": 2
        },
        {
            "option_contract": {
                "strike_price": 47000,
                "option_type": "call",
                "expiration_date": (datetime.now() + timedelta(days=30)).isoformat(),
                "underlying": "BTC"
            },
            "action": "buy",
            "quantity": 1
        }
    ]
    
    is_valid, errors, warnings = validator.validate_strategy("butterfly", legs, "测试蝶式")
    print(f"验证结果: {'通过' if is_valid else '失败'}")
    if errors:
        print("错误:")
        for error in errors:
            print(f"  - {error['message']}")
    if warnings:
        print("警告:")
        for warning in warnings:
            print(f"  - {warning['message']}")


def test_real_time_validation():
    """测试实时验证功能"""
    print("\n=== 测试实时验证功能 ===")
    
    validator = StrategyValidator(initial_capital=Decimal("100000"))
    
    # 使用标的价格进行实时验证
    print("\n1. 带标的价格的实时验证:")
    legs = [
        {
            "option_contract": {
                "strike_price": 50000,  # 远离当前价格
                "option_type": "call",
                "expiration_date": (datetime.now() + timedelta(days=30)).isoformat(),
                "underlying": "BTC"
            },
            "action": "buy",
            "quantity": 1
        }
    ]
    
    spot_price = 45000
    is_valid, errors, warnings = validator.validate_real_time(
        "single_leg", legs, "测试实时验证", spot_price
    )
    print(f"验证结果: {'通过' if is_valid else '失败'}")
    print(f"标的价格: ${spot_price}")
    if errors:
        print("错误:")
        for error in errors:
            print(f"  - {error['message']}")
    if warnings:
        print("警告:")
        for warning in warnings:
            print(f"  - {warning['message']}")


def test_risk_threshold_check():
    """测试风险阈值检查"""
    print("\n=== 测试风险阈值检查 ===")
    
    validator = StrategyValidator(initial_capital=Decimal("10000"))  # 较小的初始资金
    
    # 高风险策略（大数量）
    print("\n1. 高风险策略（大数量）:")
    legs = [
        {
            "option_contract": {
                "strike_price": 45000,
                "option_type": "call",
                "expiration_date": (datetime.now() + timedelta(days=30)).isoformat(),
                "underlying": "BTC"
            },
            "action": "buy",
            "quantity": 10  # 大数量
        }
    ]
    
    is_valid, errors, warnings = validator.validate_strategy("single_leg", legs, "高风险策略")
    print(f"验证结果: {'通过' if is_valid else '失败'}")
    if errors:
        print("错误:")
        for error in errors:
            print(f"  - {error['message']}")
    if warnings:
        print("警告:")
        for warning in warnings:
            print(f"  - {warning['message']}")


def test_quantity_validation():
    """测试数量验证"""
    print("\n=== 测试数量验证 ===")
    
    validator = StrategyValidator(initial_capital=Decimal("100000"))
    
    # 测试不相等的数量
    print("\n1. 不相等的数量:")
    legs = [
        {
            "option_contract": {
                "strike_price": 45000,
                "option_type": "call",
                "expiration_date": (datetime.now() + timedelta(days=30)).isoformat(),
                "underlying": "BTC"
            },
            "action": "buy",
            "quantity": 2
        },
        {
            "option_contract": {
                "strike_price": 45000,
                "option_type": "put",
                "expiration_date": (datetime.now() + timedelta(days=30)).isoformat(),
                "underlying": "BTC"
            },
            "action": "buy",
            "quantity": 1
        }
    ]
    
    is_valid, errors, warnings = validator.validate_strategy("straddle", legs, "不等数量跨式")
    print(f"验证结果: {'通过' if is_valid else '失败'}")
    if errors:
        print("错误:")
        for error in errors:
            print(f"  - {error['message']}")
    if warnings:
        print("警告:")
        for warning in warnings:
            print(f"  - {warning['message']}")


if __name__ == "__main__":
    print("开始测试增强的策略验证功能...")
    
    test_strangle_validation()
    test_iron_condor_validation()
    test_butterfly_validation()
    test_real_time_validation()
    test_risk_threshold_check()
    test_quantity_validation()
    
    print("\n\n测试完成！")
