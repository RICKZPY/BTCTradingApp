"""
策略管理器测试
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from src.strategy.strategy_manager import StrategyManager
from src.core.models import OptionType, StrategyType


@pytest.fixture
def strategy_manager():
    """创建策略管理器实例"""
    return StrategyManager()


@pytest.fixture
def test_params():
    """测试参数"""
    return {
        'strike': Decimal('45000'),
        'expiry': datetime.now() + timedelta(days=30),
        'quantity': 1
    }


class TestSingleLegStrategies:
    """测试单腿策略"""
    
    def test_create_long_call(self, strategy_manager, test_params):
        """测试创建买入看涨期权策略"""
        strategy = strategy_manager.create_single_leg_strategy(
            option_type=OptionType.CALL,
            action='buy',
            strike=test_params['strike'],
            expiry=test_params['expiry'],
            quantity=test_params['quantity']
        )
        
        assert strategy is not None
        assert strategy.strategy_type == StrategyType.SINGLE_LEG
        assert len(strategy.legs) == 1
        assert strategy.legs[0].option_contract.option_type == OptionType.CALL
        assert 'Long Call' in strategy.name
    
    def test_create_short_put(self, strategy_manager, test_params):
        """测试创建卖出看跌期权策略"""
        strategy = strategy_manager.create_single_leg_strategy(
            option_type=OptionType.PUT,
            action='sell',
            strike=test_params['strike'],
            expiry=test_params['expiry'],
            quantity=test_params['quantity']
        )
        
        assert strategy is not None
        assert strategy.strategy_type == StrategyType.SINGLE_LEG
        assert len(strategy.legs) == 1
        assert strategy.legs[0].option_contract.option_type == OptionType.PUT
        assert 'Short Put' in strategy.name


class TestMultiLegStrategies:
    """测试多腿策略"""
    
    def test_create_long_straddle(self, strategy_manager, test_params):
        """测试创建买入跨式策略"""
        strategy = strategy_manager.create_straddle(
            strike=test_params['strike'],
            expiry=test_params['expiry'],
            quantity=test_params['quantity'],
            long=True
        )
        
        assert strategy is not None
        assert strategy.strategy_type == StrategyType.STRADDLE
        assert len(strategy.legs) == 2
        assert 'Long Straddle' in strategy.name
        
        # 验证包含看涨和看跌期权
        option_types = [leg.option_contract.option_type for leg in strategy.legs]
        assert OptionType.CALL in option_types
        assert OptionType.PUT in option_types
    
    def test_create_short_straddle(self, strategy_manager, test_params):
        """测试创建卖出跨式策略"""
        strategy = strategy_manager.create_straddle(
            strike=test_params['strike'],
            expiry=test_params['expiry'],
            quantity=test_params['quantity'],
            long=False
        )
        
        assert strategy is not None
        assert 'Short Straddle' in strategy.name
    
    def test_create_strangle(self, strategy_manager, test_params):
        """测试创建宽跨式策略"""
        call_strike = test_params['strike'] + Decimal('1000')
        put_strike = test_params['strike'] - Decimal('1000')
        
        strategy = strategy_manager.create_strangle(
            call_strike=call_strike,
            put_strike=put_strike,
            expiry=test_params['expiry'],
            quantity=test_params['quantity'],
            long=True
        )
        
        assert strategy is not None
        assert strategy.strategy_type == StrategyType.STRANGLE
        assert len(strategy.legs) == 2
        assert 'Strangle' in strategy.name
        
        # 验证执行价不同
        strikes = [leg.option_contract.strike_price for leg in strategy.legs]
        assert len(set(strikes)) == 2
    
    def test_create_iron_condor(self, strategy_manager, test_params):
        """测试创建铁鹰策略"""
        base_strike = test_params['strike']
        strikes = [
            base_strike - Decimal('2000'),  # put buy
            base_strike - Decimal('1000'),  # put sell
            base_strike + Decimal('1000'),  # call sell
            base_strike + Decimal('2000')   # call buy
        ]
        
        strategy = strategy_manager.create_iron_condor(
            strikes=strikes,
            expiry=test_params['expiry'],
            quantity=test_params['quantity']
        )
        
        assert strategy is not None
        assert strategy.strategy_type == StrategyType.IRON_CONDOR
        assert len(strategy.legs) == 4
        assert 'Iron Condor' in strategy.name
    
    def test_iron_condor_invalid_strikes(self, strategy_manager, test_params):
        """测试铁鹰策略执行价数量错误"""
        with pytest.raises(ValueError):
            strategy_manager.create_iron_condor(
                strikes=[Decimal('45000'), Decimal('46000')],  # 只有2个执行价
                expiry=test_params['expiry'],
                quantity=test_params['quantity']
            )
    
    def test_create_butterfly(self, strategy_manager, test_params):
        """测试创建蝶式策略"""
        strategy = strategy_manager.create_butterfly(
            center_strike=test_params['strike'],
            wing_width=Decimal('1000'),
            expiry=test_params['expiry'],
            quantity=test_params['quantity']
        )
        
        assert strategy is not None
        assert strategy.strategy_type == StrategyType.BUTTERFLY
        assert len(strategy.legs) == 3
        assert 'Butterfly' in strategy.name
        
        # 验证中间腿的数量是两倍
        assert strategy.legs[1].quantity == test_params['quantity'] * 2


class TestStrategyValidation:
    """测试策略验证"""
    
    def test_validate_valid_strategy(self, strategy_manager, test_params):
        """测试验证有效策略"""
        strategy = strategy_manager.create_straddle(
            strike=test_params['strike'],
            expiry=test_params['expiry'],
            quantity=test_params['quantity'],
            long=True
        )
        
        result = strategy_manager.validate_strategy(strategy)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_validate_strategy_no_legs(self, strategy_manager, test_params):
        """测试验证无腿策略"""
        from src.core.models import Strategy
        from uuid import uuid4
        
        strategy = Strategy(
            id=uuid4(),
            name="Empty Strategy",
            description="Test",
            strategy_type=StrategyType.SINGLE_LEG,
            legs=[],
            created_at=datetime.now()
        )
        
        result = strategy_manager.validate_strategy(strategy)
        
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert any('at least one leg' in error for error in result.errors)
    
    def test_validate_strategy_invalid_quantity(self, strategy_manager, test_params):
        """测试验证无效数量"""
        strategy = strategy_manager.create_straddle(
            strike=test_params['strike'],
            expiry=test_params['expiry'],
            quantity=test_params['quantity'],
            long=True
        )
        
        # 修改数量为无效值
        strategy.legs[0].quantity = 0
        
        result = strategy_manager.validate_strategy(strategy)
        
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert any('Quantity must be positive' in error for error in result.errors)
    
    def test_validate_expired_option(self, strategy_manager):
        """测试验证过期期权"""
        expired_date = datetime.now() - timedelta(days=1)
        
        strategy = strategy_manager.create_straddle(
            strike=Decimal('45000'),
            expiry=expired_date,
            quantity=1,
            long=True
        )
        
        result = strategy_manager.validate_strategy(strategy)
        
        # 过期期权应该产生警告
        assert len(result.warnings) > 0
        assert any('expired' in warning.lower() for warning in result.warnings)


class TestStrategyProperties:
    """测试策略属性"""
    
    def test_strategy_has_id(self, strategy_manager, test_params):
        """测试策略有唯一ID"""
        strategy1 = strategy_manager.create_straddle(
            strike=test_params['strike'],
            expiry=test_params['expiry'],
            quantity=test_params['quantity'],
            long=True
        )
        
        strategy2 = strategy_manager.create_straddle(
            strike=test_params['strike'],
            expiry=test_params['expiry'],
            quantity=test_params['quantity'],
            long=True
        )
        
        assert strategy1.id != strategy2.id
    
    def test_strategy_has_timestamp(self, strategy_manager, test_params):
        """测试策略有创建时间戳"""
        strategy = strategy_manager.create_straddle(
            strike=test_params['strike'],
            expiry=test_params['expiry'],
            quantity=test_params['quantity'],
            long=True
        )
        
        assert strategy.created_at is not None
        assert isinstance(strategy.created_at, datetime)
    
    def test_strategy_has_description(self, strategy_manager, test_params):
        """测试策略有描述"""
        strategy = strategy_manager.create_straddle(
            strike=test_params['strike'],
            expiry=test_params['expiry'],
            quantity=test_params['quantity'],
            long=True
        )
        
        assert strategy.description is not None
        assert len(strategy.description) > 0
        assert str(test_params['strike']) in strategy.description
