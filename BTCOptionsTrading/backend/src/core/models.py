"""
核心数据模型定义
定义期权交易系统中使用的所有数据结构
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4


class OptionType(str, Enum):
    """期权类型枚举"""
    CALL = "call"
    PUT = "put"


class ActionType(str, Enum):
    """交易动作类型"""
    BUY = "buy"
    SELL = "sell"


class TradeAction(str, Enum):
    """交易操作类型"""
    OPEN = "open"
    CLOSE = "close"
    EXPIRE = "expire"


class StrategyType(str, Enum):
    """策略类型枚举"""
    SINGLE_LEG = "single_leg"
    STRADDLE = "straddle"
    STRANGLE = "strangle"
    IRON_CONDOR = "iron_condor"
    BUTTERFLY = "butterfly"
    CUSTOM = "custom"


@dataclass
class Greeks:
    """期权希腊字母"""
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float
    
    def __post_init__(self):
        """验证希腊字母的合理范围"""
        if not -1 <= self.delta <= 1:
            raise ValueError("Delta must be between -1 and 1")
        if self.gamma < 0:
            raise ValueError("Gamma must be non-negative")


@dataclass
class OptionContract:
    """期权合约数据模型"""
    instrument_name: str
    underlying: str
    option_type: OptionType
    strike_price: Decimal
    expiration_date: datetime
    current_price: Decimal
    bid_price: Decimal
    ask_price: Decimal
    last_price: Decimal
    implied_volatility: float
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float
    open_interest: int
    volume: int
    timestamp: datetime
    
    @property
    def greeks(self) -> Greeks:
        """获取希腊字母对象"""
        return Greeks(
            delta=self.delta,
            gamma=self.gamma,
            theta=self.theta,
            vega=self.vega,
            rho=self.rho
        )
    
    @property
    def mid_price(self) -> Decimal:
        """计算中间价"""
        return (self.bid_price + self.ask_price) / 2
    
    @property
    def spread(self) -> Decimal:
        """计算买卖价差"""
        return self.ask_price - self.bid_price


@dataclass
class MarketData:
    """市场数据"""
    symbol: str
    price: Decimal
    bid: Decimal
    ask: Decimal
    volume: int
    timestamp: datetime
    
    @property
    def mid_price(self) -> Decimal:
        """中间价"""
        return (self.bid + self.ask) / 2


@dataclass
class HistoricalData:
    """历史数据"""
    timestamp: datetime
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: int
    implied_volatility: Optional[float] = None


@dataclass
class StrategyLeg:
    """策略腿"""
    option_contract: OptionContract
    action: ActionType
    quantity: int
    
    @property
    def notional_value(self) -> Decimal:
        """名义价值"""
        return self.option_contract.current_price * Decimal(abs(self.quantity))
    
    @property
    def is_long(self) -> bool:
        """是否为多头"""
        return self.action == ActionType.BUY and self.quantity > 0


@dataclass
class Strategy:
    """期权策略"""
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    strategy_type: StrategyType = StrategyType.CUSTOM
    legs: List[StrategyLeg] = field(default_factory=list)
    max_profit: Optional[Decimal] = None
    max_loss: Optional[Decimal] = None
    breakeven_points: List[Decimal] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def total_cost(self) -> Decimal:
        """策略总成本"""
        total = Decimal(0)
        for leg in self.legs:
            if leg.action == ActionType.BUY:
                total += leg.option_contract.current_price * Decimal(leg.quantity)
            else:
                total -= leg.option_contract.current_price * Decimal(leg.quantity)
        return total
    
    @property
    def net_delta(self) -> float:
        """策略净Delta"""
        total_delta = 0.0
        for leg in self.legs:
            multiplier = 1 if leg.action == ActionType.BUY else -1
            total_delta += leg.option_contract.delta * leg.quantity * multiplier
        return total_delta


@dataclass
class Position:
    """持仓"""
    option_contract: OptionContract
    quantity: int  # 正数为多头，负数为空头
    entry_price: Decimal
    entry_date: datetime
    current_value: Decimal
    unrealized_pnl: Decimal
    
    @property
    def is_long(self) -> bool:
        """是否为多头持仓"""
        return self.quantity > 0
    
    @property
    def notional_value(self) -> Decimal:
        """持仓名义价值"""
        return self.current_value * Decimal(abs(self.quantity))


@dataclass
class Portfolio:
    """投资组合"""
    id: UUID = field(default_factory=uuid4)
    positions: List[Position] = field(default_factory=list)
    cash_balance: Decimal = Decimal(0)
    total_value: Decimal = Decimal(0)
    total_delta: float = 0.0
    total_gamma: float = 0.0
    total_theta: float = 0.0
    total_vega: float = 0.0
    margin_used: Decimal = Decimal(0)
    margin_available: Decimal = Decimal(0)
    last_updated: datetime = field(default_factory=datetime.now)
    
    def update_portfolio_greeks(self):
        """更新组合希腊字母"""
        self.total_delta = sum(pos.option_contract.delta * pos.quantity for pos in self.positions)
        self.total_gamma = sum(pos.option_contract.gamma * pos.quantity for pos in self.positions)
        self.total_theta = sum(pos.option_contract.theta * pos.quantity for pos in self.positions)
        self.total_vega = sum(pos.option_contract.vega * pos.quantity for pos in self.positions)
    
    @property
    def total_unrealized_pnl(self) -> Decimal:
        """总未实现盈亏"""
        return sum(pos.unrealized_pnl for pos in self.positions)


@dataclass
class Trade:
    """交易记录"""
    timestamp: datetime
    action: TradeAction
    option_contract: OptionContract
    quantity: int
    price: Decimal
    pnl: Decimal
    portfolio_value: Decimal
    id: UUID = field(default_factory=uuid4)
    commission: Decimal = Decimal(0)
    
    @property
    def trade_value(self) -> Decimal:
        """交易价值"""
        return self.price * Decimal(abs(self.quantity))


@dataclass
class DailyPnL:
    """每日盈亏"""
    date: datetime
    portfolio_value: Decimal
    daily_pnl: Decimal
    cumulative_pnl: Decimal
    realized_pnl: Decimal
    unrealized_pnl: Decimal


@dataclass
class BacktestResult:
    """回测结果"""
    strategy_name: str
    start_date: datetime
    end_date: datetime
    initial_capital: Decimal
    final_capital: Decimal
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    id: UUID = field(default_factory=uuid4)
    trades: List[Trade] = field(default_factory=list)
    daily_pnl: List[DailyPnL] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def profit_factor(self) -> float:
        """盈利因子"""
        winning_trades = [t for t in self.trades if t.pnl > 0]
        losing_trades = [t for t in self.trades if t.pnl < 0]
        
        if not losing_trades:
            return float('inf') if winning_trades else 0.0
        
        gross_profit = sum(float(t.pnl) for t in winning_trades)
        gross_loss = abs(sum(float(t.pnl) for t in losing_trades))
        
        return gross_profit / gross_loss if gross_loss > 0 else 0.0


@dataclass
class VolatilitySurface:
    """波动率曲面"""
    strikes: List[Decimal]
    expiries: List[datetime]
    volatilities: List[List[float]]  # 2D list of implied volatilities
    timestamp: datetime = field(default_factory=datetime.now)
    
    def interpolate_volatility(self, strike: Decimal, expiry: datetime) -> float:
        """插值计算指定执行价和到期日的波动率"""
        # 简化实现，实际应使用更复杂的插值方法
        # 这里返回平均波动率作为占位符
        if self.volatilities:
            flat = [v for row in self.volatilities for v in row]
            return sum(flat) / len(flat) if flat else 0.0
        return 0.0


@dataclass
class TermStructure:
    """期限结构"""
    expiries: List[datetime]
    volatilities: List[float]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class MarketScenario:
    """市场情景"""
    name: str
    underlying_change: float  # 标的价格变化百分比
    volatility_change: float  # 波动率绝对变化
    time_decay_days: int      # 时间衰减天数


@dataclass
class PortfolioGreeks:
    """组合希腊字母"""
    total_delta: float
    total_gamma: float
    total_theta: float
    total_vega: float
    total_rho: float


@dataclass
class StressTestResult:
    """压力测试结果"""
    scenario: MarketScenario
    portfolio_value_change: Decimal
    pnl: Decimal
    new_greeks: PortfolioGreeks


@dataclass
class RiskLimits:
    """风险限额"""
    max_delta: float
    max_gamma: float
    max_vega: float
    max_portfolio_value: Decimal
    max_single_position_size: Decimal


@dataclass
class RiskAlert:
    """风险警报"""
    alert_type: str
    message: str
    severity: str  # "low", "medium", "high", "critical"
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)