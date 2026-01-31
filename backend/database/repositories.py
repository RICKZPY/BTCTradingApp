"""
Repository layer for database operations
Provides clean interface between data models and business logic
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, and_, or_
import uuid

from database.models import (
    NewsItem, TradingRecord, Position, Portfolio, SystemConfig,
    AlertLog, BacktestResult, MarketData, TechnicalIndicator,
    SentimentAnalysis, TradingDecision, RiskAssessment, AccountBalance
)
from core.data_models import (
    NewsItem as NewsItemData, MarketData as MarketDataData,
    Portfolio as PortfolioData, Position as PositionData,
    TradingRecord as TradingRecordData, SentimentScore,
    ImpactAssessment, TradingDecision as TradingDecisionData
)


class NewsRepository:
    """Repository for news-related operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_news_item(self, news_data: NewsItemData) -> NewsItem:
        """Create a new news item"""
        news_item = NewsItem(
            id=uuid.UUID(news_data.id) if news_data.id else uuid.uuid4(),
            title=news_data.title,
            content=news_data.content,
            source=news_data.source,
            published_at=news_data.published_at,
            url=news_data.url,
            sentiment_score=news_data.sentiment_score,
            impact_assessment=news_data.impact_assessment.to_dict() if news_data.impact_assessment else None
        )
        self.db.add(news_item)
        self.db.commit()
        self.db.refresh(news_item)
        return news_item
    
    def get_news_by_id(self, news_id: str) -> Optional[NewsItem]:
        """Get news item by ID"""
        return self.db.query(NewsItem).filter(NewsItem.id == uuid.UUID(news_id)).first()
    
    def get_recent_news(self, hours: int = 24, limit: int = 100) -> List[NewsItem]:
        """Get recent news items"""
        since = datetime.utcnow() - timedelta(hours=hours)
        return self.db.query(NewsItem)\
            .filter(NewsItem.published_at >= since)\
            .order_by(desc(NewsItem.published_at))\
            .limit(limit)\
            .all()
    
    def get_unprocessed_news(self, limit: int = 50) -> List[NewsItem]:
        """Get unprocessed news items for sentiment analysis"""
        return self.db.query(NewsItem)\
            .filter(NewsItem.processed == False)\
            .order_by(asc(NewsItem.published_at))\
            .limit(limit)\
            .all()
    
    def mark_news_processed(self, news_id: str):
        """Mark news item as processed"""
        self.db.query(NewsItem)\
            .filter(NewsItem.id == uuid.UUID(news_id))\
            .update({"processed": True})
        self.db.commit()
    
    def get_news_by_source(self, source: str, limit: int = 100) -> List[NewsItem]:
        """Get news items by source"""
        return self.db.query(NewsItem)\
            .filter(NewsItem.source == source)\
            .order_by(desc(NewsItem.published_at))\
            .limit(limit)\
            .all()


class TradingRepository:
    """Repository for trading-related operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_trading_record(self, trading_data: TradingRecordData) -> TradingRecord:
        """Create a new trading record"""
        trading_record = TradingRecord(
            id=uuid.UUID(trading_data.id) if trading_data.id else uuid.uuid4(),
            action=trading_data.action.value,
            amount=trading_data.amount,
            price=trading_data.price,
            timestamp=trading_data.timestamp,
            decision_reasoning=trading_data.decision_reasoning,
            sentiment_score=trading_data.sentiment_score,
            technical_signals=trading_data.technical_signals
        )
        self.db.add(trading_record)
        self.db.commit()
        self.db.refresh(trading_record)
        return trading_record
    
    def get_trading_record_by_id(self, record_id: str) -> Optional[TradingRecord]:
        """Get trading record by ID"""
        return self.db.query(TradingRecord).filter(TradingRecord.id == uuid.UUID(record_id)).first()
    
    def get_recent_trades(self, days: int = 30, limit: int = 100) -> List[TradingRecord]:
        """Get recent trading records"""
        since = datetime.utcnow() - timedelta(days=days)
        return self.db.query(TradingRecord)\
            .filter(TradingRecord.timestamp >= since)\
            .order_by(desc(TradingRecord.timestamp))\
            .limit(limit)\
            .all()
    
    def get_trades_by_status(self, status: str) -> List[TradingRecord]:
        """Get trading records by status"""
        return self.db.query(TradingRecord)\
            .filter(TradingRecord.status == status)\
            .order_by(desc(TradingRecord.timestamp))\
            .all()
    
    def update_trade_status(self, record_id: str, status: str, 
                           executed_amount: float = None, executed_price: float = None):
        """Update trading record status"""
        update_data = {"status": status}
        if executed_amount is not None:
            update_data["executed_amount"] = executed_amount
        if executed_price is not None:
            update_data["executed_price"] = executed_price
        
        self.db.query(TradingRecord)\
            .filter(TradingRecord.id == uuid.UUID(record_id))\
            .update(update_data)
        self.db.commit()
    
    def get_trading_performance(self, days: int = 30) -> Dict[str, Any]:
        """Get trading performance metrics"""
        since = datetime.utcnow() - timedelta(days=days)
        trades = self.db.query(TradingRecord)\
            .filter(and_(
                TradingRecord.timestamp >= since,
                TradingRecord.status == "FILLED"
            ))\
            .all()
        
        if not trades:
            return {"total_trades": 0, "total_pnl": 0, "win_rate": 0}
        
        total_trades = len(trades)
        buy_trades = [t for t in trades if t.action == "BUY"]
        sell_trades = [t for t in trades if t.action == "SELL"]
        
        # Simple PnL calculation (this would be more complex in reality)
        total_pnl = sum(t.executed_price * t.executed_amount for t in sell_trades) - \
                   sum(t.executed_price * t.executed_amount for t in buy_trades)
        
        winning_trades = len([t for t in trades if t.executed_price > t.price])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        return {
            "total_trades": total_trades,
            "total_pnl": total_pnl,
            "win_rate": win_rate,
            "buy_trades": len(buy_trades),
            "sell_trades": len(sell_trades)
        }


class PortfolioRepository:
    """Repository for portfolio-related operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_portfolio_snapshot(self, portfolio_data: PortfolioData) -> Portfolio:
        """Create a portfolio snapshot"""
        portfolio = Portfolio(
            btc_balance=portfolio_data.btc_balance,
            usdt_balance=portfolio_data.usdt_balance,
            total_value_usdt=portfolio_data.total_value_usdt,
            unrealized_pnl=portfolio_data.unrealized_pnl,
            timestamp=datetime.utcnow()
        )
        self.db.add(portfolio)
        self.db.commit()
        self.db.refresh(portfolio)
        return portfolio
    
    def get_latest_portfolio(self) -> Optional[Portfolio]:
        """Get the latest portfolio snapshot"""
        return self.db.query(Portfolio)\
            .order_by(desc(Portfolio.timestamp))\
            .first()
    
    def get_portfolio_history(self, days: int = 30) -> List[Portfolio]:
        """Get portfolio history"""
        since = datetime.utcnow() - timedelta(days=days)
        return self.db.query(Portfolio)\
            .filter(Portfolio.timestamp >= since)\
            .order_by(desc(Portfolio.timestamp))\
            .all()
    
    def create_position(self, position_data: PositionData) -> Position:
        """Create a new position"""
        position = Position(
            symbol=position_data.symbol,
            amount=position_data.amount,
            entry_price=position_data.entry_price,
            entry_time=position_data.entry_time,
            pnl=position_data.pnl
        )
        self.db.add(position)
        self.db.commit()
        self.db.refresh(position)
        return position
    
    def get_open_positions(self) -> List[Position]:
        """Get all open positions"""
        return self.db.query(Position)\
            .filter(Position.status == "OPEN")\
            .all()
    
    def close_position(self, position_id: str, exit_price: float, pnl: float):
        """Close a position"""
        self.db.query(Position)\
            .filter(Position.id == uuid.UUID(position_id))\
            .update({
                "exit_price": exit_price,
                "exit_time": datetime.utcnow(),
                "pnl": pnl,
                "status": "CLOSED"
            })
        self.db.commit()


class MarketDataRepository:
    """Repository for market data operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_market_data(self, market_data: MarketDataData) -> MarketData:
        """Create market data entry"""
        data = MarketData(
            symbol=market_data.symbol,
            price=market_data.price,
            volume=market_data.volume,
            timestamp=market_data.timestamp,
            source=market_data.source
        )
        self.db.add(data)
        self.db.commit()
        self.db.refresh(data)
        return data
    
    def get_latest_price(self, symbol: str) -> Optional[MarketData]:
        """Get latest price for symbol"""
        return self.db.query(MarketData)\
            .filter(MarketData.symbol == symbol)\
            .order_by(desc(MarketData.timestamp))\
            .first()
    
    def get_price_history(self, symbol: str, hours: int = 24) -> List[MarketData]:
        """Get price history for symbol"""
        since = datetime.utcnow() - timedelta(hours=hours)
        return self.db.query(MarketData)\
            .filter(and_(
                MarketData.symbol == symbol,
                MarketData.timestamp >= since
            ))\
            .order_by(asc(MarketData.timestamp))\
            .all()


class ConfigRepository:
    """Repository for system configuration"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_config(self, key: str) -> Optional[SystemConfig]:
        """Get configuration by key"""
        return self.db.query(SystemConfig).filter(SystemConfig.key == key).first()
    
    def set_config(self, key: str, value: str, description: str = None, is_encrypted: bool = False):
        """Set configuration value"""
        config = self.get_config(key)
        if config:
            config.value = value
            config.description = description
            config.is_encrypted = is_encrypted
        else:
            config = SystemConfig(
                key=key,
                value=value,
                description=description,
                is_encrypted=is_encrypted
            )
            self.db.add(config)
        
        self.db.commit()
        return config
    
    def get_all_configs(self) -> List[SystemConfig]:
        """Get all configurations"""
        return self.db.query(SystemConfig).all()


class AlertRepository:
    """Repository for system alerts"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_alert(self, alert_type: str, message: str, details: Dict[str, Any] = None) -> AlertLog:
        """Create a new alert"""
        alert = AlertLog(
            alert_type=alert_type,
            message=message,
            details=details
        )
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        return alert
    
    def get_unresolved_alerts(self) -> List[AlertLog]:
        """Get unresolved alerts"""
        return self.db.query(AlertLog)\
            .filter(AlertLog.resolved == False)\
            .order_by(desc(AlertLog.created_at))\
            .all()
    
    def resolve_alert(self, alert_id: str):
        """Mark alert as resolved"""
        self.db.query(AlertLog)\
            .filter(AlertLog.id == uuid.UUID(alert_id))\
            .update({
                "resolved": True,
                "resolved_at": datetime.utcnow()
            })
        self.db.commit()
    
    def get_recent_alerts(self, hours: int = 24) -> List[AlertLog]:
        """Get recent alerts"""
        since = datetime.utcnow() - timedelta(hours=hours)
        return self.db.query(AlertLog)\
            .filter(AlertLog.created_at >= since)\
            .order_by(desc(AlertLog.created_at))\
            .all()


# Repository factory for dependency injection
class RepositoryFactory:
    """Factory for creating repository instances"""
    
    def __init__(self, db: Session):
        self.db = db
    
    @property
    def news(self) -> NewsRepository:
        return NewsRepository(self.db)
    
    @property
    def trading(self) -> TradingRepository:
        return TradingRepository(self.db)
    
    @property
    def portfolio(self) -> PortfolioRepository:
        return PortfolioRepository(self.db)
    
    @property
    def market_data(self) -> MarketDataRepository:
        return MarketDataRepository(self.db)
    
    @property
    def config(self) -> ConfigRepository:
        return ConfigRepository(self.db)
    
    @property
    def alerts(self) -> AlertRepository:
        return AlertRepository(self.db)