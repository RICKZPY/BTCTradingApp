"""
策略管理器实现
提供期权策略的创建、验证和管理功能
"""

from datetime import datetime
from decimal import Decimal
from typing import List
from uuid import uuid4

from src.core.interfaces import IStrategyManager
from src.core.models import (
    Strategy, StrategyLeg, StrategyType, OptionContract,
    OptionType, ActionType, ValidationResult
)
from src.config.logging_config import get_logger

logger = get_logger(__name__)


class StrategyManager(IStrategyManager):
    """策略管理器"""
    
    def __init__(self):
        """初始化策略管理器"""
        logger.info("Strategy manager initialized")
    
    def create_single_leg_strategy(
        self,
        option_type: OptionType,
        action: str,
        strike: Decimal,
        expiry: datetime,
        quantity: int
    ) -> Strategy:
        """
        创建单腿期权策略
        
        Args:
            option_type: 期权类型（看涨/看跌）
            action: 操作类型（买入/卖出）
            strike: 执行价格
            expiry: 到期日
            quantity: 数量
            
        Returns:
            Strategy对象
        """
        # 创建虚拟期权合约（实际应从市场数据获取）
        contract = self._create_dummy_contract(option_type, strike, expiry)
        
        # 创建策略腿
        leg = StrategyLeg(
            option_contract=contract,
            action=ActionType.BUY if action.lower() == "buy" else ActionType.SELL,
            quantity=quantity
        )
        
        # 创建策略
        strategy_name = f"{'Long' if action.lower() == 'buy' else 'Short'} {option_type.value.capitalize()}"
        
        strategy = Strategy(
            id=uuid4(),
            name=strategy_name,
            description=f"{strategy_name} at strike {strike}",
            strategy_type=StrategyType.SINGLE_LEG,
            legs=[leg],
            created_at=datetime.now()
        )
        
        logger.info(f"Created single leg strategy: {strategy_name}")
        return strategy
    
    def create_straddle(
        self,
        strike: Decimal,
        expiry: datetime,
        quantity: int,
        long: bool = True
    ) -> Strategy:
        """
        创建跨式策略（Straddle）
        同时买入/卖出相同执行价的看涨和看跌期权
        """
        call_contract = self._create_dummy_contract(OptionType.CALL, strike, expiry)
        put_contract = self._create_dummy_contract(OptionType.PUT, strike, expiry)
        
        action = ActionType.BUY if long else ActionType.SELL
        
        legs = [
            StrategyLeg(option_contract=call_contract, action=action, quantity=quantity),
            StrategyLeg(option_contract=put_contract, action=action, quantity=quantity)
        ]
        
        strategy_name = f"{'Long' if long else 'Short'} Straddle"
        
        strategy = Strategy(
            id=uuid4(),
            name=strategy_name,
            description=f"{strategy_name} at strike {strike}",
            strategy_type=StrategyType.STRADDLE,
            legs=legs,
            created_at=datetime.now()
        )
        
        logger.info(f"Created straddle strategy: {strategy_name}")
        return strategy
    
    def create_strangle(
        self,
        call_strike: Decimal,
        put_strike: Decimal,
        expiry: datetime,
        quantity: int,
        long: bool = True
    ) -> Strategy:
        """
        创建宽跨式策略（Strangle）
        买入/卖出不同执行价的看涨和看跌期权
        """
        call_contract = self._create_dummy_contract(OptionType.CALL, call_strike, expiry)
        put_contract = self._create_dummy_contract(OptionType.PUT, put_strike, expiry)
        
        action = ActionType.BUY if long else ActionType.SELL
        
        legs = [
            StrategyLeg(option_contract=call_contract, action=action, quantity=quantity),
            StrategyLeg(option_contract=put_contract, action=action, quantity=quantity)
        ]
        
        strategy_name = f"{'Long' if long else 'Short'} Strangle"
        
        strategy = Strategy(
            id=uuid4(),
            name=strategy_name,
            description=f"{strategy_name} with strikes {put_strike}/{call_strike}",
            strategy_type=StrategyType.STRANGLE,
            legs=legs,
            created_at=datetime.now()
        )
        
        logger.info(f"Created strangle strategy: {strategy_name}")
        return strategy
    
    def create_iron_condor(
        self,
        strikes: List[Decimal],
        expiry: datetime,
        quantity: int
    ) -> Strategy:
        """
        创建铁鹰策略（Iron Condor）
        需要4个执行价：[put_buy, put_sell, call_sell, call_buy]
        """
        if len(strikes) != 4:
            raise ValueError("Iron Condor requires 4 strikes")
        
        put_buy_strike, put_sell_strike, call_sell_strike, call_buy_strike = strikes
        
        legs = [
            StrategyLeg(
                option_contract=self._create_dummy_contract(OptionType.PUT, put_buy_strike, expiry),
                action=ActionType.BUY,
                quantity=quantity
            ),
            StrategyLeg(
                option_contract=self._create_dummy_contract(OptionType.PUT, put_sell_strike, expiry),
                action=ActionType.SELL,
                quantity=quantity
            ),
            StrategyLeg(
                option_contract=self._create_dummy_contract(OptionType.CALL, call_sell_strike, expiry),
                action=ActionType.SELL,
                quantity=quantity
            ),
            StrategyLeg(
                option_contract=self._create_dummy_contract(OptionType.CALL, call_buy_strike, expiry),
                action=ActionType.BUY,
                quantity=quantity
            )
        ]
        
        strategy = Strategy(
            id=uuid4(),
            name="Iron Condor",
            description=f"Iron Condor with strikes {strikes}",
            strategy_type=StrategyType.IRON_CONDOR,
            legs=legs,
            created_at=datetime.now()
        )
        
        logger.info("Created iron condor strategy")
        return strategy
    
    def create_butterfly(
        self,
        center_strike: Decimal,
        wing_width: Decimal,
        expiry: datetime,
        quantity: int
    ) -> Strategy:
        """
        创建蝶式策略（Butterfly）
        """
        lower_strike = center_strike - wing_width
        upper_strike = center_strike + wing_width
        
        legs = [
            StrategyLeg(
                option_contract=self._create_dummy_contract(OptionType.CALL, lower_strike, expiry),
                action=ActionType.BUY,
                quantity=quantity
            ),
            StrategyLeg(
                option_contract=self._create_dummy_contract(OptionType.CALL, center_strike, expiry),
                action=ActionType.SELL,
                quantity=quantity * 2
            ),
            StrategyLeg(
                option_contract=self._create_dummy_contract(OptionType.CALL, upper_strike, expiry),
                action=ActionType.BUY,
                quantity=quantity
            )
        ]
        
        strategy = Strategy(
            id=uuid4(),
            name="Butterfly",
            description=f"Butterfly centered at {center_strike}",
            strategy_type=StrategyType.BUTTERFLY,
            legs=legs,
            created_at=datetime.now()
        )
        
        logger.info("Created butterfly strategy")
        return strategy
    
    def validate_strategy(self, strategy: Strategy) -> ValidationResult:
        """
        验证策略配置
        """
        errors = []
        warnings = []
        
        # 检查策略是否有腿
        if not strategy.legs:
            errors.append("Strategy must have at least one leg")
        
        # 检查每个腿的数量
        for i, leg in enumerate(strategy.legs):
            if leg.quantity <= 0:
                errors.append(f"Leg {i+1}: Quantity must be positive")
        
        # 检查到期日
        for i, leg in enumerate(strategy.legs):
            if leg.option_contract.expiration_date < datetime.now():
                warnings.append(f"Leg {i+1}: Option has expired")
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings
        )
    
    def _create_dummy_contract(
        self,
        option_type: OptionType,
        strike: Decimal,
        expiry: datetime
    ) -> OptionContract:
        """创建虚拟期权合约（用于策略构建）"""
        instrument_name = f"BTC-{expiry.strftime('%d%b%y').upper()}-{int(strike)}-{option_type.value[0].upper()}"
        
        return OptionContract(
            instrument_name=instrument_name,
            underlying="BTC",
            option_type=option_type,
            strike_price=strike,
            expiration_date=expiry,
            current_price=Decimal("0"),  # 将在回测中更新
            bid_price=Decimal("0"),
            ask_price=Decimal("0"),
            last_price=Decimal("0"),
            implied_volatility=0.0,
            delta=0.0,
            gamma=0.0,
            theta=0.0,
            vega=0.0,
            rho=0.0,
            open_interest=0,
            volume=0,
            timestamp=datetime.now()
        )
