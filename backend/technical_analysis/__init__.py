"""
Technical Analysis Module for Bitcoin Trading System
Implements technical indicators and signal generation
"""

from technical_analysis.engine import TechnicalAnalysisEngine
from technical_analysis.indicators import (
    TechnicalIndicatorCalculator,
    TechnicalIndicators,
    MACDResult,
    BollingerBands,
    MovingAverages
)
from technical_analysis.signal_generator import (
    TechnicalSignalGenerator,
    SignalWeights
)

__all__ = [
    'TechnicalAnalysisEngine',
    'TechnicalIndicatorCalculator',
    'TechnicalIndicators',
    'MACDResult',
    'BollingerBands',
    'MovingAverages',
    'TechnicalSignalGenerator',
    'SignalWeights'
]