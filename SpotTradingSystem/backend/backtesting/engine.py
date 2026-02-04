"""
Backtesting Engine
Implements historical data backtesting with performance metrics calculation
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
import numpy as np
import pandas as pd
from decimal import Decimal
import uuid

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.data_models import (
    MarketData, TradingDecision, ActionType, Portfolio, Position, 
    TradingRecord, SentimentScore, TechnicalSignal
)
from decision_engine.engine import DecisionEngine, MarketAnalysis
from decision_engine.risk_parameters import RiskParameters

logger = logging.getLogger(__name__)


@dataclass
class BacktestTrade:
    """Individual trade in backtest"""
    trade_id: str
    timestamp: datetime
    action: ActionType
    symbol: str
    quantity: float
    price: float
    value: float
    decision: TradingDecision
    portfolio_value_before: float
    portfolio_value_after: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'trade_id': self.trade_id,
            'timestamp': self.timestamp.isoformat(),
            'action': self.action.value,
            'symbol': self.symbol,
            'quantity': self.quantity,
            'price': self.price,
            'value': self.value,
            'portfolio_value_before': self.portfolio_value_before,
            'portfolio_value_after': self.portfolio_value_after,
            'decision_confidence': self.decision.confidence,
            'decision_reasoning': self.decision.reasoning
        }


@dataclass
class PerformanceMetrics:
    """Performance metrics for backtest results"""
    
    # Basic metrics
    total_return: float
    annualized_return: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    
    # Risk metrics
    sharpe_ratio: float
    max_drawdown: float
    max_drawdown_duration: int  # days
    volatility: float
    
    # Trade metrics
    average_win: float
    average_loss: float
    profit_factor: float
    largest_win: float
    largest_loss: float
    
    # Portfolio metrics
    initial_capital: float
    final_capital: float
    peak_capital: float
    
    # Time metrics
    start_date: datetime
    end_date: datetime
    duration_days: int
    
    # Additional metrics
    calmar_ratio: float  # Annual return / Max drawdown
    sortino_ratio: float  # Return / Downside deviation
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'total_return': self.total_return,
            'annualized_return': self.annualized_return,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': self.win_rate,
            'sharpe_ratio': self.sharpe_ratio,
            'max_drawdown': self.max_drawdown,
            'max_drawdown_duration': self.max_drawdown_duration,
            'volatility': self.volatility,
            'average_win': self.average_win,
            'average_loss': self.average_loss,
            'profit_factor': self.profit_factor,
            'largest_win': self.largest_win,
            'largest_loss': self.largest_loss,
            'initial_capital': self.initial_capital,
            'final_capital': self.final_capital,
            'peak_capital': self.peak_capital,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'duration_days': self.duration_days,
            'calmar_ratio': self.calmar_ratio,
            'sortino_ratio': self.sortino_ratio
        }


@dataclass
class BacktestResult:
    """Complete backtest result"""
    backtest_id: str
    strategy_name: str
    strategy_config: Dict[str, Any]
    performance_metrics: PerformanceMetrics
    trades: List[BacktestTrade]
    portfolio_history: List[Dict[str, Any]]
    equity_curve: List[Tuple[datetime, float]]
    drawdown_curve: List[Tuple[datetime, float]]
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'backtest_id': self.backtest_id,
            'strategy_name': self.strategy_name,
            'strategy_config': self.strategy_config,
            'performance_metrics': self.performance_metrics.to_dict(),
            'total_trades': len(self.trades),
            'equity_curve_points': len(self.equity_curve),
            'created_at': self.created_at.isoformat()
        }


class BacktestEngine:
    """
    Historical data backtesting engine
    """
    
    def __init__(self, initial_capital: float = 10000.0):
        """
        Initialize backtesting engine
        
        Args:
            initial_capital: Starting capital in USDT
        """
        self.initial_capital = initial_capital
        self.commission_rate = 0.001  # 0.1% commission per trade
        self.slippage_rate = 0.0005   # 0.05% slippage per trade
        
        logger.info(f"Backtest engine initialized with ${initial_capital} initial capital")
    
    def run_backtest(self, 
                    start_date: datetime,
                    end_date: datetime,
                    strategy_config: Dict[str, Any],
                    historical_data: List[MarketData],
                    sentiment_data: Optional[List[Dict[str, Any]]] = None,
                    strategy_name: str = "Default Strategy") -> BacktestResult:
        """
        Run complete backtest
        
        Args:
            start_date: Backtest start date
            end_date: Backtest end date
            strategy_config: Strategy configuration parameters
            historical_data: Historical market data
            sentiment_data: Optional historical sentiment data
            strategy_name: Name of the strategy being tested
            
        Returns:
            BacktestResult with complete results and metrics
        """
        backtest_id = f"BT_{uuid.uuid4().hex[:8]}_{int(datetime.utcnow().timestamp())}"
        
        logger.info(f"Starting backtest {backtest_id}: {strategy_name} from {start_date} to {end_date}")
        
        # Filter data by date range
        filtered_data = self._filter_data_by_date(historical_data, start_date, end_date)
        
        if len(filtered_data) < 2:
            raise ValueError(f"Insufficient historical data: only {len(filtered_data)} data points")
        
        # Initialize decision engine with strategy config
        risk_params = RiskParameters.from_dict(strategy_config.get('risk_parameters', {}))
        decision_engine = DecisionEngine(risk_params)
        
        # Initialize portfolio
        portfolio = Portfolio(
            btc_balance=0.0,
            usdt_balance=self.initial_capital,
            total_value_usdt=self.initial_capital,
            unrealized_pnl=0.0
        )
        
        # Track backtest state
        trades: List[BacktestTrade] = []
        portfolio_history: List[Dict[str, Any]] = []
        equity_curve: List[Tuple[datetime, float]] = []
        
        # Process each data point
        for i, market_data in enumerate(filtered_data):
            try:
                # Update portfolio value with current price
                self._update_portfolio_value(portfolio, market_data.price)
                
                # Record portfolio state
                portfolio_snapshot = {
                    'timestamp': market_data.timestamp.isoformat(),
                    'btc_balance': portfolio.btc_balance,
                    'usdt_balance': portfolio.usdt_balance,
                    'total_value_usdt': portfolio.total_value_usdt,
                    'unrealized_pnl': portfolio.unrealized_pnl,
                    'btc_price': market_data.price
                }
                portfolio_history.append(portfolio_snapshot)
                equity_curve.append((market_data.timestamp, portfolio.total_value_usdt))
                
                # Generate signals for decision making
                sentiment_score = self._get_sentiment_for_timestamp(
                    sentiment_data, market_data.timestamp
                ) if sentiment_data else self._generate_default_sentiment()
                
                technical_signal = self._generate_technical_signal(
                    filtered_data, i, strategy_config
                )
                
                # Generate market analysis
                market_analysis = decision_engine.analyze_market_conditions(
                    sentiment_score=sentiment_score,
                    technical_signal=technical_signal,
                    portfolio=portfolio,
                    current_price=market_data.price,
                    market_data=filtered_data[max(0, i-24):i+1]  # Last 24 data points
                )
                
                # Generate trading decision
                trading_decision = decision_engine.generate_trading_decision(market_analysis)
                
                # Execute trade if decision is not HOLD
                if trading_decision.action != ActionType.HOLD:
                    trade = self._execute_simulated_trade(
                        trading_decision, portfolio, market_data
                    )
                    if trade:
                        trades.append(trade)
                        
                        # Update decision engine trade history
                        decision_engine.update_trade_history(True)
                
            except Exception as e:
                logger.error(f"Error processing data point {i} at {market_data.timestamp}: {e}")
                continue
        
        # Calculate performance metrics
        performance_metrics = self._calculate_performance_metrics(
            trades, equity_curve, start_date, end_date, self.initial_capital
        )
        
        # Calculate drawdown curve
        drawdown_curve = self._calculate_drawdown_curve(equity_curve)
        
        # Create backtest result
        result = BacktestResult(
            backtest_id=backtest_id,
            strategy_name=strategy_name,
            strategy_config=strategy_config,
            performance_metrics=performance_metrics,
            trades=trades,
            portfolio_history=portfolio_history,
            equity_curve=equity_curve,
            drawdown_curve=drawdown_curve
        )
        
        logger.info(f"Backtest {backtest_id} completed: {len(trades)} trades, "
                   f"{performance_metrics.total_return:.2%} return, "
                   f"{performance_metrics.sharpe_ratio:.2f} Sharpe ratio")
        
        return result
    
    def _filter_data_by_date(self, data: List[MarketData], 
                           start_date: datetime, end_date: datetime) -> List[MarketData]:
        """Filter market data by date range"""
        return [
            d for d in data 
            if start_date <= d.timestamp <= end_date
        ]
    
    def _update_portfolio_value(self, portfolio: Portfolio, current_price: float):
        """Update portfolio total value based on current BTC price"""
        btc_value = portfolio.btc_balance * current_price
        portfolio.total_value_usdt = portfolio.usdt_balance + btc_value
        
        # Update unrealized PnL for positions
        for position in portfolio.positions:
            if position.symbol == "BTCUSDT":
                position.update_current_price(current_price)
        
        portfolio.update_unrealized_pnl()
    
    def _get_sentiment_for_timestamp(self, sentiment_data: List[Dict[str, Any]], 
                                   timestamp: datetime) -> SentimentScore:
        """Get sentiment score for specific timestamp"""
        # Find closest sentiment data point
        closest_sentiment = None
        min_time_diff = timedelta.max
        
        for sentiment in sentiment_data:
            sentiment_time = datetime.fromisoformat(sentiment['timestamp'])
            time_diff = abs(sentiment_time - timestamp)
            
            if time_diff < min_time_diff:
                min_time_diff = time_diff
                closest_sentiment = sentiment
        
        if closest_sentiment and min_time_diff < timedelta(hours=6):  # Within 6 hours
            return SentimentScore(
                sentiment_value=closest_sentiment['sentiment_value'],
                confidence=closest_sentiment['confidence'],
                key_factors=closest_sentiment.get('key_factors', [])
            )
        else:
            return self._generate_default_sentiment()
    
    def _generate_default_sentiment(self) -> SentimentScore:
        """Generate neutral sentiment when no data available"""
        return SentimentScore(
            sentiment_value=50.0,  # Neutral
            confidence=0.5,
            key_factors=["no_sentiment_data"]
        )
    
    def _generate_technical_signal(self, data: List[MarketData], 
                                 current_index: int, 
                                 strategy_config: Dict[str, Any]) -> TechnicalSignal:
        """Generate technical signal based on historical data"""
        if current_index < 20:  # Need at least 20 data points
            return TechnicalSignal(
                signal_strength=0.0,
                signal_type=ActionType.HOLD,
                confidence=0.5,
                contributing_indicators=["insufficient_data"]
            )
        
        # Get recent prices
        recent_data = data[max(0, current_index-50):current_index+1]
        prices = [d.price for d in recent_data]
        
        # Simple moving average crossover strategy
        if len(prices) >= 20:
            sma_short = np.mean(prices[-10:])  # 10-period SMA
            sma_long = np.mean(prices[-20:])   # 20-period SMA
            
            # Calculate signal strength
            price_diff = (sma_short - sma_long) / sma_long
            signal_strength = np.clip(price_diff * 10, -1.0, 1.0)  # Scale to -1 to 1
            
            # Determine signal type
            if signal_strength > 0.2:
                signal_type = ActionType.BUY
            elif signal_strength < -0.2:
                signal_type = ActionType.SELL
            else:
                signal_type = ActionType.HOLD
            
            # Calculate confidence based on trend consistency
            recent_prices = prices[-10:]
            if len(recent_prices) > 1:
                recent_returns = np.diff(recent_prices) / recent_prices[:-1]
                trend_consistency = 1.0 - np.std(recent_returns) / (np.mean(np.abs(recent_returns)) + 1e-8)
                confidence = np.clip(trend_consistency, 0.3, 0.9)
            else:
                confidence = 0.5
            
            return TechnicalSignal(
                signal_strength=signal_strength,
                signal_type=signal_type,
                confidence=confidence,
                contributing_indicators=["sma_crossover", "trend_analysis"]
            )
        
        return TechnicalSignal(
            signal_strength=0.0,
            signal_type=ActionType.HOLD,
            confidence=0.5,
            contributing_indicators=["default"]
        )
    
    def _execute_simulated_trade(self, decision: TradingDecision, 
                               portfolio: Portfolio, 
                               market_data: MarketData) -> Optional[BacktestTrade]:
        """Execute simulated trade based on decision"""
        
        # Calculate trade price with slippage
        if decision.action == ActionType.BUY:
            trade_price = market_data.price * (1 + self.slippage_rate)
        else:  # SELL
            trade_price = market_data.price * (1 - self.slippage_rate)
        
        # Calculate quantity based on decision
        portfolio_value_before = portfolio.total_value_usdt
        
        if decision.action == ActionType.BUY:
            # Calculate how much USDT to spend
            usdt_to_spend = portfolio.usdt_balance * decision.suggested_amount
            
            # Check if we have enough USDT
            if usdt_to_spend > portfolio.usdt_balance:
                logger.warning(f"Insufficient USDT balance: need {usdt_to_spend}, have {portfolio.usdt_balance}")
                return None
            
            # Calculate BTC quantity (including commission)
            gross_btc_quantity = usdt_to_spend / trade_price
            commission = gross_btc_quantity * self.commission_rate
            net_btc_quantity = gross_btc_quantity - commission
            
            if net_btc_quantity <= 0:
                logger.warning("Trade quantity too small after commission")
                return None
            
            # Update portfolio
            portfolio.usdt_balance -= usdt_to_spend
            portfolio.btc_balance += net_btc_quantity
            
            # Create position
            position = Position(
                symbol="BTCUSDT",
                amount=net_btc_quantity,
                entry_price=trade_price,
                current_price=trade_price,
                pnl=0.0,
                entry_time=market_data.timestamp
            )
            portfolio.add_position(position)
            
            trade = BacktestTrade(
                trade_id=f"T_{uuid.uuid4().hex[:8]}",
                timestamp=market_data.timestamp,
                action=ActionType.BUY,
                symbol="BTCUSDT",
                quantity=net_btc_quantity,
                price=trade_price,
                value=usdt_to_spend,
                decision=decision,
                portfolio_value_before=portfolio_value_before,
                portfolio_value_after=portfolio.total_value_usdt
            )
            
        elif decision.action == ActionType.SELL:
            # Calculate how much BTC to sell
            btc_to_sell = portfolio.btc_balance * decision.suggested_amount
            
            # Check if we have enough BTC
            if btc_to_sell > portfolio.btc_balance:
                logger.warning(f"Insufficient BTC balance: need {btc_to_sell}, have {portfolio.btc_balance}")
                return None
            
            # Calculate USDT received (after commission)
            gross_usdt_received = btc_to_sell * trade_price
            commission = gross_usdt_received * self.commission_rate
            net_usdt_received = gross_usdt_received - commission
            
            # Update portfolio
            portfolio.btc_balance -= btc_to_sell
            portfolio.usdt_balance += net_usdt_received
            
            # Remove or update position
            for position in portfolio.positions[:]:  # Copy list to avoid modification during iteration
                if position.symbol == "BTCUSDT" and position.amount > 0:
                    if btc_to_sell >= position.amount:
                        # Close entire position
                        btc_to_sell -= position.amount
                        portfolio.remove_position(position.symbol)
                    else:
                        # Partial close
                        position.amount -= btc_to_sell
                        btc_to_sell = 0
                    
                    if btc_to_sell <= 0:
                        break
            
            trade = BacktestTrade(
                trade_id=f"T_{uuid.uuid4().hex[:8]}",
                timestamp=market_data.timestamp,
                action=ActionType.SELL,
                symbol="BTCUSDT",
                quantity=btc_to_sell,
                price=trade_price,
                value=net_usdt_received,
                decision=decision,
                portfolio_value_before=portfolio_value_before,
                portfolio_value_after=portfolio.total_value_usdt
            )
        
        else:
            return None
        
        # Update portfolio value
        self._update_portfolio_value(portfolio, market_data.price)
        trade.portfolio_value_after = portfolio.total_value_usdt
        
        logger.debug(f"Executed {decision.action.value} trade: {trade.quantity:.6f} BTC at ${trade.price:.2f}")
        
        return trade
    
    def _calculate_performance_metrics(self, trades: List[BacktestTrade],
                                     equity_curve: List[Tuple[datetime, float]],
                                     start_date: datetime,
                                     end_date: datetime,
                                     initial_capital: float) -> PerformanceMetrics:
        """Calculate comprehensive performance metrics"""
        
        if not equity_curve:
            raise ValueError("No equity curve data available")
        
        final_capital = equity_curve[-1][1]
        peak_capital = max(value for _, value in equity_curve)
        
        # Basic metrics
        total_return = (final_capital - initial_capital) / initial_capital
        duration_days = (end_date - start_date).days
        annualized_return = (1 + total_return) ** (365.25 / max(duration_days, 1)) - 1
        
        # Trade metrics
        winning_trades = len([t for t in trades if self._is_winning_trade(t)])
        losing_trades = len([t for t in trades if self._is_losing_trade(t)])
        win_rate = winning_trades / len(trades) if trades else 0.0
        
        # Calculate trade PnLs
        trade_pnls = [self._calculate_trade_pnl(t) for t in trades]
        winning_pnls = [pnl for pnl in trade_pnls if pnl > 0]
        losing_pnls = [pnl for pnl in trade_pnls if pnl < 0]
        
        average_win = np.mean(winning_pnls) if winning_pnls else 0.0
        average_loss = np.mean(losing_pnls) if losing_pnls else 0.0
        largest_win = max(winning_pnls) if winning_pnls else 0.0
        largest_loss = min(losing_pnls) if losing_pnls else 0.0
        
        # Profit factor
        gross_profit = sum(winning_pnls) if winning_pnls else 0.0
        gross_loss = abs(sum(losing_pnls)) if losing_pnls else 0.0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Risk metrics
        returns = self._calculate_returns(equity_curve)
        volatility = np.std(returns) * np.sqrt(252) if len(returns) > 1 else 0.0  # Annualized
        
        # Sharpe ratio (assuming 0% risk-free rate)
        sharpe_ratio = annualized_return / volatility if volatility > 0 else 0.0
        
        # Drawdown metrics
        max_drawdown, max_drawdown_duration = self._calculate_max_drawdown(equity_curve)
        
        # Calmar ratio
        calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0.0
        
        # Sortino ratio
        downside_returns = [r for r in returns if r < 0]
        downside_deviation = np.std(downside_returns) * np.sqrt(252) if downside_returns else 0.0
        sortino_ratio = annualized_return / downside_deviation if downside_deviation > 0 else 0.0
        
        return PerformanceMetrics(
            total_return=total_return,
            annualized_return=annualized_return,
            total_trades=len(trades),
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            max_drawdown_duration=max_drawdown_duration,
            volatility=volatility,
            average_win=average_win,
            average_loss=average_loss,
            profit_factor=profit_factor,
            largest_win=largest_win,
            largest_loss=largest_loss,
            initial_capital=initial_capital,
            final_capital=final_capital,
            peak_capital=peak_capital,
            start_date=start_date,
            end_date=end_date,
            duration_days=duration_days,
            calmar_ratio=calmar_ratio,
            sortino_ratio=sortino_ratio
        )
    
    def _is_winning_trade(self, trade: BacktestTrade) -> bool:
        """Check if trade is winning"""
        return trade.portfolio_value_after > trade.portfolio_value_before
    
    def _is_losing_trade(self, trade: BacktestTrade) -> bool:
        """Check if trade is losing"""
        return trade.portfolio_value_after < trade.portfolio_value_before
    
    def _calculate_trade_pnl(self, trade: BacktestTrade) -> float:
        """Calculate trade PnL"""
        return trade.portfolio_value_after - trade.portfolio_value_before
    
    def _calculate_returns(self, equity_curve: List[Tuple[datetime, float]]) -> List[float]:
        """Calculate daily returns from equity curve"""
        if len(equity_curve) < 2:
            return []
        
        values = [value for _, value in equity_curve]
        returns = []
        
        for i in range(1, len(values)):
            if values[i-1] > 0:
                ret = (values[i] - values[i-1]) / values[i-1]
                returns.append(ret)
        
        return returns
    
    def _calculate_max_drawdown(self, equity_curve: List[Tuple[datetime, float]]) -> Tuple[float, int]:
        """Calculate maximum drawdown and duration"""
        if len(equity_curve) < 2:
            return 0.0, 0
        
        values = [value for _, value in equity_curve]
        peak = values[0]
        max_drawdown = 0.0
        max_duration = 0
        current_duration = 0
        
        for value in values:
            if value > peak:
                peak = value
                current_duration = 0
            else:
                drawdown = (peak - value) / peak
                max_drawdown = max(max_drawdown, drawdown)
                current_duration += 1
                max_duration = max(max_duration, current_duration)
        
        return max_drawdown, max_duration
    
    def _calculate_drawdown_curve(self, equity_curve: List[Tuple[datetime, float]]) -> List[Tuple[datetime, float]]:
        """Calculate drawdown curve"""
        if len(equity_curve) < 2:
            return []
        
        drawdown_curve = []
        peak = equity_curve[0][1]
        
        for timestamp, value in equity_curve:
            if value > peak:
                peak = value
            
            drawdown = (peak - value) / peak if peak > 0 else 0.0
            drawdown_curve.append((timestamp, drawdown))
        
        return drawdown_curve
    
    def simulate_trading(self, historical_data: List[MarketData],
                        strategy_config: Dict[str, Any]) -> List[BacktestTrade]:
        """
        Simulate trading on historical data
        
        Args:
            historical_data: Historical market data
            strategy_config: Strategy configuration
            
        Returns:
            List of simulated trades
        """
        if not historical_data:
            return []
        
        start_date = historical_data[0].timestamp
        end_date = historical_data[-1].timestamp
        
        result = self.run_backtest(
            start_date=start_date,
            end_date=end_date,
            strategy_config=strategy_config,
            historical_data=historical_data,
            strategy_name="Simulation"
        )
        
        return result.trades
    
    def get_engine_status(self) -> Dict[str, Any]:
        """Get backtest engine status"""
        return {
            'initial_capital': self.initial_capital,
            'commission_rate': self.commission_rate,
            'slippage_rate': self.slippage_rate,
            'engine_ready': True,
            'supported_metrics': [
                'total_return', 'sharpe_ratio', 'max_drawdown', 'win_rate',
                'profit_factor', 'calmar_ratio', 'sortino_ratio'
            ]
        }