"""
智能策略构建器
支持相对时间和相对价格的策略模板
"""
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
import logging

from ..core.models import (
    Strategy, StrategyLeg, StrategyType, OptionContract,
    ActionType, OptionType
)
from ..connectors.deribit_connector import DeribitConnector

logger = logging.getLogger(__name__)


class RelativeExpiry(str, Enum):
    """相对到期日"""
    T_PLUS_1 = "T+1"      # 明天
    T_PLUS_2 = "T+2"      # 后天
    T_PLUS_7 = "T+7"      # 一周后
    T_PLUS_14 = "T+14"    # 两周后
    T_PLUS_30 = "T+30"    # 一个月后
    T_PLUS_60 = "T+60"    # 两个月后
    T_PLUS_90 = "T+90"    # 三个月后


class RelativeStrike(str, Enum):
    """相对行权价"""
    ATM = "ATM"           # 平值
    ITM_1 = "ITM+1"       # 实值第1档
    ITM_2 = "ITM+2"       # 实值第2档
    ITM_3 = "ITM+3"       # 实值第3档
    OTM_1 = "OTM+1"       # 虚值第1档
    OTM_2 = "OTM+2"       # 虚值第2档
    OTM_3 = "OTM+3"       # 虚值第3档


class SmartStrategyLeg:
    """智能策略腿（使用相对参数）"""
    
    def __init__(
        self,
        option_type: OptionType,
        action: ActionType,
        quantity: int,
        relative_expiry: RelativeExpiry,
        relative_strike: RelativeStrike
    ):
        self.option_type = option_type
        self.action = action
        self.quantity = quantity
        self.relative_expiry = relative_expiry
        self.relative_strike = relative_strike
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "option_type": self.option_type.value,
            "action": self.action.value,
            "quantity": self.quantity,
            "relative_expiry": self.relative_expiry.value,
            "relative_strike": self.relative_strike.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SmartStrategyLeg':
        """从字典创建"""
        return cls(
            option_type=OptionType(data["option_type"]),
            action=ActionType(data["action"]),
            quantity=data["quantity"],
            relative_expiry=RelativeExpiry(data["relative_expiry"]),
            relative_strike=RelativeStrike(data["relative_strike"])
        )


class SmartStrategyTemplate:
    """智能策略模板"""
    
    def __init__(
        self,
        name: str,
        description: str,
        strategy_type: StrategyType,
        legs: List[SmartStrategyLeg]
    ):
        self.name = name
        self.description = description
        self.strategy_type = strategy_type
        self.legs = legs
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "strategy_type": self.strategy_type.value,
            "legs": [leg.to_dict() for leg in self.legs]
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SmartStrategyTemplate':
        """从字典创建"""
        return cls(
            name=data["name"],
            description=data["description"],
            strategy_type=StrategyType(data["strategy_type"]),
            legs=[SmartStrategyLeg.from_dict(leg) for leg in data["legs"]]
        )


class SmartStrategyBuilder:
    """智能策略构建器"""
    
    def __init__(self, connector: DeribitConnector):
        """
        初始化构建器
        
        Args:
            connector: Deribit连接器
        """
        self.connector = connector
    
    def _get_expiry_date(self, relative_expiry: RelativeExpiry) -> datetime:
        """
        计算实际到期日
        
        Args:
            relative_expiry: 相对到期日
            
        Returns:
            实际到期日期
        """
        days_map = {
            RelativeExpiry.T_PLUS_1: 1,
            RelativeExpiry.T_PLUS_2: 2,
            RelativeExpiry.T_PLUS_7: 7,
            RelativeExpiry.T_PLUS_14: 14,
            RelativeExpiry.T_PLUS_30: 30,
            RelativeExpiry.T_PLUS_60: 60,
            RelativeExpiry.T_PLUS_90: 90
        }
        
        days = days_map.get(relative_expiry, 7)
        return datetime.now() + timedelta(days=days)
    
    async def _find_closest_strike(
        self,
        current_price: Decimal,
        available_strikes: List[Decimal],
        relative_strike: RelativeStrike,
        option_type: OptionType
    ) -> Decimal:
        """
        找到最接近的行权价
        
        Args:
            current_price: 当前BTC价格
            available_strikes: 可用的行权价列表
            relative_strike: 相对行权价
            option_type: 期权类型
            
        Returns:
            实际行权价
        """
        if not available_strikes:
            return current_price
        
        # 排序行权价
        sorted_strikes = sorted(available_strikes)
        
        # 找到ATM（最接近当前价格的行权价）
        atm_strike = min(sorted_strikes, key=lambda x: abs(x - current_price))
        atm_index = sorted_strikes.index(atm_strike)
        
        # 根据相对行权价计算偏移
        offset_map = {
            RelativeStrike.ATM: 0,
            RelativeStrike.ITM_1: -1 if option_type == OptionType.CALL else 1,
            RelativeStrike.ITM_2: -2 if option_type == OptionType.CALL else 2,
            RelativeStrike.ITM_3: -3 if option_type == OptionType.CALL else 3,
            RelativeStrike.OTM_1: 1 if option_type == OptionType.CALL else -1,
            RelativeStrike.OTM_2: 2 if option_type == OptionType.CALL else -2,
            RelativeStrike.OTM_3: 3 if option_type == OptionType.CALL else -3
        }
        
        offset = offset_map.get(relative_strike, 0)
        target_index = atm_index + offset
        
        # 确保索引在有效范围内
        target_index = max(0, min(target_index, len(sorted_strikes) - 1))
        
        return sorted_strikes[target_index]
    
    async def build_strategy(
        self,
        template: SmartStrategyTemplate,
        underlying: str = "BTC"
    ) -> Strategy:
        """
        根据模板构建实际策略
        
        Args:
            template: 智能策略模板
            underlying: 标的资产
            
        Returns:
            实际策略对象
        """
        logger.info(f"构建策略: {template.name}")
        
        # 获取当前BTC价格
        current_price = await self.connector.get_current_price(underlying)
        logger.info(f"当前{underlying}价格: ${current_price}")
        
        # 构建策略腿
        strategy_legs = []
        
        for smart_leg in template.legs:
            # 计算实际到期日
            target_expiry = self._get_expiry_date(smart_leg.relative_expiry)
            
            # 获取可用的期权合约
            instruments = await self.connector.get_instruments(
                currency=underlying,
                kind="option"
            )
            
            # 筛选符合条件的合约
            matching_instruments = []
            for inst in instruments:
                inst_expiry = datetime.fromtimestamp(inst['expiration_timestamp'] / 1000)
                
                # 检查到期日是否接近（±3天）
                days_diff = abs((inst_expiry - target_expiry).days)
                if days_diff <= 3 and inst['option_type'] == smart_leg.option_type.value:
                    matching_instruments.append(inst)
            
            if not matching_instruments:
                logger.warning(f"未找到匹配的合约: {smart_leg.option_type.value}, {smart_leg.relative_expiry.value}")
                continue
            
            # 获取可用的行权价
            available_strikes = [Decimal(str(inst['strike'])) for inst in matching_instruments]
            
            # 找到目标行权价
            target_strike = await self._find_closest_strike(
                current_price=current_price,
                available_strikes=available_strikes,
                relative_strike=smart_leg.relative_strike,
                option_type=smart_leg.option_type
            )
            
            # 找到匹配的合约
            selected_instrument = None
            for inst in matching_instruments:
                if Decimal(str(inst['strike'])) == target_strike:
                    selected_instrument = inst
                    break
            
            if not selected_instrument:
                logger.warning(f"未找到行权价为 {target_strike} 的合约")
                continue
            
            # 获取合约详细信息
            instrument_name = selected_instrument['instrument_name']
            orderbook = await self.connector.get_orderbook(instrument_name)
            
            if not orderbook:
                logger.warning(f"无法获取 {instrument_name} 的orderbook")
                continue
            
            # 创建期权合约对象
            option_contract = OptionContract(
                instrument_name=instrument_name,
                underlying=underlying,
                option_type=smart_leg.option_type,
                strike_price=target_strike,
                expiration_date=datetime.fromtimestamp(selected_instrument['expiration_timestamp'] / 1000),
                current_price=Decimal(str(orderbook.get('mark_price', 0))),
                bid_price=Decimal(str(orderbook['best_bid_price'])) if orderbook.get('best_bid_price') else Decimal(0),
                ask_price=Decimal(str(orderbook['best_ask_price'])) if orderbook.get('best_ask_price') else Decimal(0),
                last_price=Decimal(str(orderbook.get('last_price', 0))),
                implied_volatility=orderbook.get('mark_iv', 0) / 100,
                delta=orderbook.get('greeks', {}).get('delta', 0),
                gamma=orderbook.get('greeks', {}).get('gamma', 0),
                theta=orderbook.get('greeks', {}).get('theta', 0),
                vega=orderbook.get('greeks', {}).get('vega', 0),
                rho=orderbook.get('greeks', {}).get('rho', 0),
                open_interest=orderbook.get('open_interest', 0),
                volume=orderbook.get('stats', {}).get('volume', 0),
                timestamp=datetime.now()
            )
            
            # 创建策略腿
            leg = StrategyLeg(
                option_contract=option_contract,
                action=smart_leg.action,
                quantity=smart_leg.quantity
            )
            
            strategy_legs.append(leg)
            
            logger.info(f"添加策略腿: {instrument_name}, {smart_leg.action.value}, 数量: {smart_leg.quantity}")
        
        # 创建策略
        strategy = Strategy(
            name=template.name,
            description=template.description,
            strategy_type=template.strategy_type,
            legs=strategy_legs
        )
        
        logger.info(f"策略构建完成: {strategy.name}, 共 {len(strategy_legs)} 腿")
        
        return strategy


# 预定义的策略模板
PREDEFINED_TEMPLATES = {
    "atm_call_weekly": SmartStrategyTemplate(
        name="ATM看涨周策略",
        description="买入ATM看涨期权，一周到期",
        strategy_type=StrategyType.SINGLE_LEG,
        legs=[
            SmartStrategyLeg(
                option_type=OptionType.CALL,
                action=ActionType.BUY,
                quantity=1,
                relative_expiry=RelativeExpiry.T_PLUS_7,
                relative_strike=RelativeStrike.ATM
            )
        ]
    ),
    
    "otm_straddle": SmartStrategyTemplate(
        name="OTM跨式策略",
        description="买入OTM看涨和看跌期权",
        strategy_type=StrategyType.STRANGLE,
        legs=[
            SmartStrategyLeg(
                option_type=OptionType.CALL,
                action=ActionType.BUY,
                quantity=1,
                relative_expiry=RelativeExpiry.T_PLUS_7,
                relative_strike=RelativeStrike.OTM_1
            ),
            SmartStrategyLeg(
                option_type=OptionType.PUT,
                action=ActionType.BUY,
                quantity=1,
                relative_expiry=RelativeExpiry.T_PLUS_7,
                relative_strike=RelativeStrike.OTM_1
            )
        ]
    ),
    
    "bull_call_spread": SmartStrategyTemplate(
        name="牛市看涨价差",
        description="买入ATM看涨，卖出OTM看涨",
        strategy_type=StrategyType.CUSTOM,
        legs=[
            SmartStrategyLeg(
                option_type=OptionType.CALL,
                action=ActionType.BUY,
                quantity=1,
                relative_expiry=RelativeExpiry.T_PLUS_14,
                relative_strike=RelativeStrike.ATM
            ),
            SmartStrategyLeg(
                option_type=OptionType.CALL,
                action=ActionType.SELL,
                quantity=1,
                relative_expiry=RelativeExpiry.T_PLUS_14,
                relative_strike=RelativeStrike.OTM_2
            )
        ]
    )
}
