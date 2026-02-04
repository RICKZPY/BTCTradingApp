"""
Unit tests for the backtesting engine
Tests backtest result accuracy and performance metrics calculation
"""
import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from decimal import Decimal
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backtesting.engine import (
    BacktestEngine, PerformanceMetrics, BacktestTrade, BacktestResult
)
from core.data_models import (
    MarketData, TradingDecision, ActionType, Portfolio, Position, SentimentScore, TechnicalSignal
)
from decision_engine.risk_parameters import RiskParameters


class TestBacktestEngine(unittest.TestCase):
    """Test cases for BacktestEngine"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = BacktestEngine(initial_capital=10000.0)
        self.start_date = datetime(2024, 1, 1, 0, 0, 0)
        self.end_date = datetime(2024, 1, 7, 23, 0, 0)
        
        # Create sample market data
        self.sample_market_data = self._create_sample_market_data()
        
        # Create sample strategy config
        self.strategy_config = {
            'risk_parameters': RiskParameters().to_dict(),
            'technical_indicators': {
                'sma_short_period': 10,
                'sma_long_period': 20
            }
        }
    
    def _create_sample_market_data(self) -> list:
        """Create sample market data for testing"""
        data = []
        current_time = self.start_date
        price = 45000.0
        
        while current_time <= self.end_date:
            # Create predictable price movement for testing
            hours_elapsed = (current_time - self.start_date).total_seconds() / 3600
            price_change = 0.001 * (hours_elapsed % 24 - 12)  # Oscillating pattern
            price *= (1 + price_change)
            
            data.append(MarketData(
                symbol="BTCUSDT",
                price=round(price, 2),
                volume=100.0,
                timestamp=current_time,
                source="test"
            ))
            
            current_time += timedelta(hours=1)
        
        return data
    
    def test_engine_initialization(self):
        """Test BacktestEngine initialization"""
        engine = BacktestEngine(initial_capital=5000.0)
        
        self.assertEqual(engine.initial_capital, 5000.0)
        self.assertEqual(engine.commission_rate, 0.001)
        self.assertEqual(engine.slippage_rate, 0.0005)
    
    def test_filter_data_by_date(self):
        """Test data filtering by date range"""
        # Test normal filtering
        filtered_data = self.engine._filter_data_by_date(
            self.sample_market_data, 
            self.start_date + timedelta(days=1),
            self.start_date + timedelta(days=2)
        )
        
        # Should have 24 hours of data (1 day)
        self.assertEqual(len(filtered_data), 25)  # Inclusive of both endpoints
        
        # Test edge case: no data in range
        future_start = self.end_date + timedelta(days=1)
        future_end = self.end_date + timedelta(days=2)
        empty_data = self.engine._filter_data_by_date(
            self.sample_market_data, future_start, future_end
        )
        
        self.assertEqual(len(empty_data), 0)
    
    def test_portfolio_value_update(self):
        """Test portfolio value calculation"""
        portfolio = Portfolio(
            btc_balance=1.0,
            usdt_balance=5000.0,
            total_value_usdt=50000.0,
            unrealized_pnl=0.0
        )
        
        # Add a position
        position = Position(
            symbol="BTCUSDT",
            amount=1.0,
            entry_price=45000.0,
            current_price=45000.0,
            pnl=0.0,
            entry_time=self.start_date
        )
        portfolio.add_position(position)
        
        # Update with new price
        new_price = 46000.0
        self.engine._update_portfolio_value(portfolio, new_price)
        
        # Check calculations
        expected_total = 5000.0 + (1.0 * 46000.0)  # USDT + BTC value
        self.assertEqual(portfolio.total_value_usdt, expected_total)
    
    def test_generate_default_sentiment(self):
        """Test default sentiment generation"""
        sentiment = self.engine._generate_default_sentiment()
        
        self.assertEqual(sentiment.sentiment_value, 50.0)
        self.assertEqual(sentiment.confidence, 0.5)
        self.assertIn("no_sentiment_data", sentiment.key_factors)
    
    def test_generate_technical_signal_insufficient_data(self):
        """Test technical signal generation with insufficient data"""
        # Test with very little data
        signal = self.engine._generate_technical_signal(
            self.sample_market_data[:5], 2, self.strategy_config
        )
        
        self.assertEqual(signal.signal_type, ActionType.HOLD)
        self.assertEqual(signal.signal_strength, 0.0)
        self.assertIn("insufficient_data", signal.contributing_indicators)
    
    def test_generate_technical_signal_sufficient_data(self):
        """Test technical signal generation with sufficient data"""
        # Test with enough data
        signal = self.engine._generate_technical_signal(
            self.sample_market_data, 50, self.strategy_config
        )
        
        # Should generate a valid signal
        self.assertIn(signal.signal_type, [ActionType.BUY, ActionType.SELL, ActionType.HOLD])
        self.assertGreaterEqual(signal.signal_strength, -1.0)
        self.assertLessEqual(signal.signal_strength, 1.0)
        self.assertGreaterEqual(signal.confidence, 0.3)
        self.assertLessEqual(signal.confidence, 0.9)
    
    def test_calculate_performance_metrics_basic(self):
        """Test basic performance metrics calculation"""
        # Create sample trades
        trades = [
            BacktestTrade(
                trade_id="T1",
                timestamp=self.start_date,
                action=ActionType.BUY,
                symbol="BTCUSDT",
                quantity=0.1,
                price=45000.0,
                value=4500.0,
                decision=Mock(),
                portfolio_value_before=10000.0,
                portfolio_value_after=10500.0
            ),
            BacktestTrade(
                trade_id="T2",
                timestamp=self.start_date + timedelta(days=1),
                action=ActionType.SELL,
                symbol="BTCUSDT",
                quantity=0.1,
                price=46000.0,
                value=4600.0,
                decision=Mock(),
                portfolio_value_before=10500.0,
                portfolio_value_after=10600.0
            )
        ]
        
        # Create sample equity curve
        equity_curve = [
            (self.start_date, 10000.0),
            (self.start_date + timedelta(days=1), 10500.0),
            (self.start_date + timedelta(days=2), 10600.0),
            (self.end_date, 10800.0)
        ]
        
        metrics = self.engine._calculate_performance_metrics(
            trades, equity_curve, self.start_date, self.end_date, 10000.0
        )
        
        # Verify basic metrics
        self.assertEqual(metrics.initial_capital, 10000.0)
        self.assertEqual(metrics.final_capital, 10800.0)
        self.assertEqual(metrics.total_trades, 2)
        self.assertAlmostEqual(metrics.total_return, 0.08, places=4)  # 8% return
        
        # Verify trade metrics
        self.assertEqual(metrics.winning_trades, 2)  # Both trades are winning
        self.assertEqual(metrics.losing_trades, 0)
        self.assertEqual(metrics.win_rate, 1.0)  # 100% win rate
    
    def test_calculate_performance_metrics_with_losses(self):
        """Test performance metrics with losing trades"""
        # Create trades with losses
        trades = [
            BacktestTrade(
                trade_id="T1",
                timestamp=self.start_date,
                action=ActionType.BUY,
                symbol="BTCUSDT",
                quantity=0.1,
                price=45000.0,
                value=4500.0,
                decision=Mock(),
                portfolio_value_before=10000.0,
                portfolio_value_after=9800.0  # Loss
            ),
            BacktestTrade(
                trade_id="T2",
                timestamp=self.start_date + timedelta(days=1),
                action=ActionType.SELL,
                symbol="BTCUSDT",
                quantity=0.1,
                price=46000.0,
                value=4600.0,
                decision=Mock(),
                portfolio_value_before=9800.0,
                portfolio_value_after=10200.0  # Win
            )
        ]
        
        equity_curve = [
            (self.start_date, 10000.0),
            (self.start_date + timedelta(days=1), 9800.0),
            (self.end_date, 10200.0)
        ]
        
        metrics = self.engine._calculate_performance_metrics(
            trades, equity_curve, self.start_date, self.end_date, 10000.0
        )
        
        # Verify mixed results
        self.assertEqual(metrics.winning_trades, 1)
        self.assertEqual(metrics.losing_trades, 1)
        self.assertEqual(metrics.win_rate, 0.5)
        self.assertLess(metrics.average_loss, 0)  # Negative average loss
        self.assertGreater(metrics.average_win, 0)  # Positive average win
    
    def test_calculate_max_drawdown(self):
        """Test maximum drawdown calculation"""
        # Create equity curve with drawdown
        equity_curve = [
            (self.start_date, 10000.0),
            (self.start_date + timedelta(days=1), 11000.0),  # Peak
            (self.start_date + timedelta(days=2), 10500.0),  # Drawdown starts
            (self.start_date + timedelta(days=3), 9500.0),   # Max drawdown
            (self.start_date + timedelta(days=4), 10800.0),  # Recovery
        ]
        
        max_drawdown, max_duration = self.engine._calculate_max_drawdown(equity_curve)
        
        # Max drawdown should be (11000 - 9500) / 11000 = 13.64%
        expected_drawdown = (11000.0 - 9500.0) / 11000.0
        self.assertAlmostEqual(max_drawdown, expected_drawdown, places=4)
        self.assertEqual(max_duration, 3)  # 3 periods of drawdown (from peak to recovery)
    
    def test_calculate_drawdown_curve(self):
        """Test drawdown curve calculation"""
        equity_curve = [
            (self.start_date, 10000.0),
            (self.start_date + timedelta(days=1), 11000.0),
            (self.start_date + timedelta(days=2), 10500.0),
            (self.start_date + timedelta(days=3), 12000.0),
        ]
        
        drawdown_curve = self.engine._calculate_drawdown_curve(equity_curve)
        
        self.assertEqual(len(drawdown_curve), len(equity_curve))
        
        # First point should have 0 drawdown (at peak)
        self.assertEqual(drawdown_curve[0][1], 0.0)
        
        # Second point should still have 0 drawdown (new peak)
        self.assertEqual(drawdown_curve[1][1], 0.0)
        
        # Third point should have drawdown from 11000 peak
        expected_dd = (11000.0 - 10500.0) / 11000.0
        self.assertAlmostEqual(drawdown_curve[2][1], expected_dd, places=4)
        
        # Fourth point should have 0 drawdown (new peak)
        self.assertEqual(drawdown_curve[3][1], 0.0)
    
    def test_calculate_returns(self):
        """Test returns calculation from equity curve"""
        equity_curve = [
            (self.start_date, 10000.0),
            (self.start_date + timedelta(days=1), 10500.0),  # 5% return
            (self.start_date + timedelta(days=2), 10000.0),  # -4.76% return
            (self.start_date + timedelta(days=3), 11000.0),  # 10% return
        ]
        
        returns = self.engine._calculate_returns(equity_curve)
        
        self.assertEqual(len(returns), 3)  # n-1 returns for n values
        
        # Check first return: (10500 - 10000) / 10000 = 0.05
        self.assertAlmostEqual(returns[0], 0.05, places=4)
        
        # Check second return: (10000 - 10500) / 10500 ≈ -0.0476
        self.assertAlmostEqual(returns[1], -0.047619, places=4)
        
        # Check third return: (11000 - 10000) / 10000 = 0.10
        self.assertAlmostEqual(returns[2], 0.10, places=4)
    
    def test_is_winning_losing_trade(self):
        """Test trade classification"""
        winning_trade = BacktestTrade(
            trade_id="W1",
            timestamp=self.start_date,
            action=ActionType.BUY,
            symbol="BTCUSDT",
            quantity=0.1,
            price=45000.0,
            value=4500.0,
            decision=Mock(),
            portfolio_value_before=10000.0,
            portfolio_value_after=10500.0
        )
        
        losing_trade = BacktestTrade(
            trade_id="L1",
            timestamp=self.start_date,
            action=ActionType.SELL,
            symbol="BTCUSDT",
            quantity=0.1,
            price=44000.0,
            value=4400.0,
            decision=Mock(),
            portfolio_value_before=10000.0,
            portfolio_value_after=9800.0
        )
        
        self.assertTrue(self.engine._is_winning_trade(winning_trade))
        self.assertFalse(self.engine._is_losing_trade(winning_trade))
        
        self.assertTrue(self.engine._is_losing_trade(losing_trade))
        self.assertFalse(self.engine._is_winning_trade(losing_trade))
    
    def test_calculate_trade_pnl(self):
        """Test trade PnL calculation"""
        trade = BacktestTrade(
            trade_id="T1",
            timestamp=self.start_date,
            action=ActionType.BUY,
            symbol="BTCUSDT",
            quantity=0.1,
            price=45000.0,
            value=4500.0,
            decision=Mock(),
            portfolio_value_before=10000.0,
            portfolio_value_after=10300.0
        )
        
        pnl = self.engine._calculate_trade_pnl(trade)
        self.assertEqual(pnl, 300.0)  # 10300 - 10000
    
    def test_simulate_trading(self):
        """Test trading simulation"""
        trades = self.engine.simulate_trading(
            self.sample_market_data, 
            self.strategy_config
        )
        
        # Should return a list of trades
        self.assertIsInstance(trades, list)
        
        # All trades should be BacktestTrade objects
        for trade in trades:
            self.assertIsInstance(trade, BacktestTrade)
            self.assertIn(trade.action, [ActionType.BUY, ActionType.SELL])
            self.assertGreater(trade.price, 0)
            self.assertGreater(trade.quantity, 0)
    
    def test_get_engine_status(self):
        """Test engine status reporting"""
        status = self.engine.get_engine_status()
        
        self.assertIsInstance(status, dict)
        self.assertEqual(status['initial_capital'], 10000.0)
        self.assertEqual(status['commission_rate'], 0.001)
        self.assertEqual(status['slippage_rate'], 0.0005)
        self.assertTrue(status['engine_ready'])
        self.assertIn('supported_metrics', status)
        
        # Check supported metrics
        expected_metrics = [
            'total_return', 'sharpe_ratio', 'max_drawdown', 'win_rate',
            'profit_factor', 'calmar_ratio', 'sortino_ratio'
        ]
        for metric in expected_metrics:
            self.assertIn(metric, status['supported_metrics'])
    
    def test_run_backtest_insufficient_data(self):
        """Test backtest with insufficient data"""
        # Create minimal data (less than 2 points)
        minimal_data = [self.sample_market_data[0]]
        
        with self.assertRaises(ValueError) as context:
            self.engine.run_backtest(
                start_date=self.start_date,
                end_date=self.end_date,
                strategy_config=self.strategy_config,
                historical_data=minimal_data,
                strategy_name="Test"
            )
        
        self.assertIn("Insufficient historical data", str(context.exception))
    
    def test_run_backtest_empty_data(self):
        """Test backtest with empty data"""
        with self.assertRaises(ValueError) as context:
            self.engine.run_backtest(
                start_date=self.start_date,
                end_date=self.end_date,
                strategy_config=self.strategy_config,
                historical_data=[],
                strategy_name="Test"
            )
        
        self.assertIn("Insufficient historical data", str(context.exception))
    
    @patch('backtesting.engine.DecisionEngine')
    def test_run_backtest_success(self, mock_decision_engine_class):
        """Test successful backtest execution"""
        # Mock the decision engine
        mock_decision_engine = Mock()
        mock_decision_engine_class.return_value = mock_decision_engine
        
        # Mock market analysis
        mock_analysis = Mock()
        mock_decision_engine.analyze_market_conditions.return_value = mock_analysis
        
        # Mock trading decision (HOLD to avoid complex trade execution)
        mock_decision = Mock()
        mock_decision.action = ActionType.HOLD
        mock_decision_engine.generate_trading_decision.return_value = mock_decision
        
        # Run backtest
        result = self.engine.run_backtest(
            start_date=self.start_date,
            end_date=self.start_date + timedelta(days=1),  # Short period
            strategy_config=self.strategy_config,
            historical_data=self.sample_market_data[:25],  # 1 day of data
            strategy_name="Test Strategy"
        )
        
        # Verify result structure
        self.assertIsInstance(result, BacktestResult)
        self.assertEqual(result.strategy_name, "Test Strategy")
        self.assertIsInstance(result.performance_metrics, PerformanceMetrics)
        self.assertIsInstance(result.trades, list)
        self.assertIsInstance(result.portfolio_history, list)
        self.assertIsInstance(result.equity_curve, list)
        self.assertIsInstance(result.drawdown_curve, list)
        
        # Verify decision engine was called
        self.assertTrue(mock_decision_engine.analyze_market_conditions.called)
        self.assertTrue(mock_decision_engine.generate_trading_decision.called)


class TestPerformanceMetrics(unittest.TestCase):
    """Test cases for PerformanceMetrics"""
    
    def test_performance_metrics_to_dict(self):
        """Test PerformanceMetrics serialization"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        metrics = PerformanceMetrics(
            total_return=0.15,
            annualized_return=0.18,
            total_trades=10,
            winning_trades=6,
            losing_trades=4,
            win_rate=0.6,
            sharpe_ratio=1.2,
            max_drawdown=0.08,
            max_drawdown_duration=5,
            volatility=0.25,
            average_win=150.0,
            average_loss=-80.0,
            profit_factor=1.8,
            largest_win=300.0,
            largest_loss=-200.0,
            initial_capital=10000.0,
            final_capital=11500.0,
            peak_capital=12000.0,
            start_date=start_date,
            end_date=end_date,
            duration_days=30,
            calmar_ratio=2.25,
            sortino_ratio=1.5
        )
        
        result_dict = metrics.to_dict()
        
        # Verify all fields are present
        expected_fields = [
            'total_return', 'annualized_return', 'total_trades', 'winning_trades',
            'losing_trades', 'win_rate', 'sharpe_ratio', 'max_drawdown',
            'max_drawdown_duration', 'volatility', 'average_win', 'average_loss',
            'profit_factor', 'largest_win', 'largest_loss', 'initial_capital',
            'final_capital', 'peak_capital', 'start_date', 'end_date',
            'duration_days', 'calmar_ratio', 'sortino_ratio'
        ]
        
        for field in expected_fields:
            self.assertIn(field, result_dict)
        
        # Verify specific values
        self.assertEqual(result_dict['total_return'], 0.15)
        self.assertEqual(result_dict['win_rate'], 0.6)
        self.assertEqual(result_dict['start_date'], start_date.isoformat())
        self.assertEqual(result_dict['end_date'], end_date.isoformat())


class TestBacktestTrade(unittest.TestCase):
    """Test cases for BacktestTrade"""
    
    def test_backtest_trade_to_dict(self):
        """Test BacktestTrade serialization"""
        mock_decision = Mock()
        mock_decision.confidence = 0.8
        mock_decision.reasoning = "Test reasoning"
        
        trade = BacktestTrade(
            trade_id="T123",
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            action=ActionType.BUY,
            symbol="BTCUSDT",
            quantity=0.1,
            price=45000.0,
            value=4500.0,
            decision=mock_decision,
            portfolio_value_before=10000.0,
            portfolio_value_after=10500.0
        )
        
        result_dict = trade.to_dict()
        
        # Verify all fields are present
        expected_fields = [
            'trade_id', 'timestamp', 'action', 'symbol', 'quantity',
            'price', 'value', 'portfolio_value_before', 'portfolio_value_after',
            'decision_confidence', 'decision_reasoning'
        ]
        
        for field in expected_fields:
            self.assertIn(field, result_dict)
        
        # Verify specific values
        self.assertEqual(result_dict['trade_id'], "T123")
        self.assertEqual(result_dict['action'], ActionType.BUY.value)
        self.assertEqual(result_dict['quantity'], 0.1)
        self.assertEqual(result_dict['decision_confidence'], 0.8)


class TestBacktestResult(unittest.TestCase):
    """Test cases for BacktestResult"""
    
    def test_backtest_result_to_dict(self):
        """Test BacktestResult serialization"""
        # Create mock performance metrics
        mock_metrics = Mock()
        mock_metrics.to_dict.return_value = {'total_return': 0.15}
        
        result = BacktestResult(
            backtest_id="BT123",
            strategy_name="Test Strategy",
            strategy_config={'param1': 'value1'},
            performance_metrics=mock_metrics,
            trades=[],
            portfolio_history=[],
            equity_curve=[],
            drawdown_curve=[]
        )
        
        result_dict = result.to_dict()
        
        # Verify all fields are present
        expected_fields = [
            'backtest_id', 'strategy_name', 'strategy_config',
            'performance_metrics', 'total_trades', 'equity_curve_points',
            'created_at'
        ]
        
        for field in expected_fields:
            self.assertIn(field, result_dict)
        
        # Verify specific values
        self.assertEqual(result_dict['backtest_id'], "BT123")
        self.assertEqual(result_dict['strategy_name'], "Test Strategy")
        self.assertEqual(result_dict['total_trades'], 0)
        self.assertEqual(result_dict['equity_curve_points'], 0)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)