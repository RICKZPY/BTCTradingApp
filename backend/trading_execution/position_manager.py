"""
Position Manager
Handles position tracking, updates, and portfolio management
"""
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.data_models import Position, Portfolio, OrderResult, ActionType
from trading_execution.binance_client import BinanceClient, BinanceBalance

logger = logging.getLogger(__name__)


@dataclass
class PositionUpdate:
    """Position update record"""
    position_symbol: str
    update_type: str  # 'trade', 'price_update', 'manual_adjustment'
    old_amount: float
    new_amount: float
    old_price: float
    new_price: float
    pnl_change: float
    timestamp: datetime
    source: str = "position_manager"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'position_symbol': self.position_symbol,
            'update_type': self.update_type,
            'old_amount': self.old_amount,
            'new_amount': self.new_amount,
            'old_price': self.old_price,
            'new_price': self.new_price,
            'pnl_change': self.pnl_change,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source
        }


@dataclass
class PortfolioSnapshot:
    """Portfolio snapshot for historical tracking"""
    snapshot_id: str
    portfolio: Portfolio
    timestamp: datetime
    trigger: str  # What triggered this snapshot
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'snapshot_id': self.snapshot_id,
            'timestamp': self.timestamp.isoformat(),
            'trigger': self.trigger,
            'portfolio': {
                'btc_balance': self.portfolio.btc_balance,
                'usdt_balance': self.portfolio.usdt_balance,
                'total_value_usdt': self.portfolio.total_value_usdt,
                'unrealized_pnl': self.portfolio.unrealized_pnl,
                'positions': [
                    {
                        'symbol': pos.symbol,
                        'amount': pos.amount,
                        'entry_price': pos.entry_price,
                        'current_price': pos.current_price,
                        'pnl': pos.pnl,
                        'entry_time': pos.entry_time.isoformat()
                    }
                    for pos in self.portfolio.positions
                ]
            }
        }


class PositionManager:
    """
    Manages position tracking, updates, and portfolio synchronization
    """
    
    def __init__(self, binance_client: BinanceClient):
        """
        Initialize position manager
        
        Args:
            binance_client: Binance API client for balance and price updates
        """
        self.binance_client = binance_client
        
        # Current portfolio state
        self.current_portfolio: Optional[Portfolio] = None
        
        # Position tracking
        self.position_updates: List[PositionUpdate] = []
        self.portfolio_snapshots: List[PortfolioSnapshot] = []
        
        # Configuration
        self.auto_sync_interval = timedelta(minutes=5)  # Auto-sync every 5 minutes
        self.last_sync_time = datetime.utcnow()
        
        # Price cache
        self.price_cache: Dict[str, Tuple[float, datetime]] = {}
        self.price_cache_ttl = timedelta(seconds=30)  # 30 second cache
        
        logger.info("Position manager initialized")
    
    def initialize_portfolio(self) -> Portfolio:
        """
        Initialize portfolio from Binance account
        
        Returns:
            Initial portfolio state
        """
        try:
            # Get account balances
            balances = self.binance_client.get_balances()
            
            # Extract BTC and USDT balances
            btc_balance = 0.0
            usdt_balance = 0.0
            
            for balance in balances:
                if balance.asset == 'BTC':
                    btc_balance = balance.free
                elif balance.asset == 'USDT':
                    usdt_balance = balance.free
            
            # Get current BTC price
            btc_price = self._get_current_price("BTCUSDT")
            
            # Create BTC position if we have BTC
            positions = []
            if btc_balance > 0.001:  # Minimum meaningful BTC amount
                btc_position = Position(
                    symbol="BTCUSDT",
                    amount=btc_balance,
                    entry_price=btc_price,  # Use current price as entry for initialization
                    current_price=btc_price,
                    pnl=0.0,  # No P&L at initialization
                    entry_time=datetime.utcnow()
                )
                positions.append(btc_position)
            
            # Calculate total portfolio value
            total_value = (btc_balance * btc_price) + usdt_balance
            
            # Create portfolio
            portfolio = Portfolio(
                btc_balance=btc_balance,
                usdt_balance=usdt_balance,
                total_value_usdt=total_value,
                unrealized_pnl=0.0,  # No unrealized P&L at initialization
                positions=positions
            )
            
            self.current_portfolio = portfolio
            
            # Create initial snapshot
            self._create_snapshot("initialization")
            
            logger.info(f"Portfolio initialized: ${total_value:,.2f} total value")
            return portfolio
            
        except Exception as e:
            logger.error(f"Failed to initialize portfolio: {e}")
            raise
    
    def sync_with_exchange(self) -> Portfolio:
        """
        Synchronize portfolio with exchange balances
        
        Returns:
            Updated portfolio
        """
        try:
            if not self.current_portfolio:
                return self.initialize_portfolio()
            
            # Get current balances
            balances = self.binance_client.get_balances()
            
            # Extract balances
            new_btc_balance = 0.0
            new_usdt_balance = 0.0
            
            for balance in balances:
                if balance.asset == 'BTC':
                    new_btc_balance = balance.free
                elif balance.asset == 'USDT':
                    new_usdt_balance = balance.free
            
            # Check for balance changes
            btc_changed = abs(new_btc_balance - self.current_portfolio.btc_balance) > 0.00001
            usdt_changed = abs(new_usdt_balance - self.current_portfolio.usdt_balance) > 0.001
            
            if btc_changed or usdt_changed:
                logger.info(f"Balance changes detected - BTC: {self.current_portfolio.btc_balance:.6f} -> {new_btc_balance:.6f}, "
                          f"USDT: {self.current_portfolio.usdt_balance:.2f} -> {new_usdt_balance:.2f}")
                
                # Update balances
                self.current_portfolio.btc_balance = new_btc_balance
                self.current_portfolio.usdt_balance = new_usdt_balance
                
                # Update positions
                self._update_positions_from_balances()
                
                # Recalculate portfolio metrics
                self._recalculate_portfolio_metrics()
                
                # Create snapshot
                self._create_snapshot("exchange_sync")
            
            # Update prices regardless
            self.update_position_prices()
            
            self.last_sync_time = datetime.utcnow()
            return self.current_portfolio
            
        except Exception as e:
            logger.error(f"Failed to sync with exchange: {e}")
            raise
    
    def update_position_from_trade(self, symbol: str, trade_quantity: float, 
                                 trade_price: float, trade_type: ActionType) -> bool:
        """
        Update position based on executed trade
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            trade_quantity: Quantity traded (positive)
            trade_price: Execution price
            trade_type: BUY or SELL
            
        Returns:
            True if update successful
        """
        try:
            if not self.current_portfolio:
                logger.error("Portfolio not initialized")
                return False
            
            # Find or create position
            position = self._find_or_create_position(symbol)
            
            # Record old values
            old_amount = position.amount
            old_price = position.current_price
            
            # Update position based on trade type
            if trade_type == ActionType.BUY:
                # Calculate new weighted average entry price
                if position.amount > 0:
                    total_cost = (position.amount * position.entry_price) + (trade_quantity * trade_price)
                    new_amount = position.amount + trade_quantity
                    new_entry_price = total_cost / new_amount
                else:
                    new_amount = trade_quantity
                    new_entry_price = trade_price
                
                position.amount = new_amount
                position.entry_price = new_entry_price
                
            elif trade_type == ActionType.SELL:
                # Reduce position
                position.amount = max(0, position.amount - trade_quantity)
                
                # If position is closed, reset entry price
                if position.amount == 0:
                    position.entry_price = 0.0
            
            # Update current price and P&L
            position.current_price = trade_price
            position.pnl = (position.current_price - position.entry_price) * position.amount
            
            # Update portfolio balances
            if symbol == "BTCUSDT":
                if trade_type == ActionType.BUY:
                    self.current_portfolio.btc_balance += trade_quantity
                    self.current_portfolio.usdt_balance -= trade_quantity * trade_price
                else:  # SELL
                    self.current_portfolio.btc_balance -= trade_quantity
                    self.current_portfolio.usdt_balance += trade_quantity * trade_price
            
            # Recalculate portfolio metrics
            self._recalculate_portfolio_metrics()
            
            # Record position update
            update = PositionUpdate(
                position_symbol=symbol,
                update_type='trade',
                old_amount=old_amount,
                new_amount=position.amount,
                old_price=old_price,
                new_price=position.current_price,
                pnl_change=position.pnl - (old_price - position.entry_price) * old_amount,
                timestamp=datetime.utcnow(),
                source="trade_execution"
            )
            self.position_updates.append(update)
            
            # Create snapshot
            self._create_snapshot(f"trade_{trade_type.value.lower()}")
            
            logger.info(f"Position updated from trade: {symbol} {trade_type.value} {trade_quantity} at ${trade_price}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update position from trade: {e}")
            return False
    
    def update_position_prices(self) -> bool:
        """
        Update current prices for all positions
        
        Returns:
            True if update successful
        """
        try:
            if not self.current_portfolio or not self.current_portfolio.positions:
                return True
            
            updated_positions = 0
            
            for position in self.current_portfolio.positions:
                try:
                    # Get current price
                    current_price = self._get_current_price(position.symbol)
                    
                    if abs(current_price - position.current_price) > 0.01:  # Only update if significant change
                        old_price = position.current_price
                        old_pnl = position.pnl
                        
                        # Update price and P&L
                        position.current_price = current_price
                        position.pnl = (position.current_price - position.entry_price) * position.amount
                        
                        # Record update
                        update = PositionUpdate(
                            position_symbol=position.symbol,
                            update_type='price_update',
                            old_amount=position.amount,
                            new_amount=position.amount,
                            old_price=old_price,
                            new_price=current_price,
                            pnl_change=position.pnl - old_pnl,
                            timestamp=datetime.utcnow()
                        )
                        self.position_updates.append(update)
                        
                        updated_positions += 1
                
                except Exception as e:
                    logger.warning(f"Failed to update price for {position.symbol}: {e}")
            
            if updated_positions > 0:
                # Recalculate portfolio metrics
                self._recalculate_portfolio_metrics()
                logger.info(f"Updated prices for {updated_positions} positions")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update position prices: {e}")
            return False
    
    def _find_or_create_position(self, symbol: str) -> Position:
        """Find existing position or create new one"""
        if not self.current_portfolio:
            raise ValueError("Portfolio not initialized")
        
        # Look for existing position
        for position in self.current_portfolio.positions:
            if position.symbol == symbol:
                return position
        
        # Create new position
        current_price = self._get_current_price(symbol)
        new_position = Position(
            symbol=symbol,
            amount=0.0,
            entry_price=current_price,
            current_price=current_price,
            pnl=0.0,
            entry_time=datetime.utcnow()
        )
        
        self.current_portfolio.positions.append(new_position)
        return new_position
    
    def _update_positions_from_balances(self):
        """Update positions based on current balances"""
        if not self.current_portfolio:
            return
        
        # Update BTC position
        btc_position = None
        for position in self.current_portfolio.positions:
            if position.symbol == "BTCUSDT":
                btc_position = position
                break
        
        if self.current_portfolio.btc_balance > 0.001:
            if btc_position:
                btc_position.amount = self.current_portfolio.btc_balance
            else:
                # Create new BTC position
                btc_price = self._get_current_price("BTCUSDT")
                new_position = Position(
                    symbol="BTCUSDT",
                    amount=self.current_portfolio.btc_balance,
                    entry_price=btc_price,
                    current_price=btc_price,
                    pnl=0.0,
                    entry_time=datetime.utcnow()
                )
                self.current_portfolio.positions.append(new_position)
        else:
            # Remove BTC position if balance is zero
            if btc_position:
                self.current_portfolio.positions.remove(btc_position)
    
    def _recalculate_portfolio_metrics(self):
        """Recalculate portfolio total value and unrealized P&L"""
        if not self.current_portfolio:
            return
        
        # Calculate total value
        btc_value = self.current_portfolio.btc_balance * self._get_current_price("BTCUSDT")
        total_value = btc_value + self.current_portfolio.usdt_balance
        
        # Calculate unrealized P&L
        unrealized_pnl = sum(position.pnl for position in self.current_portfolio.positions)
        
        # Update portfolio
        self.current_portfolio.total_value_usdt = total_value
        self.current_portfolio.unrealized_pnl = unrealized_pnl
    
    def _get_current_price(self, symbol: str) -> float:
        """Get current price with caching"""
        now = datetime.utcnow()
        
        # Check cache
        if symbol in self.price_cache:
            cached_price, cached_time = self.price_cache[symbol]
            if now - cached_time < self.price_cache_ttl:
                return cached_price
        
        # Fetch new price
        try:
            price = self.binance_client.get_ticker_price(symbol)
            self.price_cache[symbol] = (price, now)
            return price
        except Exception as e:
            logger.error(f"Failed to get price for {symbol}: {e}")
            # Return cached price if available, otherwise raise
            if symbol in self.price_cache:
                return self.price_cache[symbol][0]
            raise
    
    def _create_snapshot(self, trigger: str):
        """Create portfolio snapshot"""
        if not self.current_portfolio:
            return
        
        snapshot_id = f"SNAP_{int(datetime.utcnow().timestamp())}_{trigger}"
        
        # Create deep copy of portfolio for snapshot
        snapshot_portfolio = Portfolio(
            btc_balance=self.current_portfolio.btc_balance,
            usdt_balance=self.current_portfolio.usdt_balance,
            total_value_usdt=self.current_portfolio.total_value_usdt,
            unrealized_pnl=self.current_portfolio.unrealized_pnl,
            positions=[
                Position(
                    symbol=pos.symbol,
                    amount=pos.amount,
                    entry_price=pos.entry_price,
                    current_price=pos.current_price,
                    pnl=pos.pnl,
                    entry_time=pos.entry_time
                )
                for pos in self.current_portfolio.positions
            ]
        )
        
        snapshot = PortfolioSnapshot(
            snapshot_id=snapshot_id,
            portfolio=snapshot_portfolio,
            timestamp=datetime.utcnow(),
            trigger=trigger
        )
        
        self.portfolio_snapshots.append(snapshot)
        
        # Keep only last 100 snapshots
        if len(self.portfolio_snapshots) > 100:
            self.portfolio_snapshots = self.portfolio_snapshots[-100:]
    
    def get_current_portfolio(self) -> Optional[Portfolio]:
        """
        Get current portfolio state
        
        Returns:
            Current portfolio or None if not initialized
        """
        return self.current_portfolio
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """
        Get specific position
        
        Args:
            symbol: Position symbol
            
        Returns:
            Position or None if not found
        """
        if not self.current_portfolio:
            return None
        
        for position in self.current_portfolio.positions:
            if position.symbol == symbol:
                return position
        
        return None
    
    def get_position_updates(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent position updates
        
        Args:
            limit: Maximum number of updates to return
            
        Returns:
            List of position update dictionaries
        """
        recent_updates = self.position_updates[-limit:] if limit > 0 else self.position_updates
        return [update.to_dict() for update in recent_updates]
    
    def get_portfolio_snapshots(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent portfolio snapshots
        
        Args:
            limit: Maximum number of snapshots to return
            
        Returns:
            List of portfolio snapshot dictionaries
        """
        recent_snapshots = self.portfolio_snapshots[-limit:] if limit > 0 else self.portfolio_snapshots
        return [snapshot.to_dict() for snapshot in recent_snapshots]
    
    def should_auto_sync(self) -> bool:
        """
        Check if auto-sync should be performed
        
        Returns:
            True if auto-sync is due
        """
        return datetime.utcnow() - self.last_sync_time >= self.auto_sync_interval
    
    def get_portfolio_performance(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get portfolio performance over specified time period
        
        Args:
            hours: Time period in hours
            
        Returns:
            Performance metrics
        """
        if not self.current_portfolio:
            return {}
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Find snapshot closest to cutoff time
        baseline_snapshot = None
        for snapshot in self.portfolio_snapshots:
            if snapshot.timestamp >= cutoff_time:
                baseline_snapshot = snapshot
                break
        
        if not baseline_snapshot:
            # Use oldest available snapshot
            baseline_snapshot = self.portfolio_snapshots[0] if self.portfolio_snapshots else None
        
        if not baseline_snapshot:
            return {
                'period_hours': hours,
                'performance_available': False,
                'message': 'Insufficient historical data'
            }
        
        # Calculate performance
        baseline_value = baseline_snapshot.portfolio.total_value_usdt
        current_value = self.current_portfolio.total_value_usdt
        
        absolute_change = current_value - baseline_value
        percentage_change = (absolute_change / baseline_value) * 100 if baseline_value > 0 else 0.0
        
        return {
            'period_hours': hours,
            'performance_available': True,
            'baseline_timestamp': baseline_snapshot.timestamp.isoformat(),
            'baseline_value': baseline_value,
            'current_value': current_value,
            'absolute_change': absolute_change,
            'percentage_change': percentage_change,
            'unrealized_pnl_change': self.current_portfolio.unrealized_pnl - baseline_snapshot.portfolio.unrealized_pnl
        }
    
    def get_position_manager_status(self) -> Dict[str, Any]:
        """
        Get position manager status and statistics
        
        Returns:
            Status dictionary
        """
        if not self.current_portfolio:
            return {
                'initialized': False,
                'message': 'Portfolio not initialized'
            }
        
        return {
            'initialized': True,
            'last_sync_time': self.last_sync_time.isoformat(),
            'auto_sync_due': self.should_auto_sync(),
            'portfolio_summary': {
                'total_value_usdt': self.current_portfolio.total_value_usdt,
                'btc_balance': self.current_portfolio.btc_balance,
                'usdt_balance': self.current_portfolio.usdt_balance,
                'unrealized_pnl': self.current_portfolio.unrealized_pnl,
                'position_count': len(self.current_portfolio.positions)
            },
            'tracking_statistics': {
                'total_updates': len(self.position_updates),
                'total_snapshots': len(self.portfolio_snapshots),
                'price_cache_entries': len(self.price_cache)
            },
            'status_timestamp': datetime.utcnow().isoformat()
        }