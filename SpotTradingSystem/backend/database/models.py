"""
SQLAlchemy ORM models for PostgreSQL database
"""
from sqlalchemy import Column, String, Float, DateTime, Text, Boolean, JSON, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from database.postgres import Base


class NewsItem(Base):
    """
    News items table
    """
    __tablename__ = "news_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    source = Column(String(100), nullable=False)
    published_at = Column(DateTime, nullable=False)
    url = Column(Text)
    sentiment_score = Column(Float)
    impact_assessment = Column(JSON)
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    sentiment_analysis = relationship("SentimentAnalysis", back_populates="news_item", uselist=False)


class TradingRecord(Base):
    """
    Trading records table
    """
    __tablename__ = "trading_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action = Column(String(10), nullable=False)  # BUY, SELL, HOLD
    symbol = Column(String(20), nullable=False, default="BTCUSDT")
    amount = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    decision_reasoning = Column(Text)
    sentiment_score = Column(Float)
    technical_signals = Column(JSON)
    order_id = Column(String(100))  # Binance order ID
    status = Column(String(20), default="PENDING")  # PENDING, FILLED, CANCELLED, FAILED
    executed_amount = Column(Float, default=0.0)
    executed_price = Column(Float, default=0.0)
    fees = Column(Float, default=0.0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    decision = relationship("TradingDecision", back_populates="trading_record", uselist=False)


class Position(Base):
    """
    Trading positions table
    """
    __tablename__ = "positions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String(20), nullable=False)
    amount = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    entry_time = Column(DateTime, nullable=False)
    exit_price = Column(Float)
    exit_time = Column(DateTime)
    pnl = Column(Float)
    status = Column(String(20), default="OPEN")  # OPEN, CLOSED
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class Portfolio(Base):
    """
    Portfolio status table
    """
    __tablename__ = "portfolio"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    btc_balance = Column(Float, default=0.0)
    usdt_balance = Column(Float, default=0.0)
    total_value_usdt = Column(Float, default=0.0)
    unrealized_pnl = Column(Float, default=0.0)
    realized_pnl = Column(Float, default=0.0)
    timestamp = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class SystemConfig(Base):
    """
    System configuration table
    """
    __tablename__ = "system_config"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String(100), nullable=False, unique=True)
    value = Column(Text, nullable=False)
    description = Column(Text)
    is_encrypted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class AlertLog(Base):
    """
    System alerts and notifications table
    """
    __tablename__ = "alert_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_type = Column(String(50), nullable=False)  # CRITICAL, WARNING, INFO
    message = Column(Text, nullable=False)
    details = Column(JSON)
    resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    resolved_at = Column(DateTime)


class MarketData(Base):
    """
    Market data table for storing price and volume information
    """
    __tablename__ = "market_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String(20), nullable=False)
    price = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    source = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=func.now())


class TechnicalIndicator(Base):
    """
    Technical indicators table
    """
    __tablename__ = "technical_indicators"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String(20), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    rsi = Column(Float)
    macd = Column(Float)
    macd_signal = Column(Float)
    macd_histogram = Column(Float)
    sma_20 = Column(Float)
    sma_50 = Column(Float)
    ema_12 = Column(Float)
    ema_26 = Column(Float)
    bollinger_upper = Column(Float)
    bollinger_middle = Column(Float)
    bollinger_lower = Column(Float)
    signal_strength = Column(Float)
    signal_type = Column(String(10))  # BUY, SELL, HOLD
    confidence = Column(Float)
    created_at = Column(DateTime, default=func.now())


class SentimentAnalysis(Base):
    """
    Sentiment analysis results table
    """
    __tablename__ = "sentiment_analysis"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    news_item_id = Column(UUID(as_uuid=True), ForeignKey('news_items.id'))
    sentiment_score = Column(Float, nullable=False)  # 0-100
    confidence = Column(Float, nullable=False)  # 0-1
    key_factors = Column(JSON)  # List of key factors
    short_term_impact = Column(Float)  # -1 to 1
    long_term_impact = Column(Float)  # -1 to 1
    impact_confidence = Column(Float)  # 0-1
    reasoning = Column(Text)
    created_at = Column(DateTime, default=func.now())
    
    # Relationship
    news_item = relationship("NewsItem", back_populates="sentiment_analysis")


class TradingDecision(Base):
    """
    Trading decisions table
    """
    __tablename__ = "trading_decisions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action = Column(String(10), nullable=False)  # BUY, SELL, HOLD
    confidence = Column(Float, nullable=False)
    suggested_amount = Column(Float, nullable=False)
    min_price = Column(Float, nullable=False)
    max_price = Column(Float, nullable=False)
    reasoning = Column(Text, nullable=False)
    risk_level = Column(String(20), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    sentiment_score = Column(Float)
    technical_signals = Column(JSON)
    executed = Column(Boolean, default=False)
    trading_record_id = Column(UUID(as_uuid=True), ForeignKey('trading_records.id'))
    created_at = Column(DateTime, default=func.now())
    
    # Relationship
    trading_record = relationship("TradingRecord", back_populates="decision")


class RiskAssessment(Base):
    """
    Risk assessment table
    """
    __tablename__ = "risk_assessments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trading_decision_id = Column(UUID(as_uuid=True), ForeignKey('trading_decisions.id'))
    risk_score = Column(Float, nullable=False)  # 0-100
    max_loss_potential = Column(Float, nullable=False)
    risk_factors = Column(JSON)  # List of risk factors
    recommended_position_size = Column(Float, nullable=False)
    approved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relationship
    trading_decision = relationship("TradingDecision")


class AccountBalance(Base):
    """
    Account balance snapshots table
    """
    __tablename__ = "account_balances"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    btc_balance = Column(Float, nullable=False, default=0.0)
    usdt_balance = Column(Float, nullable=False, default=0.0)
    btc_locked = Column(Float, default=0.0)
    usdt_locked = Column(Float, default=0.0)
    total_value_usdt = Column(Float, nullable=False, default=0.0)
    timestamp = Column(DateTime, nullable=False)
class BacktestResult(Base):
    """
    Backtest results table
    """
    __tablename__ = "backtest_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    strategy_name = Column(String(100), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    initial_capital = Column(Float, nullable=False)
    final_capital = Column(Float, nullable=False)
    total_return = Column(Float, nullable=False)
    sharpe_ratio = Column(Float)
    max_drawdown = Column(Float)
    win_rate = Column(Float)
    total_trades = Column(Integer)
    strategy_config = Column(JSON)
    performance_metrics = Column(JSON)
    created_at = Column(DateTime, default=func.now())
    """
    Backtest results table
    """
    __tablename__ = "backtest_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    strategy_name = Column(String(100), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    initial_capital = Column(Float, nullable=False)
    final_capital = Column(Float, nullable=False)
    total_return = Column(Float, nullable=False)
    sharpe_ratio = Column(Float)
    max_drawdown = Column(Float)
    win_rate = Column(Float)
    total_trades = Column(Integer)
    strategy_config = Column(JSON)
    performance_metrics = Column(JSON)
    created_at = Column(DateTime, default=func.now())