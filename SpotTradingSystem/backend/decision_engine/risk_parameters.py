"""
Risk Parameters Configuration
Defines risk management parameters for trading decisions
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class RiskParameters:
    """Risk management parameters for trading decisions"""
    
    # Position sizing
    max_position_size: float = 0.1  # Maximum position size as percentage of portfolio (10%)
    min_position_size: float = 0.01  # Minimum position size as percentage of portfolio (1%)
    
    # Risk limits
    max_daily_loss: float = 0.05  # Maximum daily loss as percentage of portfolio (5%)
    max_portfolio_risk: float = 0.15  # Maximum total portfolio risk (15%)
    
    # Stop loss and take profit
    stop_loss_percentage: float = 0.02  # Stop loss percentage (2%)
    take_profit_percentage: float = 0.06  # Take profit percentage (6%)
    
    # Confidence thresholds
    min_confidence_threshold: float = 0.7  # Minimum confidence for trading (70%)
    high_confidence_threshold: float = 0.85  # High confidence threshold (85%)
    
    # Sentiment and technical weights
    sentiment_weight: float = 0.4  # Weight for sentiment analysis (40%)
    technical_weight: float = 0.6  # Weight for technical analysis (60%)
    
    # Market condition filters
    min_volume_threshold: float = 1000000  # Minimum 24h volume in USDT
    max_volatility_threshold: float = 0.1  # Maximum acceptable volatility (10%)
    
    # Cooling periods
    trade_cooldown_minutes: int = 30  # Minimum time between trades (30 minutes)
    loss_cooldown_hours: int = 4  # Cooldown after loss (4 hours)
    
    def __post_init__(self):
        """Validate risk parameters"""
        if not 0 < self.max_position_size <= 1:
            raise ValueError("Max position size must be between 0 and 1")
        
        if not 0 < self.min_position_size <= self.max_position_size:
            raise ValueError("Min position size must be positive and <= max position size")
        
        if not 0 < self.max_daily_loss <= 1:
            raise ValueError("Max daily loss must be between 0 and 1")
        
        if not 0 < self.max_portfolio_risk <= 1:
            raise ValueError("Max portfolio risk must be between 0 and 1")
        
        if not 0 < self.stop_loss_percentage <= 1:
            raise ValueError("Stop loss percentage must be between 0 and 1")
        
        if not 0 < self.take_profit_percentage <= 1:
            raise ValueError("Take profit percentage must be between 0 and 1")
        
        if not 0 <= self.min_confidence_threshold <= 1:
            raise ValueError("Min confidence threshold must be between 0 and 1")
        
        if not 0 <= self.high_confidence_threshold <= 1:
            raise ValueError("High confidence threshold must be between 0 and 1")
        
        if self.min_confidence_threshold > self.high_confidence_threshold:
            raise ValueError("Min confidence threshold cannot be greater than high confidence threshold")
        
        if not 0 <= self.sentiment_weight <= 1:
            raise ValueError("Sentiment weight must be between 0 and 1")
        
        if not 0 <= self.technical_weight <= 1:
            raise ValueError("Technical weight must be between 0 and 1")
        
        if abs(self.sentiment_weight + self.technical_weight - 1.0) > 0.01:
            raise ValueError("Sentiment and technical weights must sum to 1.0")
        
        if self.min_volume_threshold < 0:
            raise ValueError("Min volume threshold must be non-negative")
        
        if not 0 < self.max_volatility_threshold <= 1:
            raise ValueError("Max volatility threshold must be between 0 and 1")
        
        if self.trade_cooldown_minutes < 0:
            raise ValueError("Trade cooldown must be non-negative")
        
        if self.loss_cooldown_hours < 0:
            raise ValueError("Loss cooldown must be non-negative")
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            'max_position_size': self.max_position_size,
            'min_position_size': self.min_position_size,
            'max_daily_loss': self.max_daily_loss,
            'max_portfolio_risk': self.max_portfolio_risk,
            'stop_loss_percentage': self.stop_loss_percentage,
            'take_profit_percentage': self.take_profit_percentage,
            'min_confidence_threshold': self.min_confidence_threshold,
            'high_confidence_threshold': self.high_confidence_threshold,
            'sentiment_weight': self.sentiment_weight,
            'technical_weight': self.technical_weight,
            'min_volume_threshold': self.min_volume_threshold,
            'max_volatility_threshold': self.max_volatility_threshold,
            'trade_cooldown_minutes': self.trade_cooldown_minutes,
            'loss_cooldown_hours': self.loss_cooldown_hours
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'RiskParameters':
        """Create instance from dictionary"""
        return cls(**data)
    
    @classmethod
    def conservative(cls) -> 'RiskParameters':
        """Create conservative risk parameters"""
        return cls(
            max_position_size=0.05,  # 5%
            min_position_size=0.01,  # 1%
            max_daily_loss=0.02,     # 2%
            stop_loss_percentage=0.015,  # 1.5%
            take_profit_percentage=0.04,  # 4%
            min_confidence_threshold=0.8,  # 80%
            sentiment_weight=0.3,
            technical_weight=0.7
        )
    
    @classmethod
    def aggressive(cls) -> 'RiskParameters':
        """Create aggressive risk parameters"""
        return cls(
            max_position_size=0.2,   # 20%
            min_position_size=0.02,  # 2%
            max_daily_loss=0.1,      # 10%
            stop_loss_percentage=0.03,  # 3%
            take_profit_percentage=0.1,  # 10%
            min_confidence_threshold=0.6,  # 60%
            sentiment_weight=0.5,
            technical_weight=0.5
        )
    
    @classmethod
    def balanced(cls) -> 'RiskParameters':
        """Create balanced risk parameters (default)"""
        return cls()  # Uses default values