"""
Tests for Technical Analysis Engine
"""
import pytest
import sys
import os
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from technical_analysis.engine import TechnicalAnalysisEngine
from technical_analysis.indicators import TechnicalIndicatorCalculator
from technical_analysis.signal_generator import TechnicalSignalGenerator, SignalWeights
from core.data_models import MarketData, SignalType


class TestTechnicalIndicatorCalculator:
    """Test technical indicator calculations"""
    
    def setup_method(self):
        """Setup test data"""
        self.calculator = TechnicalIndicatorCalculator()
        # Create sample price data with known patterns
        self.prices = [100.0, 102.0, 101.0, 103.0, 105.0, 104.0, 106.0, 108.0, 107.0, 109.0,
                      111.0, 110.0, 112.0, 114.0, 113.0, 115.0, 117.0, 116.0, 118.0, 120.0,
                      119.0, 121.0, 123.0, 122.0, 124.0, 126.0, 125.0, 127.0, 129.0, 128.0,
                      130.0, 132.0, 131.0, 133.0, 135.0, 134.0, 136.0, 138.0, 137.0, 139.0,
                      141.0, 140.0, 142.0, 144.0, 143.0, 145.0, 147.0, 146.0, 148.0, 150.0]
    
    def test_rsi_calculation(self):
        """Test RSI calculation"""
        rsi = self.calculator.calculate_rsi(self.prices)
        assert 0 <= rsi <= 100
        assert isinstance(rsi, float)
    
    def test_rsi_with_insufficient_data(self):
        """Test RSI with insufficient data"""
        short_prices = [100.0, 102.0, 101.0]
        with pytest.raises(ValueError):
            self.calculator.calculate_rsi(short_prices)
    
    def test_sma_calculation(self):
        """Test Simple Moving Average calculation"""
        sma = self.calculator.calculate_sma(self.prices, 10)
        assert isinstance(sma, float)
        assert sma > 0
    
    def test_ema_calculation(self):
        """Test Exponential Moving Average calculation"""
        ema = self.calculator.calculate_ema(self.prices, 12)
        assert isinstance(ema, float)
        assert ema > 0
    
    def test_macd_calculation(self):
        """Test MACD calculation"""
        macd = self.calculator.calculate_macd(self.prices)
        assert hasattr(macd, 'macd_line')
        assert hasattr(macd, 'signal_line')
        assert hasattr(macd, 'histogram')
        assert isinstance(macd.macd_line, float)
        assert isinstance(macd.signal_line, float)
        assert isinstance(macd.histogram, float)
    
    def test_bollinger_bands_calculation(self):
        """Test Bollinger Bands calculation"""
        bb = self.calculator.calculate_bollinger_bands(self.prices)
        assert hasattr(bb, 'upper_band')
        assert hasattr(bb, 'middle_band')
        assert hasattr(bb, 'lower_band')
        assert bb.upper_band > bb.middle_band > bb.lower_band
    
    def test_moving_averages_calculation(self):
        """Test moving averages calculation"""
        ma = self.calculator.calculate_moving_averages(self.prices)
        assert hasattr(ma, 'sma_20')
        assert hasattr(ma, 'sma_50')
        assert hasattr(ma, 'ema_12')
        assert hasattr(ma, 'ema_26')
        assert all(avg > 0 for avg in [ma.sma_20, ma.sma_50, ma.ema_12, ma.ema_26])


class TestTechnicalSignalGenerator:
    """Test signal generation"""
    
    def setup_method(self):
        """Setup test data"""
        self.generator = TechnicalSignalGenerator()
        self.calculator = TechnicalIndicatorCalculator()
        self.prices = [100.0, 102.0, 101.0, 103.0, 105.0, 104.0, 106.0, 108.0, 107.0, 109.0,
                      111.0, 110.0, 112.0, 114.0, 113.0, 115.0, 117.0, 116.0, 118.0, 120.0,
                      119.0, 121.0, 123.0, 122.0, 124.0, 126.0, 125.0, 127.0, 129.0, 128.0,
                      130.0, 132.0, 131.0, 133.0, 135.0, 134.0, 136.0, 138.0, 137.0, 139.0,
                      141.0, 140.0, 142.0, 144.0, 143.0, 145.0, 147.0, 146.0, 148.0, 150.0]
    
    def test_rsi_signal_analysis(self):
        """Test RSI signal analysis"""
        # Test oversold condition
        strength, confidence = self.generator.analyze_rsi_signal(25.0)
        assert strength > 0  # Should be buy signal
        assert 0 <= confidence <= 1
        
        # Test overbought condition
        strength, confidence = self.generator.analyze_rsi_signal(75.0)
        assert strength < 0  # Should be sell signal
        assert 0 <= confidence <= 1
        
        # Test neutral condition
        strength, confidence = self.generator.analyze_rsi_signal(50.0)
        assert abs(strength) < 0.5  # Should be weak signal
        assert 0 <= confidence <= 1
    
    def test_signal_generation(self):
        """Test complete signal generation"""
        indicators = self.calculator.calculate_all_indicators(self.prices)
        current_price = self.prices[-1]
        
        signal = self.generator.generate_technical_signals(indicators, current_price)
        
        assert hasattr(signal, 'signal_strength')
        assert hasattr(signal, 'signal_type')
        assert hasattr(signal, 'confidence')
        assert hasattr(signal, 'contributing_indicators')
        
        assert -1 <= signal.signal_strength <= 1
        assert 0 <= signal.confidence <= 1
        assert signal.signal_type in [SignalType.BUY, SignalType.SELL, SignalType.HOLD]
        assert isinstance(signal.contributing_indicators, list)
    
    def test_signal_weights_validation(self):
        """Test signal weights validation"""
        # Valid weights
        weights = SignalWeights(0.25, 0.25, 0.25, 0.25)
        assert weights.rsi_weight == 0.25
        
        # Invalid weights (don't sum to 1.0)
        with pytest.raises(ValueError):
            SignalWeights(0.5, 0.5, 0.5, 0.5)


class TestTechnicalAnalysisEngine:
    """Test the main technical analysis engine"""
    
    def setup_method(self):
        """Setup test data"""
        self.engine = TechnicalAnalysisEngine()
        self.prices = [100.0, 102.0, 101.0, 103.0, 105.0, 104.0, 106.0, 108.0, 107.0, 109.0,
                      111.0, 110.0, 112.0, 114.0, 113.0, 115.0, 117.0, 116.0, 118.0, 120.0,
                      119.0, 121.0, 123.0, 122.0, 124.0, 126.0, 125.0, 127.0, 129.0, 128.0,
                      130.0, 132.0, 131.0, 133.0, 135.0, 134.0, 136.0, 138.0, 137.0, 139.0,
                      141.0, 140.0, 142.0, 144.0, 143.0, 145.0, 147.0, 146.0, 148.0, 150.0]
        
        # Create sample market data
        self.market_data = []
        base_time = datetime.now() - timedelta(days=len(self.prices))
        for i, price in enumerate(self.prices):
            data = MarketData(
                symbol="BTCUSDT",
                price=price,
                volume=1000.0,
                timestamp=base_time + timedelta(days=i),
                source="test"
            )
            self.market_data.append(data)
    
    def test_price_extraction_from_market_data(self):
        """Test extracting prices from market data"""
        extracted_prices = self.engine.extract_prices_from_market_data(self.market_data)
        assert len(extracted_prices) == len(self.prices)
        assert extracted_prices == self.prices
    
    def test_market_analysis_from_prices(self):
        """Test complete market analysis from prices"""
        indicators, signals = self.engine.analyze_market_from_prices(self.prices)
        
        # Check indicators
        assert hasattr(indicators, 'rsi')
        assert hasattr(indicators, 'macd')
        assert hasattr(indicators, 'bollinger_bands')
        assert hasattr(indicators, 'moving_averages')
        
        # Check signals
        assert hasattr(signals, 'signal_strength')
        assert hasattr(signals, 'signal_type')
        assert hasattr(signals, 'confidence')
        
        assert -1 <= signals.signal_strength <= 1
        assert 0 <= signals.confidence <= 1
    
    def test_market_analysis_from_market_data(self):
        """Test complete market analysis from market data"""
        indicators, signals = self.engine.analyze_market_from_data(self.market_data)
        
        # Check indicators
        assert hasattr(indicators, 'rsi')
        assert hasattr(indicators, 'macd')
        assert hasattr(indicators, 'bollinger_bands')
        assert hasattr(indicators, 'moving_averages')
        
        # Check signals
        assert hasattr(signals, 'signal_strength')
        assert hasattr(signals, 'signal_type')
        assert hasattr(signals, 'confidence')
    
    def test_price_data_validation(self):
        """Test price data validation"""
        # Valid data
        assert self.engine.validate_price_data(self.prices)
        
        # Invalid data - too short
        assert not self.engine.validate_price_data([100.0, 101.0])
        
        # Invalid data - empty
        assert not self.engine.validate_price_data([])
        
        # Invalid data - negative prices
        invalid_prices = self.prices.copy()
        invalid_prices[0] = -100.0
        assert not self.engine.validate_price_data(invalid_prices)
    
    def test_signal_strength_score(self):
        """Test signal strength score calculation"""
        indicators, signals = self.engine.analyze_market_from_prices(self.prices)
        score = self.engine.get_signal_strength_score(signals)
        
        assert 0 <= score <= 100
        assert isinstance(score, float)
    
    def test_signal_interpretation(self):
        """Test signal interpretation"""
        indicators, signals = self.engine.analyze_market_from_prices(self.prices)
        interpretation = self.engine.get_signal_interpretation(signals)
        
        assert isinstance(interpretation, str)
        assert len(interpretation) > 0
    
    def test_indicator_summary(self):
        """Test indicator summary generation"""
        indicators, _ = self.engine.analyze_market_from_prices(self.prices)
        summary = self.engine.get_indicator_summary(indicators)
        
        assert 'rsi' in summary
        assert 'macd' in summary
        assert 'bollinger_bands' in summary
        assert 'moving_averages' in summary
        
        # Check RSI summary
        assert 'value' in summary['rsi']
        assert 'interpretation' in summary['rsi']
        
        # Check MACD summary
        assert 'interpretation' in summary['macd']
        
        # Check Bollinger Bands summary
        assert 'width' in summary['bollinger_bands']
        
        # Check Moving Averages summary
        assert 'trend' in summary['moving_averages']
    
    def test_required_data_length(self):
        """Test required data length"""
        required_length = self.engine.get_required_data_length()
        assert required_length == 50
        assert isinstance(required_length, int)


if __name__ == "__main__":
    pytest.main([__file__])