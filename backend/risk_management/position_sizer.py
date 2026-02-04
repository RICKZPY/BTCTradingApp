"""
Position Sizer
Calculates optimal position sizes based on risk parameters and market conditions
"""
import logging
from typing import Optional, Dict, Any, Tuple, List
import numpy as np

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.data_models import TradingDecision, Portfolio, ActionType
from decision_engine.risk_parameters import RiskParameters

logger = logging.getLogger(__name__)


class PositionSizer:
    """
    Calculates optimal position sizes using various sizing methods
    """
    
    def __init__(self, risk_params: Optional[RiskParameters] = None):
        """
        Initialize position sizer
        
        Args:
            risk_params: Risk management parameters
        """
        self.risk_params = risk_params or RiskParameters()
        logger.info("Position sizer initialized")
    
    def fixed_percentage_sizing(self, portfolio: Portfolio, 
                              percentage: Optional[float] = None) -> float:
        """
        Calculate position size using fixed percentage method
        
        Args:
            portfolio: Current portfolio state
            percentage: Fixed percentage to use (uses max_position_size if None)
            
        Returns:
            Position size as percentage of portfolio
        """
        pct = percentage or self.risk_params.max_position_size
        return min(pct, self.risk_params.max_position_size)
    
    def kelly_criterion_sizing(self, win_rate: float, avg_win: float, 
                             avg_loss: float, portfolio: Portfolio) -> float:
        """
        Calculate position size using Kelly Criterion
        
        Args:
            win_rate: Historical win rate (0 to 1)
            avg_win: Average winning trade return
            avg_loss: Average losing trade return (positive value)
            portfolio: Current portfolio state
            
        Returns:
            Optimal position size as percentage of portfolio
        """
        if avg_loss <= 0 or win_rate <= 0 or win_rate >= 1:
            return self.risk_params.min_position_size
        
        # Kelly formula: f = (bp - q) / b
        # where b = avg_win/avg_loss, p = win_rate, q = 1 - win_rate
        b = avg_win / avg_loss
        p = win_rate
        q = 1 - win_rate
        
        kelly_fraction = (b * p - q) / b
        
        # Apply safety factor (typically use 25-50% of Kelly)
        safety_factor = 0.25
        adjusted_kelly = kelly_fraction * safety_factor
        
        # Ensure within bounds
        position_size = max(self.risk_params.min_position_size,
                          min(self.risk_params.max_position_size, adjusted_kelly))
        
        logger.debug(f"Kelly sizing: win_rate={win_rate:.2%}, kelly={kelly_fraction:.2%}, adjusted={position_size:.2%}")
        
        return position_size
    
    def volatility_adjusted_sizing(self, portfolio: Portfolio, 
                                 volatility: float, 
                                 target_volatility: float = 0.02) -> float:
        """
        Calculate position size adjusted for volatility
        
        Args:
            portfolio: Current portfolio state
            volatility: Current market volatility
            target_volatility: Target portfolio volatility
            
        Returns:
            Volatility-adjusted position size
        """
        if volatility <= 0:
            return self.risk_params.min_position_size
        
        # Scale position size inversely with volatility
        volatility_adjustment = target_volatility / volatility
        base_size = self.risk_params.max_position_size
        
        adjusted_size = base_size * volatility_adjustment
        
        # Ensure within bounds
        position_size = max(self.risk_params.min_position_size,
                          min(self.risk_params.max_position_size, adjusted_size))
        
        logger.debug(f"Volatility sizing: vol={volatility:.3f}, target={target_volatility:.3f}, size={position_size:.2%}")
        
        return position_size
    
    def confidence_based_sizing(self, decision: TradingDecision, 
                              portfolio: Portfolio) -> float:
        """
        Calculate position size based on decision confidence
        
        Args:
            decision: Trading decision with confidence score
            portfolio: Current portfolio state
            
        Returns:
            Confidence-adjusted position size
        """
        # Scale position size with confidence
        confidence_factor = decision.confidence
        
        # Apply non-linear scaling (square root) to be more conservative
        adjusted_confidence = np.sqrt(confidence_factor)
        
        # Calculate size based on confidence
        size_range = self.risk_params.max_position_size - self.risk_params.min_position_size
        position_size = self.risk_params.min_position_size + (size_range * adjusted_confidence)
        
        logger.debug(f"Confidence sizing: confidence={decision.confidence:.2%}, size={position_size:.2%}")
        
        return position_size
    
    def risk_parity_sizing(self, portfolio: Portfolio, 
                          target_risk: float = 0.02) -> float:
        """
        Calculate position size for risk parity approach
        
        Args:
            portfolio: Current portfolio state
            target_risk: Target risk contribution (2% default)
            
        Returns:
            Risk parity position size
        """
        # Estimate current portfolio risk
        current_risk = abs(portfolio.unrealized_pnl) / portfolio.total_value_usdt if portfolio.total_value_usdt > 0 else 0
        
        # Calculate position size to achieve target risk
        if current_risk < target_risk:
            # Can take larger position
            risk_budget = target_risk - current_risk
            position_size = min(self.risk_params.max_position_size, risk_budget * 2)  # Conservative multiplier
        else:
            # Already at or above target risk
            position_size = self.risk_params.min_position_size
        
        logger.debug(f"Risk parity sizing: current_risk={current_risk:.2%}, target={target_risk:.2%}, size={position_size:.2%}")
        
        return position_size
    
    def adaptive_sizing(self, decision: TradingDecision, portfolio: Portfolio,
                       market_volatility: Optional[float] = None,
                       recent_performance: Optional[Dict[str, float]] = None) -> float:
        """
        Calculate adaptive position size combining multiple methods
        
        Args:
            decision: Trading decision
            portfolio: Current portfolio state
            market_volatility: Optional market volatility
            recent_performance: Optional recent performance metrics
            
        Returns:
            Adaptive position size
        """
        sizes = []
        weights = []
        
        # 1. Confidence-based sizing (always available)
        confidence_size = self.confidence_based_sizing(decision, portfolio)
        sizes.append(confidence_size)
        weights.append(0.3)
        
        # 2. Risk parity sizing (always available)
        risk_parity_size = self.risk_parity_sizing(portfolio)
        sizes.append(risk_parity_size)
        weights.append(0.2)
        
        # 3. Volatility-adjusted sizing (if volatility available)
        if market_volatility is not None:
            vol_size = self.volatility_adjusted_sizing(portfolio, market_volatility)
            sizes.append(vol_size)
            weights.append(0.3)
        else:
            # Use fixed percentage as fallback
            fixed_size = self.fixed_percentage_sizing(portfolio)
            sizes.append(fixed_size)
            weights.append(0.3)
        
        # 4. Kelly criterion (if performance data available)
        if recent_performance and all(k in recent_performance for k in ['win_rate', 'avg_win', 'avg_loss']):
            kelly_size = self.kelly_criterion_sizing(
                recent_performance['win_rate'],
                recent_performance['avg_win'],
                recent_performance['avg_loss'],
                portfolio
            )
            sizes.append(kelly_size)
            weights.append(0.2)
        else:
            # Use fixed percentage as fallback
            fixed_size = self.fixed_percentage_sizing(portfolio)
            sizes.append(fixed_size)
            weights.append(0.2)
        
        # Calculate weighted average
        weighted_size = np.average(sizes, weights=weights)
        
        # Apply final bounds check
        final_size = max(self.risk_params.min_position_size,
                        min(self.risk_params.max_position_size, weighted_size))
        
        logger.info(f"Adaptive sizing: sizes={[f'{s:.2%}' for s in sizes]}, weights={weights}, final={final_size:.2%}")
        
        return final_size
    
    def calculate_position_value(self, position_size: float, portfolio: Portfolio,
                               current_price: float) -> Dict[str, float]:
        """
        Calculate position value and quantities
        
        Args:
            position_size: Position size as percentage of portfolio
            portfolio: Current portfolio state
            current_price: Current market price
            
        Returns:
            Dictionary with position calculations
        """
        # Calculate position value in USDT
        position_value_usdt = position_size * portfolio.total_value_usdt
        
        # Calculate BTC quantity
        btc_quantity = position_value_usdt / current_price
        
        # Calculate percentage of available cash
        cash_percentage = position_value_usdt / portfolio.usdt_balance if portfolio.usdt_balance > 0 else 0
        
        return {
            'position_size_percentage': position_size,
            'position_value_usdt': position_value_usdt,
            'btc_quantity': btc_quantity,
            'cash_percentage': cash_percentage,
            'current_price': current_price
        }
    
    def validate_position_size(self, position_size: float, portfolio: Portfolio,
                             action: ActionType) -> Tuple[bool, List[str]]:
        """
        Validate if position size is acceptable
        
        Args:
            position_size: Proposed position size
            portfolio: Current portfolio state
            action: Trading action
            
        Returns:
            Tuple of (is_valid, violation_reasons)
        """
        violations = []
        
        # Check basic bounds
        if position_size < self.risk_params.min_position_size:
            violations.append(f"Position size below minimum: {position_size:.2%} < {self.risk_params.min_position_size:.2%}")
        
        if position_size > self.risk_params.max_position_size:
            violations.append(f"Position size above maximum: {position_size:.2%} > {self.risk_params.max_position_size:.2%}")
        
        # Check available funds
        position_value = position_size * portfolio.total_value_usdt
        
        if action == ActionType.BUY:
            if position_value > portfolio.usdt_balance:
                violations.append(f"Insufficient USDT balance: need ${position_value:.2f}, have ${portfolio.usdt_balance:.2f}")
        elif action == ActionType.SELL:
            # For selling, check if we have enough BTC (simplified check)
            if portfolio.btc_balance <= 0:
                violations.append("No BTC balance available for selling")
        
        # Check portfolio concentration
        if action == ActionType.BUY:
            # Estimate new BTC concentration after purchase
            current_btc_value = portfolio.btc_balance * 45000  # Simplified price estimate
            new_btc_value = current_btc_value + position_value
            new_concentration = new_btc_value / portfolio.total_value_usdt
            
            if new_concentration > 0.8:  # 80% concentration limit
                violations.append(f"Position would create excessive concentration: {new_concentration:.1%}")
        
        is_valid = len(violations) == 0
        
        if not is_valid:
            logger.warning(f"Position size validation failed: {violations}")
        
        return is_valid, violations
    
    def get_sizing_recommendation(self, decision: TradingDecision, portfolio: Portfolio,
                                market_data: Optional[Dict[str, Any]] = None,
                                performance_data: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Get comprehensive position sizing recommendation
        
        Args:
            decision: Trading decision
            portfolio: Current portfolio state
            market_data: Optional market data for volatility calculation
            performance_data: Optional recent performance metrics
            
        Returns:
            Comprehensive sizing recommendation
        """
        # Extract market volatility if available
        market_volatility = None
        if market_data and 'volatility' in market_data:
            market_volatility = market_data['volatility']
        
        # Calculate different sizing methods
        sizing_methods = {
            'fixed_percentage': self.fixed_percentage_sizing(portfolio),
            'confidence_based': self.confidence_based_sizing(decision, portfolio),
            'risk_parity': self.risk_parity_sizing(portfolio)
        }
        
        if market_volatility is not None:
            sizing_methods['volatility_adjusted'] = self.volatility_adjusted_sizing(
                portfolio, market_volatility
            )
        
        if performance_data and all(k in performance_data for k in ['win_rate', 'avg_win', 'avg_loss']):
            sizing_methods['kelly_criterion'] = self.kelly_criterion_sizing(
                performance_data['win_rate'],
                performance_data['avg_win'],
                performance_data['avg_loss'],
                portfolio
            )
        
        # Calculate adaptive size
        adaptive_size = self.adaptive_sizing(
            decision, portfolio, market_volatility, performance_data
        )
        
        # Validate the adaptive size
        is_valid, violations = self.validate_position_size(adaptive_size, portfolio, decision.action)
        
        # Calculate position details
        current_price = 45000  # Simplified - should come from market data
        if market_data and 'current_price' in market_data:
            current_price = market_data['current_price']
        
        position_details = self.calculate_position_value(adaptive_size, portfolio, current_price)
        
        return {
            'recommended_size': adaptive_size,
            'sizing_methods': sizing_methods,
            'position_details': position_details,
            'validation': {
                'is_valid': is_valid,
                'violations': violations
            },
            'risk_parameters': {
                'min_size': self.risk_params.min_position_size,
                'max_size': self.risk_params.max_position_size,
                'stop_loss_pct': self.risk_params.stop_loss_percentage
            },
            'recommendation_timestamp': logger.info.__globals__.get('datetime', __import__('datetime')).datetime.utcnow().isoformat()
        }