"""
Technical Indicator Calculations
Implements RSI, MACD, Moving Averages, and Bollinger Bands calculations
"""
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
import numpy as np
from datetime import datetime


@dataclass
class MACDResult:
    """MACD calculation result"""
    macd_line: float
    signal_line: float
    histogram: float
    
    def to_dict(self) -> Dict[str, float]:
        return {
            'macd_line': self.macd_line,
            'signal_line': self.signal_line,
            'histogram': self.histogram
        }


@dataclass
class BollingerBands:
    """Bollinger Bands calculation result"""
    upper_band: float
    middle_band: float  # Simple Moving Average
    lower_band: float
    
    def to_dict(self) -> Dict[str, float]:
        return {
            'upper_band': self.upper_band,
            'middle_band': self.middle_band,
            'lower_band': self.lower_band
        }


@dataclass
class MovingAverages:
    """Moving averages calculation result"""
    sma_20: float  # 20-period Simple Moving Average
    sma_50: float  # 50-period Simple Moving Average
    ema_12: float  # 12-period Exponential Moving Average
    ema_26: float  # 26-period Exponential Moving Average
    
    def to_dict(self) -> Dict[str, float]:
        return {
            'sma_20': self.sma_20,
            'sma_50': self.sma_50,
            'ema_12': self.ema_12,
            'ema_26': self.ema_26
        }


@dataclass
class TechnicalIndicators:
    """Combined technical indicators"""
    rsi: float
    macd: MACDResult
    bollinger_bands: BollingerBands
    moving_averages: MovingAverages
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, any]:
        return {
            'rsi': self.rsi,
            'macd': self.macd.to_dict(),
            'bollinger_bands': self.bollinger_bands.to_dict(),
            'moving_averages': self.moving_averages.to_dict(),
            'timestamp': self.timestamp.isoformat()
        }


class TechnicalIndicatorCalculator:
    """Technical indicator calculation functions"""
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> float:
        """
        Calculate Relative Strength Index (RSI)
        
        Args:
            prices: List of closing prices
            period: RSI period (default 14)
            
        Returns:
            RSI value (0-100)
        """
        if len(prices) < period + 1:
            raise ValueError(f"Need at least {period + 1} prices for RSI calculation")
        
        # Calculate price changes
        deltas = np.diff(prices)
        
        # Separate gains and losses
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        # Calculate average gains and losses
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])
        
        # Calculate subsequent averages using smoothing
        for i in range(period, len(deltas)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        
        # Calculate RSI
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return round(rsi, 2)
    
    @staticmethod
    def calculate_sma(prices: List[float], period: int) -> float:
        """
        Calculate Simple Moving Average (SMA)
        
        Args:
            prices: List of closing prices
            period: SMA period
            
        Returns:
            SMA value
        """
        if len(prices) < period:
            raise ValueError(f"Need at least {period} prices for SMA calculation")
        
        return round(np.mean(prices[-period:]), 2)
    
    @staticmethod
    def calculate_ema(prices: List[float], period: int) -> float:
        """
        Calculate Exponential Moving Average (EMA)
        
        Args:
            prices: List of closing prices
            period: EMA period
            
        Returns:
            EMA value
        """
        if len(prices) < period:
            raise ValueError(f"Need at least {period} prices for EMA calculation")
        
        # Calculate smoothing factor
        multiplier = 2 / (period + 1)
        
        # Initialize EMA with SMA
        ema = np.mean(prices[:period])
        
        # Calculate EMA for remaining prices
        for price in prices[period:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return round(ema, 2)
    
    @staticmethod
    def calculate_macd(prices: List[float], fast_period: int = 12, 
                      slow_period: int = 26, signal_period: int = 9) -> MACDResult:
        """
        Calculate MACD (Moving Average Convergence Divergence)
        
        Args:
            prices: List of closing prices
            fast_period: Fast EMA period (default 12)
            slow_period: Slow EMA period (default 26)
            signal_period: Signal line EMA period (default 9)
            
        Returns:
            MACDResult with MACD line, signal line, and histogram
        """
        if len(prices) < slow_period + signal_period:
            raise ValueError(f"Need at least {slow_period + signal_period} prices for MACD calculation")
        
        # Calculate fast and slow EMAs
        fast_ema = TechnicalIndicatorCalculator.calculate_ema(prices, fast_period)
        slow_ema = TechnicalIndicatorCalculator.calculate_ema(prices, slow_period)
        
        # Calculate MACD line
        macd_line = fast_ema - slow_ema
        
        # Calculate MACD values for signal line calculation
        macd_values = []
        for i in range(slow_period, len(prices) + 1):
            if i >= slow_period:
                fast_ema_temp = TechnicalIndicatorCalculator.calculate_ema(prices[:i], fast_period)
                slow_ema_temp = TechnicalIndicatorCalculator.calculate_ema(prices[:i], slow_period)
                macd_values.append(fast_ema_temp - slow_ema_temp)
        
        # Calculate signal line (EMA of MACD line)
        if len(macd_values) >= signal_period:
            signal_line = TechnicalIndicatorCalculator.calculate_ema(macd_values, signal_period)
        else:
            signal_line = macd_line
        
        # Calculate histogram
        histogram = macd_line - signal_line
        
        return MACDResult(
            macd_line=round(macd_line, 4),
            signal_line=round(signal_line, 4),
            histogram=round(histogram, 4)
        )
    
    @staticmethod
    def calculate_bollinger_bands(prices: List[float], period: int = 20, 
                                std_dev: float = 2.0) -> BollingerBands:
        """
        Calculate Bollinger Bands
        
        Args:
            prices: List of closing prices
            period: Moving average period (default 20)
            std_dev: Standard deviation multiplier (default 2.0)
            
        Returns:
            BollingerBands with upper, middle, and lower bands
        """
        if len(prices) < period:
            raise ValueError(f"Need at least {period} prices for Bollinger Bands calculation")
        
        # Calculate middle band (SMA)
        middle_band = TechnicalIndicatorCalculator.calculate_sma(prices, period)
        
        # Calculate standard deviation
        recent_prices = prices[-period:]
        std = np.std(recent_prices)
        
        # Calculate upper and lower bands
        upper_band = middle_band + (std_dev * std)
        lower_band = middle_band - (std_dev * std)
        
        return BollingerBands(
            upper_band=round(upper_band, 2),
            middle_band=round(middle_band, 2),
            lower_band=round(lower_band, 2)
        )
    
    @staticmethod
    def calculate_moving_averages(prices: List[float]) -> MovingAverages:
        """
        Calculate multiple moving averages
        
        Args:
            prices: List of closing prices
            
        Returns:
            MovingAverages with SMA and EMA values
        """
        if len(prices) < 50:
            raise ValueError("Need at least 50 prices for all moving averages calculation")
        
        sma_20 = TechnicalIndicatorCalculator.calculate_sma(prices, 20)
        sma_50 = TechnicalIndicatorCalculator.calculate_sma(prices, 50)
        ema_12 = TechnicalIndicatorCalculator.calculate_ema(prices, 12)
        ema_26 = TechnicalIndicatorCalculator.calculate_ema(prices, 26)
        
        return MovingAverages(
            sma_20=sma_20,
            sma_50=sma_50,
            ema_12=ema_12,
            ema_26=ema_26
        )
    
    @staticmethod
    def calculate_all_indicators(prices: List[float]) -> TechnicalIndicators:
        """
        Calculate all technical indicators
        
        Args:
            prices: List of closing prices
            
        Returns:
            TechnicalIndicators with all calculated values
        """
        if len(prices) < 50:
            raise ValueError("Need at least 50 prices for all indicators calculation")
        
        rsi = TechnicalIndicatorCalculator.calculate_rsi(prices)
        macd = TechnicalIndicatorCalculator.calculate_macd(prices)
        bollinger_bands = TechnicalIndicatorCalculator.calculate_bollinger_bands(prices)
        moving_averages = TechnicalIndicatorCalculator.calculate_moving_averages(prices)
        
        return TechnicalIndicators(
            rsi=rsi,
            macd=macd,
            bollinger_bands=bollinger_bands,
            moving_averages=moving_averages,
            timestamp=datetime.now()
        )