"""
Core data structures for Bitcoin Trading System
Implements the data classes defined in the design document with validation and serialization
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any, Union
from enum import Enum
import json
from decimal import Decimal
import uuid


class ActionType(Enum):
    """Trading action types"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class SignalType(Enum):
    """Technical signal types"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class RiskLevel(Enum):
    """Risk level classifications"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class OrderStatus(Enum):
    """Order execution status"""
    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class PriceType(Enum):
    """Order price types"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"


@dataclass
class NewsItem:
    """News item data structure"""
    id: str
    title: str
    content: str
    source: str
    published_at: datetime
    url: str
    sentiment_score: Optional[float] = None
    impact_assessment: Optional['ImpactAssessment'] = None
    
    def __post_init__(self):
        """Validate data after initialization"""
        if not self.title.strip():
            raise ValueError("Title cannot be empty")
        if not self.content.strip():
            raise ValueError("Content cannot be empty")
        if not self.source.strip():
            raise ValueError("Source cannot be empty")
        if self.sentiment_score is not None:
            if not 0 <= self.sentiment_score <= 100:
                raise ValueError("Sentiment score must be between 0 and 100")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'source': self.source,
            'published_at': self.published_at.isoformat(),
            'url': self.url,
            'sentiment_score': self.sentiment_score,
            'impact_assessment': self.impact_assessment.to_dict() if self.impact_assessment else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NewsItem':
        """Create instance from dictionary"""
        impact_assessment = None
        if data.get('impact_assessment'):
            impact_assessment = ImpactAssessment.from_dict(data['impact_assessment'])
        
        return cls(
            id=data['id'],
            title=data['title'],
            content=data['content'],
            source=data['source'],
            published_at=datetime.fromisoformat(data['published_at']),
            url=data['url'],
            sentiment_score=data.get('sentiment_score'),
            impact_assessment=impact_assessment
        )


@dataclass
class MarketData:
    """Market data structure"""
    symbol: str
    price: float
    volume: float
    timestamp: datetime
    source: str
    
    def __post_init__(self):
        """Validate data after initialization"""
        if not self.symbol.strip():
            raise ValueError("Symbol cannot be empty")
        if self.price <= 0:
            raise ValueError("Price must be positive")
        if self.volume < 0:
            raise ValueError("Volume cannot be negative")
        if not self.source.strip():
            raise ValueError("Source cannot be empty")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'symbol': self.symbol,
            'price': self.price,
            'volume': self.volume,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MarketData':
        """Create instance from dictionary"""
        return cls(
            symbol=data['symbol'],
            price=data['price'],
            volume=data['volume'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            source=data['source']
        )


@dataclass
class Position:
    """Trading position data structure"""
    symbol: str
    amount: float
    entry_price: float
    current_price: float
    pnl: float
    entry_time: datetime
    
    def __post_init__(self):
        """Validate data after initialization"""
        if not self.symbol.strip():
            raise ValueError("Symbol cannot be empty")
        if self.amount == 0:
            raise ValueError("Amount cannot be zero")
        if self.entry_price <= 0:
            raise ValueError("Entry price must be positive")
        if self.current_price <= 0:
            raise ValueError("Current price must be positive")
    
    def calculate_pnl(self) -> float:
        """Calculate profit/loss for the position"""
        if self.amount > 0:  # Long position
            return (self.current_price - self.entry_price) * self.amount
        else:  # Short position
            return (self.entry_price - self.current_price) * abs(self.amount)
    
    def update_current_price(self, new_price: float):
        """Update current price and recalculate PnL"""
        if new_price <= 0:
            raise ValueError("Price must be positive")
        self.current_price = new_price
        self.pnl = self.calculate_pnl()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'symbol': self.symbol,
            'amount': self.amount,
            'entry_price': self.entry_price,
            'current_price': self.current_price,
            'pnl': self.pnl,
            'entry_time': self.entry_time.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Position':
        """Create instance from dictionary"""
        return cls(
            symbol=data['symbol'],
            amount=data['amount'],
            entry_price=data['entry_price'],
            current_price=data['current_price'],
            pnl=data['pnl'],
            entry_time=datetime.fromisoformat(data['entry_time'])
        )


@dataclass
class Portfolio:
    """Portfolio data structure"""
    btc_balance: float
    usdt_balance: float
    total_value_usdt: float
    unrealized_pnl: float
    positions: List[Position] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate data after initialization"""
        if self.btc_balance < 0:
            raise ValueError("BTC balance cannot be negative")
        if self.usdt_balance < 0:
            raise ValueError("USDT balance cannot be negative")
        if self.total_value_usdt < 0:
            raise ValueError("Total value cannot be negative")
    
    def add_position(self, position: Position):
        """Add a position to the portfolio"""
        self.positions.append(position)
        self.update_unrealized_pnl()
    
    def remove_position(self, symbol: str):
        """Remove a position from the portfolio"""
        self.positions = [p for p in self.positions if p.symbol != symbol]
        self.update_unrealized_pnl()
    
    def update_unrealized_pnl(self):
        """Update unrealized PnL based on current positions"""
        self.unrealized_pnl = sum(pos.pnl for pos in self.positions)
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get position by symbol"""
        for position in self.positions:
            if position.symbol == symbol:
                return position
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'btc_balance': self.btc_balance,
            'usdt_balance': self.usdt_balance,
            'total_value_usdt': self.total_value_usdt,
            'unrealized_pnl': self.unrealized_pnl,
            'positions': [pos.to_dict() for pos in self.positions]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Portfolio':
        """Create instance from dictionary"""
        positions = [Position.from_dict(pos_data) for pos_data in data.get('positions', [])]
        return cls(
            btc_balance=data['btc_balance'],
            usdt_balance=data['usdt_balance'],
            total_value_usdt=data['total_value_usdt'],
            unrealized_pnl=data['unrealized_pnl'],
            positions=positions
        )


@dataclass
class SentimentScore:
    """Sentiment analysis result"""
    sentiment_value: float  # 0-100
    confidence: float
    key_factors: List[str]
    
    def __post_init__(self):
        """Validate data after initialization"""
        if not 0 <= self.sentiment_value <= 100:
            raise ValueError("Sentiment value must be between 0 and 100")
        if not 0 <= self.confidence <= 1:
            raise ValueError("Confidence must be between 0 and 1")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'sentiment_value': self.sentiment_value,
            'confidence': self.confidence,
            'key_factors': self.key_factors
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SentimentScore':
        """Create instance from dictionary"""
        return cls(
            sentiment_value=data['sentiment_value'],
            confidence=data['confidence'],
            key_factors=data['key_factors']
        )


@dataclass
class ImpactAssessment:
    """Impact assessment for news items"""
    short_term_impact: float  # -1 to 1 (negative to positive)
    long_term_impact: float
    impact_confidence: float
    reasoning: str
    
    def __post_init__(self):
        """Validate data after initialization"""
        if not -1 <= self.short_term_impact <= 1:
            raise ValueError("Short term impact must be between -1 and 1")
        if not -1 <= self.long_term_impact <= 1:
            raise ValueError("Long term impact must be between -1 and 1")
        if not 0 <= self.impact_confidence <= 1:
            raise ValueError("Impact confidence must be between 0 and 1")
        if not self.reasoning.strip():
            raise ValueError("Reasoning cannot be empty")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'short_term_impact': self.short_term_impact,
            'long_term_impact': self.long_term_impact,
            'impact_confidence': self.impact_confidence,
            'reasoning': self.reasoning
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ImpactAssessment':
        """Create instance from dictionary"""
        return cls(
            short_term_impact=data['short_term_impact'],
            long_term_impact=data['long_term_impact'],
            impact_confidence=data['impact_confidence'],
            reasoning=data['reasoning']
        )


@dataclass
class TechnicalSignal:
    """Technical analysis signal"""
    signal_strength: float  # -1 to 1
    signal_type: SignalType
    confidence: float
    contributing_indicators: List[str]
    
    def __post_init__(self):
        """Validate data after initialization"""
        if not -1 <= self.signal_strength <= 1:
            raise ValueError("Signal strength must be between -1 and 1")
        if not 0 <= self.confidence <= 1:
            raise ValueError("Confidence must be between 0 and 1")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'signal_strength': self.signal_strength,
            'signal_type': self.signal_type.value,
            'confidence': self.confidence,
            'contributing_indicators': self.contributing_indicators
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TechnicalSignal':
        """Create instance from dictionary"""
        return cls(
            signal_strength=data['signal_strength'],
            signal_type=SignalType(data['signal_type']),
            confidence=data['confidence'],
            contributing_indicators=data['contributing_indicators']
        )


@dataclass
class PriceRange:
    """Price range for trading decisions"""
    min_price: float
    max_price: float
    
    def __post_init__(self):
        """Validate data after initialization"""
        if self.min_price <= 0:
            raise ValueError("Min price must be positive")
        if self.max_price <= 0:
            raise ValueError("Max price must be positive")
        if self.min_price > self.max_price:
            raise ValueError("Min price cannot be greater than max price")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'min_price': self.min_price,
            'max_price': self.max_price
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PriceRange':
        """Create instance from dictionary"""
        return cls(
            min_price=data['min_price'],
            max_price=data['max_price']
        )


@dataclass
class TradingDecision:
    """Trading decision data structure"""
    action: ActionType
    confidence: float
    suggested_amount: float
    price_range: PriceRange
    reasoning: str
    risk_level: RiskLevel
    
    def __post_init__(self):
        """Validate data after initialization"""
        if not 0 <= self.confidence <= 1:
            raise ValueError("Confidence must be between 0 and 1")
        if self.suggested_amount < 0:
            raise ValueError("Suggested amount cannot be negative")
        if not self.reasoning.strip():
            raise ValueError("Reasoning cannot be empty")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'action': self.action.value,
            'confidence': self.confidence,
            'suggested_amount': self.suggested_amount,
            'price_range': self.price_range.to_dict(),
            'reasoning': self.reasoning,
            'risk_level': self.risk_level.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TradingDecision':
        """Create instance from dictionary"""
        return cls(
            action=ActionType(data['action']),
            confidence=data['confidence'],
            suggested_amount=data['suggested_amount'],
            price_range=PriceRange.from_dict(data['price_range']),
            reasoning=data['reasoning'],
            risk_level=RiskLevel(data['risk_level'])
        )


@dataclass
class OrderResult:
    """Order execution result"""
    order_id: str
    status: OrderStatus
    executed_amount: float
    executed_price: float
    timestamp: datetime
    
    def __post_init__(self):
        """Validate data after initialization"""
        if not self.order_id.strip():
            raise ValueError("Order ID cannot be empty")
        if self.executed_amount < 0:
            raise ValueError("Executed amount cannot be negative")
        if self.executed_price < 0:
            raise ValueError("Executed price cannot be negative")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'order_id': self.order_id,
            'status': self.status.value,
            'executed_amount': self.executed_amount,
            'executed_price': self.executed_price,
            'timestamp': self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OrderResult':
        """Create instance from dictionary"""
        return cls(
            order_id=data['order_id'],
            status=OrderStatus(data['status']),
            executed_amount=data['executed_amount'],
            executed_price=data['executed_price'],
            timestamp=datetime.fromisoformat(data['timestamp'])
        )


@dataclass
class TradingRecord:
    """Trading record data structure"""
    id: str
    action: ActionType
    amount: float
    price: float
    timestamp: datetime
    decision_reasoning: str
    sentiment_score: float
    technical_signals: Dict[str, float]
    
    def __post_init__(self):
        """Validate data after initialization"""
        if not self.id.strip():
            raise ValueError("ID cannot be empty")
        if self.amount <= 0:
            raise ValueError("Amount must be positive")
        if self.price <= 0:
            raise ValueError("Price must be positive")
        if not self.decision_reasoning.strip():
            raise ValueError("Decision reasoning cannot be empty")
        if not 0 <= self.sentiment_score <= 100:
            raise ValueError("Sentiment score must be between 0 and 100")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'id': self.id,
            'action': self.action.value,
            'amount': self.amount,
            'price': self.price,
            'timestamp': self.timestamp.isoformat(),
            'decision_reasoning': self.decision_reasoning,
            'sentiment_score': self.sentiment_score,
            'technical_signals': self.technical_signals
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TradingRecord':
        """Create instance from dictionary"""
        return cls(
            id=data['id'],
            action=ActionType(data['action']),
            amount=data['amount'],
            price=data['price'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            decision_reasoning=data['decision_reasoning'],
            sentiment_score=data['sentiment_score'],
            technical_signals=data['technical_signals']
        )


# Utility functions for data validation and conversion

def validate_price(price: float) -> bool:
    """Validate price value"""
    return price > 0


def validate_amount(amount: float) -> bool:
    """Validate amount value"""
    return amount != 0


def validate_percentage(value: float) -> bool:
    """Validate percentage value (0-100)"""
    return 0 <= value <= 100


def validate_confidence(confidence: float) -> bool:
    """Validate confidence value (0-1)"""
    return 0 <= confidence <= 1


def generate_id() -> str:
    """Generate unique ID"""
    return str(uuid.uuid4())


def serialize_to_json(obj: Any) -> str:
    """Serialize object to JSON string"""
    if hasattr(obj, 'to_dict'):
        return json.dumps(obj.to_dict(), default=str)
    return json.dumps(obj, default=str)


def deserialize_from_json(json_str: str, cls: type) -> Any:
    """Deserialize JSON string to object"""
    data = json.loads(json_str)
    if hasattr(cls, 'from_dict'):
        return cls.from_dict(data)
    return cls(**data)