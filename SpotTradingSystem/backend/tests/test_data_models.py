"""
Tests for core data models
"""
import pytest
from datetime import datetime
from core.data_models import (
    NewsItem, MarketData, Portfolio, Position, SentimentScore,
    ImpactAssessment, TradingDecision, OrderResult, TradingRecord,
    ActionType, SignalType, RiskLevel, OrderStatus, PriceRange,
    validate_price, validate_amount, validate_percentage, validate_confidence,
    generate_id, serialize_to_json, deserialize_from_json
)


class TestNewsItem:
    """Test NewsItem data model"""
    
    def test_create_news_item(self):
        """Test creating a valid news item"""
        news = NewsItem(
            id="test-id",
            title="Bitcoin Reaches New High",
            content="Bitcoin has reached a new all-time high today...",
            source="CoinDesk",
            published_at=datetime.now(),
            url="https://example.com/news"
        )
        
        assert news.title == "Bitcoin Reaches New High"
        assert news.source == "CoinDesk"
        assert news.sentiment_score is None
    
    def test_news_item_validation(self):
        """Test news item validation"""
        with pytest.raises(ValueError, match="Title cannot be empty"):
            NewsItem(
                id="test-id",
                title="",
                content="Content",
                source="Source",
                published_at=datetime.now(),
                url="https://example.com"
            )
        
        with pytest.raises(ValueError, match="Sentiment score must be between 0 and 100"):
            NewsItem(
                id="test-id",
                title="Title",
                content="Content",
                source="Source",
                published_at=datetime.now(),
                url="https://example.com",
                sentiment_score=150
            )
    
    def test_news_item_serialization(self):
        """Test news item serialization"""
        news = NewsItem(
            id="test-id",
            title="Test Title",
            content="Test Content",
            source="Test Source",
            published_at=datetime(2024, 1, 1, 12, 0, 0),
            url="https://example.com",
            sentiment_score=75.5
        )
        
        data = news.to_dict()
        assert data['title'] == "Test Title"
        assert data['sentiment_score'] == 75.5
        
        # Test deserialization
        news_restored = NewsItem.from_dict(data)
        assert news_restored.title == news.title
        assert news_restored.sentiment_score == news.sentiment_score


class TestMarketData:
    """Test MarketData data model"""
    
    def test_create_market_data(self):
        """Test creating valid market data"""
        market_data = MarketData(
            symbol="BTCUSDT",
            price=50000.0,
            volume=1000.0,
            timestamp=datetime.now(),
            source="binance"
        )
        
        assert market_data.symbol == "BTCUSDT"
        assert market_data.price == 50000.0
        assert market_data.volume == 1000.0
    
    def test_market_data_validation(self):
        """Test market data validation"""
        with pytest.raises(ValueError, match="Price must be positive"):
            MarketData(
                symbol="BTCUSDT",
                price=-100.0,
                volume=1000.0,
                timestamp=datetime.now(),
                source="binance"
            )
        
        with pytest.raises(ValueError, match="Volume cannot be negative"):
            MarketData(
                symbol="BTCUSDT",
                price=50000.0,
                volume=-100.0,
                timestamp=datetime.now(),
                source="binance"
            )


class TestPosition:
    """Test Position data model"""
    
    def test_create_position(self):
        """Test creating a valid position"""
        position = Position(
            symbol="BTCUSDT",
            amount=0.1,
            entry_price=50000.0,
            current_price=51000.0,
            pnl=100.0,
            entry_time=datetime.now()
        )
        
        assert position.symbol == "BTCUSDT"
        assert position.amount == 0.1
        assert position.pnl == 100.0
    
    def test_position_pnl_calculation(self):
        """Test PnL calculation"""
        position = Position(
            symbol="BTCUSDT",
            amount=0.1,
            entry_price=50000.0,
            current_price=51000.0,
            pnl=0.0,
            entry_time=datetime.now()
        )
        
        # Test long position PnL
        calculated_pnl = position.calculate_pnl()
        expected_pnl = (51000.0 - 50000.0) * 0.1  # 100.0
        assert calculated_pnl == expected_pnl
        
        # Test short position PnL
        position.amount = -0.1
        calculated_pnl = position.calculate_pnl()
        expected_pnl = (50000.0 - 51000.0) * 0.1  # -100.0
        assert calculated_pnl == expected_pnl
    
    def test_update_current_price(self):
        """Test updating current price"""
        position = Position(
            symbol="BTCUSDT",
            amount=0.1,
            entry_price=50000.0,
            current_price=50000.0,
            pnl=0.0,
            entry_time=datetime.now()
        )
        
        position.update_current_price(52000.0)
        assert position.current_price == 52000.0
        assert position.pnl == 200.0  # (52000 - 50000) * 0.1


class TestPortfolio:
    """Test Portfolio data model"""
    
    def test_create_portfolio(self):
        """Test creating a valid portfolio"""
        portfolio = Portfolio(
            btc_balance=1.0,
            usdt_balance=10000.0,
            total_value_usdt=60000.0,
            unrealized_pnl=500.0
        )
        
        assert portfolio.btc_balance == 1.0
        assert portfolio.usdt_balance == 10000.0
        assert len(portfolio.positions) == 0
    
    def test_portfolio_validation(self):
        """Test portfolio validation"""
        with pytest.raises(ValueError, match="BTC balance cannot be negative"):
            Portfolio(
                btc_balance=-1.0,
                usdt_balance=10000.0,
                total_value_usdt=60000.0,
                unrealized_pnl=500.0
            )
    
    def test_add_remove_position(self):
        """Test adding and removing positions"""
        portfolio = Portfolio(
            btc_balance=1.0,
            usdt_balance=10000.0,
            total_value_usdt=60000.0,
            unrealized_pnl=0.0
        )
        
        position = Position(
            symbol="BTCUSDT",
            amount=0.1,
            entry_price=50000.0,
            current_price=51000.0,
            pnl=100.0,
            entry_time=datetime.now()
        )
        
        portfolio.add_position(position)
        assert len(portfolio.positions) == 1
        assert portfolio.unrealized_pnl == 100.0
        
        portfolio.remove_position("BTCUSDT")
        assert len(portfolio.positions) == 0
        assert portfolio.unrealized_pnl == 0.0


class TestSentimentScore:
    """Test SentimentScore data model"""
    
    def test_create_sentiment_score(self):
        """Test creating valid sentiment score"""
        sentiment = SentimentScore(
            sentiment_value=75.5,
            confidence=0.85,
            key_factors=["positive news", "market rally"]
        )
        
        assert sentiment.sentiment_value == 75.5
        assert sentiment.confidence == 0.85
        assert len(sentiment.key_factors) == 2
    
    def test_sentiment_validation(self):
        """Test sentiment score validation"""
        with pytest.raises(ValueError, match="Sentiment value must be between 0 and 100"):
            SentimentScore(
                sentiment_value=150.0,
                confidence=0.85,
                key_factors=[]
            )
        
        with pytest.raises(ValueError, match="Confidence must be between 0 and 1"):
            SentimentScore(
                sentiment_value=75.0,
                confidence=1.5,
                key_factors=[]
            )


class TestTradingDecision:
    """Test TradingDecision data model"""
    
    def test_create_trading_decision(self):
        """Test creating valid trading decision"""
        price_range = PriceRange(min_price=49000.0, max_price=51000.0)
        decision = TradingDecision(
            action=ActionType.BUY,
            confidence=0.8,
            suggested_amount=0.1,
            price_range=price_range,
            reasoning="Strong bullish signals",
            risk_level=RiskLevel.MEDIUM
        )
        
        assert decision.action == ActionType.BUY
        assert decision.confidence == 0.8
        assert decision.risk_level == RiskLevel.MEDIUM
    
    def test_trading_decision_validation(self):
        """Test trading decision validation"""
        price_range = PriceRange(min_price=49000.0, max_price=51000.0)
        
        with pytest.raises(ValueError, match="Confidence must be between 0 and 1"):
            TradingDecision(
                action=ActionType.BUY,
                confidence=1.5,
                suggested_amount=0.1,
                price_range=price_range,
                reasoning="Test",
                risk_level=RiskLevel.LOW
            )


class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_validation_functions(self):
        """Test validation utility functions"""
        assert validate_price(100.0) is True
        assert validate_price(-100.0) is False
        assert validate_price(0.0) is False
        
        assert validate_amount(0.1) is True
        assert validate_amount(-0.1) is True
        assert validate_amount(0.0) is False
        
        assert validate_percentage(50.0) is True
        assert validate_percentage(150.0) is False
        assert validate_percentage(-10.0) is False
        
        assert validate_confidence(0.8) is True
        assert validate_confidence(1.5) is False
        assert validate_confidence(-0.1) is False
    
    def test_generate_id(self):
        """Test ID generation"""
        id1 = generate_id()
        id2 = generate_id()
        
        assert id1 != id2
        assert len(id1) > 0
        assert len(id2) > 0
    
    def test_serialization(self):
        """Test JSON serialization"""
        market_data = MarketData(
            symbol="BTCUSDT",
            price=50000.0,
            volume=1000.0,
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            source="binance"
        )
        
        json_str = serialize_to_json(market_data)
        assert "BTCUSDT" in json_str
        assert "50000" in json_str
        
        # Test deserialization
        restored_data = deserialize_from_json(json_str, MarketData)
        assert restored_data.symbol == market_data.symbol
        assert restored_data.price == market_data.price


if __name__ == "__main__":
    pytest.main([__file__])