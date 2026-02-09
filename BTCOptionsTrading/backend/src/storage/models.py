"""
数据库ORM模型
定义SQLAlchemy数据库表结构
"""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, 
    ForeignKey, Text, Enum as SQLEnum, DECIMAL, Boolean
)
from sqlalchemy.orm import relationship
import uuid

from src.storage.database import Base
from src.core.models import OptionType as CoreOptionType, ActionType as CoreActionType


def generate_uuid():
    """生成UUID字符串"""
    return str(uuid.uuid4())


class OptionContractModel(Base):
    """期权合约表"""
    __tablename__ = "option_contracts"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    instrument_name = Column(String(50), unique=True, nullable=False, index=True)
    underlying = Column(String(10), nullable=False)
    option_type = Column(SQLEnum(CoreOptionType), nullable=False)
    strike_price = Column(DECIMAL(18, 2), nullable=False)
    expiration_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    strategy_legs = relationship("StrategyLegModel", back_populates="option_contract")


class StrategyModel(Base):
    """策略表"""
    __tablename__ = "strategies"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    strategy_type = Column(String(50), nullable=False)
    max_profit = Column(DECIMAL(18, 2))
    max_loss = Column(DECIMAL(18, 2))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    legs = relationship("StrategyLegModel", back_populates="strategy", cascade="all, delete-orphan")
    backtest_results = relationship("BacktestResultModel", back_populates="strategy")


class StrategyLegModel(Base):
    """策略腿表"""
    __tablename__ = "strategy_legs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    strategy_id = Column(String(36), ForeignKey("strategies.id"), nullable=False)
    option_contract_id = Column(String(36), ForeignKey("option_contracts.id"), nullable=False)
    action = Column(SQLEnum(CoreActionType), nullable=False)
    quantity = Column(Integer, nullable=False)
    leg_order = Column(Integer, nullable=False)
    
    # 关系
    strategy = relationship("StrategyModel", back_populates="legs")
    option_contract = relationship("OptionContractModel", back_populates="strategy_legs")


class BacktestResultModel(Base):
    """回测结果表"""
    __tablename__ = "backtest_results"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    strategy_id = Column(String(36), ForeignKey("strategies.id"), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    initial_capital = Column(DECIMAL(18, 2), nullable=False)
    final_capital = Column(DECIMAL(18, 2), nullable=False)
    total_return = Column(Float, nullable=False)
    sharpe_ratio = Column(Float)
    max_drawdown = Column(Float)
    win_rate = Column(Float)
    total_trades = Column(Integer)
    created_at = Column(DateTime, default=datetime.now)
    
    # 关系
    strategy = relationship("StrategyModel", back_populates="backtest_results")
    trades = relationship("TradeModel", back_populates="backtest_result", cascade="all, delete-orphan")
    daily_pnl = relationship("DailyPnLModel", back_populates="backtest_result", cascade="all, delete-orphan")


class TradeModel(Base):
    """交易记录表"""
    __tablename__ = "trades"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    backtest_id = Column(String(36), ForeignKey("backtest_results.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    action = Column(String(10), nullable=False)
    option_contract_id = Column(String(36), ForeignKey("option_contracts.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(DECIMAL(18, 8), nullable=False)
    pnl = Column(DECIMAL(18, 2))
    portfolio_value = Column(DECIMAL(18, 2))
    commission = Column(DECIMAL(18, 2), default=0)
    
    # 关系
    backtest_result = relationship("BacktestResultModel", back_populates="trades")


class DailyPnLModel(Base):
    """每日盈亏表"""
    __tablename__ = "daily_pnl"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    backtest_id = Column(String(36), ForeignKey("backtest_results.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    portfolio_value = Column(DECIMAL(18, 2), nullable=False)
    daily_pnl = Column(DECIMAL(18, 2), nullable=False)
    cumulative_pnl = Column(DECIMAL(18, 2), nullable=False)
    realized_pnl = Column(DECIMAL(18, 2), nullable=False)
    unrealized_pnl = Column(DECIMAL(18, 2), nullable=False)
    
    # 关系
    backtest_result = relationship("BacktestResultModel", back_populates="daily_pnl")


class OptionPriceHistoryModel(Base):
    """期权价格历史表"""
    __tablename__ = "option_price_history"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    option_contract_id = Column(String(36), ForeignKey("option_contracts.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    bid_price = Column(DECIMAL(18, 8), nullable=False)
    ask_price = Column(DECIMAL(18, 8), nullable=False)
    last_price = Column(DECIMAL(18, 8), nullable=False)
    implied_volatility = Column(Float)
    delta = Column(Float)
    gamma = Column(Float)
    theta = Column(Float)
    vega = Column(Float)
    rho = Column(Float)
    volume = Column(Integer)
    open_interest = Column(Integer)


class UnderlyingPriceHistoryModel(Base):
    """标的资产价格历史表"""
    __tablename__ = "underlying_price_history"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    symbol = Column(String(10), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    open_price = Column(DECIMAL(18, 2), nullable=False)
    high_price = Column(DECIMAL(18, 2), nullable=False)
    low_price = Column(DECIMAL(18, 2), nullable=False)
    close_price = Column(DECIMAL(18, 2), nullable=False)
    volume = Column(Integer)
    volatility_30d = Column(Float)
    volatility_60d = Column(Float)
    volatility_90d = Column(Float)
