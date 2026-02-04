"""
Technical Analysis Engine
Main interface for technical indicator calculations and signal generation
"""
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import logging
import sys
import os

# Add the backend directory to the Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.data_models import TechnicalSignal, MarketData
from technical_analysis.indicators import TechnicalIndicators, TechnicalIndicatorCalculator
from technical_analysis.signal_generator import TechnicalSignalGenerator, SignalWeights


logger = logging.getLogger(__name__)


class TechnicalAnalysisEngine:
    """
    Main technical analysis engine that provides a unified interface
    for calculating technical indicators and generating trading signals
    """
    
    def __init__(self, signal_weights: Optional[SignalWeights] = None):
        """
        Initialize the technical analysis engine
        
        Args:
            signal_weights: Custom weights for signal generation (optional)
        """
        self.calculator = TechnicalIndicatorCalculator()
        self.signal_generator = TechnicalSignalGenerator(signal_weights)
        self.logger = logging.getLogger(__name__)
    
    def extract_prices_from_market_data(self, market_data: List[MarketData]) -> List[float]:
        """
        Extract price list from MarketData objects
        
        Args:
            market_data: List of MarketData objects
            
        Returns:
            List of prices
        """
        if not market_data:
            raise ValueError("Market data cannot be empty")
        
        # Sort by timestamp to ensure chronological order
        sorted_data = sorted(market_data, key=lambda x: x.timestamp)
        return [data.price for data in sorted_data]
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """
        Calculate Relative Strength Index (RSI)
        
        Args:
            prices: List of closing prices
            period: RSI period (default 14)
            
        Returns:
            RSI value (0-100)
        """
        try:
            return self.calculator.calculate_rsi(prices, period)
        except Exception as e:
            self.logger.error(f"Error calculating RSI: {e}")
            raise
    
    def calculate_macd(self, prices: List[float]) -> 'MACDResult':
        """
        Calculate MACD (Moving Average Convergence Divergence)
        
        Args:
            prices: List of closing prices
            
        Returns:
            MACDResult object
        """
        try:
            return self.calculator.calculate_macd(prices)
        except Exception as e:
            self.logger.error(f"Error calculating MACD: {e}")
            raise
    
    def calculate_bollinger_bands(self, prices: List[float]) -> 'BollingerBands':
        """
        Calculate Bollinger Bands
        
        Args:
            prices: List of closing prices
            
        Returns:
            BollingerBands object
        """
        try:
            return self.calculator.calculate_bollinger_bands(prices)
        except Exception as e:
            self.logger.error(f"Error calculating Bollinger Bands: {e}")
            raise
    
    def calculate_moving_averages(self, prices: List[float]) -> 'MovingAverages':
        """
        Calculate moving averages
        
        Args:
            prices: List of closing prices
            
        Returns:
            MovingAverages object
        """
        try:
            return self.calculator.calculate_moving_averages(prices)
        except Exception as e:
            self.logger.error(f"Error calculating moving averages: {e}")
            raise
    
    def calculate_all_indicators(self, prices: List[float]) -> TechnicalIndicators:
        """
        Calculate all technical indicators
        
        Args:
            prices: List of closing prices
            
        Returns:
            TechnicalIndicators object with all calculated values
        """
        try:
            return self.calculator.calculate_all_indicators(prices)
        except Exception as e:
            self.logger.error(f"Error calculating technical indicators: {e}")
            raise
    
    def generate_technical_signals(self, indicators: TechnicalIndicators, 
                                 current_price: float) -> TechnicalSignal:
        """
        Generate trading signals from technical indicators
        
        Args:
            indicators: Technical indicators
            current_price: Current market price
            
        Returns:
            TechnicalSignal object
        """
        try:
            return self.signal_generator.generate_technical_signals(indicators, current_price)
        except Exception as e:
            self.logger.error(f"Error generating technical signals: {e}")
            raise
    
    def analyze_market_from_data(self, market_data: List[MarketData]) -> Tuple[TechnicalIndicators, TechnicalSignal]:
        """
        Perform complete market analysis from MarketData objects
        
        Args:
            market_data: List of MarketData objects
            
        Returns:
            Tuple of (TechnicalIndicators, TechnicalSignal)
        """
        try:
            # Extract prices and get current price
            prices = self.extract_prices_from_market_data(market_data)
            current_price = prices[-1]  # Most recent price
            
            # Calculate indicators
            indicators = self.calculate_all_indicators(prices)
            
            # Generate signals
            signals = self.generate_technical_signals(indicators, current_price)
            
            self.logger.info(f"Market analysis completed. Signal: {signals.signal_type.value}, "
                           f"Strength: {signals.signal_strength}, Confidence: {signals.confidence}")
            
            return indicators, signals
            
        except Exception as e:
            self.logger.error(f"Error in market analysis: {e}")
            raise
    
    def analyze_market_from_prices(self, prices: List[float]) -> Tuple[TechnicalIndicators, TechnicalSignal]:
        """
        Perform complete market analysis from price list
        
        Args:
            prices: List of closing prices
            
        Returns:
            Tuple of (TechnicalIndicators, TechnicalSignal)
        """
        try:
            current_price = prices[-1]  # Most recent price
            
            # Calculate indicators
            indicators = self.calculate_all_indicators(prices)
            
            # Generate signals
            signals = self.generate_technical_signals(indicators, current_price)
            
            self.logger.info(f"Market analysis completed. Signal: {signals.signal_type.value}, "
                           f"Strength: {signals.signal_strength}, Confidence: {signals.confidence}")
            
            return indicators, signals
            
        except Exception as e:
            self.logger.error(f"Error in market analysis: {e}")
            raise
    
    def get_signal_strength_score(self, signal: TechnicalSignal) -> float:
        """
        Get signal strength score (0-100)
        
        Args:
            signal: Technical signal
            
        Returns:
            Signal strength score
        """
        return self.signal_generator.calculate_signal_strength_score(signal)
    
    def get_signal_interpretation(self, signal: TechnicalSignal) -> str:
        """
        Get human-readable signal interpretation
        
        Args:
            signal: Technical signal
            
        Returns:
            Signal interpretation string
        """
        return self.signal_generator.get_signal_interpretation(signal)
    
    def validate_price_data(self, prices: List[float], min_length: int = 50) -> bool:
        """
        Validate price data for technical analysis
        
        Args:
            prices: List of prices to validate
            min_length: Minimum required length
            
        Returns:
            True if data is valid
        """
        if not prices:
            return False
        
        if len(prices) < min_length:
            return False
        
        # Check for valid price values
        for price in prices:
            if price <= 0:
                return False
        
        return True
    
    def get_required_data_length(self) -> int:
        """
        Get minimum required data length for all indicators
        
        Returns:
            Minimum number of data points required
        """
        return 50  # Required for 50-period SMA and other indicators
    
    def get_indicator_summary(self, indicators: TechnicalIndicators) -> Dict[str, any]:
        """
        Get summary of all indicators
        
        Args:
            indicators: Technical indicators
            
        Returns:
            Dictionary with indicator summary
        """
        return {
            'timestamp': indicators.timestamp.isoformat(),
            'rsi': {
                'value': indicators.rsi,
                'interpretation': 'Oversold' if indicators.rsi <= 30 else 'Overbought' if indicators.rsi >= 70 else 'Neutral'
            },
            'macd': {
                'macd_line': indicators.macd.macd_line,
                'signal_line': indicators.macd.signal_line,
                'histogram': indicators.macd.histogram,
                'interpretation': 'Bullish' if indicators.macd.histogram > 0 else 'Bearish'
            },
            'bollinger_bands': {
                'upper': indicators.bollinger_bands.upper_band,
                'middle': indicators.bollinger_bands.middle_band,
                'lower': indicators.bollinger_bands.lower_band,
                'width': indicators.bollinger_bands.upper_band - indicators.bollinger_bands.lower_band
            },
            'moving_averages': {
                'sma_20': indicators.moving_averages.sma_20,
                'sma_50': indicators.moving_averages.sma_50,
                'ema_12': indicators.moving_averages.ema_12,
                'ema_26': indicators.moving_averages.ema_26,
                'trend': 'Bullish' if indicators.moving_averages.sma_20 > indicators.moving_averages.sma_50 else 'Bearish'
            }
        }