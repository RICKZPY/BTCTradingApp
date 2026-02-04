"""
Decision Engine Example Usage
Demonstrates how to use the decision engine to generate trading decisions
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add the backend directory to the Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.data_models import (
    SentimentScore, TechnicalSignal, SignalType, Portfolio, Position, MarketData
)
from decision_engine.engine import DecisionEngine, MarketAnalysis
from decision_engine.risk_parameters import RiskParameters


def create_sample_sentiment_score(sentiment_value: float = 75.0, confidence: float = 0.8) -> SentimentScore:
    """Create a sample sentiment score for testing"""
    return SentimentScore(
        sentiment_value=sentiment_value,
        confidence=confidence,
        key_factors=["positive_regulatory_news", "institutional_adoption", "technical_breakthrough"]
    )


def create_sample_technical_signal(signal_strength: float = 0.6, signal_type: SignalType = SignalType.BUY) -> TechnicalSignal:
    """Create a sample technical signal for testing"""
    return TechnicalSignal(
        signal_strength=signal_strength,
        signal_type=signal_type,
        confidence=0.75,
        contributing_indicators=["RSI(25.5)", "MACD(0.0045)", "Bollinger_Bands"]
    )


def create_sample_portfolio() -> Portfolio:
    """Create a sample portfolio for testing"""
    btc_position = Position(
        symbol="BTCUSDT",
        amount=0.5,
        entry_price=45000.0,
        current_price=47000.0,
        pnl=1000.0,
        entry_time=datetime.utcnow() - timedelta(days=2)
    )
    
    return Portfolio(
        btc_balance=0.5,
        usdt_balance=10000.0,
        total_value_usdt=33500.0,  # 0.5 * 47000 + 10000
        unrealized_pnl=1000.0,
        positions=[btc_position]
    )


def create_sample_market_data(current_price: float = 47000.0) -> list:
    """Create sample market data for volume and volatility analysis"""
    market_data = []
    base_time = datetime.utcnow() - timedelta(hours=24)
    
    for i in range(24):
        # Simulate price movement with some volatility
        price_variation = (i % 3 - 1) * 100  # Simple price variation
        price = current_price + price_variation
        
        # Simulate volume
        volume = 1500000 + (i % 5) * 200000
        
        market_data.append(MarketData(
            symbol="BTCUSDT",
            price=price,
            volume=volume,
            timestamp=base_time + timedelta(hours=i),
            source="binance"
        ))
    
    return market_data


def demonstrate_basic_decision_making():
    """Demonstrate basic decision making functionality"""
    print("=== Decision Engine Basic Demo ===")
    
    # Create decision engine with default risk parameters
    engine = DecisionEngine()
    
    # Create sample data
    sentiment = create_sample_sentiment_score(75.0, 0.8)  # Positive sentiment
    technical = create_sample_technical_signal(0.6, SignalType.BUY)  # Buy signal
    portfolio = create_sample_portfolio()
    current_price = 47000.0
    market_data = create_sample_market_data(current_price)
    
    print(f"Input Data:")
    print(f"  Sentiment: {sentiment.sentiment_value}/100 (confidence: {sentiment.confidence})")
    print(f"  Technical: {technical.signal_type.value} signal (strength: {technical.signal_strength})")
    print(f"  Current Price: ${current_price:,.2f}")
    print(f"  Portfolio Value: ${portfolio.total_value_usdt:,.2f}")
    
    # Analyze market conditions
    analysis = engine.analyze_market_conditions(
        sentiment_score=sentiment,
        technical_signal=technical,
        portfolio=portfolio,
        current_price=current_price,
        market_data=market_data
    )
    
    print(f"\nMarket Analysis:")
    print(f"  Combined Signal Strength: {analysis.combined_signal_strength}")
    print(f"  Overall Confidence: {analysis.overall_confidence:.2%}")
    print(f"  Market Condition: {analysis.market_condition}")
    print(f"  Risk Assessment: {analysis.risk_assessment}")
    print(f"  Sentiment Contribution: {analysis.sentiment_contribution}")
    print(f"  Technical Contribution: {analysis.technical_contribution}")
    
    # Generate trading decision
    decision = engine.generate_trading_decision(analysis)
    
    print(f"\nTrading Decision:")
    print(f"  Action: {decision.action.value}")
    print(f"  Confidence: {decision.confidence:.2%}")
    print(f"  Suggested Amount: {decision.suggested_amount:.2%} of portfolio")
    print(f"  Price Range: ${decision.price_range.min_price:,.2f} - ${decision.price_range.max_price:,.2f}")
    print(f"  Risk Level: {decision.risk_level.value}")
    print(f"  Reasoning: {decision.reasoning}")


def demonstrate_different_scenarios():
    """Demonstrate decision making under different market scenarios"""
    print("\n=== Different Market Scenarios ===")
    
    engine = DecisionEngine()
    portfolio = create_sample_portfolio()
    current_price = 47000.0
    
    scenarios = [
        {
            "name": "Bullish Scenario",
            "sentiment": create_sample_sentiment_score(85.0, 0.9),
            "technical": create_sample_technical_signal(0.8, SignalType.BUY)
        },
        {
            "name": "Bearish Scenario", 
            "sentiment": create_sample_sentiment_score(25.0, 0.8),
            "technical": create_sample_technical_signal(-0.7, SignalType.SELL)
        },
        {
            "name": "Conflicting Signals",
            "sentiment": create_sample_sentiment_score(80.0, 0.7),
            "technical": create_sample_technical_signal(-0.6, SignalType.SELL)
        },
        {
            "name": "Low Confidence",
            "sentiment": create_sample_sentiment_score(60.0, 0.4),
            "technical": create_sample_technical_signal(0.3, SignalType.HOLD)
        }
    ]
    
    for scenario in scenarios:
        print(f"\n--- {scenario['name']} ---")
        
        analysis = engine.analyze_market_conditions(
            sentiment_score=scenario['sentiment'],
            technical_signal=scenario['technical'],
            portfolio=portfolio,
            current_price=current_price
        )
        
        decision = engine.generate_trading_decision(analysis)
        
        print(f"  Signal Strength: {analysis.combined_signal_strength}")
        print(f"  Confidence: {analysis.overall_confidence:.2%}")
        print(f"  Decision: {decision.action.value}")
        print(f"  Position Size: {decision.suggested_amount:.2%}")
        print(f"  Risk Level: {decision.risk_level.value}")


def demonstrate_risk_parameters():
    """Demonstrate different risk parameter configurations"""
    print("\n=== Risk Parameter Configurations ===")
    
    sentiment = create_sample_sentiment_score(75.0, 0.8)
    technical = create_sample_technical_signal(0.6, SignalType.BUY)
    portfolio = create_sample_portfolio()
    current_price = 47000.0
    
    risk_configs = [
        ("Conservative", RiskParameters.conservative()),
        ("Balanced", RiskParameters.balanced()),
        ("Aggressive", RiskParameters.aggressive())
    ]
    
    for config_name, risk_params in risk_configs:
        print(f"\n--- {config_name} Configuration ---")
        
        engine = DecisionEngine(risk_params)
        
        analysis = engine.analyze_market_conditions(
            sentiment_score=sentiment,
            technical_signal=technical,
            portfolio=portfolio,
            current_price=current_price
        )
        
        decision = engine.generate_trading_decision(analysis)
        
        print(f"  Max Position Size: {risk_params.max_position_size:.1%}")
        print(f"  Min Confidence: {risk_params.min_confidence_threshold:.1%}")
        print(f"  Decision: {decision.action.value}")
        print(f"  Position Size: {decision.suggested_amount:.2%}")
        print(f"  Confidence Required: {analysis.overall_confidence:.2%}")


def demonstrate_constraint_checking():
    """Demonstrate trading constraint checking"""
    print("\n=== Trading Constraint Checking ===")
    
    # Create engine with restrictive parameters
    risk_params = RiskParameters(
        max_daily_loss=0.02,  # 2% daily loss limit
        trade_cooldown_minutes=60  # 1 hour cooldown
    )
    engine = DecisionEngine(risk_params)
    
    # Simulate daily loss
    engine.daily_loss = 0.025  # 2.5% loss (exceeds limit)
    
    sentiment = create_sample_sentiment_score(80.0, 0.9)
    technical = create_sample_technical_signal(0.8, SignalType.BUY)
    portfolio = create_sample_portfolio()
    current_price = 47000.0
    
    print("Testing with daily loss limit exceeded...")
    
    analysis = engine.analyze_market_conditions(
        sentiment_score=sentiment,
        technical_signal=technical,
        portfolio=portfolio,
        current_price=current_price
    )
    
    decision = engine.generate_trading_decision(analysis)
    
    print(f"  Daily Loss: {engine.daily_loss:.1%} (limit: {risk_params.max_daily_loss:.1%})")
    print(f"  Decision: {decision.action.value}")
    print(f"  Reasoning: {decision.reasoning}")
    
    # Test cooldown period
    print("\nTesting trade cooldown...")
    engine.daily_loss = 0.01  # Reset daily loss
    engine.last_trade_time = datetime.utcnow() - timedelta(minutes=30)  # 30 minutes ago
    
    decision2 = engine.generate_trading_decision(analysis)
    print(f"  Last Trade: 30 minutes ago (cooldown: {risk_params.trade_cooldown_minutes} minutes)")
    print(f"  Decision: {decision2.action.value}")
    print(f"  Reasoning: {decision2.reasoning}")


def demonstrate_engine_status():
    """Demonstrate engine status reporting"""
    print("\n=== Engine Status ===")
    
    engine = DecisionEngine()
    engine.daily_loss = 0.015  # 1.5% daily loss
    engine.last_trade_time = datetime.utcnow() - timedelta(minutes=45)
    
    status = engine.get_engine_status()
    
    print("Engine Status:")
    for key, value in status.items():
        if key == "risk_parameters":
            continue  # Skip detailed risk params for brevity
        print(f"  {key}: {value}")


def main():
    """Run all demonstration examples"""
    print("Decision Engine Demonstration")
    print("=" * 50)
    
    try:
        demonstrate_basic_decision_making()
        demonstrate_different_scenarios()
        demonstrate_risk_parameters()
        demonstrate_constraint_checking()
        demonstrate_engine_status()
        
        print("\n" + "=" * 50)
        print("Decision Engine demonstration completed successfully!")
        
    except Exception as e:
        print(f"Error during demonstration: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()