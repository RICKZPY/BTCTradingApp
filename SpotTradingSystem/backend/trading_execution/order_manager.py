"""
Order Manager
Handles order execution, tracking, and management
"""
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import uuid

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.data_models import (
    TradingDecision, OrderResult, OrderStatus, ActionType, Portfolio, Position
)
from trading_execution.binance_client import (
    BinanceClient, BinanceOrderRequest, OrderSide, OrderType, TimeInForce
)

logger = logging.getLogger(__name__)


class OrderExecutionStrategy(Enum):
    """Order execution strategies"""
    MARKET = "market"
    LIMIT = "limit"
    TWAP = "twap"  # Time-Weighted Average Price
    VWAP = "vwap"  # Volume-Weighted Average Price


@dataclass
class OrderExecution:
    """Order execution tracking"""
    execution_id: str
    decision: TradingDecision
    strategy: OrderExecutionStrategy
    symbol: str
    target_quantity: float
    executed_quantity: float
    remaining_quantity: float
    average_price: float
    total_cost: float
    
    # Status tracking
    status: OrderStatus
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    
    # Binance order IDs
    binance_orders: List[int] = None
    
    # Execution details
    execution_details: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.binance_orders is None:
            self.binance_orders = []
        if self.execution_details is None:
            self.execution_details = []
    
    @property
    def fill_percentage(self) -> float:
        """Calculate fill percentage"""
        if self.target_quantity == 0:
            return 0.0
        return (self.executed_quantity / self.target_quantity) * 100
    
    @property
    def is_complete(self) -> bool:
        """Check if execution is complete"""
        return self.status in [OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.FAILED]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'execution_id': self.execution_id,
            'symbol': self.symbol,
            'strategy': self.strategy.value,
            'target_quantity': self.target_quantity,
            'executed_quantity': self.executed_quantity,
            'remaining_quantity': self.remaining_quantity,
            'average_price': self.average_price,
            'total_cost': self.total_cost,
            'status': self.status.value,
            'fill_percentage': self.fill_percentage,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'binance_orders': self.binance_orders,
            'execution_details': self.execution_details
        }


class OrderManager:
    """
    Manages order execution and tracking
    """
    
    def __init__(self, binance_client: BinanceClient):
        """
        Initialize order manager
        
        Args:
            binance_client: Binance API client
        """
        self.binance_client = binance_client
        
        # Active executions
        self.active_executions: Dict[str, OrderExecution] = {}
        
        # Execution history
        self.execution_history: List[OrderExecution] = []
        
        # Configuration
        self.max_slippage = 0.005  # 0.5% max slippage
        self.order_timeout = timedelta(minutes=5)  # 5 minute timeout for limit orders
        
        logger.info("Order manager initialized")
    
    def execute_trading_decision(self, decision: TradingDecision, portfolio: Portfolio,
                               strategy: OrderExecutionStrategy = OrderExecutionStrategy.MARKET,
                               symbol: str = "BTCUSDT") -> OrderExecution:
        """
        Execute a trading decision
        
        Args:
            decision: Trading decision to execute
            portfolio: Current portfolio
            strategy: Execution strategy
            symbol: Trading symbol
            
        Returns:
            Order execution tracking object
        """
        # Generate execution ID
        execution_id = f"EXEC_{uuid.uuid4().hex[:8]}_{int(datetime.utcnow().timestamp())}"
        
        # Calculate target quantity
        target_quantity = self._calculate_target_quantity(decision, portfolio, symbol)
        
        if target_quantity == 0:
            logger.warning("Target quantity is zero, skipping execution")
            return self._create_empty_execution(execution_id, decision, strategy, symbol)
        
        # Create execution tracking
        execution = OrderExecution(
            execution_id=execution_id,
            decision=decision,
            strategy=strategy,
            symbol=symbol,
            target_quantity=abs(target_quantity),
            executed_quantity=0.0,
            remaining_quantity=abs(target_quantity),
            average_price=0.0,
            total_cost=0.0,
            status=OrderStatus.PENDING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Store execution
        self.active_executions[execution_id] = execution
        
        try:
            # Execute based on strategy
            if strategy == OrderExecutionStrategy.MARKET:
                self._execute_market_order(execution, target_quantity)
            elif strategy == OrderExecutionStrategy.LIMIT:
                self._execute_limit_order(execution, target_quantity)
            elif strategy == OrderExecutionStrategy.TWAP:
                self._execute_twap_order(execution, target_quantity)
            else:
                raise ValueError(f"Unsupported execution strategy: {strategy}")
            
            logger.info(f"Started execution {execution_id} for {decision.action.value} {target_quantity}")
            
        except Exception as e:
            logger.error(f"Failed to execute order {execution_id}: {e}")
            execution.status = OrderStatus.FAILED
            execution.updated_at = datetime.utcnow()
            execution.completed_at = datetime.utcnow()
        
        return execution
    
    def _calculate_target_quantity(self, decision: TradingDecision, portfolio: Portfolio,
                                 symbol: str) -> float:
        """
        Calculate target quantity for the order
        
        Args:
            decision: Trading decision
            portfolio: Current portfolio
            symbol: Trading symbol
            
        Returns:
            Target quantity (positive for buy, negative for sell)
        """
        try:
            # Get current price
            current_price = self.binance_client.get_ticker_price(symbol)
            
            # Calculate position value
            position_value = decision.suggested_amount * portfolio.total_value_usdt
            
            # Calculate quantity
            if decision.action == ActionType.BUY:
                quantity = position_value / current_price
                return quantity
            elif decision.action == ActionType.SELL:
                # For sell orders, use the amount from existing position
                existing_position = None
                for pos in portfolio.positions:
                    if pos.symbol == symbol:
                        existing_position = pos
                        break
                
                if existing_position and existing_position.amount > 0:
                    # Sell percentage of existing position
                    quantity = existing_position.amount * decision.suggested_amount
                    return -quantity  # Negative for sell
                else:
                    logger.warning(f"No existing position to sell for {symbol}")
                    return 0.0
            else:  # HOLD
                return 0.0
                
        except Exception as e:
            logger.error(f"Failed to calculate target quantity: {e}")
            return 0.0
    
    def _create_empty_execution(self, execution_id: str, decision: TradingDecision,
                              strategy: OrderExecutionStrategy, symbol: str) -> OrderExecution:
        """Create empty execution for zero quantity orders"""
        execution = OrderExecution(
            execution_id=execution_id,
            decision=decision,
            strategy=strategy,
            symbol=symbol,
            target_quantity=0.0,
            executed_quantity=0.0,
            remaining_quantity=0.0,
            average_price=0.0,
            total_cost=0.0,
            status=OrderStatus.FILLED,  # Consider zero quantity as filled
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )
        
        self.execution_history.append(execution)
        return execution
    
    def _execute_market_order(self, execution: OrderExecution, target_quantity: float):
        """Execute market order"""
        try:
            # Determine order side
            side = OrderSide.BUY if target_quantity > 0 else OrderSide.SELL
            quantity = abs(target_quantity)
            
            # Place market order
            binance_order = self.binance_client.place_market_order(
                symbol=execution.symbol,
                side=side,
                quantity=quantity,
                client_order_id=f"{execution.execution_id}_MARKET"
            )
            
            # Update execution
            execution.binance_orders.append(binance_order.order_id)
            execution.executed_quantity = binance_order.executed_quantity
            execution.remaining_quantity = quantity - binance_order.executed_quantity
            execution.average_price = binance_order.executed_price
            execution.total_cost = binance_order.executed_quantity * binance_order.executed_price
            execution.status = OrderStatus.FILLED if binance_order.status == 'FILLED' else OrderStatus.PARTIALLY_FILLED
            execution.updated_at = datetime.utcnow()
            
            if execution.status == OrderStatus.FILLED:
                execution.completed_at = datetime.utcnow()
                self._move_to_history(execution)
            
            # Record execution details
            execution.execution_details.append({
                'binance_order_id': binance_order.order_id,
                'type': 'MARKET',
                'quantity': binance_order.executed_quantity,
                'price': binance_order.executed_price,
                'timestamp': binance_order.time.isoformat()
            })
            
            logger.info(f"Market order executed: {binance_order.executed_quantity} at ${binance_order.executed_price}")
            
        except Exception as e:
            logger.error(f"Market order execution failed: {e}")
            execution.status = OrderStatus.FAILED
            execution.updated_at = datetime.utcnow()
            execution.completed_at = datetime.utcnow()
            self._move_to_history(execution)
            raise
    
    def _execute_limit_order(self, execution: OrderExecution, target_quantity: float):
        """Execute limit order with price improvement"""
        try:
            # Get current market price
            current_price = self.binance_client.get_ticker_price(execution.symbol)
            
            # Determine order side and limit price
            side = OrderSide.BUY if target_quantity > 0 else OrderSide.SELL
            quantity = abs(target_quantity)
            
            # Set limit price with small improvement
            if side == OrderSide.BUY:
                limit_price = current_price * (1 - 0.001)  # 0.1% below market for buy
            else:
                limit_price = current_price * (1 + 0.001)  # 0.1% above market for sell
            
            # Place limit order
            binance_order = self.binance_client.place_limit_order(
                symbol=execution.symbol,
                side=side,
                quantity=quantity,
                price=limit_price,
                client_order_id=f"{execution.execution_id}_LIMIT"
            )
            
            # Update execution
            execution.binance_orders.append(binance_order.order_id)
            execution.executed_quantity = binance_order.executed_quantity
            execution.remaining_quantity = quantity - binance_order.executed_quantity
            execution.average_price = binance_order.executed_price if binance_order.executed_quantity > 0 else limit_price
            execution.total_cost = binance_order.executed_quantity * binance_order.executed_price
            execution.status = self._map_binance_status(binance_order.status)
            execution.updated_at = datetime.utcnow()
            
            if execution.status in [OrderStatus.FILLED, OrderStatus.FAILED]:
                execution.completed_at = datetime.utcnow()
                self._move_to_history(execution)
            
            # Record execution details
            execution.execution_details.append({
                'binance_order_id': binance_order.order_id,
                'type': 'LIMIT',
                'quantity': binance_order.executed_quantity,
                'price': limit_price,
                'executed_price': binance_order.executed_price,
                'timestamp': binance_order.time.isoformat()
            })
            
            logger.info(f"Limit order placed: {quantity} at ${limit_price}")
            
        except Exception as e:
            logger.error(f"Limit order execution failed: {e}")
            execution.status = OrderStatus.FAILED
            execution.updated_at = datetime.utcnow()
            execution.completed_at = datetime.utcnow()
            self._move_to_history(execution)
            raise
    
    def _execute_twap_order(self, execution: OrderExecution, target_quantity: float):
        """Execute TWAP (Time-Weighted Average Price) order"""
        try:
            # TWAP parameters
            num_slices = 5  # Split into 5 orders
            slice_quantity = abs(target_quantity) / num_slices
            side = OrderSide.BUY if target_quantity > 0 else OrderSide.SELL
            
            # Execute first slice immediately
            first_slice = self.binance_client.place_market_order(
                symbol=execution.symbol,
                side=side,
                quantity=slice_quantity,
                client_order_id=f"{execution.execution_id}_TWAP_1"
            )
            
            # Update execution with first slice
            execution.binance_orders.append(first_slice.order_id)
            execution.executed_quantity = first_slice.executed_quantity
            execution.remaining_quantity = abs(target_quantity) - first_slice.executed_quantity
            execution.average_price = first_slice.executed_price
            execution.total_cost = first_slice.executed_quantity * first_slice.executed_price
            execution.status = OrderStatus.PARTIALLY_FILLED
            execution.updated_at = datetime.utcnow()
            
            # Record first slice
            execution.execution_details.append({
                'binance_order_id': first_slice.order_id,
                'type': 'TWAP_SLICE_1',
                'quantity': first_slice.executed_quantity,
                'price': first_slice.executed_price,
                'timestamp': first_slice.time.isoformat()
            })
            
            logger.info(f"TWAP order started: first slice {first_slice.executed_quantity} at ${first_slice.executed_price}")
            
            # Note: In a real implementation, remaining slices would be executed over time
            # For this demo, we'll mark as partially filled and let the update mechanism handle it
            
        except Exception as e:
            logger.error(f"TWAP order execution failed: {e}")
            execution.status = OrderStatus.FAILED
            execution.updated_at = datetime.utcnow()
            execution.completed_at = datetime.utcnow()
            self._move_to_history(execution)
            raise
    
    def _map_binance_status(self, binance_status: str) -> OrderStatus:
        """Map Binance order status to internal status"""
        mapping = {
            'NEW': OrderStatus.PENDING,
            'PARTIALLY_FILLED': OrderStatus.PARTIALLY_FILLED,
            'FILLED': OrderStatus.FILLED,
            'CANCELED': OrderStatus.CANCELLED,
            'REJECTED': OrderStatus.FAILED,
            'EXPIRED': OrderStatus.CANCELLED
        }
        return mapping.get(binance_status, OrderStatus.FAILED)
    
    def _move_to_history(self, execution: OrderExecution):
        """Move execution from active to history"""
        if execution.execution_id in self.active_executions:
            del self.active_executions[execution.execution_id]
        
        self.execution_history.append(execution)
        
        # Keep only last 1000 executions in history
        if len(self.execution_history) > 1000:
            self.execution_history = self.execution_history[-1000:]
    
    def update_execution_status(self, execution_id: str) -> Optional[OrderExecution]:
        """
        Update execution status by checking Binance orders
        
        Args:
            execution_id: Execution ID to update
            
        Returns:
            Updated execution or None if not found
        """
        if execution_id not in self.active_executions:
            logger.warning(f"Execution {execution_id} not found in active executions")
            return None
        
        execution = self.active_executions[execution_id]
        
        try:
            total_executed = 0.0
            total_cost = 0.0
            all_filled = True
            
            # Check status of all Binance orders
            for binance_order_id in execution.binance_orders:
                binance_order = self.binance_client.get_order(
                    symbol=execution.symbol,
                    order_id=binance_order_id
                )
                
                total_executed += binance_order.executed_quantity
                total_cost += binance_order.executed_quantity * binance_order.executed_price
                
                if binance_order.status not in ['FILLED']:
                    all_filled = False
            
            # Update execution
            execution.executed_quantity = total_executed
            execution.remaining_quantity = execution.target_quantity - total_executed
            execution.total_cost = total_cost
            execution.average_price = total_cost / total_executed if total_executed > 0 else 0.0
            execution.updated_at = datetime.utcnow()
            
            # Update status
            if all_filled and execution.remaining_quantity <= 0.001:  # Allow small rounding errors
                execution.status = OrderStatus.FILLED
                execution.completed_at = datetime.utcnow()
                self._move_to_history(execution)
            elif total_executed > 0:
                execution.status = OrderStatus.PARTIALLY_FILLED
            
            return execution
            
        except Exception as e:
            logger.error(f"Failed to update execution status for {execution_id}: {e}")
            return execution
    
    def cancel_execution(self, execution_id: str) -> bool:
        """
        Cancel an active execution
        
        Args:
            execution_id: Execution ID to cancel
            
        Returns:
            True if cancellation successful
        """
        if execution_id not in self.active_executions:
            logger.warning(f"Execution {execution_id} not found in active executions")
            return False
        
        execution = self.active_executions[execution_id]
        
        try:
            # Cancel all active Binance orders
            cancelled_orders = 0
            for binance_order_id in execution.binance_orders:
                try:
                    self.binance_client.cancel_order(
                        symbol=execution.symbol,
                        order_id=binance_order_id
                    )
                    cancelled_orders += 1
                except Exception as e:
                    logger.warning(f"Failed to cancel Binance order {binance_order_id}: {e}")
            
            # Update execution status
            execution.status = OrderStatus.CANCELLED
            execution.updated_at = datetime.utcnow()
            execution.completed_at = datetime.utcnow()
            self._move_to_history(execution)
            
            logger.info(f"Execution {execution_id} cancelled ({cancelled_orders} orders cancelled)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel execution {execution_id}: {e}")
            return False
    
    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        Get execution status
        
        Args:
            execution_id: Execution ID
            
        Returns:
            Execution status dictionary or None if not found
        """
        # Check active executions
        if execution_id in self.active_executions:
            return self.active_executions[execution_id].to_dict()
        
        # Check history
        for execution in self.execution_history:
            if execution.execution_id == execution_id:
                return execution.to_dict()
        
        return None
    
    def get_active_executions(self) -> List[Dict[str, Any]]:
        """
        Get all active executions
        
        Returns:
            List of active execution dictionaries
        """
        return [execution.to_dict() for execution in self.active_executions.values()]
    
    def get_execution_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get execution history
        
        Args:
            limit: Maximum number of executions to return
            
        Returns:
            List of historical execution dictionaries
        """
        recent_history = self.execution_history[-limit:] if limit > 0 else self.execution_history
        return [execution.to_dict() for execution in recent_history]
    
    def update_all_active_executions(self):
        """Update status of all active executions"""
        execution_ids = list(self.active_executions.keys())
        
        for execution_id in execution_ids:
            try:
                self.update_execution_status(execution_id)
            except Exception as e:
                logger.error(f"Failed to update execution {execution_id}: {e}")
    
    def cleanup_old_executions(self, max_age_hours: int = 24):
        """
        Clean up old completed executions
        
        Args:
            max_age_hours: Maximum age in hours for keeping executions
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        # Clean up history
        self.execution_history = [
            execution for execution in self.execution_history
            if execution.completed_at is None or execution.completed_at > cutoff_time
        ]
        
        logger.info(f"Cleaned up old executions (keeping last {max_age_hours} hours)")
    
    def get_order_manager_status(self) -> Dict[str, Any]:
        """
        Get order manager status and statistics
        
        Returns:
            Status dictionary
        """
        # Calculate statistics
        total_executions = len(self.execution_history) + len(self.active_executions)
        completed_executions = len([e for e in self.execution_history if e.is_complete])
        
        # Calculate success rate
        filled_executions = len([e for e in self.execution_history if e.status == OrderStatus.FILLED])
        success_rate = (filled_executions / completed_executions) if completed_executions > 0 else 0.0
        
        # Calculate average fill time for completed executions
        fill_times = []
        for execution in self.execution_history:
            if execution.completed_at and execution.status == OrderStatus.FILLED:
                fill_time = (execution.completed_at - execution.created_at).total_seconds()
                fill_times.append(fill_time)
        
        avg_fill_time = sum(fill_times) / len(fill_times) if fill_times else 0.0
        
        return {
            'total_executions': total_executions,
            'active_executions': len(self.active_executions),
            'completed_executions': completed_executions,
            'success_rate': success_rate,
            'average_fill_time_seconds': avg_fill_time,
            'execution_strategies': {
                'market': len([e for e in self.execution_history if e.strategy == OrderExecutionStrategy.MARKET]),
                'limit': len([e for e in self.execution_history if e.strategy == OrderExecutionStrategy.LIMIT]),
                'twap': len([e for e in self.execution_history if e.strategy == OrderExecutionStrategy.TWAP])
            },
            'status_timestamp': datetime.utcnow().isoformat()
        }