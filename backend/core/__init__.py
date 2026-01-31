"""
Core module for Bitcoin Trading System
Contains data models and core business logic
"""

from .data_models import (
    # Enums
    ActionType,
    SignalType,
    RiskLevel,
    OrderStatus,
    PriceType,
    
    # Data classes
    NewsItem,
    MarketData,
    Position,
    Portfolio,
    SentimentScore,
    ImpactAssessment,
    TechnicalSignal,
    PriceRange,
    TradingDecision,
    OrderResult,
    TradingRecord,
    
    # Utility functions
    validate_price,
    validate_amount,
    validate_percentage,
    validate_confidence,
    generate_id,
    serialize_to_json,
    deserialize_from_json
)

__all__ = [
    # Enums
    'ActionType',
    'SignalType',
    'RiskLevel',
    'OrderStatus',
    'PriceType',
    
    # Data classes
    'NewsItem',
    'MarketData',
    'Position',
    'Portfolio',
    'SentimentScore',
    'ImpactAssessment',
    'TechnicalSignal',
    'PriceRange',
    'TradingDecision',
    'OrderResult',
    'TradingRecord',
    
    # Utility functions
    'validate_price',
    'validate_amount',
    'validate_percentage',
    'validate_confidence',
    'generate_id',
    'serialize_to_json',
    'deserialize_from_json'
]