"""
Trading Signal Generator
Combines technical indicators to generate trading signals with strength and confidence scores
"""
from typing import Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np
import sys
import os

# Add the backend directory to the Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.data_models import TechnicalSignal, SignalType
from technical_analysis.indicators import TechnicalIndicators, TechnicalIndicatorCalculator


@dataclass
class SignalWeights:
    """Weights for different technical indicators in signal generation"""
    rsi_weight: float = 0.25
    macd_weight: float = 0.30
    bollinger_weight: float = 0.20
    moving_average_weight: float = 0.25
    
    def __post_init__(self):
        """Validate weights sum to 1.0"""
        total = self.rsi_weight + self.macd_weight + self.bollinger_weight + self.moving_average_weight
        if abs(total - 1.0) > 0.01:
            raise ValueError("Signal weights must sum to 1.0")


class TechnicalSignalGenerator:
    """Generates trading signals from technical indicators"""
    
    def __init__(self, weights: SignalWeights = None):
        """
        Initialize signal generator with optional custom weights
        
        Args:
            weights: Custom weights for indicators (uses default if None)
        """
        self.weights = weights or SignalWeights()
    
    def analyze_rsi_signal(self, rsi: float) -> Tuple[float, float]:
        """
        Analyze RSI for trading signal
        
        Args:
            rsi: RSI value (0-100)
            
        Returns:
            Tuple of (signal_strength, confidence)
            signal_strength: -1 (strong sell) to 1 (strong buy)
            confidence: 0 to 1
        """
        if rsi <= 30:
            # Oversold - buy signal
            strength = min(1.0, (30 - rsi) / 20)  # Stronger signal as RSI gets lower
            confidence = min(0.9, (30 - rsi) / 15)
        elif rsi >= 70:
            # Overbought - sell signal
            strength = max(-1.0, (70 - rsi) / 20)  # Stronger signal as RSI gets higher
            confidence = min(0.9, (rsi - 70) / 15)
        else:
            # Neutral zone
            if rsi < 50:
                strength = (rsi - 50) / 50  # Slight buy bias
            else:
                strength = (rsi - 50) / 50  # Slight sell bias
            confidence = 0.3  # Low confidence in neutral zone
        
        return round(strength, 3), round(confidence, 3)
    
    def analyze_macd_signal(self, macd_line: float, signal_line: float, histogram: float) -> Tuple[float, float]:
        """
        Analyze MACD for trading signal
        
        Args:
            macd_line: MACD line value
            signal_line: Signal line value
            histogram: MACD histogram value
            
        Returns:
            Tuple of (signal_strength, confidence)
        """
        # MACD line above signal line = bullish
        # MACD line below signal line = bearish
        line_diff = macd_line - signal_line
        
        # Histogram shows momentum
        if histogram > 0 and line_diff > 0:
            # Bullish momentum
            strength = min(1.0, abs(histogram) * 10)  # Scale histogram to strength
            confidence = min(0.8, abs(line_diff) * 5)
        elif histogram < 0 and line_diff < 0:
            # Bearish momentum
            strength = max(-1.0, -abs(histogram) * 10)
            confidence = min(0.8, abs(line_diff) * 5)
        else:
            # Mixed signals - lower confidence
            strength = np.sign(line_diff) * min(0.5, abs(line_diff) * 2)
            confidence = 0.4
        
        return round(strength, 3), round(confidence, 3)
    
    def analyze_bollinger_signal(self, current_price: float, upper_band: float, 
                                middle_band: float, lower_band: float) -> Tuple[float, float]:
        """
        Analyze Bollinger Bands for trading signal
        
        Args:
            current_price: Current price
            upper_band: Upper Bollinger Band
            middle_band: Middle Bollinger Band (SMA)
            lower_band: Lower Bollinger Band
            
        Returns:
            Tuple of (signal_strength, confidence)
        """
        band_width = upper_band - lower_band
        
        if current_price <= lower_band:
            # Price at or below lower band - buy signal
            distance_below = (lower_band - current_price) / band_width
            strength = min(1.0, distance_below * 2)
            confidence = min(0.8, distance_below * 3)
        elif current_price >= upper_band:
            # Price at or above upper band - sell signal
            distance_above = (current_price - upper_band) / band_width
            strength = max(-1.0, -distance_above * 2)
            confidence = min(0.8, distance_above * 3)
        else:
            # Price within bands
            position = (current_price - middle_band) / (band_width / 2)
            strength = position * 0.5  # Moderate signal based on position
            confidence = 0.4
        
        return round(strength, 3), round(confidence, 3)
    
    def analyze_moving_average_signal(self, current_price: float, sma_20: float, 
                                    sma_50: float, ema_12: float, ema_26: float) -> Tuple[float, float]:
        """
        Analyze Moving Averages for trading signal
        
        Args:
            current_price: Current price
            sma_20: 20-period Simple Moving Average
            sma_50: 50-period Simple Moving Average
            ema_12: 12-period Exponential Moving Average
            ema_26: 26-period Exponential Moving Average
            
        Returns:
            Tuple of (signal_strength, confidence)
        """
        signals = []
        
        # Price vs SMA signals
        if current_price > sma_20:
            signals.append(0.5)
        else:
            signals.append(-0.5)
        
        if current_price > sma_50:
            signals.append(0.3)
        else:
            signals.append(-0.3)
        
        # SMA crossover signal
        if sma_20 > sma_50:
            signals.append(0.4)  # Golden cross tendency
        else:
            signals.append(-0.4)  # Death cross tendency
        
        # EMA crossover signal
        if ema_12 > ema_26:
            signals.append(0.6)  # Bullish EMA crossover
        else:
            signals.append(-0.6)  # Bearish EMA crossover
        
        # Calculate overall signal
        strength = np.mean(signals)
        
        # Confidence based on signal alignment
        signal_alignment = 1 - (np.std(signals) / np.mean(np.abs(signals)) if np.mean(np.abs(signals)) > 0 else 0)
        confidence = min(0.8, signal_alignment)
        
        return round(strength, 3), round(confidence, 3)
    
    def generate_technical_signals(self, indicators: TechnicalIndicators, 
                                 current_price: float) -> TechnicalSignal:
        """
        Generate comprehensive trading signal from all technical indicators
        
        Args:
            indicators: Technical indicators
            current_price: Current market price
            
        Returns:
            TechnicalSignal with combined analysis
        """
        # Analyze individual indicators
        rsi_strength, rsi_confidence = self.analyze_rsi_signal(indicators.rsi)
        
        macd_strength, macd_confidence = self.analyze_macd_signal(
            indicators.macd.macd_line,
            indicators.macd.signal_line,
            indicators.macd.histogram
        )
        
        bollinger_strength, bollinger_confidence = self.analyze_bollinger_signal(
            current_price,
            indicators.bollinger_bands.upper_band,
            indicators.bollinger_bands.middle_band,
            indicators.bollinger_bands.lower_band
        )
        
        ma_strength, ma_confidence = self.analyze_moving_average_signal(
            current_price,
            indicators.moving_averages.sma_20,
            indicators.moving_averages.sma_50,
            indicators.moving_averages.ema_12,
            indicators.moving_averages.ema_26
        )
        
        # Calculate weighted signal strength
        weighted_strength = (
            rsi_strength * self.weights.rsi_weight +
            macd_strength * self.weights.macd_weight +
            bollinger_strength * self.weights.bollinger_weight +
            ma_strength * self.weights.moving_average_weight
        )
        
        # Calculate weighted confidence
        weighted_confidence = (
            rsi_confidence * self.weights.rsi_weight +
            macd_confidence * self.weights.macd_weight +
            bollinger_confidence * self.weights.bollinger_weight +
            ma_confidence * self.weights.moving_average_weight
        )
        
        # Determine signal type based on strength
        if weighted_strength > 0.3:
            signal_type = SignalType.BUY
        elif weighted_strength < -0.3:
            signal_type = SignalType.SELL
        else:
            signal_type = SignalType.HOLD
        
        # Contributing indicators
        contributing_indicators = []
        if abs(rsi_strength) > 0.3:
            contributing_indicators.append(f"RSI({indicators.rsi:.1f})")
        if abs(macd_strength) > 0.3:
            contributing_indicators.append(f"MACD({indicators.macd.macd_line:.4f})")
        if abs(bollinger_strength) > 0.3:
            contributing_indicators.append("Bollinger_Bands")
        if abs(ma_strength) > 0.3:
            contributing_indicators.append("Moving_Averages")
        
        return TechnicalSignal(
            signal_strength=round(weighted_strength, 3),
            signal_type=signal_type,
            confidence=round(weighted_confidence, 3),
            contributing_indicators=contributing_indicators
        )
    
    def calculate_signal_strength_score(self, signal: TechnicalSignal) -> float:
        """
        Calculate overall signal strength score (0-100)
        
        Args:
            signal: Technical signal
            
        Returns:
            Signal strength score
        """
        # Combine signal strength and confidence
        base_score = abs(signal.signal_strength) * signal.confidence * 100
        
        # Bonus for strong signals
        if abs(signal.signal_strength) > 0.7 and signal.confidence > 0.7:
            base_score *= 1.2
        
        # Penalty for weak signals
        if abs(signal.signal_strength) < 0.3 or signal.confidence < 0.4:
            base_score *= 0.8
        
        return min(100.0, round(base_score, 1))
    
    def get_signal_interpretation(self, signal: TechnicalSignal) -> str:
        """
        Get human-readable interpretation of the signal
        
        Args:
            signal: Technical signal
            
        Returns:
            Signal interpretation string
        """
        strength_score = self.calculate_signal_strength_score(signal)
        
        if signal.signal_type == SignalType.BUY:
            if strength_score >= 70:
                return f"Strong BUY signal (Score: {strength_score})"
            elif strength_score >= 50:
                return f"Moderate BUY signal (Score: {strength_score})"
            else:
                return f"Weak BUY signal (Score: {strength_score})"
        elif signal.signal_type == SignalType.SELL:
            if strength_score >= 70:
                return f"Strong SELL signal (Score: {strength_score})"
            elif strength_score >= 50:
                return f"Moderate SELL signal (Score: {strength_score})"
            else:
                return f"Weak SELL signal (Score: {strength_score})"
        else:
            return f"HOLD signal - No clear direction (Score: {strength_score})"


class TechnicalIndicatorEngine:
    """Main technical indicator engine combining calculation and signal generation"""
    
    def __init__(self, signal_weights: SignalWeights = None):
        """
        Initialize technical indicator engine
        
        Args:
            signal_weights: Custom weights for signal generation
        """
        self.calculator = TechnicalIndicatorCalculator()
        self.signal_generator = TechnicalSignalGenerator(signal_weights)
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI indicator"""
        return self.calculator.calculate_rsi(prices, period)
    
    def calculate_macd(self, prices: List[float]) -> 'MACDResult':
        """Calculate MACD indicator"""
        return self.calculator.calculate_macd(prices)
    
    def calculate_bollinger_bands(self, prices: List[float]) -> 'BollingerBands':
        """Calculate Bollinger Bands"""
        return self.calculator.calculate_bollinger_bands(prices)
    
    def calculate_moving_averages(self, prices: List[float]) -> 'MovingAverages':
        """Calculate moving averages"""
        return self.calculator.calculate_moving_averages(prices)
    
    def generate_technical_signals(self, indicators: TechnicalIndicators, 
                                 current_price: float) -> TechnicalSignal:
        """Generate trading signals from technical indicators"""
        return self.signal_generator.generate_technical_signals(indicators, current_price)
    
    def analyze_market(self, prices: List[float], current_price: float = None) -> Tuple[TechnicalIndicators, TechnicalSignal]:
        """
        Complete market analysis with indicators and signals
        
        Args:
            prices: Historical price data
            current_price: Current market price (uses last price if None)
            
        Returns:
            Tuple of (TechnicalIndicators, TechnicalSignal)
        """
        if current_price is None:
            current_price = prices[-1]
        
        # Calculate all indicators
        indicators = self.calculator.calculate_all_indicators(prices)
        
        # Generate trading signal
        signal = self.signal_generator.generate_technical_signals(indicators, current_price)
        
        return indicators, signal