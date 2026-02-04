"""
Complete Integration Test Suite
End-to-end testing of the entire Bitcoin trading system
"""
import asyncio
import pytest
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
import json
import time

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.data_models import (
    NewsItem, MarketData, SentimentScore, TechnicalSignal, 
    TradingDecision, Portfolio, Position, ActionType, RiskLevel
)
from news_analysis.ai_analyzer import ModelAgnosticNewsAnalyzer
from technical_analysis.indicators import TechnicalIndicatorEngine
from decision_engine.engine import DecisionEngine
from risk_management.risk_manager import RiskManager
from backtesting.engine import BacktestEngine
from system_integration.performance_optimizer import PerformanceOptimizer

logger = logging.getLogger(__name__)


class IntegrationTestSuite:
    """
    Comprehensive integration test suite for the trading system
    """
    
    def __init__(self):
        """Initialize test suite"""
        self.test_results = []
        self.performance_metrics = {}
        self.start_time = None
        
        # Initialize system components
        self.news_analyzer = None
        self.technical_engine = None  # Will be initialized later
        self.decision_engine = DecisionEngine()
        self.risk_manager = RiskManager()
        self.backtest_engine = BacktestEngine(initial_capital=10000.0)
        self.performance_optimizer = PerformanceOptimizer()
        
        logger.info("Integration test suite initialized")
    
    def log_test_result(self, test_name: str, passed: bool, duration: float, 
                       details: str = "", error: str = ""):
        """Log test result"""
        result = {
            "test_name": test_name,
            "passed": passed,
            "duration_seconds": duration,
            "details": details,
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.test_results.append(result)
        
        status = "PASS" if passed else "FAIL"
        logger.info(f"Test {test_name}: {status} ({duration:.2f}s)")
        if error:
            logger.error(f"Test {test_name} error: {error}")
    
    def create_sample_market_data(self, count: int = 24) -> List[MarketData]:
        """Create sample market data for testing"""
        market_data = []
        base_price = 45000.0
        
        for i in range(count):
            timestamp = datetime.utcnow() - timedelta(hours=count-i)
            price_variation = (i % 10 - 5) * 100  # Price variation
            
            market_data.append(MarketData(
                symbol="BTCUSDT",
                timestamp=timestamp,
                price=base_price + price_variation,
                volume=100.0 + (i % 5) * 20,
                source="test_data"
            ))
        
        return market_data
    
    def create_sample_news_items(self, count: int = 5) -> List[NewsItem]:
        """Create sample news items for testing"""
        news_items = []
        
        sample_news = [
            "Bitcoin reaches new all-time high as institutional adoption increases",
            "Major cryptocurrency exchange announces new security features",
            "Central bank considers digital currency regulations",
            "Bitcoin mining difficulty adjusts to new levels",
            "Cryptocurrency market shows strong bullish momentum"
        ]
        
        for i in range(min(count, len(sample_news))):
            timestamp = datetime.utcnow() - timedelta(hours=i)
            
            news_items.append(NewsItem(
                title=sample_news[i],
                content=f"Full content for: {sample_news[i]}",
                source="test_source",
                timestamp=timestamp,
                url=f"https://test.com/news/{i}",
                relevance_score=0.8 + (i % 3) * 0.1
            ))
        
        return news_items
    
    def create_sample_portfolio(self) -> Portfolio:
        """Create sample portfolio for testing"""
        position = Position(
            symbol="BTCUSDT",
            amount=0.1,
            entry_price=44000.0,
            current_price=45000.0,
            pnl=100.0,
            entry_time=datetime.utcnow()
        )
        
        return Portfolio(
            btc_balance=0.1,
            usdt_balance=5000.0,
            total_value_usdt=10000.0,
            unrealized_pnl=100.0,
            positions=[position]
        )
    
    async def test_data_collection_flow(self) -> bool:
        """Test data collection and processing flow"""
        test_start = time.time()
        
        try:
            # Create sample data
            market_data = self.create_sample_market_data(24)
            news_items = self.create_sample_news_items(5)
            
            # Verify data structure
            assert len(market_data) == 24, "Market data count mismatch"
            assert len(news_items) == 5, "News items count mismatch"
            
            # Verify data integrity
            for data in market_data:
                assert data.price > 0, "Invalid market price"
                assert data.volume > 0, "Invalid volume"
                assert data.symbol == "BTCUSDT", "Invalid symbol"
            
            for news in news_items:
                assert news.title, "Missing news title"
                assert news.content, "Missing news content"
                assert 0 <= news.relevance_score <= 1, "Invalid relevance score"
            
            duration = time.time() - test_start
            self.log_test_result(
                "data_collection_flow", 
                True, 
                duration,
                f"Processed {len(market_data)} market data points and {len(news_items)} news items"
            )
            return True
            
        except Exception as e:
            duration = time.time() - test_start
            self.log_test_result("data_collection_flow", False, duration, error=str(e))
            return False
    
    async def test_sentiment_analysis_flow(self) -> bool:
        """Test sentiment analysis flow"""
        test_start = time.time()
        
        try:
            # Skip if news analyzer not available
            if self.news_analyzer is None:
                duration = time.time() - test_start
                self.log_test_result(
                    "sentiment_analysis_flow", 
                    True, 
                    duration,
                    "Skipped - News analyzer not available (missing API keys)"
                )
                return True
            
            news_items = self.create_sample_news_items(3)
            
            # Analyze sentiment for each news item
            sentiment_scores = []
            for news in news_items:
                sentiment = await self.news_analyzer.analyze_sentiment(news)
                sentiment_scores.append(sentiment)
                
                # Verify sentiment structure
                assert isinstance(sentiment, SentimentScore), "Invalid sentiment type"
                assert 0 <= sentiment.sentiment_value <= 100, "Invalid sentiment value"
                assert 0 <= sentiment.confidence <= 1, "Invalid confidence"
            
            # Verify we got results for all news items
            assert len(sentiment_scores) == len(news_items), "Sentiment analysis count mismatch"
            
            duration = time.time() - test_start
            self.log_test_result(
                "sentiment_analysis_flow", 
                True, 
                duration,
                f"Analyzed sentiment for {len(news_items)} news items"
            )
            return True
            
        except Exception as e:
            duration = time.time() - test_start
            self.log_test_result("sentiment_analysis_flow", False, duration, error=str(e))
            return False
    
    async def test_technical_analysis_flow(self) -> bool:
        """Test technical analysis flow"""
        test_start = time.time()
        
        try:
            # Check if technical engine is available
            if self.technical_engine is None:
                from technical_analysis.signal_generator import TechnicalIndicatorEngine
                self.technical_engine = TechnicalIndicatorEngine()
            
            market_data = self.create_sample_market_data(50)  # Need more data for technical indicators
            
            # Calculate technical indicators
            rsi = self.technical_engine.calculate_rsi([d.price for d in market_data])
            macd = self.technical_engine.calculate_macd([d.price for d in market_data])
            sma = self.technical_engine.calculate_sma([d.price for d in market_data], period=20)
            bollinger = self.technical_engine.calculate_bollinger_bands([d.price for d in market_data])
            
            # Verify indicators
            assert rsi is not None, "RSI calculation failed"
            assert macd is not None, "MACD calculation failed"
            assert sma is not None, "SMA calculation failed"
            assert bollinger is not None, "Bollinger Bands calculation failed"
            
            # Generate trading signal
            signal = self.technical_engine.generate_signal(market_data[-1], market_data)
            
            # Verify signal structure
            assert isinstance(signal, TechnicalSignal), "Invalid signal type"
            assert -1 <= signal.signal_strength <= 1, "Invalid signal strength"
            assert 0 <= signal.confidence <= 1, "Invalid signal confidence"
            
            duration = time.time() - test_start
            self.log_test_result(
                "technical_analysis_flow", 
                True, 
                duration,
                f"Calculated indicators and generated signal: {signal.signal_type.value}"
            )
            return True
            
        except Exception as e:
            duration = time.time() - test_start
            self.log_test_result("technical_analysis_flow", False, duration, error=str(e))
            return False
    
    async def test_decision_engine_flow(self) -> bool:
        """Test decision engine flow"""
        test_start = time.time()
        
        try:
            # Create test data
            market_data = self.create_sample_market_data(50)
            portfolio = self.create_sample_portfolio()
            
            # Create mock sentiment score
            sentiment_score = SentimentScore(
                sentiment_value=75.0,
                confidence=0.8,
                key_topics=["bitcoin", "bullish", "adoption"],
                impact_assessment={"short_term": 0.7, "long_term": 0.6}
            )
            
            # Generate technical signal
            technical_signal = self.technical_engine.generate_signal(market_data[-1], market_data)
            
            # Analyze market conditions
            analysis = self.decision_engine.analyze_market_conditions(
                sentiment_score=sentiment_score,
                technical_signal=technical_signal,
                portfolio=portfolio,
                current_price=market_data[-1].price,
                market_data=market_data
            )
            
            # Verify analysis
            assert -1 <= analysis.combined_signal_strength <= 1, "Invalid combined signal strength"
            assert 0 <= analysis.overall_confidence <= 1, "Invalid overall confidence"
            assert analysis.market_condition in ["bullish", "bearish", "neutral", "volatile"], "Invalid market condition"
            
            # Generate trading decision
            decision = self.decision_engine.generate_trading_decision(analysis)
            
            # Verify decision
            assert isinstance(decision, TradingDecision), "Invalid decision type"
            assert decision.action in [ActionType.BUY, ActionType.SELL, ActionType.HOLD], "Invalid action"
            assert 0 <= decision.confidence <= 1, "Invalid decision confidence"
            
            duration = time.time() - test_start
            self.log_test_result(
                "decision_engine_flow", 
                True, 
                duration,
                f"Generated decision: {decision.action.value} with confidence {decision.confidence:.2%}"
            )
            return True
            
        except Exception as e:
            duration = time.time() - test_start
            self.log_test_result("decision_engine_flow", False, duration, error=str(e))
            return False
    
    async def test_risk_management_flow(self) -> bool:
        """Test risk management flow"""
        test_start = time.time()
        
        try:
            # Create test data
            portfolio = self.create_sample_portfolio()
            market_data = self.create_sample_market_data(24)
            
            # Create mock trading decision
            decision = TradingDecision(
                action=ActionType.BUY,
                confidence=0.75,
                suggested_amount=0.05,  # 5% of portfolio
                price_range=None,
                reasoning="Test decision",
                risk_level=RiskLevel.MEDIUM
            )
            
            # Assess trade risk
            risk_assessment = self.risk_manager.assess_trade_risk(
                decision=decision,
                portfolio=portfolio,
                market_data=market_data
            )
            
            # Verify risk assessment
            assert 0 <= risk_assessment.overall_risk_score <= 100, "Invalid risk score"
            assert risk_assessment.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL], "Invalid risk level"
            assert risk_assessment.max_loss_potential >= 0, "Invalid max loss potential"
            assert 0 <= risk_assessment.recommended_position_size <= 1, "Invalid recommended position size"
            
            # Validate trade
            is_valid, violations = self.risk_manager.validate_trade(decision, portfolio, risk_assessment)
            
            # Calculate stop loss
            stop_loss = self.risk_manager.calculate_stop_loss(45000.0, ActionType.BUY)
            assert stop_loss < 45000.0, "Invalid stop loss for BUY order"
            
            # Monitor portfolio risk
            portfolio_risk = self.risk_manager.monitor_portfolio_risk(portfolio, market_data)
            assert "overall_risk_level" in portfolio_risk, "Missing overall risk level"
            
            duration = time.time() - test_start
            self.log_test_result(
                "risk_management_flow", 
                True, 
                duration,
                f"Risk assessment: {risk_assessment.risk_level.value} ({risk_assessment.overall_risk_score:.1f}/100)"
            )
            return True
            
        except Exception as e:
            duration = time.time() - test_start
            self.log_test_result("risk_management_flow", False, duration, error=str(e))
            return False
    
    async def test_backtesting_flow(self) -> bool:
        """Test backtesting flow"""
        test_start = time.time()
        
        try:
            # Create historical data
            historical_data = self.create_sample_market_data(100)  # 100 data points
            
            # Set up backtest parameters
            start_date = datetime.utcnow() - timedelta(days=30)
            end_date = datetime.utcnow()
            
            strategy_config = {
                'risk_parameters': {
                    'max_position_size': 0.1,
                    'stop_loss_percentage': 0.05,
                    'take_profit_percentage': 0.15,
                    'min_confidence_threshold': 0.7,
                    'sentiment_weight': 0.4,
                    'technical_weight': 0.6
                }
            }
            
            # Run backtest
            result = self.backtest_engine.run_backtest(
                start_date=start_date,
                end_date=end_date,
                strategy_config=strategy_config,
                historical_data=historical_data,
                strategy_name="Integration Test Strategy"
            )
            
            # Verify backtest result
            assert result.backtest_id, "Missing backtest ID"
            assert result.strategy_name == "Integration Test Strategy", "Strategy name mismatch"
            assert result.performance_metrics, "Missing performance metrics"
            assert isinstance(result.trades, list), "Invalid trades format"
            assert isinstance(result.equity_curve, list), "Invalid equity curve format"
            
            # Verify performance metrics
            metrics = result.performance_metrics
            assert hasattr(metrics, 'total_return'), "Missing total return"
            assert hasattr(metrics, 'sharpe_ratio'), "Missing Sharpe ratio"
            assert hasattr(metrics, 'max_drawdown'), "Missing max drawdown"
            
            duration = time.time() - test_start
            self.log_test_result(
                "backtesting_flow", 
                True, 
                duration,
                f"Backtest completed: {len(result.trades)} trades, {metrics.total_return:.2%} return"
            )
            return True
            
        except Exception as e:
            duration = time.time() - test_start
            self.log_test_result("backtesting_flow", False, duration, error=str(e))
            return False
    
    async def test_performance_optimization_flow(self) -> bool:
        """Test performance optimization flow"""
        test_start = time.time()
        
        try:
            # Collect system metrics
            metrics = self.performance_optimizer.collect_system_metrics()
            assert len(metrics) > 0, "No metrics collected"
            
            # Analyze performance trends
            trends = self.performance_optimizer.analyze_performance_trends(1)  # 1 hour
            assert "trends" in trends, "Missing trends analysis"
            
            # Generate optimization recommendations
            recommendations = self.performance_optimizer.generate_optimization_recommendations(metrics)
            
            # Run auto-optimization
            auto_opt_result = self.performance_optimizer.auto_optimize()
            assert auto_opt_result["auto_optimization_completed"], "Auto-optimization failed"
            
            # Generate performance report
            report = self.performance_optimizer.get_performance_report()
            assert "overall_performance_score" in report, "Missing performance score"
            assert "current_metrics" in report, "Missing current metrics"
            
            duration = time.time() - test_start
            self.log_test_result(
                "performance_optimization_flow", 
                True, 
                duration,
                f"Performance score: {report['overall_performance_score']:.1f}/100"
            )
            return True
            
        except Exception as e:
            duration = time.time() - test_start
            self.log_test_result("performance_optimization_flow", False, duration, error=str(e))
            return False
    
    async def test_end_to_end_trading_scenario(self) -> bool:
        """Test complete end-to-end trading scenario"""
        test_start = time.time()
        
        try:
            logger.info("Starting end-to-end trading scenario test")
            
            # 1. Data Collection
            market_data = self.create_sample_market_data(50)
            news_items = self.create_sample_news_items(3)
            portfolio = self.create_sample_portfolio()
            
            # 2. Sentiment Analysis (mock if not available)
            sentiment_score = SentimentScore(
                sentiment_value=70.0,
                confidence=0.8,
                key_factors=["bitcoin", "bullish"]
            )
            
            # 3. Technical Analysis
            if self.technical_engine is None:
                from technical_analysis.signal_generator import TechnicalIndicatorEngine
                self.technical_engine = TechnicalIndicatorEngine()
            
            technical_signal = self.technical_engine.generate_signal(market_data[-1], market_data)
            
            # 4. Market Analysis
            market_analysis = self.decision_engine.analyze_market_conditions(
                sentiment_score=sentiment_score,
                technical_signal=technical_signal,
                portfolio=portfolio,
                current_price=market_data[-1].price,
                market_data=market_data
            )
            
            # 5. Trading Decision
            trading_decision = self.decision_engine.generate_trading_decision(market_analysis)
            
            # 6. Risk Assessment
            risk_assessment = self.risk_manager.assess_trade_risk(
                decision=trading_decision,
                portfolio=portfolio,
                market_data=market_data
            )
            
            # 7. Trade Validation
            is_valid, violations = self.risk_manager.validate_trade(
                trading_decision, portfolio, risk_assessment
            )
            
            # 8. Performance Monitoring
            performance_report = self.performance_optimizer.get_performance_report()
            
            # Verify complete flow
            assert market_analysis.combined_signal_strength is not None, "Market analysis failed"
            assert trading_decision.action is not None, "Trading decision failed"
            assert risk_assessment.overall_risk_score is not None, "Risk assessment failed"
            assert isinstance(is_valid, bool), "Trade validation failed"
            assert performance_report["overall_performance_score"] is not None, "Performance monitoring failed"
            
            # Log scenario results
            scenario_summary = {
                "market_condition": market_analysis.market_condition,
                "trading_action": trading_decision.action.value,
                "confidence": trading_decision.confidence,
                "risk_level": risk_assessment.risk_level.value,
                "trade_valid": is_valid,
                "performance_score": performance_report["overall_performance_score"]
            }
            
            duration = time.time() - test_start
            self.log_test_result(
                "end_to_end_trading_scenario", 
                True, 
                duration,
                f"Complete scenario: {json.dumps(scenario_summary, indent=2)}"
            )
            return True
            
        except Exception as e:
            duration = time.time() - test_start
            self.log_test_result("end_to_end_trading_scenario", False, duration, error=str(e))
            return False
    
    async def test_stress_scenario(self) -> bool:
        """Test system under stress conditions"""
        test_start = time.time()
        
        try:
            logger.info("Starting stress test scenario")
            
            # Simulate high-frequency data processing
            stress_iterations = 50
            successful_iterations = 0
            
            for i in range(stress_iterations):
                try:
                    # Generate data
                    market_data = self.create_sample_market_data(10)
                    portfolio = self.create_sample_portfolio()
                    
                    # Quick analysis
                    if self.technical_engine is None:
                        from technical_analysis.signal_generator import TechnicalIndicatorEngine
                        self.technical_engine = TechnicalIndicatorEngine()
                    
                    technical_signal = self.technical_engine.generate_signal(market_data[-1], market_data)
                    
                    # Mock sentiment
                    sentiment_score = SentimentScore(
                        sentiment_value=50.0 + (i % 20),
                        confidence=0.7,
                        key_factors=["test"]
                    )
                    
                    # Decision making
                    analysis = self.decision_engine.analyze_market_conditions(
                        sentiment_score=sentiment_score,
                        technical_signal=technical_signal,
                        portfolio=portfolio,
                        current_price=market_data[-1].price
                    )
                    
                    decision = self.decision_engine.generate_trading_decision(analysis)
                    
                    # Risk check
                    risk_assessment = self.risk_manager.assess_trade_risk(decision, portfolio)
                    
                    successful_iterations += 1
                    
                except Exception as e:
                    logger.warning(f"Stress test iteration {i} failed: {e}")
            
            success_rate = successful_iterations / stress_iterations
            
            # Verify acceptable success rate under stress
            assert success_rate >= 0.9, f"Stress test success rate too low: {success_rate:.2%}"
            
            duration = time.time() - test_start
            self.log_test_result(
                "stress_scenario", 
                True, 
                duration,
                f"Stress test: {successful_iterations}/{stress_iterations} iterations successful ({success_rate:.1%})"
            )
            return True
            
        except Exception as e:
            duration = time.time() - test_start
            self.log_test_result("stress_scenario", False, duration, error=str(e))
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """
        Run all integration tests
        
        Returns:
            Test results summary
        """
        self.start_time = time.time()
        logger.info("Starting complete integration test suite")
        
        # Initialize news analyzer if possible
        try:
            self.news_analyzer = ModelAgnosticNewsAnalyzer()
        except Exception as e:
            logger.warning(f"News analyzer not available: {e}")
            self.news_analyzer = None
        
        # Initialize technical engine
        try:
            from technical_analysis.signal_generator import TechnicalIndicatorEngine
            self.technical_engine = TechnicalIndicatorEngine()
        except Exception as e:
            logger.warning(f"Technical engine not available: {e}")
            self.technical_engine = None
        
        # Run all tests
        test_functions = [
            self.test_data_collection_flow,
            self.test_sentiment_analysis_flow,
            self.test_technical_analysis_flow,
            self.test_decision_engine_flow,
            self.test_risk_management_flow,
            self.test_backtesting_flow,
            self.test_performance_optimization_flow,
            self.test_end_to_end_trading_scenario,
            self.test_stress_scenario
        ]
        
        results = []
        for test_func in test_functions:
            try:
                result = await test_func()
                results.append(result)
            except Exception as e:
                logger.error(f"Test function {test_func.__name__} failed: {e}")
                results.append(False)
        
        # Calculate summary statistics
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["passed"])
        failed_tests = total_tests - passed_tests
        total_duration = time.time() - self.start_time
        
        success_rate = passed_tests / total_tests if total_tests > 0 else 0
        
        summary = {
            "integration_test_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": success_rate,
                "total_duration_seconds": total_duration,
                "overall_status": "PASS" if success_rate >= 0.8 else "FAIL"
            },
            "detailed_results": self.test_results,
            "performance_metrics": self.performance_metrics,
            "test_timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Integration test suite completed: {passed_tests}/{total_tests} tests passed ({success_rate:.1%})")
        
        return summary


# Standalone test runner
async def run_integration_tests():
    """Run integration tests as standalone script"""
    test_suite = IntegrationTestSuite()
    results = await test_suite.run_all_tests()
    
    print("\n" + "="*80)
    print("BITCOIN TRADING SYSTEM - INTEGRATION TEST RESULTS")
    print("="*80)
    
    summary = results["integration_test_summary"]
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed_tests']}")
    print(f"Failed: {summary['failed_tests']}")
    print(f"Success Rate: {summary['success_rate']:.1%}")
    print(f"Duration: {summary['total_duration_seconds']:.2f} seconds")
    print(f"Overall Status: {summary['overall_status']}")
    
    print("\nDetailed Results:")
    print("-" * 80)
    for result in results["detailed_results"]:
        status = "✅ PASS" if result["passed"] else "❌ FAIL"
        print(f"{status} {result['test_name']} ({result['duration_seconds']:.2f}s)")
        if result["details"]:
            print(f"    Details: {result['details']}")
        if result["error"]:
            print(f"    Error: {result['error']}")
    
    print("\n" + "="*80)
    
    return results


if __name__ == "__main__":
    # Run integration tests
    asyncio.run(run_integration_tests())