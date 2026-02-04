"""
Market Conditions Evaluator Example Usage
Demonstrates market condition assessment and dynamic strategy adjustments
"""
import sys
import os
from datetime import datetime, timedelta
import random
import numpy as np

# Add the backend directory to the Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.data_models import MarketData, SentimentScore, TechnicalSignal, SignalType, NewsItem
from decision_engine.market_conditions import MarketConditionEvaluator, MarketRegime, TradingRecommendation


def create_trending_market_data(base_price: float = 45000, trend_direction: int = 1, 
                               hours: int = 24, volatility: float = 0.02) -> list:
    """Create market data with a trending pattern"""
    market_data = []
    current_price = base_price
    base_time = datetime.utcnow() - timedelta(hours=hours)
    
    for i in range(hours):
        # Add trend
        trend_component = trend_direction * (i / hours) * 0.05 * base_price  # 5% trend over period
        
        # Add volatility
        volatility_component = random.gauss(0, volatility * base_price)
        
        current_price = base_price + trend_component + volatility_component
        
        # Volume varies with price movement
        base_volume = 1500000
        volume_variation = abs(volatility_component) / (volatility * base_price) * 500000
        volume = base_volume + volume_variation
        
        market_data.append(MarketData(
            symbol="BTCUSDT",
            price=current_price,
            volume=volume,
            timestamp=base_time + timedelta(hours=i),
            source="binance"
        ))
    
    return market_data


def create_volatile_market_data(base_price: float = 45000, hours: int = 24, 
                               volatility: float = 0.08) -> list:
    """Create market data with high volatility"""
    market_data = []
    current_price = base_price
    base_time = datetime.utcnow() - timedelta(hours=hours)
    
    for i in range(hours):
        # High volatility with no clear trend
        price_change = random.gauss(0, volatility * base_price)
        current_price = max(base_price * 0.8, min(base_price * 1.2, current_price + price_change))
        
        # High volume during volatile periods
        volume = random.uniform(2000000, 4000000)
        
        market_data.append(MarketData(
            symbol="BTCUSDT",
            price=current_price,
            volume=volume,
            timestamp=base_time + timedelta(hours=i),
            source="binance"
        ))
    
    return market_data


def create_sideways_market_data(base_price: float = 45000, hours: int = 24,
                               range_pct: float = 0.02) -> list:
    """Create market data with sideways movement"""
    market_data = []
    base_time = datetime.utcnow() - timedelta(hours=hours)
    
    for i in range(hours):
        # Oscillate within a range
        oscillation = np.sin(i / 6) * range_pct * base_price  # 6-hour cycle
        noise = random.gauss(0, 0.005 * base_price)
        current_price = base_price + oscillation + noise
        
        # Moderate volume
        volume = random.uniform(1000000, 1800000)
        
        market_data.append(MarketData(
            symbol="BTCUSDT",
            price=current_price,
            volume=volume,
            timestamp=base_time + timedelta(hours=i),
            source="binance"
        ))
    
    return market_data


def create_low_volume_market_data(base_price: float = 45000, hours: int = 24) -> list:
    """Create market data with low volume"""
    market_data = []
    current_price = base_price
    base_time = datetime.utcnow() - timedelta(hours=hours)
    
    for i in range(hours):
        # Small price movements due to low volume
        price_change = random.gauss(0, 0.01 * base_price)
        current_price += price_change
        
        # Consistently low volume
        volume = random.uniform(300000, 600000)
        
        market_data.append(MarketData(
            symbol="BTCUSDT",
            price=current_price,
            volume=volume,
            timestamp=base_time + timedelta(hours=i),
            source="binance"
        ))
    
    return market_data


def create_sample_sentiment(sentiment_value: float = 60.0, confidence: float = 0.7) -> SentimentScore:
    """Create sample sentiment score"""
    return SentimentScore(
        sentiment_value=sentiment_value,
        confidence=confidence,
        key_factors=["market_news", "regulatory_updates", "institutional_activity"]
    )


def create_sample_technical_signal(signal_strength: float = 0.5, 
                                 signal_type: SignalType = SignalType.BUY) -> TechnicalSignal:
    """Create sample technical signal"""
    return TechnicalSignal(
        signal_strength=signal_strength,
        signal_type=signal_type,
        confidence=0.7,
        contributing_indicators=["RSI", "MACD", "Moving_Averages"]
    )


def demonstrate_market_regime_detection():
    """Demonstrate market regime detection for different scenarios"""
    print("=== Market Regime Detection Demo ===")
    
    evaluator = MarketConditionEvaluator()
    
    scenarios = [
        {
            "name": "Bullish Trend",
            "data": create_trending_market_data(45000, 1, 24, 0.02),
            "sentiment": create_sample_sentiment(75.0, 0.8)
        },
        {
            "name": "Bearish Trend", 
            "data": create_trending_market_data(45000, -1, 24, 0.02),
            "sentiment": create_sample_sentiment(30.0, 0.8)
        },
        {
            "name": "High Volatility",
            "data": create_volatile_market_data(45000, 24, 0.08),
            "sentiment": create_sample_sentiment(50.0, 0.5)
        },
        {
            "name": "Sideways Market",
            "data": create_sideways_market_data(45000, 24, 0.02),
            "sentiment": create_sample_sentiment(55.0, 0.6)
        },
        {
            "name": "Low Volume",
            "data": create_low_volume_market_data(45000, 24),
            "sentiment": create_sample_sentiment(60.0, 0.7)
        }
    ]
    
    for scenario in scenarios:
        print(f"\n--- {scenario['name']} ---")
        
        assessment = evaluator.evaluate_market_conditions(
            market_data=scenario['data'],
            sentiment_score=scenario['sentiment']
        )
        
        print(f"  Primary Regime: {assessment.primary_regime.value}")
        print(f"  Secondary Regimes: {[r.value for r in assessment.secondary_regimes]}")
        print(f"  Regime Confidence: {assessment.regime_confidence:.2%}")
        print(f"  Trading Recommendation: {assessment.trading_recommendation.value}")
        print(f"  Volatility Score: {assessment.volatility_score:.2f}")
        print(f"  Volume Score: {assessment.volume_score:.2f}")
        print(f"  Trend Strength: {assessment.trend_strength:.2f}")
        print(f"  Momentum Score: {assessment.momentum_score:.2f}")
        print(f"  Risk Factors: {assessment.risk_factors}")
        print(f"  Opportunity Factors: {assessment.opportunity_factors}")


def demonstrate_trading_suitability():
    """Demonstrate trading suitability assessment"""
    print("\n=== Trading Suitability Assessment ===")
    
    evaluator = MarketConditionEvaluator()
    
    # Test different market conditions
    test_cases = [
        {
            "name": "Ideal Conditions",
            "data": create_trending_market_data(45000, 1, 24, 0.015),  # Low volatility uptrend
            "sentiment": create_sample_sentiment(80.0, 0.9)
        },
        {
            "name": "High Risk Conditions",
            "data": create_volatile_market_data(45000, 24, 0.12),  # Very high volatility
            "sentiment": create_sample_sentiment(40.0, 0.4)
        },
        {
            "name": "Low Volume Conditions",
            "data": create_low_volume_market_data(45000, 24),
            "sentiment": create_sample_sentiment(60.0, 0.7)
        }
    ]
    
    for case in test_cases:
        print(f"\n--- {case['name']} ---")
        
        assessment = evaluator.evaluate_market_conditions(
            market_data=case['data'],
            sentiment_score=case['sentiment']
        )
        
        is_suitable = evaluator.is_suitable_for_trading(assessment)
        
        print(f"  Trading Recommendation: {assessment.trading_recommendation.value}")
        print(f"  Suitable for Trading: {is_suitable}")
        print(f"  Data Quality Score: {assessment.data_quality_score:.2f}")
        print(f"  Entry Timing Score: {assessment.entry_timing_score:.2f}")
        print(f"  Exit Timing Score: {assessment.exit_timing_score:.2f}")
        print(f"  Reasoning: {assessment.recommendation_reasoning}")


def demonstrate_dynamic_strategy_adjustments():
    """Demonstrate dynamic strategy adjustments"""
    print("\n=== Dynamic Strategy Adjustments ===")
    
    evaluator = MarketConditionEvaluator()
    
    # Test different market conditions for strategy adjustments
    scenarios = [
        {
            "name": "High Volatility Market",
            "data": create_volatile_market_data(45000, 24, 0.08)
        },
        {
            "name": "Strong Trending Market",
            "data": create_trending_market_data(45000, 1, 24, 0.02)
        },
        {
            "name": "Low Volume Market",
            "data": create_low_volume_market_data(45000, 24)
        }
    ]
    
    for scenario in scenarios:
        print(f"\n--- {scenario['name']} ---")
        
        assessment = evaluator.evaluate_market_conditions(
            market_data=scenario['data'],
            sentiment_score=create_sample_sentiment(60.0, 0.7)
        )
        
        adjustments = evaluator.get_dynamic_strategy_adjustments(assessment)
        
        print(f"  Primary Regime: {assessment.primary_regime.value}")
        print(f"  Position Size Multiplier: {adjustments['position_size_multiplier']:.2f}")
        print(f"  Stop Loss Adjustment: {adjustments['stop_loss_adjustment']:.2f}")
        print(f"  Take Profit Adjustment: {adjustments['take_profit_adjustment']:.2f}")
        print(f"  Confidence Threshold Adjustment: {adjustments['confidence_threshold_adjustment']:+.2f}")
        print(f"  Recommended Timeframe: {adjustments['recommended_timeframe']}")
        print(f"  Special Instructions: {adjustments['special_instructions']}")


def demonstrate_comprehensive_analysis():
    """Demonstrate comprehensive market analysis"""
    print("\n=== Comprehensive Market Analysis ===")
    
    evaluator = MarketConditionEvaluator(
        volatility_threshold=0.04,  # 4% volatility threshold
        volume_threshold=1200000,   # 1.2M volume threshold
        trend_lookback_hours=48,    # 48-hour trend analysis
        momentum_lookback_hours=12  # 12-hour momentum analysis
    )
    
    # Create a complex market scenario
    market_data = create_trending_market_data(45000, 1, 48, 0.03)  # 48-hour uptrend
    
    # Add some recent volatility
    recent_volatile_data = create_volatile_market_data(
        market_data[-1].price, 6, 0.06  # Last 6 hours volatile
    )
    
    # Combine the data
    combined_data = market_data[:-6] + recent_volatile_data
    
    sentiment = create_sample_sentiment(70.0, 0.8)
    technical = create_sample_technical_signal(0.6, SignalType.BUY)
    
    print("Analyzing complex market scenario:")
    print(f"  Data Points: {len(combined_data)}")
    print(f"  Price Range: ${combined_data[0].price:.0f} - ${combined_data[-1].price:.0f}")
    print(f"  Time Span: {(combined_data[-1].timestamp - combined_data[0].timestamp).total_seconds() / 3600:.1f} hours")
    
    assessment = evaluator.evaluate_market_conditions(
        market_data=combined_data,
        sentiment_score=sentiment,
        technical_signal=technical
    )
    
    print(f"\nComprehensive Assessment:")
    print(f"  Primary Regime: {assessment.primary_regime.value}")
    print(f"  Secondary Regimes: {[r.value for r in assessment.secondary_regimes]}")
    print(f"  Regime Confidence: {assessment.regime_confidence:.2%}")
    print(f"  Trading Recommendation: {assessment.trading_recommendation.value}")
    print(f"  Recommendation Reasoning: {assessment.recommendation_reasoning}")
    
    print(f"\nMarket Metrics:")
    print(f"  Volatility Score: {assessment.volatility_score:.2f}")
    print(f"  Volume Score: {assessment.volume_score:.2f}")
    print(f"  Trend Strength: {assessment.trend_strength:.2f}")
    print(f"  Momentum Score: {assessment.momentum_score:.2f}")
    
    print(f"\nTiming Analysis:")
    print(f"  Entry Timing Score: {assessment.entry_timing_score:.2f}")
    print(f"  Exit Timing Score: {assessment.exit_timing_score:.2f}")
    
    print(f"\nRisk Assessment:")
    print(f"  Risk Factors: {assessment.risk_factors}")
    print(f"  Opportunity Factors: {assessment.opportunity_factors}")
    print(f"  Data Quality Score: {assessment.data_quality_score:.2f}")
    
    # Get strategy adjustments
    adjustments = evaluator.get_dynamic_strategy_adjustments(assessment)
    print(f"\nStrategy Adjustments:")
    for key, value in adjustments.items():
        if key != 'special_instructions':
            print(f"  {key}: {value}")
    if adjustments['special_instructions']:
        print(f"  Special Instructions: {', '.join(adjustments['special_instructions'])}")
    
    # Check trading suitability
    is_suitable = evaluator.is_suitable_for_trading(assessment)
    print(f"\nTrading Suitability: {'✓ Suitable' if is_suitable else '✗ Not Suitable'}")


def main():
    """Run all demonstration examples"""
    print("Market Conditions Evaluator Demonstration")
    print("=" * 60)
    
    try:
        demonstrate_market_regime_detection()
        demonstrate_trading_suitability()
        demonstrate_dynamic_strategy_adjustments()
        demonstrate_comprehensive_analysis()
        
        print("\n" + "=" * 60)
        print("Market conditions evaluation demonstration completed successfully!")
        
    except Exception as e:
        print(f"Error during demonstration: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()