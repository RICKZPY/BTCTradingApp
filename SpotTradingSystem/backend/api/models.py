"""
API data models using Pydantic
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class SystemStatus(str, Enum):
    """System status enumeration"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class OrderSide(str, Enum):
    """Order side enumeration"""
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    """Order type enumeration"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class OrderStatus(str, Enum):
    """Order status enumeration"""
    NEW = "NEW"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


# Response Models
class APIResponse(BaseModel):
    """Base API response model"""
    success: bool
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(APIResponse):
    """Error response model"""
    success: bool = False
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


# System Models
class ComponentStatus(BaseModel):
    """Component status model"""
    name: str
    status: str
    healthy: bool
    last_check: datetime
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SystemStatusResponse(APIResponse):
    """System status response"""
    success: bool = True
    system_state: SystemStatus
    start_time: Optional[datetime] = None
    uptime_seconds: Optional[float] = None
    components: Dict[str, Any]
    event_bus: Dict[str, Any]
    message_queue: Dict[str, Any]
    task_scheduler: Dict[str, Any]


class SystemMetrics(BaseModel):
    """System metrics model"""
    system_healthy: bool
    uptime_seconds: float
    total_components: int
    healthy_components: int
    total_events: int
    total_messages: int
    total_tasks: int
    event_success_rate: float
    message_success_rate: float
    task_success_rate: float
    timestamp: datetime


# Trading Models
class Position(BaseModel):
    """Position model"""
    symbol: str
    quantity: float
    average_price: float
    current_price: Optional[float] = None
    current_value: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    unrealized_pnl_percent: Optional[float] = None
    side: str  # LONG or SHORT
    timestamp: datetime


class Portfolio(BaseModel):
    """Portfolio model"""
    total_value: float
    available_balance: float
    positions: List[Position]
    total_unrealized_pnl: float
    total_unrealized_pnl_percent: float
    timestamp: datetime


class PortfolioResponse(APIResponse):
    """Portfolio response"""
    success: bool = True
    portfolio: Portfolio


class TradingOrder(BaseModel):
    """Trading order model"""
    order_id: str
    symbol: str
    side: OrderSide
    type: OrderType
    quantity: float
    price: Optional[float] = None
    status: OrderStatus
    filled_quantity: float = 0.0
    average_price: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class OrderHistory(BaseModel):
    """Order history model"""
    orders: List[TradingOrder]
    total_count: int
    page: int
    page_size: int


class OrderHistoryResponse(APIResponse):
    """Order history response"""
    success: bool = True
    data: OrderHistory


# Request Models
class PlaceOrderRequest(BaseModel):
    """Place order request"""
    symbol: str = Field(..., description="Trading symbol (e.g., BTCUSDT)")
    side: OrderSide = Field(..., description="Order side (BUY or SELL)")
    type: OrderType = Field(..., description="Order type (MARKET or LIMIT)")
    quantity: float = Field(..., gt=0, description="Order quantity")
    price: Optional[float] = Field(None, gt=0, description="Order price (required for LIMIT orders)")


class CancelOrderRequest(BaseModel):
    """Cancel order request"""
    order_id: str = Field(..., description="Order ID to cancel")


class SystemControlRequest(BaseModel):
    """System control request"""
    action: str = Field(..., description="Action to perform (start, stop, restart)")


# Market Data Models
class MarketData(BaseModel):
    """Market data model"""
    symbol: str
    price: float
    volume: float
    change_24h: Optional[float] = None
    change_24h_percent: Optional[float] = None
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None
    timestamp: datetime


class MarketDataResponse(APIResponse):
    """Market data response"""
    success: bool = True
    data: MarketData


# Analysis Models
class SentimentAnalysis(BaseModel):
    """Sentiment analysis model"""
    sentiment_score: float = Field(..., ge=-1, le=1, description="Sentiment score between -1 and 1")
    confidence: float = Field(..., ge=0, le=1, description="Confidence level")
    key_topics: List[str]
    impact_assessment: Dict[str, float]
    timestamp: datetime


class TechnicalSignal(BaseModel):
    """Technical signal model"""
    signal_type: str  # BUY, SELL, HOLD
    strength: float = Field(..., ge=0, le=1)
    confidence: float = Field(..., ge=0, le=1)
    indicators: Dict[str, Any]
    timestamp: datetime


class TradingDecision(BaseModel):
    """Trading decision model"""
    action: str  # BUY, SELL, HOLD
    symbol: str
    quantity: Optional[float] = None
    confidence: float = Field(..., ge=0, le=1)
    reasoning: str
    sentiment_data: Optional[SentimentAnalysis] = None
    technical_data: Optional[TechnicalSignal] = None
    timestamp: datetime


class AnalysisResponse(APIResponse):
    """Analysis response"""
    success: bool = True
    sentiment: Optional[SentimentAnalysis] = None
    technical: Optional[TechnicalSignal] = None
    decision: Optional[TradingDecision] = None


# Configuration Models
class TradingConfig(BaseModel):
    """Trading configuration model"""
    max_position_size: float = Field(..., gt=0, le=1, description="Maximum position size as percentage of portfolio")
    stop_loss_percentage: float = Field(..., gt=0, le=1, description="Stop loss percentage")
    min_confidence_threshold: float = Field(..., ge=0, le=1, description="Minimum confidence threshold for trades")
    market_data_interval: int = Field(..., gt=0, description="Market data collection interval in seconds")
    news_collection_interval: int = Field(..., gt=0, description="News collection interval in seconds")
    decision_interval: int = Field(..., gt=0, description="Decision making interval in seconds")


class ConfigResponse(APIResponse):
    """Configuration response"""
    success: bool = True
    config: TradingConfig


class UpdateConfigRequest(BaseModel):
    """Update configuration request"""
    config: TradingConfig


# Health Check Models
class HealthCheckResponse(APIResponse):
    """Health check response"""
    success: bool = True
    healthy: bool
    components: List[ComponentStatus]
    system_metrics: SystemMetrics