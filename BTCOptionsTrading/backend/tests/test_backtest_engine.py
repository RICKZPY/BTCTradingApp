"""
回测引擎测试
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from src.backtest.backtest_engine import BacktestEngine
from src.strategy.strategy_manager import StrategyManager
from src.core.models import OptionType, OptionContract


@pytest.mark.asyncio
class TestBacktestEngine:
    """回测引擎测试类"""
    
    @pytest.fixture
    def backtest_engine(self):
        """创建回测引擎实例"""
        return BacktestEngine()
    
    @pytest.fixture
    def strategy_manager(self):
        """创建策略管理器实例"""
        return StrategyManager()
    
    @pytest.fixture
    def simple_strategy(self, strategy_manager):
        """创建简单的单腿策略"""
        expiry = datetime.now() + timedelta(days=30)
        return strategy_manager.create_single_leg_strategy(
            option_type=OptionType.CALL,
            action="buy",
            strike=Decimal("50000"),
            expiry=expiry,
            quantity=1
        )
    
    async def test_backtest_initialization(self, backtest_engine):
        """测试回测引擎初始化"""
        assert backtest_engine is not None
        assert backtest_engine.options_engine is not None
    
    async def test_run_backtest_basic(self, backtest_engine, simple_strategy):
        """测试基本回测执行"""
        start_date = datetime.now()
        end_date = start_date + timedelta(days=10)
        initial_capital = Decimal("10000")
        
        result = await backtest_engine.run_backtest(
            strategy=simple_strategy,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital
        )
        
        # 验证回测结果
        assert result is not None
        assert result.strategy_name == simple_strategy.name
        assert result.start_date == start_date
        assert result.end_date == end_date
        assert result.initial_capital == initial_capital
        assert result.final_capital >= 0
        assert len(result.trades) > 0
        assert len(result.daily_pnl) > 0
    
    async def test_simulate_option_expiry_call(self, backtest_engine):
        """测试看涨期权到期价值计算"""
        option = OptionContract(
            instrument_name="BTC-TEST-50000-C",
            underlying="BTC",
            option_type=OptionType.CALL,
            strike_price=Decimal("50000"),
            expiration_date=datetime.now(),
            current_price=Decimal("1000"),
            bid_price=Decimal("950"),
            ask_price=Decimal("1050"),
            last_price=Decimal("1000"),
            implied_volatility=0.8,
            delta=0.5,
            gamma=0.0001,
            theta=-10.0,
            vega=50.0,
            rho=5.0,
            open_interest=100,
            volume=10,
            timestamp=datetime.now()
        )
        
        # 标的价格高于执行价
        underlying_price = Decimal("52000")
        expiry_value = backtest_engine.simulate_option_expiry(option, underlying_price)
        assert expiry_value == Decimal("2000")  # 52000 - 50000
        
        # 标的价格低于执行价
        underlying_price = Decimal("48000")
        expiry_value = backtest_engine.simulate_option_expiry(option, underlying_price)
        assert expiry_value == Decimal("0")  # max(48000 - 50000, 0)
    
    async def test_simulate_option_expiry_put(self, backtest_engine):
        """测试看跌期权到期价值计算"""
        option = OptionContract(
            instrument_name="BTC-TEST-50000-P",
            underlying="BTC",
            option_type=OptionType.PUT,
            strike_price=Decimal("50000"),
            expiration_date=datetime.now(),
            current_price=Decimal("1000"),
            bid_price=Decimal("950"),
            ask_price=Decimal("1050"),
            last_price=Decimal("1000"),
            implied_volatility=0.8,
            delta=-0.5,
            gamma=0.0001,
            theta=-10.0,
            vega=50.0,
            rho=-5.0,
            open_interest=100,
            volume=10,
            timestamp=datetime.now()
        )
        
        # 标的价格低于执行价
        underlying_price = Decimal("48000")
        expiry_value = backtest_engine.simulate_option_expiry(option, underlying_price)
        assert expiry_value == Decimal("2000")  # 50000 - 48000
        
        # 标的价格高于执行价
        underlying_price = Decimal("52000")
        expiry_value = backtest_engine.simulate_option_expiry(option, underlying_price)
        assert expiry_value == Decimal("0")  # max(50000 - 52000, 0)
    
    async def test_calculate_time_decay(self, backtest_engine):
        """测试时间价值衰减计算"""
        option = OptionContract(
            instrument_name="BTC-TEST-50000-C",
            underlying="BTC",
            option_type=OptionType.CALL,
            strike_price=Decimal("50000"),
            expiration_date=datetime.now() + timedelta(days=30),
            current_price=Decimal("1000"),
            bid_price=Decimal("950"),
            ask_price=Decimal("1050"),
            last_price=Decimal("1000"),
            implied_volatility=0.8,
            delta=0.5,
            gamma=0.0001,
            theta=-10.0,  # 每日衰减10美元
            vega=50.0,
            rho=5.0,
            open_interest=100,
            volume=10,
            timestamp=datetime.now()
        )
        
        # 计算1天的时间衰减
        decay_1day = backtest_engine.calculate_time_decay(option, 1)
        assert decay_1day == Decimal("-10.0")
        
        # 计算5天的时间衰减
        decay_5days = backtest_engine.calculate_time_decay(option, 5)
        assert decay_5days == Decimal("-50.0")
    
    async def test_handle_early_exercise(self, backtest_engine):
        """测试提前行权逻辑"""
        # 深度实值期权，时间价值很小
        option = OptionContract(
            instrument_name="BTC-TEST-40000-C",
            underlying="BTC",
            option_type=OptionType.CALL,
            strike_price=Decimal("40000"),
            expiration_date=datetime.now() + timedelta(days=30),
            current_price=Decimal("10100"),  # 内在价值10000 + 时间价值100
            bid_price=Decimal("10050"),
            ask_price=Decimal("10150"),
            last_price=Decimal("10100"),
            implied_volatility=0.5,
            delta=0.95,
            gamma=0.00001,
            theta=-5.0,
            vega=10.0,
            rho=20.0,
            open_interest=50,
            volume=5,
            timestamp=datetime.now()
        )
        
        underlying_price = Decimal("50000")
        
        # 时间价值很小，应该考虑提前行权
        should_exercise = backtest_engine.handle_early_exercise(option, underlying_price)
        assert should_exercise is True
        
        # 虚值期权，不应该提前行权
        option.strike_price = Decimal("55000")
        option.current_price = Decimal("500")
        should_exercise = backtest_engine.handle_early_exercise(option, underlying_price)
        assert should_exercise is False
    
    async def test_backtest_result_metrics(self, backtest_engine, simple_strategy):
        """测试回测结果指标计算"""
        start_date = datetime.now()
        end_date = start_date + timedelta(days=5)
        initial_capital = Decimal("10000")
        
        result = await backtest_engine.run_backtest(
            strategy=simple_strategy,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital
        )
        
        # 验证绩效指标
        assert isinstance(result.total_return, float)
        assert isinstance(result.sharpe_ratio, float)
        assert isinstance(result.max_drawdown, float)
        assert isinstance(result.win_rate, float)
        
        # 验证指标范围
        assert -1.0 <= result.total_return <= 10.0  # 合理的收益率范围
        assert 0.0 <= result.win_rate <= 1.0  # 胜率在0-1之间
        assert 0.0 <= result.max_drawdown <= 1.0  # 回撤在0-1之间
    
    async def test_straddle_strategy_backtest(self, backtest_engine, strategy_manager):
        """测试跨式策略回测"""
        expiry = datetime.now() + timedelta(days=15)
        straddle = strategy_manager.create_straddle(
            strike=Decimal("50000"),
            expiry=expiry,
            quantity=1,
            long=True
        )
        
        start_date = datetime.now()
        end_date = start_date + timedelta(days=7)
        initial_capital = Decimal("20000")
        
        result = await backtest_engine.run_backtest(
            strategy=straddle,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital
        )
        
        # 验证跨式策略有两个腿
        assert len(straddle.legs) == 2
        
        # 验证回测结果
        assert result is not None
        assert result.strategy_name == straddle.name
        assert len(result.trades) >= 2  # 至少有开仓交易
    
    async def test_backtest_with_expiry(self, backtest_engine, strategy_manager):
        """测试包含期权到期的回测"""
        # 创建一个很快到期的策略
        expiry = datetime.now() + timedelta(days=3)
        strategy = strategy_manager.create_single_leg_strategy(
            option_type=OptionType.PUT,
            action="buy",
            strike=Decimal("50000"),
            expiry=expiry,
            quantity=1
        )
        
        start_date = datetime.now()
        end_date = start_date + timedelta(days=5)  # 超过到期日
        initial_capital = Decimal("10000")
        
        result = await backtest_engine.run_backtest(
            strategy=strategy,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital
        )
        
        # 验证有到期交易
        expire_trades = [t for t in result.trades if t.action == "expire"]
        assert len(expire_trades) > 0
