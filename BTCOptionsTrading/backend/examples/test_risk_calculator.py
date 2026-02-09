"""
Example usage of Risk Calculator.

Demonstrates:
1. Portfolio Greeks calculation
2. Value at Risk (VaR) calculation
3. Margin requirement calculation
4. Risk limit monitoring
5. Stress testing
"""

from datetime import datetime, timedelta
from src.core.models import OptionContract, Portfolio, Position, OptionType
from src.pricing.options_engine import OptionsEngine
from src.risk.risk_calculator import RiskCalculator


def print_section(title):
    """Print section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def main():
    """Run risk calculator examples."""
    
    # Initialize components
    options_engine = OptionsEngine()
    risk_calculator = RiskCalculator(options_engine)
    
    # Create a sample portfolio
    print_section("Creating Sample Portfolio")
    
    expiry = datetime.now() + timedelta(days=30)
    spot_price = 29000.0
    
    # Long call position (bullish)
    call_contract = OptionContract(
        symbol="BTC-30000-C",
        underlying="BTC",
        option_type=OptionType.CALL,
        strike_price=30000.0,
        expiry_date=expiry,
        implied_volatility=0.8
    )
    
    # Short put position (bullish)
    put_contract = OptionContract(
        symbol="BTC-28000-P",
        underlying="BTC",
        option_type=OptionType.PUT,
        strike_price=28000.0,
        expiry_date=expiry,
        implied_volatility=0.8
    )
    
    # Long straddle (volatility play)
    straddle_call = OptionContract(
        symbol="BTC-29000-C",
        underlying="BTC",
        option_type=OptionType.CALL,
        strike_price=29000.0,
        expiry_date=expiry,
        implied_volatility=0.8
    )
    
    straddle_put = OptionContract(
        symbol="BTC-29000-P",
        underlying="BTC",
        option_type=OptionType.PUT,
        strike_price=29000.0,
        expiry_date=expiry,
        implied_volatility=0.8
    )
    
    portfolio = Portfolio(name="Mixed Strategy Portfolio", initial_balance=100000.0)
    portfolio.add_position(Position(contract=call_contract, quantity=10))
    portfolio.add_position(Position(contract=put_contract, quantity=-5))
    portfolio.add_position(Position(contract=straddle_call, quantity=3))
    portfolio.add_position(Position(contract=straddle_put, quantity=3))
    
    print(f"Portfolio: {portfolio.name}")
    print(f"Initial Balance: ${portfolio.initial_balance:,.2f}")
    print(f"Number of Positions: {len(portfolio.positions)}")
    print(f"Current Spot Price: ${spot_price:,.2f}")
    
    for i, pos in enumerate(portfolio.positions, 1):
        print(f"\nPosition {i}:")
        print(f"  Symbol: {pos.contract.symbol}")
        print(f"  Type: {pos.contract.option_type.value}")
        print(f"  Strike: ${pos.contract.strike_price:,.2f}")
        print(f"  Quantity: {pos.quantity}")
        print(f"  IV: {pos.contract.implied_volatility:.1%}")
    
    # 1. Calculate Portfolio Greeks
    print_section("1. Portfolio Greeks")
    
    greeks = risk_calculator.calculate_portfolio_greeks(
        portfolio=portfolio,
        spot_price=spot_price
    )
    
    print(f"Total Delta: {greeks['delta']:.4f}")
    print(f"  → Portfolio will gain ${abs(greeks['delta']):.2f} for every $1 increase in BTC price")
    print(f"\nTotal Gamma: {greeks['gamma']:.6f}")
    print(f"  → Delta will change by {greeks['gamma']:.6f} for every $1 move in BTC price")
    print(f"\nTotal Theta: {greeks['theta']:.4f}")
    print(f"  → Portfolio loses ${abs(greeks['theta']):.2f} per day due to time decay")
    print(f"\nTotal Vega: {greeks['vega']:.4f}")
    print(f"  → Portfolio gains ${greeks['vega']:.2f} for every 1% increase in volatility")
    print(f"\nTotal Rho: {greeks['rho']:.4f}")
    print(f"  → Portfolio gains ${greeks['rho']:.2f} for every 1% increase in interest rates")
    
    # 2. Calculate Value at Risk (VaR)
    print_section("2. Value at Risk (VaR)")
    
    volatility = 0.8
    
    # 1-day VaR at 95% confidence
    var_1day_95 = risk_calculator.calculate_var(
        portfolio=portfolio,
        spot_price=spot_price,
        volatility=volatility,
        confidence_level=0.95,
        time_horizon_days=1
    )
    
    print("1-Day VaR (95% confidence):")
    print(f"  Portfolio Value: ${var_1day_95['portfolio_value']:,.2f}")
    print(f"  VaR: ${var_1day_95['var']:,.2f} ({var_1day_95['var_percentage']:.2f}%)")
    print(f"  CVaR (Expected Shortfall): ${var_1day_95['cvar']:,.2f}")
    print(f"  → 95% confident that losses won't exceed ${var_1day_95['var']:,.2f} in 1 day")
    
    # 1-day VaR at 99% confidence
    var_1day_99 = risk_calculator.calculate_var(
        portfolio=portfolio,
        spot_price=spot_price,
        volatility=volatility,
        confidence_level=0.99,
        time_horizon_days=1
    )
    
    print(f"\n1-Day VaR (99% confidence):")
    print(f"  VaR: ${var_1day_99['var']:,.2f} ({var_1day_99['var_percentage']:.2f}%)")
    print(f"  CVaR: ${var_1day_99['cvar']:,.2f}")
    
    # 10-day VaR
    var_10day = risk_calculator.calculate_var(
        portfolio=portfolio,
        spot_price=spot_price,
        volatility=volatility,
        confidence_level=0.95,
        time_horizon_days=10
    )
    
    print(f"\n10-Day VaR (95% confidence):")
    print(f"  VaR: ${var_10day['var']:,.2f} ({var_10day['var_percentage']:.2f}%)")
    print(f"  CVaR: ${var_10day['cvar']:,.2f}")
    
    # 3. Calculate Margin Requirements
    print_section("3. Margin Requirements (Deribit Rules)")
    
    margin = risk_calculator.calculate_margin_requirement(
        portfolio=portfolio,
        spot_price=spot_price
    )
    
    print(f"Initial Margin: ${margin['initial_margin']:,.2f}")
    print(f"Maintenance Margin: ${margin['maintenance_margin']:,.2f}")
    print(f"Premium Paid (Long Positions): ${margin['premium_paid']:,.2f}")
    print(f"Premium Received (Short Positions): ${margin['premium_received']:,.2f}")
    print(f"Total Margin Required: ${margin['total_margin_required']:,.2f}")
    
    available_balance = portfolio.initial_balance - margin['total_margin_required']
    print(f"\nAvailable Balance: ${available_balance:,.2f}")
    print(f"Margin Usage: {(margin['total_margin_required'] / portfolio.initial_balance * 100):.2f}%")
    
    # 4. Check Risk Limits
    print_section("4. Risk Limit Monitoring")
    
    # Set some risk limits
    risk_limits = risk_calculator.check_risk_limits(
        portfolio=portfolio,
        spot_price=spot_price,
        max_delta=20.0,
        max_gamma=0.01,
        max_vega=500.0,
        max_var_percentage=15.0
    )
    
    print(f"Risk Limit Check:")
    print(f"  Has Violations: {risk_limits['has_violations']}")
    print(f"  Number of Violations: {len(risk_limits['violations'])}")
    print(f"  Number of Warnings: {len(risk_limits['warnings'])}")
    
    if risk_limits['violations']:
        print("\n⚠️  VIOLATIONS:")
        for violation in risk_limits['violations']:
            print(f"  - {violation['message']}")
    
    if risk_limits['warnings']:
        print("\n⚠️  WARNINGS:")
        for warning in risk_limits['warnings']:
            print(f"  - {warning}")
    
    if not risk_limits['has_violations'] and not risk_limits['warnings']:
        print("\n✅ All risk limits are within acceptable ranges")
    
    # 5. Stress Testing
    print_section("5. Stress Testing")
    
    stress_result = risk_calculator.stress_test(
        portfolio=portfolio,
        spot_price=spot_price,
        price_shocks=[-0.30, -0.20, -0.10, -0.05, 0.05, 0.10, 0.20, 0.30],
        volatility_shocks=[-0.50, -0.25, 0.25, 0.50, 1.0]
    )
    
    print(f"Base Portfolio Value: ${stress_result['base_portfolio_value']:,.2f}")
    
    print("\nPrice Shock Scenarios:")
    print(f"{'Shock':<10} {'Price':<12} {'Portfolio Value':<18} {'P&L':<15} {'P&L %':<10}")
    print("-" * 75)
    for scenario in stress_result['price_scenarios']:
        shock_str = f"{scenario['shock_percentage']:+.1f}%"
        price_str = f"${scenario['shocked_price']:,.0f}"
        value_str = f"${scenario['portfolio_value']:,.2f}"
        pnl_str = f"${scenario['pnl']:+,.2f}"
        pnl_pct_str = f"{scenario['pnl_percentage']:+.2f}%"
        print(f"{shock_str:<10} {price_str:<12} {value_str:<18} {pnl_str:<15} {pnl_pct_str:<10}")
    
    print("\nVolatility Shock Scenarios:")
    print(f"{'Shock':<10} {'Portfolio Value':<18} {'P&L':<15} {'P&L %':<10}")
    print("-" * 60)
    for scenario in stress_result['volatility_scenarios']:
        shock_str = f"{scenario['shock_percentage']:+.1f}%"
        value_str = f"${scenario['portfolio_value']:,.2f}"
        pnl_str = f"${scenario['pnl']:+,.2f}"
        pnl_pct_str = f"{scenario['pnl_percentage']:+.2f}%"
        print(f"{shock_str:<10} {value_str:<18} {pnl_str:<15} {pnl_pct_str:<10}")
    
    print("\n⚠️  Worst Case Scenarios:")
    print(f"  Worst Price Shock: {stress_result['worst_price_scenario']['shock_percentage']:+.1f}% "
          f"→ P&L: ${stress_result['worst_price_scenario']['pnl']:+,.2f}")
    print(f"  Worst Volatility Shock: {stress_result['worst_volatility_scenario']['shock_percentage']:+.1f}% "
          f"→ P&L: ${stress_result['worst_volatility_scenario']['pnl']:+,.2f}")
    print(f"  Maximum Loss: ${stress_result['max_loss']:+,.2f}")
    
    # Summary
    print_section("Risk Summary")
    
    print(f"Portfolio: {portfolio.name}")
    print(f"Current Value: ${var_1day_95['portfolio_value']:,.2f}")
    print(f"Initial Balance: ${portfolio.initial_balance:,.2f}")
    print(f"\nRisk Metrics:")
    print(f"  Delta Exposure: {greeks['delta']:.2f}")
    print(f"  Gamma Exposure: {greeks['gamma']:.6f}")
    print(f"  Vega Exposure: {greeks['vega']:.2f}")
    print(f"  1-Day VaR (95%): ${var_1day_95['var']:,.2f} ({var_1day_95['var_percentage']:.2f}%)")
    print(f"  Margin Required: ${margin['total_margin_required']:,.2f}")
    print(f"  Max Stress Loss: ${stress_result['max_loss']:+,.2f}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
