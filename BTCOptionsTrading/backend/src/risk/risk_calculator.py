"""
Risk Calculator for portfolio risk analysis.

Implements:
- Portfolio Greeks aggregation
- Value at Risk (VaR) calculation
- Margin requirements (Deribit rules)
- Risk limit monitoring
- Stress testing
"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from scipy import stats

from ..core.models import OptionContract, Portfolio, OptionType
from ..pricing.options_engine import OptionsEngine

logger = logging.getLogger(__name__)


class RiskCalculator:
    """Calculate portfolio risk metrics and perform stress testing."""
    
    def __init__(self, options_engine: OptionsEngine):
        """
        Initialize risk calculator.
        
        Args:
            options_engine: Options pricing engine for Greeks calculation
        """
        self.options_engine = options_engine
        
    def calculate_portfolio_greeks(
        self,
        portfolio: Portfolio,
        spot_price: float,
        risk_free_rate: float = 0.05
    ) -> Dict[str, float]:
        """
        Calculate aggregated Greeks for entire portfolio.
        
        Args:
            portfolio: Portfolio containing option positions
            spot_price: Current spot price of underlying
            risk_free_rate: Risk-free interest rate
            
        Returns:
            Dictionary with total Delta, Gamma, Theta, Vega, Rho
        """
        total_greeks = {
            'delta': 0.0,
            'gamma': 0.0,
            'theta': 0.0,
            'vega': 0.0,
            'rho': 0.0
        }
        
        for position in portfolio.positions:
            contract = position.option_contract
            quantity = position.quantity
            
            # Calculate time to expiry in years
            time_to_expiry = (contract.expiration_date - datetime.now()).days / 365.0
            if time_to_expiry <= 0:
                continue  # Skip expired options
            
            # Calculate Greeks for this position
            greeks = self.options_engine.calculate_greeks(
                S=spot_price,
                K=float(contract.strike_price),
                T=time_to_expiry,
                sigma=contract.implied_volatility,
                r=risk_free_rate,
                option_type=contract.option_type
            )
            
            # Aggregate Greeks (multiply by quantity)
            total_greeks['delta'] += greeks.delta * quantity
            total_greeks['gamma'] += greeks.gamma * quantity
            total_greeks['theta'] += greeks.theta * quantity
            total_greeks['vega'] += greeks.vega * quantity
            total_greeks['rho'] += greeks.rho * quantity
            
        logger.info(f"Portfolio Greeks calculated: {total_greeks}")
        return total_greeks
    
    def calculate_var(
        self,
        portfolio: Portfolio,
        spot_price: float,
        volatility: float,
        confidence_level: float = 0.95,
        time_horizon_days: int = 1,
        risk_free_rate: float = 0.05
    ) -> Dict[str, float]:
        """
        Calculate Value at Risk (VaR) using delta-normal method.
        
        Args:
            portfolio: Portfolio containing option positions
            spot_price: Current spot price
            volatility: Historical volatility of underlying
            confidence_level: Confidence level (e.g., 0.95 for 95%)
            time_horizon_days: Time horizon in days
            risk_free_rate: Risk-free interest rate
            
        Returns:
            Dictionary with VaR, CVaR (Expected Shortfall), and portfolio value
        """
        # Calculate portfolio Greeks
        greeks = self.calculate_portfolio_greeks(portfolio, spot_price, risk_free_rate)
        
        # Calculate current portfolio value
        portfolio_value = 0.0
        for position in portfolio.positions:
            contract = position.option_contract
            time_to_expiry = (contract.expiration_date - datetime.now()).days / 365.0
            if time_to_expiry <= 0:
                continue
                
            price = self.options_engine.black_scholes_price(
                S=spot_price,
                K=float(contract.strike_price),
                T=time_to_expiry,
                r=risk_free_rate,
                sigma=contract.implied_volatility,
                option_type=contract.option_type
            )
            portfolio_value += price * position.quantity
        
        # Delta-normal VaR calculation
        # VaR = Portfolio_Delta * Spot_Price * Volatility * sqrt(time_horizon) * z_score
        time_factor = np.sqrt(time_horizon_days / 365.0)
        z_score = stats.norm.ppf(confidence_level)
        
        var_amount = abs(greeks['delta'] * spot_price * volatility * time_factor * z_score)
        
        # Calculate CVaR (Expected Shortfall)
        # CVaR = Portfolio_Delta * Spot_Price * Volatility * sqrt(time_horizon) * E[Z|Z>z]
        # E[Z|Z>z] = phi(z) / (1 - Phi(z)) where phi is PDF, Phi is CDF
        expected_excess = stats.norm.pdf(z_score) / (1 - stats.norm.cdf(z_score))
        cvar_amount = abs(greeks['delta'] * spot_price * volatility * time_factor * expected_excess)
        
        result = {
            'var': var_amount,
            'cvar': cvar_amount,
            'portfolio_value': portfolio_value,
            'var_percentage': (var_amount / portfolio_value * 100) if portfolio_value > 0 else 0,
            'confidence_level': confidence_level,
            'time_horizon_days': time_horizon_days
        }
        
        logger.info(f"VaR calculated: {var_amount:.2f} ({result['var_percentage']:.2f}%)")
        return result
    
    def calculate_margin_requirement(
        self,
        portfolio: Portfolio,
        spot_price: float,
        risk_free_rate: float = 0.05
    ) -> Dict[str, float]:
        """
        Calculate margin requirements based on Deribit rules.
        
        Deribit margin formula (simplified):
        - Long options: Premium paid (no additional margin)
        - Short options: max(0.15 * underlying - OTM_amount, 0.1 * underlying) + premium
        
        Args:
            portfolio: Portfolio containing option positions
            spot_price: Current spot price
            risk_free_rate: Risk-free interest rate
            
        Returns:
            Dictionary with initial margin, maintenance margin, and margin usage
        """
        initial_margin = 0.0
        maintenance_margin = 0.0
        premium_paid = 0.0
        premium_received = 0.0
        
        for position in portfolio.positions:
            contract = position.option_contract
            quantity = position.quantity
            
            # Calculate time to expiry
            time_to_expiry = (contract.expiration_date - datetime.now()).days / 365.0
            if time_to_expiry <= 0:
                continue
            
            # Calculate option price
            price = self.options_engine.black_scholes_price(
                S=spot_price,
                K=float(contract.strike_price),
                T=time_to_expiry,
                r=risk_free_rate,
                sigma=contract.implied_volatility,
                option_type=contract.option_type
            )
            
            if quantity > 0:
                # Long position - only premium paid
                premium_paid += price * quantity
            else:
                # Short position - calculate margin requirement
                premium_received += price * abs(quantity)
                
                # Calculate OTM amount
                if contract.option_type == OptionType.CALL:
                    otm_amount = max(0, float(contract.strike_price) - spot_price)
                else:  # PUT
                    otm_amount = max(0, spot_price - float(contract.strike_price))
                
                # Deribit margin formula
                margin_per_contract = max(
                    0.15 * spot_price - otm_amount,
                    0.1 * spot_price
                ) + price
                
                initial_margin += margin_per_contract * abs(quantity)
                maintenance_margin += margin_per_contract * 0.75 * abs(quantity)  # 75% of initial
        
        # Total margin requirement
        total_margin = initial_margin + premium_paid
        
        result = {
            'initial_margin': initial_margin,
            'maintenance_margin': maintenance_margin,
            'premium_paid': premium_paid,
            'premium_received': premium_received,
            'total_margin_required': total_margin,
            'margin_usage_percentage': 0.0  # Would need account balance to calculate
        }
        
        logger.info(f"Margin requirement: {total_margin:.2f}")
        return result
    
    def check_risk_limits(
        self,
        portfolio: Portfolio,
        spot_price: float,
        risk_free_rate: float = 0.05,
        max_delta: Optional[float] = None,
        max_gamma: Optional[float] = None,
        max_vega: Optional[float] = None,
        max_var_percentage: Optional[float] = None
    ) -> Dict[str, any]:
        """
        Check if portfolio exceeds risk limits.
        
        Args:
            portfolio: Portfolio to check
            spot_price: Current spot price
            risk_free_rate: Risk-free interest rate
            max_delta: Maximum allowed delta exposure
            max_gamma: Maximum allowed gamma exposure
            max_vega: Maximum allowed vega exposure
            max_var_percentage: Maximum allowed VaR as percentage of portfolio
            
        Returns:
            Dictionary with violations and warnings
        """
        violations = []
        warnings = []
        
        # Calculate Greeks
        greeks = self.calculate_portfolio_greeks(portfolio, spot_price, risk_free_rate)
        
        # Check delta limit
        if max_delta is not None and abs(greeks['delta']) > max_delta:
            violations.append({
                'type': 'delta',
                'current': greeks['delta'],
                'limit': max_delta,
                'message': f"Delta exposure {greeks['delta']:.2f} exceeds limit {max_delta:.2f}"
            })
        
        # Check gamma limit
        if max_gamma is not None and abs(greeks['gamma']) > max_gamma:
            violations.append({
                'type': 'gamma',
                'current': greeks['gamma'],
                'limit': max_gamma,
                'message': f"Gamma exposure {greeks['gamma']:.4f} exceeds limit {max_gamma:.4f}"
            })
        
        # Check vega limit
        if max_vega is not None and abs(greeks['vega']) > max_vega:
            violations.append({
                'type': 'vega',
                'current': greeks['vega'],
                'limit': max_vega,
                'message': f"Vega exposure {greeks['vega']:.2f} exceeds limit {max_vega:.2f}"
            })
        
        # Check VaR limit
        if max_var_percentage is not None:
            var_result = self.calculate_var(portfolio, spot_price, volatility=0.8)
            if var_result['var_percentage'] > max_var_percentage:
                violations.append({
                    'type': 'var',
                    'current': var_result['var_percentage'],
                    'limit': max_var_percentage,
                    'message': f"VaR {var_result['var_percentage']:.2f}% exceeds limit {max_var_percentage:.2f}%"
                })
        
        # Generate warnings for approaching limits (80% threshold)
        if max_delta is not None and abs(greeks['delta']) > max_delta * 0.8:
            warnings.append(f"Delta approaching limit: {greeks['delta']:.2f} / {max_delta:.2f}")
        
        if max_gamma is not None and abs(greeks['gamma']) > max_gamma * 0.8:
            warnings.append(f"Gamma approaching limit: {greeks['gamma']:.4f} / {max_gamma:.4f}")
        
        result = {
            'has_violations': len(violations) > 0,
            'violations': violations,
            'warnings': warnings,
            'greeks': greeks
        }
        
        if violations:
            logger.warning(f"Risk limit violations detected: {len(violations)}")
        
        return result
    
    def stress_test(
        self,
        portfolio: Portfolio,
        spot_price: float,
        risk_free_rate: float = 0.05,
        price_shocks: Optional[List[float]] = None,
        volatility_shocks: Optional[List[float]] = None
    ) -> Dict[str, any]:
        """
        Perform stress testing on portfolio under extreme scenarios.
        
        Args:
            portfolio: Portfolio to stress test
            spot_price: Current spot price
            risk_free_rate: Risk-free interest rate
            price_shocks: List of price shock percentages (e.g., [-0.2, -0.1, 0.1, 0.2])
            volatility_shocks: List of volatility shock percentages
            
        Returns:
            Dictionary with stress test results
        """
        if price_shocks is None:
            price_shocks = [-0.30, -0.20, -0.10, -0.05, 0.05, 0.10, 0.20, 0.30]
        
        if volatility_shocks is None:
            volatility_shocks = [-0.50, -0.25, 0.25, 0.50, 1.0]
        
        # Calculate base portfolio value
        base_value = 0.0
        for position in portfolio.positions:
            contract = position.option_contract
            time_to_expiry = (contract.expiration_date - datetime.now()).days / 365.0
            if time_to_expiry <= 0:
                continue
                
            price = self.options_engine.black_scholes_price(
                S=spot_price,
                K=float(contract.strike_price),
                T=time_to_expiry,
                r=risk_free_rate,
                sigma=contract.implied_volatility,
                option_type=contract.option_type
            )
            base_value += price * position.quantity
        
        # Test price shocks
        price_scenarios = []
        for shock in price_shocks:
            shocked_price = spot_price * (1 + shock)
            portfolio_value = 0.0
            
            for position in portfolio.positions:
                contract = position.option_contract
                time_to_expiry = (contract.expiration_date - datetime.now()).days / 365.0
                if time_to_expiry <= 0:
                    continue
                    
                price = self.options_engine.black_scholes_price(
                    S=shocked_price,
                    K=float(contract.strike_price),
                    T=time_to_expiry,
                    r=risk_free_rate,
                    sigma=contract.implied_volatility,
                    option_type=contract.option_type
                )
                portfolio_value += price * position.quantity
            
            pnl = portfolio_value - base_value
            pnl_percentage = (pnl / base_value * 100) if base_value != 0 else 0
            
            price_scenarios.append({
                'shock_percentage': shock * 100,
                'shocked_price': shocked_price,
                'portfolio_value': portfolio_value,
                'pnl': pnl,
                'pnl_percentage': pnl_percentage
            })
        
        # Test volatility shocks
        volatility_scenarios = []
        for shock in volatility_shocks:
            portfolio_value = 0.0
            
            for position in portfolio.positions:
                contract = position.option_contract
                time_to_expiry = (contract.expiration_date - datetime.now()).days / 365.0
                if time_to_expiry <= 0:
                    continue
                    
                shocked_vol = contract.implied_volatility * (1 + shock)
                price = self.options_engine.black_scholes_price(
                    S=spot_price,
                    K=float(contract.strike_price),
                    T=time_to_expiry,
                    r=risk_free_rate,
                    sigma=shocked_vol,
                    option_type=contract.option_type
                )
                portfolio_value += price * position.quantity
            
            pnl = portfolio_value - base_value
            pnl_percentage = (pnl / base_value * 100) if base_value != 0 else 0
            
            volatility_scenarios.append({
                'shock_percentage': shock * 100,
                'portfolio_value': portfolio_value,
                'pnl': pnl,
                'pnl_percentage': pnl_percentage
            })
        
        # Find worst case scenarios
        worst_price_scenario = min(price_scenarios, key=lambda x: x['pnl'])
        worst_vol_scenario = min(volatility_scenarios, key=lambda x: x['pnl'])
        
        result = {
            'base_portfolio_value': base_value,
            'price_scenarios': price_scenarios,
            'volatility_scenarios': volatility_scenarios,
            'worst_price_scenario': worst_price_scenario,
            'worst_volatility_scenario': worst_vol_scenario,
            'max_loss': min(worst_price_scenario['pnl'], worst_vol_scenario['pnl'])
        }
        
        logger.info(f"Stress test completed. Max loss: {result['max_loss']:.2f}")
        return result
    
    def calculate_strategy_risk(
        self,
        strategy_legs: List[Dict],
        spot_price: float,
        risk_free_rate: float = 0.05,
        volatility: float = 0.8
    ) -> Dict[str, any]:
        """
        Calculate comprehensive risk metrics for a strategy.
        
        Args:
            strategy_legs: List of strategy legs with option contracts
            spot_price: Current spot price of underlying
            risk_free_rate: Risk-free interest rate
            volatility: Historical volatility for VaR calculation
            
        Returns:
            Dictionary with Greeks, max profit/loss, breakeven points, and risk metrics
        """
        from ..core.models import OptionContract, OptionType
        from decimal import Decimal
        
        # Aggregate Greeks
        total_greeks = {
            'delta': 0.0,
            'gamma': 0.0,
            'theta': 0.0,
            'vega': 0.0,
            'rho': 0.0
        }
        
        # Calculate initial cost and Greeks
        initial_cost = 0.0
        legs_data = []
        
        for leg in strategy_legs:
            contract_data = leg['option_contract']
            action = leg['action']
            quantity = leg['quantity']
            
            # Parse expiration date
            if isinstance(contract_data['expiration_date'], str):
                expiry = datetime.fromisoformat(contract_data['expiration_date'].replace('Z', '+00:00'))
            else:
                expiry = contract_data['expiration_date']
            
            time_to_expiry = (expiry - datetime.now()).days / 365.0
            if time_to_expiry <= 0:
                time_to_expiry = 0.001  # Minimum time to avoid division by zero
            
            # Determine option type
            option_type = OptionType.CALL if contract_data['option_type'].lower() == 'call' else OptionType.PUT
            strike = float(contract_data['strike_price'])
            
            # Get implied volatility from contract or use default
            iv = contract_data.get('implied_volatility', volatility)
            
            # Calculate option price
            price = self.options_engine.black_scholes_price(
                S=spot_price,
                K=strike,
                T=time_to_expiry,
                r=risk_free_rate,
                sigma=iv,
                option_type=option_type
            )
            
            # Calculate Greeks
            greeks = self.options_engine.calculate_greeks(
                S=spot_price,
                K=strike,
                T=time_to_expiry,
                sigma=iv,
                r=risk_free_rate,
                option_type=option_type
            )
            
            # Determine multiplier based on action
            multiplier = 1 if action == 'buy' else -1
            
            # Update initial cost
            initial_cost += price * quantity * multiplier
            
            # Aggregate Greeks
            total_greeks['delta'] += greeks.delta * quantity * multiplier
            total_greeks['gamma'] += greeks.gamma * quantity * multiplier
            total_greeks['theta'] += greeks.theta * quantity * multiplier
            total_greeks['vega'] += greeks.vega * quantity * multiplier
            total_greeks['rho'] += greeks.rho * quantity * multiplier
            
            # Store leg data for payoff calculation
            legs_data.append({
                'strike': strike,
                'option_type': option_type,
                'action': action,
                'quantity': quantity,
                'price': price
            })
        
        # Calculate max profit, max loss, and breakeven points
        payoff_analysis = self._calculate_payoff_profile(legs_data, spot_price)
        
        result = {
            'greeks': total_greeks,
            'initial_cost': initial_cost,
            'max_profit': payoff_analysis['max_profit'],
            'max_loss': payoff_analysis['max_loss'],
            'breakeven_points': payoff_analysis['breakeven_points'],
            'risk_reward_ratio': payoff_analysis['risk_reward_ratio'],
            'probability_of_profit': payoff_analysis.get('probability_of_profit', None)
        }
        
        logger.info(f"Strategy risk calculated: Max Profit={result['max_profit']:.2f}, Max Loss={result['max_loss']:.2f}")
        return result
    
    def _calculate_payoff_profile(
        self,
        legs_data: List[Dict],
        spot_price: float,
        num_points: int = 200
    ) -> Dict[str, any]:
        """
        Calculate payoff profile for a strategy.
        
        Args:
            legs_data: List of leg data with strike, type, action, quantity
            spot_price: Current spot price
            num_points: Number of points to evaluate
            
        Returns:
            Dictionary with max profit, max loss, breakeven points
        """
        from ..core.models import OptionType
        
        # Determine price range for evaluation
        strikes = [leg['strike'] for leg in legs_data]
        min_strike = min(strikes)
        max_strike = max(strikes)
        
        # Extend range significantly for strategies with wide strikes
        price_range = max_strike - min_strike
        if price_range == 0:
            # For same-strike strategies (straddle), use spot price as reference
            price_range = spot_price * 0.5
            min_price = max(1, spot_price - price_range)
            max_price = spot_price + price_range
        else:
            # For different-strike strategies, extend beyond strikes
            extension = max(price_range * 0.5, spot_price * 0.3)
            min_price = max(1, min_strike - extension)
            max_price = max_strike + extension
        
        # Generate price points
        prices = np.linspace(min_price, max_price, num_points)
        payoffs = []
        
        # Calculate initial cost
        initial_cost = sum(leg['price'] * leg['quantity'] * (1 if leg['action'] == 'buy' else -1) 
                          for leg in legs_data)
        
        # Calculate payoff at each price point
        for price in prices:
            payoff = -initial_cost  # Start with initial cost
            
            for leg in legs_data:
                strike = leg['strike']
                option_type = leg['option_type']
                action = leg['action']
                quantity = leg['quantity']
                
                # Calculate intrinsic value at expiration
                if option_type == OptionType.CALL:
                    intrinsic = max(0, price - strike)
                else:  # PUT
                    intrinsic = max(0, strike - price)
                
                # Apply action and quantity
                if action == 'buy':
                    payoff += intrinsic * quantity
                else:  # sell
                    payoff -= intrinsic * quantity
            
            payoffs.append(payoff)
        
        payoffs = np.array(payoffs)
        
        # Find max profit and max loss
        max_profit = float(np.max(payoffs))
        max_loss = float(np.min(payoffs))
        
        # Find breakeven points (where payoff crosses zero)
        breakeven_points = []
        for i in range(len(payoffs) - 1):
            # Check if payoff crosses zero between consecutive points
            if (payoffs[i] < 0 and payoffs[i + 1] >= 0) or (payoffs[i] > 0 and payoffs[i + 1] <= 0) or \
               (payoffs[i] <= 0 and payoffs[i + 1] > 0) or (payoffs[i] >= 0 and payoffs[i + 1] < 0):
                # Linear interpolation to find exact breakeven
                x1, x2 = prices[i], prices[i + 1]
                y1, y2 = payoffs[i], payoffs[i + 1]
                if abs(y2 - y1) > 1e-10:  # Avoid division by zero
                    breakeven = x1 - y1 * (x2 - x1) / (y2 - y1)
                    # Avoid duplicate breakeven points
                    if not breakeven_points or abs(breakeven - breakeven_points[-1]) > 1.0:
                        breakeven_points.append(float(breakeven))
        
        # Calculate risk-reward ratio
        if max_loss != 0:
            risk_reward_ratio = abs(max_profit / max_loss)
        else:
            risk_reward_ratio = float('inf') if max_profit > 0 else 0
        
        # Estimate probability of profit (simplified)
        profitable_points = np.sum(payoffs > 0)
        probability_of_profit = (profitable_points / len(payoffs)) * 100
        
        return {
            'max_profit': max_profit,
            'max_loss': max_loss,
            'breakeven_points': breakeven_points,
            'risk_reward_ratio': risk_reward_ratio,
            'probability_of_profit': probability_of_profit
        }
