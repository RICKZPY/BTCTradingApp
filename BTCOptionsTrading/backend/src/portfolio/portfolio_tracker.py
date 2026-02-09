"""
Portfolio Tracker for real-time portfolio monitoring and reporting.

This module provides functionality to:
1. Track portfolio positions and calculate real-time value
2. Monitor portfolio Greeks and risk metrics
3. Record trading history
4. Generate performance reports
5. Calculate excess returns vs BTC spot
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import numpy as np

from ..core.models import OptionContract, Portfolio, OptionType


@dataclass
class PortfolioGreeks:
    """Portfolio-level Greeks (no validation constraints)."""
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float
from ..pricing.options_engine import OptionsEngine


@dataclass
class PortfolioSnapshot:
    """Snapshot of portfolio state at a point in time."""
    timestamp: datetime
    total_value: float
    cash: float
    options_value: float
    total_pnl: float
    pnl_percent: float
    greeks: PortfolioGreeks
    num_positions: int


@dataclass
class TradeRecord:
    """Record of a single trade."""
    trade_id: str
    timestamp: datetime
    option: OptionContract
    action: str  # 'BUY' or 'SELL'
    quantity: int
    price: float
    total_cost: float
    commission: float = 0.0


@dataclass
class PerformanceReport:
    """Portfolio performance report."""
    start_date: datetime
    end_date: datetime
    initial_value: float
    final_value: float
    total_return: float
    total_return_pct: float
    btc_return_pct: float
    excess_return_pct: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    num_trades: int
    avg_trade_pnl: float
    best_trade: float
    worst_trade: float


class PortfolioTracker:
    """
    Portfolio tracker for real-time monitoring and reporting.
    
    Features:
    - Real-time portfolio valuation
    - Greeks tracking
    - Trade history recording
    - Performance analysis
    - Excess return calculation vs BTC spot
    """
    
    def __init__(
        self,
        initial_cash: float,
        options_engine: OptionsEngine,
        commission_rate: float = 0.0003  # 0.03% Deribit taker fee
    ):
        """
        Initialize portfolio tracker.
        
        Args:
            initial_cash: Initial cash balance
            options_engine: Options pricing engine
            commission_rate: Commission rate per trade
        """
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.options_engine = options_engine
        self.commission_rate = commission_rate
        
        # Portfolio state
        self.positions: Dict[str, Tuple[OptionContract, int]] = {}  # instrument_name -> (option, quantity)
        self.trade_history: List[TradeRecord] = []
        self.snapshots: List[PortfolioSnapshot] = []
        
        # Performance tracking
        self.initial_btc_price: Optional[float] = None
        self.trade_counter = 0
    
    def add_position(
        self,
        option: OptionContract,
        quantity: int,
        price: float,
        timestamp: Optional[datetime] = None
    ) -> TradeRecord:
        """
        Add a position to the portfolio (buy).
        
        Args:
            option: Option contract
            quantity: Number of contracts (positive for buy)
            price: Price per contract
            timestamp: Trade timestamp
            
        Returns:
            Trade record
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # Calculate costs
        total_cost = price * quantity  # No contract_size in model
        commission = total_cost * self.commission_rate
        total_with_commission = total_cost + commission
        
        # Check if we have enough cash
        if total_with_commission > self.cash:
            raise ValueError(f"Insufficient cash: need {total_with_commission}, have {self.cash}")
        
        # Update cash
        self.cash -= total_with_commission
        
        # Update position
        instrument_name = option.instrument_name
        if instrument_name in self.positions:
            existing_option, existing_qty = self.positions[instrument_name]
            self.positions[instrument_name] = (option, existing_qty + quantity)
        else:
            self.positions[instrument_name] = (option, quantity)
        
        # Record trade
        self.trade_counter += 1
        trade = TradeRecord(
            trade_id=f"T{self.trade_counter:06d}",
            timestamp=timestamp,
            option=option,
            action='BUY',
            quantity=quantity,
            price=price,
            total_cost=total_cost,
            commission=commission
        )
        self.trade_history.append(trade)
        
        return trade
    
    def remove_position(
        self,
        option: OptionContract,
        quantity: int,
        price: float,
        timestamp: Optional[datetime] = None
    ) -> TradeRecord:
        """
        Remove a position from the portfolio (sell).
        
        Args:
            option: Option contract
            quantity: Number of contracts (positive for sell)
            price: Price per contract
            timestamp: Trade timestamp
            
        Returns:
            Trade record
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        instrument_name = option.instrument_name
        if instrument_name not in self.positions:
            raise ValueError(f"No position found for {instrument_name}")
        
        existing_option, existing_qty = self.positions[instrument_name]
        if quantity > existing_qty:
            raise ValueError(f"Cannot sell {quantity} contracts, only have {existing_qty}")
        
        # Calculate proceeds
        total_proceeds = price * quantity  # No contract_size in model
        commission = total_proceeds * self.commission_rate
        net_proceeds = total_proceeds - commission
        
        # Update cash
        self.cash += net_proceeds
        
        # Update position
        new_qty = existing_qty - quantity
        if new_qty == 0:
            del self.positions[instrument_name]
        else:
            self.positions[instrument_name] = (option, new_qty)
        
        # Record trade
        self.trade_counter += 1
        trade = TradeRecord(
            trade_id=f"T{self.trade_counter:06d}",
            timestamp=timestamp,
            option=option,
            action='SELL',
            quantity=quantity,
            price=price,
            total_cost=total_proceeds,
            commission=commission
        )
        self.trade_history.append(trade)
        
        return trade
    
    def calculate_portfolio_value(
        self,
        spot_price: float,
        volatility: float,
        risk_free_rate: float = 0.05,
        timestamp: Optional[datetime] = None
    ) -> float:
        """
        Calculate current portfolio value.
        
        Args:
            spot_price: Current spot price
            volatility: Current implied volatility
            risk_free_rate: Risk-free rate
            timestamp: Valuation timestamp
            
        Returns:
            Total portfolio value (cash + options)
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        options_value = 0.0
        
        for instrument_name, (option, quantity) in self.positions.items():
            # Calculate time to expiry
            time_to_expiry = (option.expiration_date - timestamp).total_seconds() / (365.25 * 24 * 3600)
            
            if time_to_expiry <= 0:
                # Option expired, calculate intrinsic value
                if option.option_type == OptionType.CALL:
                    intrinsic = max(0, spot_price - float(option.strike_price))
                else:
                    intrinsic = max(0, float(option.strike_price) - spot_price)
                option_value = intrinsic
            else:
                # Calculate option price
                option_value = self.options_engine.black_scholes_price(
                    spot_price,
                    float(option.strike_price),
                    time_to_expiry,
                    risk_free_rate,
                    volatility,
                    option.option_type
                )
            
            options_value += option_value * quantity  # No contract_size in model
        
        return self.cash + options_value
    
    def calculate_portfolio_greeks(
        self,
        spot_price: float,
        volatility: float,
        risk_free_rate: float = 0.05,
        timestamp: Optional[datetime] = None
    ) -> PortfolioGreeks:
        """
        Calculate portfolio Greeks.
        
        Args:
            spot_price: Current spot price
            volatility: Current implied volatility
            risk_free_rate: Risk-free rate
            timestamp: Valuation timestamp
            
        Returns:
            Aggregated portfolio Greeks
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        total_delta = 0.0
        total_gamma = 0.0
        total_theta = 0.0
        total_vega = 0.0
        total_rho = 0.0
        
        for instrument_name, (option, quantity) in self.positions.items():
            # Calculate time to expiry
            time_to_expiry = (option.expiration_date - timestamp).total_seconds() / (365.25 * 24 * 3600)
            
            if time_to_expiry <= 0:
                # Option expired, no Greeks
                continue
            
            # Calculate Greeks
            greeks = self.options_engine.calculate_greeks(
                spot_price,
                float(option.strike_price),
                time_to_expiry,
                risk_free_rate,
                volatility,
                option.option_type
            )
            
            # Aggregate Greeks (weighted by quantity, no contract_size in model)
            weight = quantity
            total_delta += greeks.delta * weight
            total_gamma += greeks.gamma * weight
            total_theta += greeks.theta * weight
            total_vega += greeks.vega * weight
            total_rho += greeks.rho * weight
        
        return PortfolioGreeks(
            delta=total_delta,
            gamma=total_gamma,
            theta=total_theta,
            vega=total_vega,
            rho=total_rho
        )
    
    def take_snapshot(
        self,
        spot_price: float,
        volatility: float,
        risk_free_rate: float = 0.05,
        timestamp: Optional[datetime] = None
    ) -> PortfolioSnapshot:
        """
        Take a snapshot of current portfolio state.
        
        Args:
            spot_price: Current spot price
            volatility: Current implied volatility
            risk_free_rate: Risk-free rate
            timestamp: Snapshot timestamp
            
        Returns:
            Portfolio snapshot
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # Calculate values
        total_value = self.calculate_portfolio_value(
            spot_price, volatility, risk_free_rate, timestamp
        )
        options_value = total_value - self.cash
        total_pnl = total_value - self.initial_cash
        pnl_percent = (total_pnl / self.initial_cash) * 100
        
        # Calculate Greeks
        greeks = self.calculate_portfolio_greeks(
            spot_price, volatility, risk_free_rate, timestamp
        )
        
        # Create snapshot
        snapshot = PortfolioSnapshot(
            timestamp=timestamp,
            total_value=total_value,
            cash=self.cash,
            options_value=options_value,
            total_pnl=total_pnl,
            pnl_percent=pnl_percent,
            greeks=greeks,
            num_positions=len(self.positions)
        )
        
        self.snapshots.append(snapshot)
        return snapshot
    
    def get_trade_history(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[TradeRecord]:
        """
        Get trade history within a date range.
        
        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            
        Returns:
            List of trade records
        """
        trades = self.trade_history
        
        if start_date:
            trades = [t for t in trades if t.timestamp >= start_date]
        
        if end_date:
            trades = [t for t in trades if t.timestamp <= end_date]
        
        return trades
    
    def generate_performance_report(
        self,
        final_spot_price: float,
        final_volatility: float,
        initial_btc_price: Optional[float] = None,
        final_btc_price: Optional[float] = None,
        risk_free_rate: float = 0.05
    ) -> PerformanceReport:
        """
        Generate performance report.
        
        Args:
            final_spot_price: Final spot price
            final_volatility: Final volatility
            initial_btc_price: Initial BTC price for excess return calculation
            final_btc_price: Final BTC price for excess return calculation
            risk_free_rate: Risk-free rate
            
        Returns:
            Performance report
        """
        if len(self.snapshots) == 0:
            raise ValueError("No snapshots available for performance report")
        
        # Get date range
        start_date = self.snapshots[0].timestamp
        end_date = self.snapshots[-1].timestamp
        
        # Calculate final value
        final_value = self.calculate_portfolio_value(
            final_spot_price, final_volatility, risk_free_rate, end_date
        )
        
        # Calculate returns
        total_return = final_value - self.initial_cash
        total_return_pct = (total_return / self.initial_cash) * 100
        
        # Calculate BTC returns
        if initial_btc_price and final_btc_price:
            btc_return_pct = ((final_btc_price - initial_btc_price) / initial_btc_price) * 100
            excess_return_pct = total_return_pct - btc_return_pct
        else:
            btc_return_pct = 0.0
            excess_return_pct = 0.0
        
        # Calculate Sharpe ratio from snapshots
        if len(self.snapshots) > 1:
            returns = []
            for i in range(1, len(self.snapshots)):
                prev_value = self.snapshots[i-1].total_value
                curr_value = self.snapshots[i].total_value
                ret = (curr_value - prev_value) / prev_value
                returns.append(ret)
            
            if len(returns) > 0 and np.std(returns) > 0:
                sharpe_ratio = (np.mean(returns) / np.std(returns)) * np.sqrt(252)
            else:
                sharpe_ratio = 0.0
        else:
            sharpe_ratio = 0.0
        
        # Calculate max drawdown
        max_drawdown = 0.0
        peak_value = self.initial_cash
        for snapshot in self.snapshots:
            if snapshot.total_value > peak_value:
                peak_value = snapshot.total_value
            drawdown = (peak_value - snapshot.total_value) / peak_value
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        max_drawdown *= 100  # Convert to percentage
        
        # Analyze trades
        num_trades = len(self.trade_history)
        if num_trades > 0:
            # Calculate trade PnL (simplified - match buy/sell pairs)
            trade_pnls = []
            buy_trades = {}
            
            for trade in self.trade_history:
                instrument_name = trade.option.instrument_name
                if trade.action == 'BUY':
                    if instrument_name not in buy_trades:
                        buy_trades[instrument_name] = []
                    buy_trades[instrument_name].append(trade)
                elif trade.action == 'SELL':
                    if instrument_name in buy_trades and len(buy_trades[instrument_name]) > 0:
                        buy_trade = buy_trades[instrument_name].pop(0)
                        pnl = (trade.price - buy_trade.price) * trade.quantity  # No contract_size
                        pnl -= (trade.commission + buy_trade.commission)
                        trade_pnls.append(pnl)
            
            if len(trade_pnls) > 0:
                avg_trade_pnl = np.mean(trade_pnls)
                best_trade = max(trade_pnls)
                worst_trade = min(trade_pnls)
                win_rate = (sum(1 for pnl in trade_pnls if pnl > 0) / len(trade_pnls)) * 100
            else:
                avg_trade_pnl = 0.0
                best_trade = 0.0
                worst_trade = 0.0
                win_rate = 0.0
        else:
            avg_trade_pnl = 0.0
            best_trade = 0.0
            worst_trade = 0.0
            win_rate = 0.0
        
        return PerformanceReport(
            start_date=start_date,
            end_date=end_date,
            initial_value=self.initial_cash,
            final_value=final_value,
            total_return=total_return,
            total_return_pct=total_return_pct,
            btc_return_pct=btc_return_pct,
            excess_return_pct=excess_return_pct,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            num_trades=num_trades,
            avg_trade_pnl=avg_trade_pnl,
            best_trade=best_trade,
            worst_trade=worst_trade
        )
    
    def get_current_positions(self) -> List[Tuple[OptionContract, int]]:
        """
        Get current positions.
        
        Returns:
            List of (option, quantity) tuples
        """
        return list(self.positions.values())
    
    def get_position_count(self) -> int:
        """Get number of positions."""
        return len(self.positions)
    
    def get_cash_balance(self) -> float:
        """Get current cash balance."""
        return self.cash
