"""
回测引擎使用示例
演示如何使用回测引擎进行期权策略回测
"""

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal

from src.backtest.backtest_engine import BacktestEngine
from src.strategy.strategy_manager import StrategyManager
from src.core.models import OptionType


async def example_single_leg_backtest():
    """示例1: 单腿期权策略回测"""
    print("=" * 60)
    print("示例1: 单腿看涨期权策略回测")
    print("=" * 60)
    
    # 创建策略管理器和回测引擎
    strategy_manager = StrategyManager()
    backtest_engine = BacktestEngine()
    
    # 创建买入看涨期权策略
    expiry = datetime.now() + timedelta(days=30)
    strategy = strategy_manager.create_single_leg_strategy(
        option_type=OptionType.CALL,
        action="buy",
        strike=Decimal("50000"),
        expiry=expiry,
        quantity=1
    )
    
    print(f"\n策略: {strategy.name}")
    print(f"策略类型: {strategy.strategy_type.value}")
    print(f"腿数: {len(strategy.legs)}")
    
    # 设置回测参数
    start_date = datetime.now()
    end_date = start_date + timedelta(days=15)
    initial_capital = Decimal("10000")
    
    print(f"\n回测参数:")
    print(f"开始日期: {start_date.strftime('%Y-%m-%d')}")
    print(f"结束日期: {end_date.strftime('%Y-%m-%d')}")
    print(f"初始资金: ${initial_capital}")
    
    # 运行回测
    print("\n正在运行回测...")
    result = await backtest_engine.run_backtest(
        strategy=strategy,
        start_date=start_date,
        end_date=end_date,
        initial_capital=initial_capital
    )
    
    # 显示回测结果
    print("\n" + "=" * 60)
    print("回测结果")
    print("=" * 60)
    print(f"策略名称: {result.strategy_name}")
    print(f"初始资金: ${result.initial_capital}")
    print(f"最终资金: ${result.final_capital}")
    print(f"总收益率: {result.total_return:.2%}")
    print(f"夏普比率: {result.sharpe_ratio:.2f}")
    print(f"最大回撤: {result.max_drawdown:.2%}")
    print(f"胜率: {result.win_rate:.2%}")
    print(f"总交易次数: {result.total_trades}")
    print(f"盈利因子: {result.profit_factor:.2f}")
    
    # 显示交易记录
    print(f"\n交易记录 (共{len(result.trades)}笔):")
    for i, trade in enumerate(result.trades[:5], 1):  # 只显示前5笔
        print(f"{i}. {trade.timestamp.strftime('%Y-%m-%d')} | "
              f"{trade.action.value.upper()} | "
              f"{trade.option_contract.instrument_name} | "
              f"数量: {trade.quantity} | "
              f"价格: ${trade.price} | "
              f"盈亏: ${trade.pnl}")
    
    if len(result.trades) > 5:
        print(f"... 还有 {len(result.trades) - 5} 笔交易")


async def example_straddle_backtest():
    """示例2: 跨式策略回测"""
    print("\n\n" + "=" * 60)
    print("示例2: 跨式策略回测")
    print("=" * 60)
    
    strategy_manager = StrategyManager()
    backtest_engine = BacktestEngine()
    
    # 创建多头跨式策略
    expiry = datetime.now() + timedelta(days=30)
    strategy = strategy_manager.create_straddle(
        strike=Decimal("50000"),
        expiry=expiry,
        quantity=1,
        long=True
    )
    
    print(f"\n策略: {strategy.name}")
    print(f"策略类型: {strategy.strategy_type.value}")
    print(f"腿数: {len(strategy.legs)}")
    
    for i, leg in enumerate(strategy.legs, 1):
        print(f"  腿{i}: {leg.action.value.upper()} {leg.option_contract.option_type.value.upper()} "
              f"@ ${leg.option_contract.strike_price}")
    
    # 运行回测
    start_date = datetime.now()
    end_date = start_date + timedelta(days=20)
    initial_capital = Decimal("20000")
    
    print(f"\n回测参数:")
    print(f"回测期间: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
    print(f"初始资金: ${initial_capital}")
    
    print("\n正在运行回测...")
    result = await backtest_engine.run_backtest(
        strategy=strategy,
        start_date=start_date,
        end_date=end_date,
        initial_capital=initial_capital
    )
    
    # 显示结果
    print("\n" + "=" * 60)
    print("回测结果")
    print("=" * 60)
    print(f"总收益率: {result.total_return:.2%}")
    print(f"夏普比率: {result.sharpe_ratio:.2f}")
    print(f"最大回撤: {result.max_drawdown:.2%}")
    print(f"胜率: {result.win_rate:.2%}")
    print(f"盈利因子: {result.profit_factor:.2f}")


async def example_iron_condor_backtest():
    """示例3: 铁鹰策略回测"""
    print("\n\n" + "=" * 60)
    print("示例3: 铁鹰策略回测")
    print("=" * 60)
    
    strategy_manager = StrategyManager()
    backtest_engine = BacktestEngine()
    
    # 创建铁鹰策略
    expiry = datetime.now() + timedelta(days=30)
    strikes = [
        Decimal("45000"),  # 买入看跌
        Decimal("47000"),  # 卖出看跌
        Decimal("53000"),  # 卖出看涨
        Decimal("55000")   # 买入看涨
    ]
    
    strategy = strategy_manager.create_iron_condor(
        strikes=strikes,
        expiry=expiry,
        quantity=1
    )
    
    print(f"\n策略: {strategy.name}")
    print(f"策略类型: {strategy.strategy_type.value}")
    print(f"腿数: {len(strategy.legs)}")
    
    print("\n策略结构:")
    for i, leg in enumerate(strategy.legs, 1):
        print(f"  腿{i}: {leg.action.value.upper()} {leg.option_contract.option_type.value.upper()} "
              f"@ ${leg.option_contract.strike_price}")
    
    # 运行回测
    start_date = datetime.now()
    end_date = start_date + timedelta(days=25)
    initial_capital = Decimal("30000")
    
    print(f"\n回测参数:")
    print(f"回测期间: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
    print(f"初始资金: ${initial_capital}")
    
    print("\n正在运行回测...")
    result = await backtest_engine.run_backtest(
        strategy=strategy,
        start_date=start_date,
        end_date=end_date,
        initial_capital=initial_capital
    )
    
    # 显示结果
    print("\n" + "=" * 60)
    print("回测结果")
    print("=" * 60)
    print(f"初始资金: ${result.initial_capital}")
    print(f"最终资金: ${result.final_capital}")
    print(f"总收益: ${result.final_capital - result.initial_capital}")
    print(f"总收益率: {result.total_return:.2%}")
    print(f"夏普比率: {result.sharpe_ratio:.2f}")
    print(f"最大回撤: {result.max_drawdown:.2%}")
    print(f"胜率: {result.win_rate:.2%}")
    print(f"总交易次数: {result.total_trades}")


async def example_compare_strategies():
    """示例4: 比较不同策略的回测结果"""
    print("\n\n" + "=" * 60)
    print("示例4: 策略比较")
    print("=" * 60)
    
    strategy_manager = StrategyManager()
    backtest_engine = BacktestEngine()
    
    expiry = datetime.now() + timedelta(days=30)
    start_date = datetime.now()
    end_date = start_date + timedelta(days=20)
    initial_capital = Decimal("20000")
    
    # 创建多个策略
    strategies = [
        strategy_manager.create_single_leg_strategy(
            OptionType.CALL, "buy", Decimal("50000"), expiry, 1
        ),
        strategy_manager.create_straddle(
            Decimal("50000"), expiry, 1, long=True
        ),
        strategy_manager.create_strangle(
            Decimal("52000"), Decimal("48000"), expiry, 1, long=True
        )
    ]
    
    print("\n正在回测多个策略...")
    results = []
    
    for strategy in strategies:
        result = await backtest_engine.run_backtest(
            strategy=strategy,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital
        )
        results.append(result)
    
    # 比较结果
    print("\n" + "=" * 60)
    print("策略比较结果")
    print("=" * 60)
    print(f"{'策略名称':<20} {'收益率':<12} {'夏普比率':<12} {'最大回撤':<12} {'胜率':<10}")
    print("-" * 60)
    
    for result in results:
        print(f"{result.strategy_name:<20} "
              f"{result.total_return:>10.2%}  "
              f"{result.sharpe_ratio:>10.2f}  "
              f"{result.max_drawdown:>10.2%}  "
              f"{result.win_rate:>8.2%}")
    
    # 找出最佳策略
    best_return = max(results, key=lambda r: r.total_return)
    best_sharpe = max(results, key=lambda r: r.sharpe_ratio)
    
    print("\n最佳策略:")
    print(f"  最高收益率: {best_return.strategy_name} ({best_return.total_return:.2%})")
    print(f"  最高夏普比率: {best_sharpe.strategy_name} ({best_sharpe.sharpe_ratio:.2f})")


async def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("BTC期权回测引擎使用示例")
    print("=" * 60)
    
    try:
        # 运行各个示例
        await example_single_leg_backtest()
        await example_straddle_backtest()
        await example_iron_condor_backtest()
        await example_compare_strategies()
        
        print("\n\n" + "=" * 60)
        print("所有示例运行完成!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
