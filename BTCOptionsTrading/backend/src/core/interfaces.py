"""
核心接口定义
定义系统各组件之间的接口契约
"""

from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Optional, Any

from .models import (
    OptionContract, MarketData, HistoricalData, Strategy, StrategyLeg,
    Portfolio, Position, BacktestResult, Greeks, VolatilitySurface,
    TermStructure, MarketScenario, StressTestResult, RiskLimits,
    RiskAlert, ValidationResult, PortfolioGreeks, OptionType
)


class IDeribitConnector(ABC):
    """Deribit API连接器接口"""
    
    @abstractmethod
    async def authenticate(self, api_key: str, api_secret: str) -> bool:
        """认证API连接"""
        pass
    
    @abstractmethod
    async def get_options_chain(self, currency: str = "BTC") -> List[OptionContract]:
        """获取期权链数据"""
        pass
    
    @abstractmethod
    async def get_historical_data(
        self, 
        instrument: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[HistoricalData]:
        """获取历史数据"""
        pass
    
    @abstractmethod
    async def get_real_time_data(self, instruments: List[str]) -> Dict[str, MarketData]:
        """获取实时数据"""
        pass
    
    @abstractmethod
    async def get_volatility_surface(self, currency: str = "BTC") -> VolatilitySurface:
        """获取波动率曲面"""
        pass


class IOptionsEngine(ABC):
    """期权定价引擎接口"""
    
    @abstractmethod
    def black_scholes_price(
        self, 
        S: float, 
        K: float, 
        T: float, 
        r: float, 
        sigma: float, 
        option_type: OptionType
    ) -> float:
        """Black-Scholes期权定价"""
        pass
    
    @abstractmethod
    def calculate_greeks(
        self, 
        S: float, 
        K: float, 
        T: float, 
        r: float, 
        sigma: float, 
        option_type: OptionType
    ) -> Greeks:
        """计算希腊字母"""
        pass
    
    @abstractmethod
    def binomial_tree_price(
        self, 
        S: float, 
        K: float, 
        T: float, 
        r: float, 
        sigma: float, 
        steps: int, 
        option_type: OptionType
    ) -> float:
        """二叉树定价"""
        pass
    
    @abstractmethod
    def monte_carlo_price(
        self, 
        S: float, 
        K: float, 
        T: float, 
        r: float, 
        sigma: float, 
        simulations: int, 
        option_type: OptionType
    ) -> float:
        """蒙特卡洛定价"""
        pass
    
    @abstractmethod
    def implied_volatility(
        self, 
        market_price: float, 
        S: float, 
        K: float, 
        T: float, 
        r: float, 
        option_type: OptionType
    ) -> float:
        """隐含波动率计算"""
        pass


class IStrategyManager(ABC):
    """策略管理器接口"""
    
    @abstractmethod
    def create_single_leg_strategy(
        self, 
        option_type: OptionType, 
        action: str, 
        strike: Decimal, 
        expiry: datetime, 
        quantity: int
    ) -> Strategy:
        """创建单腿策略"""
        pass
    
    @abstractmethod
    def create_straddle(
        self, 
        strike: Decimal, 
        expiry: datetime, 
        quantity: int, 
        long: bool = True
    ) -> Strategy:
        """创建跨式策略"""
        pass
    
    @abstractmethod
    def create_strangle(
        self, 
        call_strike: Decimal, 
        put_strike: Decimal, 
        expiry: datetime, 
        quantity: int, 
        long: bool = True
    ) -> Strategy:
        """创建宽跨式策略"""
        pass
    
    @abstractmethod
    def create_iron_condor(
        self, 
        strikes: List[Decimal], 
        expiry: datetime, 
        quantity: int
    ) -> Strategy:
        """创建铁鹰策略"""
        pass
    
    @abstractmethod
    def create_butterfly(
        self, 
        center_strike: Decimal, 
        wing_width: Decimal, 
        expiry: datetime, 
        quantity: int
    ) -> Strategy:
        """创建蝶式策略"""
        pass
    
    @abstractmethod
    def validate_strategy(self, strategy: Strategy) -> ValidationResult:
        """验证策略"""
        pass


class IVolatilityAnalyzer(ABC):
    """波动率分析器接口"""
    
    @abstractmethod
    def calculate_historical_volatility(
        self, 
        prices: List[float], 
        window: int = 30
    ) -> float:
        """计算历史波动率"""
        pass
    
    @abstractmethod
    def build_volatility_surface(
        self, 
        options_data: List[OptionContract]
    ) -> VolatilitySurface:
        """构建波动率曲面"""
        pass
    
    @abstractmethod
    def calculate_term_structure(
        self, 
        options_data: List[OptionContract]
    ) -> TermStructure:
        """计算期限结构"""
        pass
    
    @abstractmethod
    def detect_volatility_anomalies(
        self, 
        historical_vol: float, 
        implied_vol: float, 
        threshold: float = 0.1
    ) -> bool:
        """检测波动率异常"""
        pass
    
    @abstractmethod
    def garch_forecast(
        self, 
        returns: List[float], 
        horizon: int = 30
    ) -> List[float]:
        """GARCH波动率预测"""
        pass


class IBacktestEngine(ABC):
    """回测引擎接口"""
    
    @abstractmethod
    async def run_backtest(
        self, 
        strategy: Strategy, 
        start_date: datetime, 
        end_date: datetime, 
        initial_capital: Decimal
    ) -> BacktestResult:
        """运行回测"""
        pass
    
    @abstractmethod
    def simulate_option_expiry(
        self, 
        option: OptionContract, 
        underlying_price: Decimal
    ) -> Decimal:
        """模拟期权到期"""
        pass
    
    @abstractmethod
    def calculate_time_decay(
        self, 
        option: OptionContract, 
        days_passed: int
    ) -> Decimal:
        """计算时间价值衰减"""
        pass
    
    @abstractmethod
    def handle_early_exercise(
        self, 
        option: OptionContract, 
        underlying_price: Decimal
    ) -> bool:
        """处理提前行权"""
        pass


class IRiskCalculator(ABC):
    """风险计算器接口"""
    
    @abstractmethod
    def calculate_portfolio_greeks(self, positions: List[Position]) -> PortfolioGreeks:
        """计算组合希腊字母"""
        pass
    
    @abstractmethod
    def calculate_var(
        self, 
        positions: List[Position], 
        confidence: float = 0.95, 
        horizon: int = 1
    ) -> Decimal:
        """计算风险价值(VaR)"""
        pass
    
    @abstractmethod
    def stress_test(
        self, 
        positions: List[Position], 
        scenarios: List[MarketScenario]
    ) -> List[StressTestResult]:
        """压力测试"""
        pass
    
    @abstractmethod
    def calculate_margin_requirement(self, positions: List[Position]) -> Decimal:
        """计算保证金需求"""
        pass
    
    @abstractmethod
    def check_risk_limits(
        self, 
        positions: List[Position], 
        limits: RiskLimits
    ) -> List[RiskAlert]:
        """检查风险限额"""
        pass


class IPortfolioTracker(ABC):
    """组合跟踪器接口"""
    
    @abstractmethod
    async def update_portfolio_value(self, portfolio: Portfolio) -> Portfolio:
        """更新组合价值"""
        pass
    
    @abstractmethod
    def track_position_greeks(self, position: Position) -> Position:
        """跟踪持仓希腊字母"""
        pass
    
    @abstractmethod
    def record_trade(self, portfolio: Portfolio, trade: Any) -> Portfolio:
        """记录交易"""
        pass
    
    @abstractmethod
    def generate_performance_report(self, portfolio: Portfolio) -> Dict[str, Any]:
        """生成绩效报告"""
        pass
    
    @abstractmethod
    def calculate_excess_return(
        self, 
        portfolio: Portfolio, 
        benchmark_return: float
    ) -> float:
        """计算超额收益"""
        pass


class IDataStorage(ABC):
    """数据存储接口"""
    
    @abstractmethod
    async def store_option_data(self, options: List[OptionContract]) -> bool:
        """存储期权数据"""
        pass
    
    @abstractmethod
    async def query_historical_data(
        self, 
        symbol: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[HistoricalData]:
        """查询历史数据"""
        pass
    
    @abstractmethod
    async def cache_calculation_result(self, key: str, result: Any) -> bool:
        """缓存计算结果"""
        pass
    
    @abstractmethod
    async def get_cached_result(self, key: str) -> Optional[Any]:
        """获取缓存结果"""
        pass
    
    @abstractmethod
    async def backup_data(self) -> bool:
        """备份数据"""
        pass
    
    @abstractmethod
    async def cleanup_expired_data(self) -> bool:
        """清理过期数据"""
        pass


class IConfigurationManager(ABC):
    """配置管理器接口"""
    
    @abstractmethod
    def store_api_credentials(self, api_key: str, api_secret: str) -> bool:
        """存储API凭证"""
        pass
    
    @abstractmethod
    def validate_pricing_parameters(self, params: Dict[str, Any]) -> ValidationResult:
        """验证定价参数"""
        pass
    
    @abstractmethod
    def hot_reload_config(self, config: Dict[str, Any]) -> bool:
        """热更新配置"""
        pass
    
    @abstractmethod
    def get_system_health(self) -> Dict[str, Any]:
        """获取系统健康状态"""
        pass
    
    @abstractmethod
    def log_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """记录错误日志"""
        pass