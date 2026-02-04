"""
Stop Loss Calculator
Calculates optimal stop loss levels using various methods
"""
import logging
from typing import List, Optional, Dict, Any, Tuple
import numpy as np
from enum import Enum

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.data_models import ActionType, MarketData
from decision_engine.risk_parameters import RiskParameters

logger = logging.getLogger(__name__)


class StopLossMethod(Enum):
    """Stop loss calculation methods"""
    FIXED_PERCENTAGE = "fixed_percentage"
    ATR_BASED = "atr_based"
    SUPPORT_RESISTANCE = "support_resistance"
    VOLATILITY_ADJUSTED = "volatility_adjusted"
    TRAILING = "trailing"


class StopLossCalculator:
    """
    Calculates optimal stop loss levels using various methods
    """
    
    def __init__(self, risk_params: Optional[RiskParameters] = None):
        """
        Initialize stop loss calculator
        
        Args:
            risk_params: Risk management parameters
        """
        self.risk_params = risk_params or RiskParameters()
        logger.info("Stop loss calculator initialized")
    
    def fixed_percentage_stop_loss(self, entry_price: float, action: ActionType,
                                 stop_loss_pct: Optional[float] = None) -> float:
        """
        Calculate stop loss using fixed percentage method
        
        Args:
            entry_price: Entry price for the position
            action: Trading action (BUY or SELL)
            stop_loss_pct: Custom stop loss percentage (uses default if None)
            
        Returns:
            Stop loss price
        """
        pct = stop_loss_pct or self.risk_params.stop_loss_percentage
        
        if action == ActionType.BUY:
            # For long positions, stop loss is below entry price
            stop_loss = entry_price * (1 - pct)
        elif action == ActionType.SELL:
            # For short positions, stop loss is above entry price
            stop_loss = entry_price * (1 + pct)
        else:
            # For HOLD, return entry price
            stop_loss = entry_price
        
        return stop_loss
    
    def atr_based_stop_loss(self, entry_price: float, action: ActionType,
                          market_data: List[MarketData], 
                          atr_multiplier: float = 2.0,
                          atr_period: int = 14) -> float:
        """
        Calculate stop loss using Average True Range (ATR) method
        
        Args:
            entry_price: Entry price for the position
            action: Trading action
            market_data: Recent market data for ATR calculation
            atr_multiplier: Multiplier for ATR (default 2.0)
            atr_period: Period for ATR calculation (default 14)
            
        Returns:
            ATR-based stop loss price
        """
        if len(market_data) < atr_period + 1:
            # Fallback to fixed percentage if insufficient data
            return self.fixed_percentage_stop_loss(entry_price, action)
        
        # Calculate True Range for each period
        true_ranges = []
        for i in range(1, len(market_data)):
            current = market_data[i]
            previous = market_data[i-1]
            
            # True Range = max(high-low, |high-prev_close|, |low-prev_close|)
            # For simplified calculation, use price as both high and low
            tr1 = abs(current.price - previous.price)  # Simplified TR
            true_ranges.append(tr1)
        
        # Calculate ATR (Average True Range)
        if len(true_ranges) >= atr_period:
            atr = np.mean(true_ranges[-atr_period:])
        else:
            atr = np.mean(true_ranges)
        
        # Calculate stop loss based on ATR
        atr_distance = atr * atr_multiplier
        
        if action == ActionType.BUY:
            stop_loss = entry_price - atr_distance
        elif action == ActionType.SELL:
            stop_loss = entry_price + atr_distance
        else:
            stop_loss = entry_price
        
        logger.debug(f"ATR stop loss: ATR={atr:.2f}, distance={atr_distance:.2f}, stop_loss=${stop_loss:.2f}")
        
        return stop_loss
    
    def support_resistance_stop_loss(self, entry_price: float, action: ActionType,
                                   market_data: List[MarketData],
                                   lookback_periods: int = 20) -> float:
        """
        Calculate stop loss based on support/resistance levels
        
        Args:
            entry_price: Entry price for the position
            action: Trading action
            market_data: Recent market data
            lookback_periods: Number of periods to look back for S/R levels
            
        Returns:
            Support/resistance based stop loss price
        """
        if len(market_data) < lookback_periods:
            # Fallback to fixed percentage if insufficient data
            return self.fixed_percentage_stop_loss(entry_price, action)
        
        recent_data = market_data[-lookback_periods:]
        prices = [data.price for data in recent_data]
        
        if action == ActionType.BUY:
            # For long positions, find support level (recent low)
            support_level = min(prices)
            # Add small buffer below support
            buffer = (entry_price - support_level) * 0.1  # 10% buffer
            stop_loss = support_level - buffer
            
            # Ensure stop loss is not too far from entry (max 5%)
            max_stop_loss = entry_price * 0.95
            stop_loss = max(stop_loss, max_stop_loss)
            
        elif action == ActionType.SELL:
            # For short positions, find resistance level (recent high)
            resistance_level = max(prices)
            # Add small buffer above resistance
            buffer = (resistance_level - entry_price) * 0.1  # 10% buffer
            stop_loss = resistance_level + buffer
            
            # Ensure stop loss is not too far from entry (max 5%)
            max_stop_loss = entry_price * 1.05
            stop_loss = min(stop_loss, max_stop_loss)
            
        else:
            stop_loss = entry_price
        
        logger.debug(f"S/R stop loss: entry=${entry_price:.2f}, stop_loss=${stop_loss:.2f}")
        
        return stop_loss
    
    def volatility_adjusted_stop_loss(self, entry_price: float, action: ActionType,
                                    market_data: List[MarketData],
                                    volatility_multiplier: float = 1.5) -> float:
        """
        Calculate stop loss adjusted for current market volatility
        
        Args:
            entry_price: Entry price for the position
            action: Trading action
            market_data: Recent market data for volatility calculation
            volatility_multiplier: Multiplier for volatility adjustment
            
        Returns:
            Volatility-adjusted stop loss price
        """
        if len(market_data) < 2:
            # Fallback to fixed percentage if insufficient data
            return self.fixed_percentage_stop_loss(entry_price, action)
        
        # Calculate recent volatility
        prices = [data.price for data in market_data[-20:]]  # Last 20 periods
        if len(prices) > 1:
            returns = np.diff(prices) / prices[:-1]
            volatility = np.std(returns)
        else:
            volatility = 0.02  # Default volatility assumption
        
        # Adjust stop loss percentage based on volatility
        base_stop_pct = self.risk_params.stop_loss_percentage
        volatility_adjustment = volatility * volatility_multiplier
        adjusted_stop_pct = base_stop_pct + volatility_adjustment
        
        # Cap the adjustment to reasonable limits
        adjusted_stop_pct = min(0.1, max(0.005, adjusted_stop_pct))  # Between 0.5% and 10%
        
        if action == ActionType.BUY:
            stop_loss = entry_price * (1 - adjusted_stop_pct)
        elif action == ActionType.SELL:
            stop_loss = entry_price * (1 + adjusted_stop_pct)
        else:
            stop_loss = entry_price
        
        logger.debug(f"Volatility stop loss: vol={volatility:.3f}, adj_pct={adjusted_stop_pct:.3f}, stop_loss=${stop_loss:.2f}")
        
        return stop_loss
    
    def trailing_stop_loss(self, entry_price: float, current_price: float,
                          action: ActionType, highest_price: Optional[float] = None,
                          lowest_price: Optional[float] = None,
                          trail_percentage: Optional[float] = None) -> float:
        """
        Calculate trailing stop loss that follows price movement
        
        Args:
            entry_price: Original entry price
            current_price: Current market price
            action: Trading action
            highest_price: Highest price since entry (for long positions)
            lowest_price: Lowest price since entry (for short positions)
            trail_percentage: Trailing percentage (uses stop_loss_percentage if None)
            
        Returns:
            Trailing stop loss price
        """
        trail_pct = trail_percentage or self.risk_params.stop_loss_percentage
        
        if action == ActionType.BUY:
            # For long positions, trail below the highest price
            peak_price = highest_price or max(entry_price, current_price)
            trailing_stop = peak_price * (1 - trail_pct)
            
            # Initial stop loss (don't trail below this)
            initial_stop = entry_price * (1 - trail_pct)
            stop_loss = max(trailing_stop, initial_stop)
            
        elif action == ActionType.SELL:
            # For short positions, trail above the lowest price
            trough_price = lowest_price or min(entry_price, current_price)
            trailing_stop = trough_price * (1 + trail_pct)
            
            # Initial stop loss (don't trail above this)
            initial_stop = entry_price * (1 + trail_pct)
            stop_loss = min(trailing_stop, initial_stop)
            
        else:
            stop_loss = entry_price
        
        return stop_loss
    
    def calculate_optimal_stop_loss(self, entry_price: float, action: ActionType,
                                  market_data: Optional[List[MarketData]] = None,
                                  method: StopLossMethod = StopLossMethod.FIXED_PERCENTAGE,
                                  **kwargs) -> Dict[str, Any]:
        """
        Calculate optimal stop loss using specified method
        
        Args:
            entry_price: Entry price for the position
            action: Trading action
            market_data: Optional market data for advanced calculations
            method: Stop loss calculation method
            **kwargs: Additional parameters for specific methods
            
        Returns:
            Dictionary with stop loss calculation results
        """
        if method == StopLossMethod.FIXED_PERCENTAGE:
            stop_loss = self.fixed_percentage_stop_loss(
                entry_price, action, kwargs.get('stop_loss_pct')
            )
            
        elif method == StopLossMethod.ATR_BASED:
            if market_data:
                stop_loss = self.atr_based_stop_loss(
                    entry_price, action, market_data,
                    kwargs.get('atr_multiplier', 2.0),
                    kwargs.get('atr_period', 14)
                )
            else:
                stop_loss = self.fixed_percentage_stop_loss(entry_price, action)
                
        elif method == StopLossMethod.SUPPORT_RESISTANCE:
            if market_data:
                stop_loss = self.support_resistance_stop_loss(
                    entry_price, action, market_data,
                    kwargs.get('lookback_periods', 20)
                )
            else:
                stop_loss = self.fixed_percentage_stop_loss(entry_price, action)
                
        elif method == StopLossMethod.VOLATILITY_ADJUSTED:
            if market_data:
                stop_loss = self.volatility_adjusted_stop_loss(
                    entry_price, action, market_data,
                    kwargs.get('volatility_multiplier', 1.5)
                )
            else:
                stop_loss = self.fixed_percentage_stop_loss(entry_price, action)
                
        elif method == StopLossMethod.TRAILING:
            stop_loss = self.trailing_stop_loss(
                entry_price, kwargs.get('current_price', entry_price), action,
                kwargs.get('highest_price'), kwargs.get('lowest_price'),
                kwargs.get('trail_percentage')
            )
            
        else:
            # Default to fixed percentage
            stop_loss = self.fixed_percentage_stop_loss(entry_price, action)
        
        # Calculate risk metrics
        if action == ActionType.BUY:
            risk_amount = entry_price - stop_loss
            risk_percentage = risk_amount / entry_price
        elif action == ActionType.SELL:
            risk_amount = stop_loss - entry_price
            risk_percentage = risk_amount / entry_price
        else:
            risk_amount = 0
            risk_percentage = 0
        
        return {
            'stop_loss_price': stop_loss,
            'entry_price': entry_price,
            'risk_amount': risk_amount,
            'risk_percentage': risk_percentage,
            'method': method.value,
            'action': action.value,
            'calculation_timestamp': __import__('datetime').datetime.utcnow().isoformat()
        }
    
    def calculate_multiple_stop_losses(self, entry_price: float, action: ActionType,
                                     market_data: Optional[List[MarketData]] = None) -> Dict[str, Dict[str, Any]]:
        """
        Calculate stop losses using multiple methods for comparison
        
        Args:
            entry_price: Entry price for the position
            action: Trading action
            market_data: Optional market data
            
        Returns:
            Dictionary with results from multiple methods
        """
        methods = [
            StopLossMethod.FIXED_PERCENTAGE,
            StopLossMethod.VOLATILITY_ADJUSTED
        ]
        
        # Add methods that require market data
        if market_data and len(market_data) > 14:
            methods.extend([
                StopLossMethod.ATR_BASED,
                StopLossMethod.SUPPORT_RESISTANCE
            ])
        
        results = {}
        for method in methods:
            try:
                result = self.calculate_optimal_stop_loss(
                    entry_price, action, market_data, method
                )
                results[method.value] = result
            except Exception as e:
                logger.warning(f"Failed to calculate stop loss using {method.value}: {str(e)}")
                continue
        
        # Calculate recommended stop loss (average of available methods)
        if results:
            stop_losses = [r['stop_loss_price'] for r in results.values()]
            recommended_stop_loss = np.mean(stop_losses)
            
            # Find the method closest to the average
            closest_method = min(results.keys(), 
                               key=lambda k: abs(results[k]['stop_loss_price'] - recommended_stop_loss))
            
            results['recommended'] = {
                'stop_loss_price': recommended_stop_loss,
                'entry_price': entry_price,
                'risk_amount': abs(entry_price - recommended_stop_loss),
                'risk_percentage': abs(entry_price - recommended_stop_loss) / entry_price,
                'method': 'average',
                'closest_method': closest_method,
                'action': action.value,
                'calculation_timestamp': __import__('datetime').datetime.utcnow().isoformat()
            }
        
        return results
    
    def update_trailing_stop(self, current_stop: float, current_price: float,
                           action: ActionType, trail_percentage: Optional[float] = None) -> Tuple[float, bool]:
        """
        Update trailing stop loss based on current price
        
        Args:
            current_stop: Current stop loss price
            current_price: Current market price
            action: Trading action
            trail_percentage: Trailing percentage
            
        Returns:
            Tuple of (new_stop_loss, was_updated)
        """
        trail_pct = trail_percentage or self.risk_params.stop_loss_percentage
        
        if action == ActionType.BUY:
            # For long positions, only move stop loss up
            new_stop = current_price * (1 - trail_pct)
            if new_stop > current_stop:
                return new_stop, True
            else:
                return current_stop, False
                
        elif action == ActionType.SELL:
            # For short positions, only move stop loss down
            new_stop = current_price * (1 + trail_pct)
            if new_stop < current_stop:
                return new_stop, True
            else:
                return current_stop, False
                
        else:
            return current_stop, False
    
    def validate_stop_loss(self, stop_loss: float, entry_price: float,
                         action: ActionType) -> Tuple[bool, List[str]]:
        """
        Validate stop loss price
        
        Args:
            stop_loss: Proposed stop loss price
            entry_price: Entry price
            action: Trading action
            
        Returns:
            Tuple of (is_valid, violation_reasons)
        """
        violations = []
        
        # Check basic validity
        if stop_loss <= 0:
            violations.append("Stop loss price must be positive")
        
        # Check direction is correct
        if action == ActionType.BUY and stop_loss >= entry_price:
            violations.append("Stop loss for long position must be below entry price")
        elif action == ActionType.SELL and stop_loss <= entry_price:
            violations.append("Stop loss for short position must be above entry price")
        
        # Check risk percentage is reasonable
        risk_pct = abs(entry_price - stop_loss) / entry_price
        max_risk = 0.15  # 15% maximum risk
        
        if risk_pct > max_risk:
            violations.append(f"Stop loss risk too high: {risk_pct:.1%} > {max_risk:.1%}")
        
        min_risk = 0.002  # 0.2% minimum risk
        if risk_pct < min_risk:
            violations.append(f"Stop loss risk too low: {risk_pct:.1%} < {min_risk:.1%}")
        
        is_valid = len(violations) == 0
        
        if not is_valid:
            logger.warning(f"Stop loss validation failed: {violations}")
        
        return is_valid, violations
    
    def get_stop_loss_recommendation(self, entry_price: float, action: ActionType,
                                   market_data: Optional[List[MarketData]] = None,
                                   position_size: float = 0.1) -> Dict[str, Any]:
        """
        Get comprehensive stop loss recommendation
        
        Args:
            entry_price: Entry price for the position
            action: Trading action
            market_data: Optional market data
            position_size: Position size as percentage of portfolio
            
        Returns:
            Comprehensive stop loss recommendation
        """
        # Calculate multiple stop loss methods
        stop_loss_results = self.calculate_multiple_stop_losses(entry_price, action, market_data)
        
        # Get recommended stop loss
        if 'recommended' in stop_loss_results:
            recommended = stop_loss_results['recommended']
        else:
            # Fallback to fixed percentage
            recommended = self.calculate_optimal_stop_loss(entry_price, action)
        
        # Validate the recommendation
        is_valid, violations = self.validate_stop_loss(
            recommended['stop_loss_price'], entry_price, action
        )
        
        # Calculate position impact
        risk_per_share = recommended['risk_amount']
        total_risk = risk_per_share * position_size  # Simplified calculation
        
        return {
            'recommended_stop_loss': recommended['stop_loss_price'],
            'risk_amount_per_unit': risk_per_share,
            'risk_percentage': recommended['risk_percentage'],
            'total_position_risk': total_risk,
            'all_methods': stop_loss_results,
            'validation': {
                'is_valid': is_valid,
                'violations': violations
            },
            'parameters': {
                'entry_price': entry_price,
                'action': action.value,
                'position_size': position_size,
                'default_stop_loss_pct': self.risk_params.stop_loss_percentage
            },
            'recommendation_timestamp': __import__('datetime').datetime.utcnow().isoformat()
        }