"""
Example usage of Technical Analysis Engine
Demonstrates how to use the technical indicators and signal generation
"""
from typing import List
import sys
import os
from datetime import datetime, timedelta
import random

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from technical_analysis.engine import TechnicalAnalysisEngine
from technical_analysis.signal_generator import SignalWeights
from core.data_models import MarketData


def generate_sample_price_data(days: int = 100, start_price: float = 50000.0) -> List[float]:
    """
    Generate sample price data for testing
    
    Args:
        days: Number of days of data
        start_price: Starting price
        
    Returns:
        List of prices with some random walk behavior
    """
    prices = [start_price]
    
    for _ in range(days - 1):
        # Random walk with slight upward bias
        change_percent = random.gauss(0.001, 0.02)  # 0.1% average daily gain, 2% volatility
        new_price = prices[-1] * (1 + change_percent)
        prices.append(max(new_price, 1000))  # Minimum price of $1000
    
    return prices


def generate_sample_market_data(days: int = 100) -> List[MarketData]:
    """
    Generate sample MarketData objects for testing
    
    Args:
        days: Number of days of data
        
    Returns:
        List of MarketData objects
    """
    prices = generate_sample_price_data(days)
    market_data = []
    
    base_time = datetime.now() - timedelta(days=days)
    
    for i, price in enumerate(prices):
        data = MarketData(
            symbol="BTCUSDT",
            price=price,
            volume=random.uniform(1000, 10000),
            timestamp=base_time + timedelta(days=i),
            source="sample_data"
        )
        market_data.append(data)
    
    return market_data


def main():
    """Main example function"""
    print("=== Technical Analysis Engine Example ===\n")
    
    # Create engine with default weights
    engine = TechnicalAnalysisEngine()
    
    # Generate sample data
    print("Generating sample market data...")
    market_data = generate_sample_market_data(100)
    prices = [data.price for data in market_data]
    
    print(f"Generated {len(prices)} price points")
    print(f"Price range: ${min(prices):,.2f} - ${max(prices):,.2f}")
    print(f"Current price: ${prices[-1]:,.2f}\n")
    
    try:
        # Calculate individual indicators
        print("=== Individual Indicators ===")
        
        rsi = engine.calculate_rsi(prices)
        print(f"RSI (14): {rsi:.2f}")
        
        macd = engine.calculate_macd(prices)
        print(f"MACD: {macd.macd_line:.4f}")
        print(f"Signal: {macd.signal_line:.4f}")
        print(f"Histogram: {macd.histogram:.4f}")
        
        bollinger = engine.calculate_bollinger_bands(prices)
        print(f"Bollinger Bands:")
        print(f"  Upper: ${bollinger.upper_band:,.2f}")
        print(f"  Middle: ${bollinger.middle_band:,.2f}")
        print(f"  Lower: ${bollinger.lower_band:,.2f}")
        
        ma = engine.calculate_moving_averages(prices)
        print(f"Moving Averages:")
        print(f"  SMA 20: ${ma.sma_20:,.2f}")
        print(f"  SMA 50: ${ma.sma_50:,.2f}")
        print(f"  EMA 12: ${ma.ema_12:,.2f}")
        print(f"  EMA 26: ${ma.ema_26:,.2f}")
        
        # Complete market analysis
        print("\n=== Complete Market Analysis ===")
        indicators, signals = engine.analyze_market_from_prices(prices)
        
        print(f"Signal Type: {signals.signal_type.value}")
        print(f"Signal Strength: {signals.signal_strength:.3f}")
        print(f"Confidence: {signals.confidence:.3f}")
        print(f"Contributing Indicators: {', '.join(signals.contributing_indicators)}")
        
        # Get signal interpretation
        interpretation = engine.get_signal_interpretation(signals)
        print(f"Interpretation: {interpretation}")
        
        # Get indicator summary
        print("\n=== Indicator Summary ===")
        summary = engine.get_indicator_summary(indicators)
        
        print(f"RSI: {summary['rsi']['value']:.2f} ({summary['rsi']['interpretation']})")
        print(f"MACD: {summary['macd']['interpretation']}")
        print(f"Bollinger Width: ${summary['bollinger_bands']['width']:,.2f}")
        print(f"MA Trend: {summary['moving_averages']['trend']}")
        
        # Test with custom weights
        print("\n=== Custom Signal Weights Example ===")
        custom_weights = SignalWeights(
            rsi_weight=0.4,
            macd_weight=0.3,
            bollinger_weight=0.2,
            moving_average_weight=0.1
        )
        
        custom_engine = TechnicalAnalysisEngine(custom_weights)
        _, custom_signals = custom_engine.analyze_market_from_prices(prices)
        
        print(f"Custom Signal Type: {custom_signals.signal_type.value}")
        print(f"Custom Signal Strength: {custom_signals.signal_strength:.3f}")
        print(f"Custom Confidence: {custom_signals.confidence:.3f}")
        
        custom_interpretation = custom_engine.get_signal_interpretation(custom_signals)
        print(f"Custom Interpretation: {custom_interpretation}")
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        return
    
    print("\n=== Example completed successfully! ===")


if __name__ == "__main__":
    main()