"""
Protection Manager
Implements stop loss and protection mechanisms for trading positions
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum
import numpy as np

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.data_models import Position, Portfolio, ActionType, OrderResult, OrderStatus, MarketData
from decision_engine.risk_parameters import RiskParameters
from risk_management.stop_loss_calculator import StopLossCalculator, StopLossMethod

logger = logging.getLogger(__name__)


class ProtectionType(Enum):
    """Types of protection mechanisms"""
    STOP_LOSS = "stop_loss"
    TRAILING_STOP = "trailing_stop"
    TAKE_PROFIT = "take_profit"
    TIME_BASED = "time_based"
    DRAWDOWN_PROTECTION = "drawdown_protection"


class ProtectionStatus(Enum):
    """Status of protection orders"""
    ACTIVE = "active"
    TRIGGERED = "triggered"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


@dataclass
class ProtectionOrder:
    """Protection order configuration"""
    
    id: str
    position_symbol: str
    protection_type: ProtectionType
    trigger_price: float
    order_action: ActionType  # BUY or SELL
    quantity: float
    
    # Status and timing
    status: ProtectionStatus
    created_at: datetime
    expires_at: Optional[datetime] = None
    triggered_at: Optional[datetime] = None
    
    # Configuration
    is_trailing: bool = False
    trail_amount: Optional[float] = None
    trail_percentage: Optional[float] = None
    
    # Execution details
    order_id: Optional[str] = None
    executed_price: Optional[float] = None
    executed_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate protection order data"""
        if self.trigger_price <= 0:
            raise ValueError("Trigger price must be positive")
        
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")
        
        if self.trail_percentage is not None and not 0 < self.trail_percentage <= 1:
            raise ValueError("Trail percentage must be between 0 and 1")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'id': self.id,
            'position_symbol': self.position_symbol,
            'protection_type': self.protection_type.value,
            'trigger_price': self.trigger_price,
            'order_action': self.order_action.value,
            'quantity': self.quantity,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'triggered_at': self.triggered_at.isoformat() if self.triggered_at else None,
            'is_trailing': self.is_trailing,
            'trail_amount': self.trail_amount,
            'trail_percentage': self.trail_percentage,
            'order_id': self.order_id,
            'executed_price': self.executed_price,
            'executed_at': self.executed_at.isoformat() if self.executed_at else None
        }


@dataclass
class ProtectionSummary:
    """Summary of protection status for a portfolio"""
    
    total_positions: int
    protected_positions: int
    active_stop_losses: int
    active_take_profits: int
    active_trailing_stops: int
    
    # Risk metrics
    total_exposure: float
    protected_exposure: float
    max_potential_loss: float
    protection_coverage: float  # Percentage of exposure protected
    
    # Recent activity
    recent_triggers: int  # Triggers in last 24 hours
    recent_adjustments: int  # Adjustments in last 24 hours
    
    summary_timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'total_positions': self.total_positions,
            'protected_positions': self.protected_positions,
            'active_stop_losses': self.active_stop_losses,
            'active_take_profits': self.active_take_profits,
            'active_trailing_stops': self.active_trailing_stops,
            'total_exposure': self.total_exposure,
            'protected_exposure': self.protected_exposure,
            'max_potential_loss': self.max_potential_loss,
            'protection_coverage': self.protection_coverage,
            'recent_triggers': self.recent_triggers,
            'recent_adjustments': self.recent_adjustments,
            'summary_timestamp': self.summary_timestamp.isoformat()
        }


class ProtectionManager:
    """
    Manages stop loss and protection mechanisms for trading positions
    """
    
    def __init__(self, risk_params: Optional[RiskParameters] = None):
        """
        Initialize protection manager
        
        Args:
            risk_params: Risk management parameters
        """
        self.risk_params = risk_params or RiskParameters()
        self.stop_loss_calc = StopLossCalculator(risk_params)
        
        # Active protection orders
        self.protection_orders: Dict[str, ProtectionOrder] = {}
        
        # Position tracking for trailing stops
        self.position_peaks: Dict[str, float] = {}  # Highest price for long positions
        self.position_troughs: Dict[str, float] = {}  # Lowest price for short positions
        
        # Statistics
        self.total_triggers: int = 0
        self.successful_protections: int = 0
        self.protection_history: List[Dict] = []
        
        logger.info("Protection manager initialized")
    
    def create_stop_loss_order(self, position: Position, 
                             stop_loss_price: Optional[float] = None,
                             method: StopLossMethod = StopLossMethod.FIXED_PERCENTAGE) -> ProtectionOrder:
        """
        Create stop loss order for a position
        
        Args:
            position: Position to protect
            stop_loss_price: Custom stop loss price (calculated if None)
            method: Stop loss calculation method
            
        Returns:
            Created protection order
        """
        # Calculate stop loss price if not provided
        if stop_loss_price is None:
            if position.amount > 0:  # Long position
                action = ActionType.BUY
            else:  # Short position
                action = ActionType.SELL
            
            stop_loss_result = self.stop_loss_calc.calculate_optimal_stop_loss(
                position.entry_price, action, method=method
            )
            stop_loss_price = stop_loss_result['stop_loss_price']
        
        # Determine order action (opposite of position)
        if position.amount > 0:  # Long position needs sell stop
            order_action = ActionType.SELL
        else:  # Short position needs buy stop
            order_action = ActionType.BUY
        
        # Create protection order
        order_id = f"SL_{position.symbol}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        protection_order = ProtectionOrder(
            id=order_id,
            position_symbol=position.symbol,
            protection_type=ProtectionType.STOP_LOSS,
            trigger_price=stop_loss_price,
            order_action=order_action,
            quantity=abs(position.amount),
            status=ProtectionStatus.ACTIVE,
            created_at=datetime.utcnow()
        )
        
        # Store the order
        self.protection_orders[order_id] = protection_order
        
        logger.info(f"Created stop loss order {order_id} for {position.symbol} at ${stop_loss_price:.2f}")
        
        return protection_order
    
    def create_trailing_stop_order(self, position: Position,
                                 trail_percentage: Optional[float] = None,
                                 trail_amount: Optional[float] = None) -> ProtectionOrder:
        """
        Create trailing stop order for a position
        
        Args:
            position: Position to protect
            trail_percentage: Trailing percentage (uses default if None)
            trail_amount: Fixed trailing amount (alternative to percentage)
            
        Returns:
            Created protection order
        """
        # Use default trail percentage if not provided
        if trail_percentage is None and trail_amount is None:
            trail_percentage = self.risk_params.stop_loss_percentage
        
        # Calculate initial trigger price
        if position.amount > 0:  # Long position
            order_action = ActionType.SELL
            if trail_percentage:
                trigger_price = position.current_price * (1 - trail_percentage)
            else:
                trigger_price = position.current_price - trail_amount
            
            # Initialize peak tracking
            self.position_peaks[position.symbol] = position.current_price
            
        else:  # Short position
            order_action = ActionType.BUY
            if trail_percentage:
                trigger_price = position.current_price * (1 + trail_percentage)
            else:
                trigger_price = position.current_price + trail_amount
            
            # Initialize trough tracking
            self.position_troughs[position.symbol] = position.current_price
        
        # Create protection order
        order_id = f"TS_{position.symbol}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        protection_order = ProtectionOrder(
            id=order_id,
            position_symbol=position.symbol,
            protection_type=ProtectionType.TRAILING_STOP,
            trigger_price=trigger_price,
            order_action=order_action,
            quantity=abs(position.amount),
            status=ProtectionStatus.ACTIVE,
            created_at=datetime.utcnow(),
            is_trailing=True,
            trail_percentage=trail_percentage,
            trail_amount=trail_amount
        )
        
        # Store the order
        self.protection_orders[order_id] = protection_order
        
        logger.info(f"Created trailing stop order {order_id} for {position.symbol} at ${trigger_price:.2f}")
        
        return protection_order
    
    def create_take_profit_order(self, position: Position,
                               take_profit_price: Optional[float] = None,
                               profit_percentage: Optional[float] = None) -> ProtectionOrder:
        """
        Create take profit order for a position
        
        Args:
            position: Position to protect
            take_profit_price: Custom take profit price
            profit_percentage: Profit percentage target (uses default if None)
            
        Returns:
            Created protection order
        """
        # Calculate take profit price if not provided
        if take_profit_price is None:
            profit_pct = profit_percentage or self.risk_params.take_profit_percentage
            
            if position.amount > 0:  # Long position
                take_profit_price = position.entry_price * (1 + profit_pct)
            else:  # Short position
                take_profit_price = position.entry_price * (1 - profit_pct)
        
        # Determine order action (opposite of position)
        if position.amount > 0:  # Long position needs sell order
            order_action = ActionType.SELL
        else:  # Short position needs buy order
            order_action = ActionType.BUY
        
        # Create protection order
        order_id = f"TP_{position.symbol}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        protection_order = ProtectionOrder(
            id=order_id,
            position_symbol=position.symbol,
            protection_type=ProtectionType.TAKE_PROFIT,
            trigger_price=take_profit_price,
            order_action=order_action,
            quantity=abs(position.amount),
            status=ProtectionStatus.ACTIVE,
            created_at=datetime.utcnow()
        )
        
        # Store the order
        self.protection_orders[order_id] = protection_order
        
        logger.info(f"Created take profit order {order_id} for {position.symbol} at ${take_profit_price:.2f}")
        
        return protection_order
    
    def update_trailing_stops(self, current_prices: Dict[str, float]):
        """
        Update trailing stop orders based on current prices
        
        Args:
            current_prices: Dictionary of symbol -> current price
        """
        updated_orders = []
        
        for order in self.protection_orders.values():
            if (order.protection_type == ProtectionType.TRAILING_STOP and 
                order.status == ProtectionStatus.ACTIVE and
                order.position_symbol in current_prices):
                
                current_price = current_prices[order.position_symbol]
                symbol = order.position_symbol
                
                # Update trailing stop based on position direction
                if order.order_action == ActionType.SELL:  # Long position
                    # Update peak price
                    if symbol not in self.position_peaks:
                        self.position_peaks[symbol] = current_price
                    else:
                        self.position_peaks[symbol] = max(self.position_peaks[symbol], current_price)
                    
                    # Calculate new trigger price
                    if order.trail_percentage:
                        new_trigger = self.position_peaks[symbol] * (1 - order.trail_percentage)
                    else:
                        new_trigger = self.position_peaks[symbol] - order.trail_amount
                    
                    # Only move stop loss up (more favorable)
                    if new_trigger > order.trigger_price:
                        old_trigger = order.trigger_price
                        order.trigger_price = new_trigger
                        updated_orders.append((order.id, old_trigger, new_trigger))
                        
                elif order.order_action == ActionType.BUY:  # Short position
                    # Update trough price
                    if symbol not in self.position_troughs:
                        self.position_troughs[symbol] = current_price
                    else:
                        self.position_troughs[symbol] = min(self.position_troughs[symbol], current_price)
                    
                    # Calculate new trigger price
                    if order.trail_percentage:
                        new_trigger = self.position_troughs[symbol] * (1 + order.trail_percentage)
                    else:
                        new_trigger = self.position_troughs[symbol] + order.trail_amount
                    
                    # Only move stop loss down (more favorable)
                    if new_trigger < order.trigger_price:
                        old_trigger = order.trigger_price
                        order.trigger_price = new_trigger
                        updated_orders.append((order.id, old_trigger, new_trigger))
        
        # Log updates
        for order_id, old_price, new_price in updated_orders:
            logger.info(f"Updated trailing stop {order_id}: ${old_price:.2f} -> ${new_price:.2f}")
        
        return len(updated_orders)
    
    def check_protection_triggers(self, current_prices: Dict[str, float]) -> List[ProtectionOrder]:
        """
        Check if any protection orders should be triggered
        
        Args:
            current_prices: Dictionary of symbol -> current price
            
        Returns:
            List of triggered protection orders
        """
        triggered_orders = []
        
        for order in self.protection_orders.values():
            if (order.status == ProtectionStatus.ACTIVE and 
                order.position_symbol in current_prices):
                
                current_price = current_prices[order.position_symbol]
                should_trigger = False
                
                # Check trigger conditions based on protection type and order action
                if order.order_action == ActionType.SELL:
                    # Sell order triggers when price falls to or below trigger price
                    should_trigger = current_price <= order.trigger_price
                elif order.order_action == ActionType.BUY:
                    # Buy order triggers when price rises to or above trigger price
                    should_trigger = current_price >= order.trigger_price
                
                if should_trigger:
                    order.status = ProtectionStatus.TRIGGERED
                    order.triggered_at = datetime.utcnow()
                    triggered_orders.append(order)
                    
                    logger.warning(f"Protection order {order.id} triggered at ${current_price:.2f}")
        
        return triggered_orders
    
    def execute_protection_order(self, order: ProtectionOrder, 
                               execution_price: float) -> OrderResult:
        """
        Execute a triggered protection order
        
        Args:
            order: Protection order to execute
            execution_price: Price at which order was executed
            
        Returns:
            Order execution result
        """
        # Create order result
        order_result = OrderResult(
            order_id=f"EXEC_{order.id}",
            status=OrderStatus.FILLED,
            executed_amount=order.quantity,
            executed_price=execution_price,
            timestamp=datetime.utcnow()
        )
        
        # Update protection order
        order.order_id = order_result.order_id
        order.executed_price = execution_price
        order.executed_at = order_result.timestamp
        
        # Update statistics
        self.total_triggers += 1
        
        # Record in history
        self.protection_history.append({
            'protection_id': order.id,
            'protection_type': order.protection_type.value,
            'symbol': order.position_symbol,
            'trigger_price': order.trigger_price,
            'execution_price': execution_price,
            'quantity': order.quantity,
            'timestamp': order_result.timestamp.isoformat()
        })
        
        # Clean up position tracking for trailing stops
        if order.protection_type == ProtectionType.TRAILING_STOP:
            self.position_peaks.pop(order.position_symbol, None)
            self.position_troughs.pop(order.position_symbol, None)
        
        logger.info(f"Executed protection order {order.id}: {order.quantity} at ${execution_price:.2f}")
        
        return order_result
    
    def cancel_protection_order(self, order_id: str, reason: str = "Manual cancellation") -> bool:
        """
        Cancel a protection order
        
        Args:
            order_id: ID of order to cancel
            reason: Reason for cancellation
            
        Returns:
            True if order was cancelled successfully
        """
        if order_id not in self.protection_orders:
            logger.warning(f"Cannot cancel order {order_id}: not found")
            return False
        
        order = self.protection_orders[order_id]
        
        if order.status != ProtectionStatus.ACTIVE:
            logger.warning(f"Cannot cancel order {order_id}: status is {order.status.value}")
            return False
        
        # Update order status
        order.status = ProtectionStatus.CANCELLED
        
        # Clean up tracking data
        if order.protection_type == ProtectionType.TRAILING_STOP:
            self.position_peaks.pop(order.position_symbol, None)
            self.position_troughs.pop(order.position_symbol, None)
        
        logger.info(f"Cancelled protection order {order_id}: {reason}")
        
        return True
    
    def get_position_protection(self, symbol: str) -> List[ProtectionOrder]:
        """
        Get all protection orders for a specific position
        
        Args:
            symbol: Position symbol
            
        Returns:
            List of protection orders for the position
        """
        return [order for order in self.protection_orders.values() 
                if order.position_symbol == symbol and order.status == ProtectionStatus.ACTIVE]
    
    def monitor_continuous_losses(self, recent_trades: List[Dict]) -> bool:
        """
        Monitor for continuous losses and recommend trading suspension
        
        Args:
            recent_trades: List of recent trade results
            
        Returns:
            True if trading should be suspended due to continuous losses
        """
        if len(recent_trades) < 3:
            return False
        
        # Check last few trades for continuous losses
        recent_losses = []
        for trade in recent_trades[-5:]:  # Last 5 trades
            if trade.get('pnl', 0) < 0:
                recent_losses.append(trade['pnl'])
            else:
                break  # Stop at first non-loss
        
        # Suspend if 3+ continuous losses
        if len(recent_losses) >= 3:
            total_loss = sum(recent_losses)
            loss_percentage = abs(total_loss) / 10000  # Assume $10k base
            
            if loss_percentage > self.risk_params.loss_cooldown_hours / 100:  # Threshold based on cooldown
                logger.warning(f"Continuous losses detected: {len(recent_losses)} losses totaling ${total_loss:.2f}")
                return True
        
        return False
    
    def auto_adjust_protection_levels(self, portfolio: Portfolio, 
                                    market_volatility: Optional[float] = None):
        """
        Automatically adjust protection levels based on market conditions
        
        Args:
            portfolio: Current portfolio
            market_volatility: Current market volatility
        """
        adjustments_made = 0
        
        # Adjust based on volatility
        if market_volatility and market_volatility > self.risk_params.max_volatility_threshold:
            # Tighten stop losses in high volatility
            volatility_multiplier = 0.8  # Reduce stop loss distance by 20%
            
            for order in self.protection_orders.values():
                if (order.protection_type == ProtectionType.STOP_LOSS and 
                    order.status == ProtectionStatus.ACTIVE):
                    
                    # Get position to calculate new stop loss
                    position = portfolio.get_position(order.position_symbol)
                    if position:
                        # Calculate tighter stop loss
                        if position.amount > 0:  # Long position
                            distance = position.current_price - order.trigger_price
                            new_trigger = position.current_price - (distance * volatility_multiplier)
                            
                            if new_trigger > order.trigger_price:  # Only move up
                                order.trigger_price = new_trigger
                                adjustments_made += 1
                        else:  # Short position
                            distance = order.trigger_price - position.current_price
                            new_trigger = position.current_price + (distance * volatility_multiplier)
                            
                            if new_trigger < order.trigger_price:  # Only move down
                                order.trigger_price = new_trigger
                                adjustments_made += 1
        
        # Adjust based on portfolio drawdown
        portfolio_risk = abs(portfolio.unrealized_pnl) / portfolio.total_value_usdt if portfolio.total_value_usdt > 0 else 0
        
        if portfolio_risk > self.risk_params.max_portfolio_risk * 0.7:  # 70% of max risk
            # Tighten all protection orders
            tightening_factor = 0.9  # Reduce distances by 10%
            
            for order in self.protection_orders.values():
                if order.status == ProtectionStatus.ACTIVE:
                    position = portfolio.get_position(order.position_symbol)
                    if position:
                        if position.amount > 0:  # Long position
                            distance = position.current_price - order.trigger_price
                            new_trigger = position.current_price - (distance * tightening_factor)
                            
                            if new_trigger > order.trigger_price:
                                order.trigger_price = new_trigger
                                adjustments_made += 1
                        else:  # Short position
                            distance = order.trigger_price - position.current_price
                            new_trigger = position.current_price + (distance * tightening_factor)
                            
                            if new_trigger < order.trigger_price:
                                order.trigger_price = new_trigger
                                adjustments_made += 1
        
        if adjustments_made > 0:
            logger.info(f"Auto-adjusted {adjustments_made} protection orders due to market conditions")
        
        return adjustments_made
    
    def get_protection_summary(self, portfolio: Portfolio) -> ProtectionSummary:
        """
        Get summary of protection status for the portfolio
        
        Args:
            portfolio: Current portfolio
            
        Returns:
            Protection summary
        """
        # Count active orders by type
        active_orders = [order for order in self.protection_orders.values() 
                        if order.status == ProtectionStatus.ACTIVE]
        
        active_stop_losses = len([o for o in active_orders if o.protection_type == ProtectionType.STOP_LOSS])
        active_take_profits = len([o for o in active_orders if o.protection_type == ProtectionType.TAKE_PROFIT])
        active_trailing_stops = len([o for o in active_orders if o.protection_type == ProtectionType.TRAILING_STOP])
        
        # Calculate exposure and protection coverage
        total_exposure = 0.0
        protected_exposure = 0.0
        max_potential_loss = 0.0
        
        protected_symbols = set(order.position_symbol for order in active_orders)
        
        for position in portfolio.positions:
            position_value = abs(position.amount) * position.current_price
            total_exposure += position_value
            
            if position.symbol in protected_symbols:
                protected_exposure += position_value
                
                # Calculate potential loss from stop losses
                stop_losses = [o for o in active_orders 
                             if o.position_symbol == position.symbol and 
                             o.protection_type == ProtectionType.STOP_LOSS]
                
                for sl in stop_losses:
                    if position.amount > 0:  # Long position
                        potential_loss = (position.current_price - sl.trigger_price) * position.amount
                    else:  # Short position
                        potential_loss = (sl.trigger_price - position.current_price) * abs(position.amount)
                    
                    max_potential_loss += max(0, potential_loss)
        
        protection_coverage = protected_exposure / total_exposure if total_exposure > 0 else 0
        
        # Count recent activity (last 24 hours)
        recent_cutoff = datetime.utcnow() - timedelta(hours=24)
        recent_triggers = len([h for h in self.protection_history 
                             if datetime.fromisoformat(h['timestamp']) > recent_cutoff])
        
        # Count recent adjustments (simplified - count trailing stop updates)
        recent_adjustments = len([order for order in active_orders 
                                if order.protection_type == ProtectionType.TRAILING_STOP])
        
        return ProtectionSummary(
            total_positions=len(portfolio.positions),
            protected_positions=len(protected_symbols),
            active_stop_losses=active_stop_losses,
            active_take_profits=active_take_profits,
            active_trailing_stops=active_trailing_stops,
            total_exposure=total_exposure,
            protected_exposure=protected_exposure,
            max_potential_loss=max_potential_loss,
            protection_coverage=protection_coverage,
            recent_triggers=recent_triggers,
            recent_adjustments=recent_adjustments,
            summary_timestamp=datetime.utcnow()
        )
    
    def cleanup_expired_orders(self):
        """Clean up expired and completed protection orders"""
        current_time = datetime.utcnow()
        expired_orders = []
        
        for order_id, order in self.protection_orders.items():
            # Mark expired orders
            if (order.expires_at and current_time > order.expires_at and 
                order.status == ProtectionStatus.ACTIVE):
                order.status = ProtectionStatus.EXPIRED
                expired_orders.append(order_id)
        
        # Remove old completed orders (keep last 100)
        completed_orders = [(order_id, order) for order_id, order in self.protection_orders.items()
                          if order.status in [ProtectionStatus.TRIGGERED, ProtectionStatus.CANCELLED, ProtectionStatus.EXPIRED]]
        
        if len(completed_orders) > 100:
            # Sort by completion time and remove oldest
            completed_orders.sort(key=lambda x: x[1].triggered_at or x[1].created_at)
            for order_id, _ in completed_orders[:-100]:
                del self.protection_orders[order_id]
        
        if expired_orders:
            logger.info(f"Cleaned up {len(expired_orders)} expired protection orders")
        
        return len(expired_orders)
    
    def get_protection_manager_status(self) -> Dict[str, Any]:
        """
        Get protection manager status and statistics
        
        Returns:
            Status dictionary
        """
        active_orders = [order for order in self.protection_orders.values() 
                        if order.status == ProtectionStatus.ACTIVE]
        
        return {
            'total_protection_orders': len(self.protection_orders),
            'active_orders': len(active_orders),
            'total_triggers': self.total_triggers,
            'successful_protections': self.successful_protections,
            'protection_types': {
                'stop_loss': len([o for o in active_orders if o.protection_type == ProtectionType.STOP_LOSS]),
                'trailing_stop': len([o for o in active_orders if o.protection_type == ProtectionType.TRAILING_STOP]),
                'take_profit': len([o for o in active_orders if o.protection_type == ProtectionType.TAKE_PROFIT])
            },
            'tracked_positions': {
                'peaks': len(self.position_peaks),
                'troughs': len(self.position_troughs)
            },
            'recent_history_count': len(self.protection_history),
            'status_timestamp': datetime.utcnow().isoformat()
        }