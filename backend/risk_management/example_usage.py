"""
Risk Management Example Usage
Demonstrates comprehensive risk assessment and management functionality
"""
import sys
import os
from datetime import datetime, timedelta
import random
import numpy as np

# Add the backend directory to the Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.data_models import (
    TradingDecision, Portfolio, Position, ActionType, RiskLevel, 
    PriceRange, MarketData
)
from decision_engine.risk_parameters import RiskParameters
from risk_management.risk_manager import RiskManager
from risk_management.position_sizer import PositionSizer
from risk_management.stop_loss_calculator import StopLossCalculator, StopLossMethod
from risk_management.protection_manager import ProtectionManager


def create_sample_portfolio(btc_balance: float = 0.5, usdt_balance: float = 10000.0,
                          current_btc_price: float = 45000.0) -> Portfolio:
    """Create a sample portfolio for testing"""
    btc_position = Position(
        symbol="BTCUSDT",
        amount=btc_balance,
        entry_price=current_btc_price * 0.95,  # Entered at 5% lower
        current_price=current_btc_price,
        pnl=btc_balance * current_btc_price * 0.05,  # 5% profit
        entry_time=datetime.utcnow() - timedelta(days=2)
    )
    
    total_value = btc_balance * current_btc_price + usdt_balance
    
    return Portfolio(
        btc_balance=btc_balance,
        usdt_balance=usdt_balance,
        total_value_usdt=total_value,
        unrealized_pnl=btc_position.pnl,
        positions=[btc_position]
    )


def create_sample_trading_decision(action: ActionType = ActionType.BUY,
                                 confidence: float = 0.75,
                                 suggested_amount: float = 0.1) -> TradingDecision:
    """Create a sample trading decision"""
    current_price = 45000.0
    
    return TradingDecision(
        action=action,
        confidence=confidence,
        suggested_amount=suggested_amount,
        price_range=PriceRange(
            min_price=current_price * 0.995,
            max_price=current_price * 1.005
        ),
        reasoning="Sample trading decision for risk assessment",
        risk_level=RiskLevel.MEDIUM
    )


def create_sample_market_data(hours: int = 48, base_price: float = 45000.0,
                            volatility: float = 0.03) -> list:
    """Create sample market data with realistic price movements"""
    market_data = []
    current_price = base_price
    base_time = datetime.utcnow() - timedelta(hours=hours)
    
    for i in range(hours):
        # Add some trend and volatility
        trend = np.sin(i / 12) * 0.001  # Slight cyclical trend
        noise = random.gauss(0, volatility)
        
        price_change = (trend + noise) * current_price
        current_price = max(base_price * 0.8, min(base_price * 1.2, current_price + price_change))
        
        # Volume varies with volatility
        base_volume = 1500000
        volume_variation = abs(noise) * 1000000
        volume = base_volume + volume_variation
        
        market_data.append(MarketData(
            symbol="BTCUSDT",
            price=current_price,
            volume=volume,
            timestamp=base_time + timedelta(hours=i),
            source="binance"
        ))
    
    return market_data


def demonstrate_risk_assessment():
    """Demonstrate comprehensive risk assessment"""
    print("=== Risk Assessment Demo ===")
    
    # Create test data
    portfolio = create_sample_portfolio()
    decision = create_sample_trading_decision()
    market_data = create_sample_market_data()
    
    # Initialize risk manager
    risk_manager = RiskManager()
    
    print(f"Portfolio: ${portfolio.total_value_usdt:,.2f} total value")
    print(f"Decision: {decision.action.value} {decision.suggested_amount:.1%} with {decision.confidence:.1%} confidence")
    
    # Perform risk assessment
    risk_assessment = risk_manager.assess_trade_risk(decision, portfolio, market_data)
    
    print(f"\nRisk Assessment Results:")
    print(f"  Overall Risk Score: {risk_assessment.overall_risk_score:.1f}/100")
    print(f"  Risk Level: {risk_assessment.risk_level.value}")
    print(f"  Max Loss Potential: ${risk_assessment.max_loss_potential:,.2f}")
    print(f"  Recommended Position Size: {risk_assessment.recommended_position_size:.2%}")
    
    print(f"\nRisk Breakdown:")
    print(f"  Market Risk: {risk_assessment.market_risk_score:.2f}")
    print(f"  Liquidity Risk: {risk_assessment.liquidity_risk_score:.2f}")
    print(f"  Concentration Risk: {risk_assessment.concentration_risk_score:.2f}")
    print(f"  Volatility Risk: {risk_assessment.volatility_risk_score:.2f}")
    print(f"  Drawdown Risk: {risk_assessment.drawdown_risk_score:.2f}")
    print(f"  Operational Risk: {risk_assessment.operational_risk_score:.2f}")
    
    print(f"\nPortfolio Impact:")
    print(f"  Risk Before Trade: {risk_assessment.portfolio_risk_before:.2%}")
    print(f"  Risk After Trade: {risk_assessment.portfolio_risk_after:.2%}")
    print(f"  Risk Change: {risk_assessment.risk_change:+.2%}")
    
    if risk_assessment.risk_factors:
        print(f"\nRisk Factors:")
        for rf in risk_assessment.risk_factors:
            if rf.score > 0.5:  # Only show significant risk factors
                print(f"  - {rf.name}: {rf.score:.2f} (Impact: {rf.impact:.2f})")
                print(f"    {rf.description}")
    
    if risk_assessment.risk_mitigation_actions:
        print(f"\nRisk Mitigation Actions:")
        for action in risk_assessment.risk_mitigation_actions[:3]:  # Show top 3
            print(f"  - {action}")


def demonstrate_trade_validation():
    """Demonstrate trade validation"""
    print("\n=== Trade Validation Demo ===")
    
    portfolio = create_sample_portfolio()
    risk_manager = RiskManager()
    
    # Test different scenarios
    scenarios = [
        {
            "name": "Normal Trade",
            "decision": create_sample_trading_decision(ActionType.BUY, 0.8, 0.05)
        },
        {
            "name": "High Risk Trade",
            "decision": create_sample_trading_decision(ActionType.BUY, 0.6, 0.2)
        },
        {
            "name": "Low Confidence Trade",
            "decision": create_sample_trading_decision(ActionType.BUY, 0.4, 0.1)
        }
    ]
    
    for scenario in scenarios:
        print(f"\n--- {scenario['name']} ---")
        decision = scenario['decision']
        
        is_valid, violations = risk_manager.validate_trade(decision, portfolio)
        
        print(f"  Action: {decision.action.value}")
        print(f"  Position Size: {decision.suggested_amount:.1%}")
        print(f"  Confidence: {decision.confidence:.1%}")
        print(f"  Valid: {'✓' if is_valid else '✗'}")
        
        if violations:
            print(f"  Violations:")
            for violation in violations:
                print(f"    - {violation}")


def demonstrate_position_sizing():
    """Demonstrate position sizing methods"""
    print("\n=== Position Sizing Demo ===")
    
    portfolio = create_sample_portfolio()
    decision = create_sample_trading_decision()
    position_sizer = PositionSizer()
    
    print(f"Portfolio Value: ${portfolio.total_value_usdt:,.2f}")
    print(f"Decision Confidence: {decision.confidence:.1%}")
    
    # Test different sizing methods
    print(f"\nPosition Sizing Methods:")
    
    # Fixed percentage
    fixed_size = position_sizer.fixed_percentage_sizing(portfolio)
    print(f"  Fixed Percentage: {fixed_size:.2%}")
    
    # Confidence-based
    confidence_size = position_sizer.confidence_based_sizing(decision, portfolio)
    print(f"  Confidence-Based: {confidence_size:.2%}")
    
    # Risk parity
    risk_parity_size = position_sizer.risk_parity_sizing(portfolio)
    print(f"  Risk Parity: {risk_parity_size:.2%}")
    
    # Volatility-adjusted (with sample volatility)
    vol_size = position_sizer.volatility_adjusted_sizing(portfolio, 0.04)
    print(f"  Volatility-Adjusted: {vol_size:.2%}")
    
    # Kelly criterion (with sample performance data)
    kelly_size = position_sizer.kelly_criterion_sizing(0.6, 0.08, 0.04, portfolio)
    print(f"  Kelly Criterion: {kelly_size:.2%}")
    
    # Adaptive sizing
    market_data = {'volatility': 0.04, 'current_price': 45000}
    performance_data = {'win_rate': 0.6, 'avg_win': 0.08, 'avg_loss': 0.04}
    
    adaptive_size = position_sizer.adaptive_sizing(
        decision, portfolio, market_data['volatility'], performance_data
    )
    print(f"  Adaptive Sizing: {adaptive_size:.2%}")
    
    # Get comprehensive recommendation
    recommendation = position_sizer.get_sizing_recommendation(
        decision, portfolio, market_data, performance_data
    )
    
    print(f"\nRecommended Size: {recommendation['recommended_size']:.2%}")
    print(f"Position Value: ${recommendation['position_details']['position_value_usdt']:,.2f}")
    print(f"BTC Quantity: {recommendation['position_details']['btc_quantity']:.4f}")
    print(f"Validation: {'✓' if recommendation['validation']['is_valid'] else '✗'}")


def demonstrate_stop_loss_calculation():
    """Demonstrate stop loss calculation methods"""
    print("\n=== Stop Loss Calculation Demo ===")
    
    entry_price = 45000.0
    action = ActionType.BUY
    market_data = create_sample_market_data()
    
    stop_loss_calc = StopLossCalculator()
    
    print(f"Entry Price: ${entry_price:,.2f}")
    print(f"Action: {action.value}")
    
    # Test different stop loss methods
    methods = [
        (StopLossMethod.FIXED_PERCENTAGE, "Fixed Percentage"),
        (StopLossMethod.ATR_BASED, "ATR-Based"),
        (StopLossMethod.SUPPORT_RESISTANCE, "Support/Resistance"),
        (StopLossMethod.VOLATILITY_ADJUSTED, "Volatility-Adjusted")
    ]
    
    print(f"\nStop Loss Methods:")
    
    for method, name in methods:
        try:
            result = stop_loss_calc.calculate_optimal_stop_loss(
                entry_price, action, market_data, method
            )
            
            print(f"  {name}:")
            print(f"    Stop Loss: ${result['stop_loss_price']:,.2f}")
            print(f"    Risk Amount: ${result['risk_amount']:,.2f}")
            print(f"    Risk Percentage: {result['risk_percentage']:.2%}")
            
        except Exception as e:
            print(f"  {name}: Error - {str(e)}")
    
    # Get comprehensive recommendation
    recommendation = stop_loss_calc.get_stop_loss_recommendation(
        entry_price, action, market_data, 0.1
    )
    
    print(f"\nRecommended Stop Loss: ${recommendation['recommended_stop_loss']:,.2f}")
    print(f"Risk per Unit: ${recommendation['risk_amount_per_unit']:,.2f}")
    print(f"Total Position Risk: ${recommendation['total_position_risk']:,.2f}")
    print(f"Validation: {'✓' if recommendation['validation']['is_valid'] else '✗'}")


def demonstrate_portfolio_monitoring():
    """Demonstrate portfolio risk monitoring"""
    print("\n=== Portfolio Risk Monitoring Demo ===")
    
    portfolio = create_sample_portfolio()
    market_data = create_sample_market_data()
    risk_manager = RiskManager()
    
    # Simulate some trading activity
    risk_manager.update_trade_outcome(-500.0, False)  # Losing trade
    risk_manager.update_trade_outcome(800.0, True)    # Winning trade
    risk_manager.update_trade_outcome(-200.0, False)  # Small loss
    
    # Monitor portfolio risk
    risk_status = risk_manager.monitor_portfolio_risk(portfolio, market_data)
    
    print(f"Portfolio Risk Monitoring:")
    print(f"  Overall Risk Level: {risk_status['overall_risk_level']}")
    print(f"  Current Drawdown: {risk_status['current_drawdown']:.2%}")
    print(f"  Max Drawdown: {risk_status['max_drawdown']:.2%}")
    print(f"  Portfolio Volatility: {risk_status['portfolio_volatility']:.2%}")
    print(f"  Daily Loss: ${risk_status['daily_loss']:,.2f}")
    print(f"  Daily Loss Limit: ${risk_status['daily_loss_limit'] * portfolio.total_value_usdt:,.2f}")
    
    if risk_status['risk_alerts']:
        print(f"  Risk Alerts:")
        for alert in risk_status['risk_alerts']:
            print(f"    - {alert}")
    
    # Get risk manager status
    manager_status = risk_manager.get_risk_manager_status()
    
    print(f"\nRisk Manager Statistics:")
    print(f"  Total Trades: {manager_status['total_trades']}")
    print(f"  Recent Win Rate: {manager_status['recent_win_rate']:.1%}")
    print(f"  Recent Avg PnL: ${manager_status['recent_avg_pnl']:,.2f}")
    print(f"  Recent Total PnL: ${manager_status['recent_total_pnl']:,.2f}")


def demonstrate_protection_management():
    """Demonstrate protection manager integration"""
    print("\n=== Protection Management Demo ===")
    
    portfolio = create_sample_portfolio()
    protection_manager = ProtectionManager()
    
    print(f"Portfolio: ${portfolio.total_value_usdt:,.2f} total value")
    
    # Create protection for all positions
    for position in portfolio.positions:
        # Create stop loss
        stop_loss = protection_manager.create_stop_loss_order(position)
        print(f"  Stop Loss for {position.symbol}: ${stop_loss.trigger_price:,.2f}")
        
        # Create trailing stop
        trailing_stop = protection_manager.create_trailing_stop_order(position, trail_percentage=0.05)
        print(f"  Trailing Stop for {position.symbol}: ${trailing_stop.trigger_price:,.2f}")
    
    # Get protection summary
    summary = protection_manager.get_protection_summary(portfolio)
    print(f"\nProtection Summary:")
    print(f"  Protected Positions: {summary.protected_positions}/{summary.total_positions}")
    print(f"  Protection Coverage: {summary.protection_coverage:.1%}")
    print(f"  Max Potential Loss: ${summary.max_potential_loss:,.2f}")
    
    # Simulate price movements
    print(f"\nSimulating price movements...")
    current_prices = {"BTCUSDT": 44000.0}  # Price drop
    
    # Update trailing stops
    updates = protection_manager.update_trailing_stops(current_prices)
    print(f"  Trailing stop updates: {updates}")
    
    # Check for triggers
    triggered = protection_manager.check_protection_triggers(current_prices)
    print(f"  Triggered orders: {len(triggered)}")
    
    for order in triggered:
        execution_result = protection_manager.execute_protection_order(order, current_prices[order.position_symbol])
        print(f"    Executed {order.protection_type.value} for {order.position_symbol}")


def demonstrate_integrated_risk_management():
    """Demonstrate integrated risk management workflow"""
    print("\n=== Integrated Risk Management Workflow ===")
    
    # Setup
    portfolio = create_sample_portfolio()
    decision = create_sample_trading_decision(ActionType.BUY, 0.8, 0.08)
    market_data = create_sample_market_data()
    
    risk_manager = RiskManager()
    position_sizer = PositionSizer()
    stop_loss_calc = StopLossCalculator()
    protection_manager = ProtectionManager()
    
    print(f"Initial Decision: {decision.action.value} {decision.suggested_amount:.1%}")
    
    # Step 1: Risk Assessment
    risk_assessment = risk_manager.assess_trade_risk(decision, portfolio, market_data)
    print(f"\n1. Risk Assessment: {risk_assessment.risk_level.value} ({risk_assessment.overall_risk_score:.1f}/100)")
    
    # Step 2: Position Sizing
    sizing_recommendation = position_sizer.get_sizing_recommendation(
        decision, portfolio, 
        {'volatility': 0.04, 'current_price': 45000},
        {'win_rate': 0.65, 'avg_win': 0.06, 'avg_loss': 0.03}
    )
    adjusted_size = sizing_recommendation['recommended_size']
    print(f"2. Position Sizing: {adjusted_size:.2%} (adjusted from {decision.suggested_amount:.2%})")
    
    # Step 3: Stop Loss Calculation
    entry_price = 45000.0
    stop_loss_recommendation = stop_loss_calc.get_stop_loss_recommendation(
        entry_price, decision.action, market_data, adjusted_size
    )
    stop_loss_price = stop_loss_recommendation['recommended_stop_loss']
    print(f"3. Stop Loss: ${stop_loss_price:,.2f} (risk: {stop_loss_recommendation['risk_percentage']:.2%})")
    
    # Step 4: Trade Validation
    # Create adjusted decision
    adjusted_decision = TradingDecision(
        action=decision.action,
        confidence=decision.confidence,
        suggested_amount=adjusted_size,
        price_range=decision.price_range,
        reasoning=decision.reasoning,
        risk_level=risk_assessment.risk_level
    )
    
    is_valid, violations = risk_manager.validate_trade(adjusted_decision, portfolio, risk_assessment)
    print(f"4. Trade Validation: {'✓ Approved' if is_valid else '✗ Rejected'}")
    
    if violations:
        print(f"   Violations: {', '.join(violations)}")
    
    # Step 5: Protection Setup (if trade is valid)
    if is_valid:
        # Simulate position creation after trade execution
        new_position = Position(
            symbol="BTCUSDT",
            amount=adjusted_size * portfolio.total_value_usdt / entry_price,
            entry_price=entry_price,
            current_price=entry_price,
            pnl=0.0,
            entry_time=datetime.utcnow()
        )
        
        # Create protection orders
        stop_loss_order = protection_manager.create_stop_loss_order(new_position, stop_loss_price)
        take_profit_order = protection_manager.create_take_profit_order(new_position, profit_percentage=0.08)
        
        print(f"5. Protection Setup:")
        print(f"   Stop Loss Order: ${stop_loss_order.trigger_price:,.2f}")
        print(f"   Take Profit Order: ${take_profit_order.trigger_price:,.2f}")
    
    # Step 6: Final Recommendation
    print(f"\nFinal Recommendation:")
    if is_valid:
        position_value = adjusted_size * portfolio.total_value_usdt
        max_loss = stop_loss_recommendation['total_position_risk']
        
        print(f"  Execute {decision.action.value} order")
        print(f"  Position Size: {adjusted_size:.2%} (${position_value:,.2f})")
        print(f"  Entry Price: ${entry_price:,.2f}")
        print(f"  Stop Loss: ${stop_loss_price:,.2f}")
        print(f"  Maximum Risk: ${max_loss:,.2f}")
        print(f"  Risk/Reward Ratio: 1:{(entry_price * 0.04) / (entry_price - stop_loss_price):.1f}")
        print(f"  Protection orders will be automatically created")
    else:
        print(f"  Do not execute trade due to risk violations")


def main():
    """Run all risk management demonstrations"""
    print("Risk Management System Demonstration")
    print("=" * 60)
    
    try:
        demonstrate_risk_assessment()
        demonstrate_trade_validation()
        demonstrate_position_sizing()
        demonstrate_stop_loss_calculation()
        demonstrate_portfolio_monitoring()
        demonstrate_protection_management()
        demonstrate_integrated_risk_management()
        
        print("\n" + "=" * 60)
        print("Risk management demonstration completed successfully!")
        
    except Exception as e:
        print(f"Error during demonstration: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()