# Technical Analysis Engine

This module implements a comprehensive technical analysis engine for the Bitcoin Trading System. It provides calculation of various technical indicators and generates trading signals based on these indicators.

## Features

### Technical Indicators
- **RSI (Relative Strength Index)**: Momentum oscillator measuring speed and magnitude of price changes
- **MACD (Moving Average Convergence Divergence)**: Trend-following momentum indicator
- **Bollinger Bands**: Volatility indicator with upper, middle, and lower bands
- **Moving Averages**: Simple Moving Average (SMA) and Exponential Moving Average (EMA)

### Signal Generation
- Combines multiple technical indicators to generate trading signals
- Provides signal strength (-1 to 1) and confidence (0 to 1) scores
- Supports customizable weights for different indicators
- Generates BUY, SELL, or HOLD recommendations

## Usage

### Basic Usage

```python
from technical_analysis.engine import TechnicalAnalysisEngine

# Create engine
engine = TechnicalAnalysisEngine()

# Analyze market with price data
prices = [100.0, 102.0, 101.0, ...]  # At least 50 data points
indicators, signals = engine.analyze_market_from_prices(prices)

print(f"Signal: {signals.signal_type.value}")
print(f"Strength: {signals.signal_strength}")
print(f"Confidence: {signals.confidence}")
```

### Custom Signal Weights

```python
from technical_analysis.signal_generator import SignalWeights

# Create custom weights
weights = SignalWeights(
    rsi_weight=0.4,
    macd_weight=0.3,
    bollinger_weight=0.2,
    moving_average_weight=0.1
)

# Create engine with custom weights
engine = TechnicalAnalysisEngine(weights)
```

### Individual Indicators

```python
# Calculate individual indicators
rsi = engine.calculate_rsi(prices)
macd = engine.calculate_macd(prices)
bollinger = engine.calculate_bollinger_bands(prices)
moving_averages = engine.calculate_moving_averages(prices)
```

## Data Requirements

- Minimum 50 data points required for all indicators
- Prices must be positive values
- Data should be in chronological order

## Signal Interpretation

### Signal Types
- **BUY**: Signal strength > 0.3
- **SELL**: Signal strength < -0.3
- **HOLD**: -0.3 ≤ signal strength ≤ 0.3

### Signal Strength
- **Strong**: |strength| > 0.7 and confidence > 0.7
- **Moderate**: 0.3 < |strength| ≤ 0.7
- **Weak**: |strength| ≤ 0.3

## Architecture

### Components

1. **TechnicalIndicatorCalculator**: Core mathematical calculations
2. **TechnicalSignalGenerator**: Signal generation and analysis
3. **TechnicalAnalysisEngine**: Main interface combining all functionality

### Data Models

- **TechnicalIndicators**: Container for all calculated indicators
- **TechnicalSignal**: Signal with strength, type, and confidence
- **MACDResult**: MACD line, signal line, and histogram
- **BollingerBands**: Upper, middle, and lower bands
- **MovingAverages**: Various moving average calculations

## Testing

Run tests with:
```bash
python -m pytest tests/test_technical_analysis.py -v
```

## Example

See `example_usage.py` for a complete example demonstrating all features.

## Requirements Validation

This implementation satisfies the following requirements:
- **需求 3.1**: RSI indicator calculation ✓
- **需求 3.2**: MACD indicator calculation ✓
- **需求 3.3**: Moving averages calculation ✓
- **需求 3.4**: Bollinger Bands calculation ✓
- **需求 3.5**: Trading signal generation with strength scoring ✓