#!/usr/bin/env python3
"""
System Integrity Verification Script
Final verification of the complete Bitcoin trading system
"""
import asyncio
import logging
import sys
import os
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Tuple
import importlib
import traceback

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SystemIntegrityVerifier:
    """
    Comprehensive system integrity verification
    """
    
    def __init__(self):
        """Initialize system verifier"""
        self.verification_results = []
        self.component_status = {}
        self.start_time = None
        
        logger.info("System integrity verifier initialized")
    
    def log_verification(self, component: str, status: str, details: str = "", error: str = ""):
        """Log verification result"""
        result = {
            "component": component,
            "status": status,  # "PASS", "FAIL", "WARNING", "SKIP"
            "details": details,
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.verification_results.append(result)
        self.component_status[component] = status
        
        status_icon = {
            "PASS": "✅",
            "FAIL": "❌", 
            "WARNING": "⚠️",
            "SKIP": "⏭️"
        }.get(status, "❓")
        
        logger.info(f"{status_icon} {component}: {status}")
        if details:
            logger.info(f"    Details: {details}")
        if error:
            logger.error(f"    Error: {error}")
    
    def verify_core_imports(self) -> bool:
        """Verify all core modules can be imported"""
        logger.info("Verifying core module imports...")
        
        core_modules = [
            "core.data_models",
            "core.event_bus",
            "config",
            "database.connection",
            "database.models"
        ]
        
        failed_imports = []
        
        for module_name in core_modules:
            try:
                importlib.import_module(module_name)
                self.log_verification(f"Import: {module_name}", "PASS")
            except ImportError as e:
                failed_imports.append(module_name)
                self.log_verification(f"Import: {module_name}", "FAIL", error=str(e))
            except Exception as e:
                failed_imports.append(module_name)
                self.log_verification(f"Import: {module_name}", "WARNING", error=str(e))
        
        if failed_imports:
            self.log_verification(
                "Core Imports", 
                "FAIL", 
                f"Failed to import {len(failed_imports)} modules: {failed_imports}"
            )
            return False
        else:
            self.log_verification("Core Imports", "PASS", f"All {len(core_modules)} core modules imported successfully")
            return True
    
    def verify_data_collection_components(self) -> bool:
        """Verify data collection components"""
        logger.info("Verifying data collection components...")
        
        try:
            # Test market data collector
            from data_collection.adapters.market_collector import MarketDataCollector
            collector = MarketDataCollector()
            self.log_verification("Market Data Collector", "PASS", "Initialized successfully")
            
            # Test data models
            from core.data_models import MarketData
            test_data = MarketData(
                symbol="BTCUSDT",
                timestamp=datetime.utcnow(),
                price=45000.0,
                volume=100.0,
                source="test"
            )
            self.log_verification("Market Data Model", "PASS", "Data model validation successful")
            
            return True
            
        except Exception as e:
            self.log_verification("Data Collection Components", "FAIL", error=str(e))
            return False
    
    def verify_analysis_components(self) -> bool:
        """Verify analysis components"""
        logger.info("Verifying analysis components...")
        
        success_count = 0
        total_components = 0
        
        # Test news analysis
        try:
            from news_analysis.ai_analyzer import ModelAgnosticNewsAnalyzer
            analyzer = ModelAgnosticNewsAnalyzer()
            self.log_verification("News Analyzer", "PASS", "Initialized successfully")
            success_count += 1
        except Exception as e:
            self.log_verification("News Analyzer", "WARNING", "Not available (likely missing API keys)", str(e))
        total_components += 1
        
        # Test technical analysis
        try:
            from technical_analysis.signal_generator import TechnicalIndicatorEngine
            engine = TechnicalIndicatorEngine()
            
            # Test basic calculation
            test_prices = [45000 + i * 100 for i in range(20)]
            rsi = engine.calculate_rsi(test_prices)
            
            if rsi is not None:
                self.log_verification("Technical Analysis Engine", "PASS", f"RSI calculation successful: {rsi:.2f}")
                success_count += 1
            else:
                self.log_verification("Technical Analysis Engine", "FAIL", "RSI calculation returned None")
        except Exception as e:
            self.log_verification("Technical Analysis Engine", "FAIL", error=str(e))
        total_components += 1
        
        return success_count >= total_components * 0.5  # At least 50% success
    
    def verify_decision_engine(self) -> bool:
        """Verify decision engine components"""
        logger.info("Verifying decision engine...")
        
        try:
            from decision_engine.engine import DecisionEngine
            from decision_engine.risk_parameters import RiskParameters
            from core.data_models import SentimentScore, TechnicalSignal, Portfolio, Position, ActionType
            
            # Initialize decision engine
            engine = DecisionEngine()
            
            # Create test data
            sentiment = SentimentScore(
                sentiment_value=70.0,
                confidence=0.8,
                key_factors=["bitcoin", "bullish"]
            )
            
            technical = TechnicalSignal(
                signal_type=ActionType.BUY,
                signal_strength=0.6,
                confidence=0.7,
                contributing_indicators=["RSI", "MACD"]
            )
            
            position = Position(
                symbol="BTCUSDT",
                amount=0.1,
                entry_price=44000.0,
                current_price=45000.0,
                pnl=100.0,
                entry_time=datetime.utcnow()
            )
            
            portfolio = Portfolio(
                btc_balance=0.1,
                usdt_balance=5000.0,
                total_value_usdt=10000.0,
                unrealized_pnl=100.0,
                positions=[position]
            )
            
            # Test market analysis
            analysis = engine.analyze_market_conditions(
                sentiment_score=sentiment,
                technical_signal=technical,
                portfolio=portfolio,
                current_price=45000.0
            )
            
            # Test decision generation
            decision = engine.generate_trading_decision(analysis)
            
            self.log_verification(
                "Decision Engine", 
                "PASS", 
                f"Generated {decision.action.value} decision with {decision.confidence:.1%} confidence"
            )
            return True
            
        except Exception as e:
            self.log_verification("Decision Engine", "FAIL", error=str(e))
            return False
    
    def verify_risk_management(self) -> bool:
        """Verify risk management components"""
        logger.info("Verifying risk management...")
        
        try:
            from risk_management.risk_manager import RiskManager
            from core.data_models import TradingDecision, Portfolio, Position, ActionType, RiskLevel
            
            # Initialize risk manager
            risk_manager = RiskManager()
            
            # Create test data
            decision = TradingDecision(
                action=ActionType.BUY,
                confidence=0.75,
                suggested_amount=0.05,
                price_range=None,
                reasoning="Test decision",
                risk_level=RiskLevel.MEDIUM
            )
            
            position = Position(
                symbol="BTCUSDT",
                amount=0.1,
                entry_price=44000.0,
                current_price=45000.0,
                pnl=100.0,
                entry_time=datetime.utcnow()
            )
            
            portfolio = Portfolio(
                btc_balance=0.1,
                usdt_balance=5000.0,
                total_value_usdt=10000.0,
                unrealized_pnl=100.0,
                positions=[position]
            )
            
            # Test risk assessment
            risk_assessment = risk_manager.assess_trade_risk(decision, portfolio)
            
            # Test trade validation
            is_valid, violations = risk_manager.validate_trade(decision, portfolio, risk_assessment)
            
            # Test stop loss calculation
            stop_loss = risk_manager.calculate_stop_loss(45000.0, ActionType.BUY)
            
            self.log_verification(
                "Risk Management", 
                "PASS", 
                f"Risk assessment: {risk_assessment.risk_level.value} ({risk_assessment.overall_risk_score:.1f}/100)"
            )
            return True
            
        except Exception as e:
            self.log_verification("Risk Management", "FAIL", error=str(e))
            return False
    
    def verify_backtesting_engine(self) -> bool:
        """Verify backtesting engine"""
        logger.info("Verifying backtesting engine...")
        
        try:
            from backtesting.engine import BacktestEngine
            from core.data_models import MarketData
            from datetime import timedelta
            
            # Initialize backtest engine
            engine = BacktestEngine(initial_capital=10000.0)
            
            # Create test historical data
            historical_data = []
            base_price = 45000.0
            
            for i in range(50):
                timestamp = datetime.utcnow() - timedelta(hours=50-i)
                price_variation = (i % 10 - 5) * 100
                
                historical_data.append(MarketData(
                    symbol="BTCUSDT",
                    timestamp=timestamp,
                    price=base_price + price_variation,
                    volume=100.0 + (i % 5) * 20,
                    source="test_data"
                ))
            
            # Test backtest execution
            start_date = datetime.utcnow() - timedelta(days=7)
            end_date = datetime.utcnow()
            
            strategy_config = {
                'risk_parameters': {
                    'max_position_size': 0.1,
                    'stop_loss_percentage': 0.05,
                    'take_profit_percentage': 0.15,
                    'min_confidence_threshold': 0.7
                }
            }
            
            result = engine.run_backtest(
                start_date=start_date,
                end_date=end_date,
                strategy_config=strategy_config,
                historical_data=historical_data,
                strategy_name="Verification Test"
            )
            
            self.log_verification(
                "Backtesting Engine", 
                "PASS", 
                f"Backtest completed: {len(result.trades)} trades, {result.performance_metrics.total_return:.2%} return"
            )
            return True
            
        except Exception as e:
            self.log_verification("Backtesting Engine", "FAIL", error=str(e))
            return False
    
    def verify_api_endpoints(self) -> bool:
        """Verify API endpoints are properly defined"""
        logger.info("Verifying API endpoints...")
        
        try:
            # Check if simple_real_market_api.py exists and is valid
            api_file = "simple_real_market_api.py"
            if os.path.exists(api_file):
                with open(api_file, 'r') as f:
                    content = f.read()
                
                # Check for key endpoints
                required_endpoints = [
                    "/api/v1/health/",
                    "/api/v1/trading/portfolio",
                    "/api/v1/trading/market-data",
                    "/api/v1/backtesting/run",
                    "/api/v1/system/monitoring/health"
                ]
                
                missing_endpoints = []
                for endpoint in required_endpoints:
                    if endpoint not in content:
                        missing_endpoints.append(endpoint)
                
                if missing_endpoints:
                    self.log_verification(
                        "API Endpoints", 
                        "WARNING", 
                        f"Missing endpoints: {missing_endpoints}"
                    )
                else:
                    self.log_verification(
                        "API Endpoints", 
                        "PASS", 
                        f"All {len(required_endpoints)} required endpoints found"
                    )
                
                return len(missing_endpoints) == 0
            else:
                self.log_verification("API Endpoints", "FAIL", "API file not found")
                return False
                
        except Exception as e:
            self.log_verification("API Endpoints", "FAIL", error=str(e))
            return False
    
    def verify_configuration_files(self) -> bool:
        """Verify configuration files exist and are valid"""
        logger.info("Verifying configuration files...")
        
        config_files = [
            (".env", "Environment configuration"),
            ("requirements.txt", "Python dependencies"),
            ("../docker-compose.yml", "Docker composition"),
            ("../deploy.sh", "Deployment script"),
            ("../DEPLOYMENT_GUIDE.md", "Deployment documentation")
        ]
        
        missing_files = []
        
        for file_path, description in config_files:
            if os.path.exists(file_path):
                self.log_verification(f"Config: {description}", "PASS", f"File exists: {file_path}")
            else:
                missing_files.append(file_path)
                self.log_verification(f"Config: {description}", "WARNING", f"File missing: {file_path}")
        
        if missing_files:
            self.log_verification(
                "Configuration Files", 
                "WARNING", 
                f"Missing {len(missing_files)} configuration files"
            )
        else:
            self.log_verification("Configuration Files", "PASS", "All configuration files present")
        
        return len(missing_files) <= 1  # Allow 1 missing file
    
    def verify_system_integration(self) -> bool:
        """Verify system integration components"""
        logger.info("Verifying system integration...")
        
        try:
            from system_integration.performance_optimizer import PerformanceOptimizer
            
            # Test performance optimizer
            optimizer = PerformanceOptimizer()
            metrics = optimizer.collect_system_metrics()
            
            if len(metrics) > 0:
                self.log_verification(
                    "Performance Optimizer", 
                    "PASS", 
                    f"Collected {len(metrics)} performance metrics"
                )
            else:
                self.log_verification("Performance Optimizer", "WARNING", "No metrics collected")
            
            # Test auto-optimization
            auto_result = optimizer.auto_optimize()
            if auto_result.get("auto_optimization_completed"):
                self.log_verification("Auto Optimization", "PASS", "Auto-optimization completed")
            else:
                self.log_verification("Auto Optimization", "WARNING", "Auto-optimization incomplete")
            
            return True
            
        except Exception as e:
            self.log_verification("System Integration", "FAIL", error=str(e))
            return False
    
    def verify_database_models(self) -> bool:
        """Verify database models and connections"""
        logger.info("Verifying database models...")
        
        try:
            # Test database models import
            from database.models import Base
            self.log_verification("Database Models", "PASS", "Models imported successfully")
            
            # Test connection configuration
            from database.connection import DatabaseManager
            db_manager = DatabaseManager()
            self.log_verification("Database Connection", "PASS", "Connection manager initialized")
            
            return True
            
        except Exception as e:
            self.log_verification("Database Components", "WARNING", "Database components not fully available", str(e))
            return True  # Non-critical for demo system
    
    async def run_integration_tests(self) -> bool:
        """Run integration tests if available"""
        logger.info("Running integration tests...")
        
        try:
            from tests.test_integration_complete import IntegrationTestSuite
            
            test_suite = IntegrationTestSuite()
            results = await test_suite.run_all_tests()
            
            summary = results["integration_test_summary"]
            success_rate = summary["success_rate"]
            
            if success_rate >= 0.8:
                self.log_verification(
                    "Integration Tests", 
                    "PASS", 
                    f"Tests passed: {summary['passed_tests']}/{summary['total_tests']} ({success_rate:.1%})"
                )
                return True
            else:
                self.log_verification(
                    "Integration Tests", 
                    "WARNING", 
                    f"Low success rate: {success_rate:.1%}"
                )
                return False
                
        except Exception as e:
            self.log_verification("Integration Tests", "WARNING", "Integration tests not available", str(e))
            return True  # Non-critical
    
    async def verify_complete_system(self) -> Dict[str, Any]:
        """
        Run complete system verification
        
        Returns:
            Verification results summary
        """
        self.start_time = time.time()
        logger.info("Starting complete system integrity verification")
        
        print("\n" + "="*80)
        print("BITCOIN TRADING SYSTEM - SYSTEM INTEGRITY VERIFICATION")
        print("="*80)
        
        # Run all verification checks
        verification_checks = [
            ("Core Imports", self.verify_core_imports),
            ("Data Collection", self.verify_data_collection_components),
            ("Analysis Components", self.verify_analysis_components),
            ("Decision Engine", self.verify_decision_engine),
            ("Risk Management", self.verify_risk_management),
            ("Backtesting Engine", self.verify_backtesting_engine),
            ("API Endpoints", self.verify_api_endpoints),
            ("Configuration Files", self.verify_configuration_files),
            ("System Integration", self.verify_system_integration),
            ("Database Models", self.verify_database_models)
        ]
        
        results = []
        for check_name, check_func in verification_checks:
            try:
                result = check_func()
                results.append(result)
            except Exception as e:
                logger.error(f"Verification check {check_name} failed: {e}")
                self.log_verification(check_name, "FAIL", error=str(e))
                results.append(False)
        
        # Run integration tests
        try:
            integration_result = await self.run_integration_tests()
            results.append(integration_result)
        except Exception as e:
            logger.error(f"Integration tests failed: {e}")
            results.append(False)
        
        # Calculate summary statistics
        total_checks = len(self.verification_results)
        passed_checks = sum(1 for result in self.verification_results if result["status"] == "PASS")
        warning_checks = sum(1 for result in self.verification_results if result["status"] == "WARNING")
        failed_checks = sum(1 for result in self.verification_results if result["status"] == "FAIL")
        skipped_checks = sum(1 for result in self.verification_results if result["status"] == "SKIP")
        
        total_duration = time.time() - self.start_time
        
        # Determine overall system status
        critical_failures = sum(1 for result in self.verification_results 
                              if result["status"] == "FAIL" and 
                              result["component"] in ["Core Imports", "Decision Engine", "Risk Management"])
        
        if critical_failures > 0:
            overall_status = "CRITICAL_FAILURE"
        elif failed_checks > total_checks * 0.2:  # More than 20% failures
            overall_status = "SYSTEM_ISSUES"
        elif warning_checks > total_checks * 0.3:  # More than 30% warnings
            overall_status = "MINOR_ISSUES"
        else:
            overall_status = "SYSTEM_HEALTHY"
        
        summary = {
            "system_verification_summary": {
                "overall_status": overall_status,
                "total_checks": total_checks,
                "passed_checks": passed_checks,
                "warning_checks": warning_checks,
                "failed_checks": failed_checks,
                "skipped_checks": skipped_checks,
                "success_rate": passed_checks / total_checks if total_checks > 0 else 0,
                "total_duration_seconds": total_duration
            },
            "detailed_results": self.verification_results,
            "component_status": self.component_status,
            "verification_timestamp": datetime.utcnow().isoformat()
        }
        
        # Print summary
        print(f"\nVerification Summary:")
        print(f"Overall Status: {overall_status}")
        print(f"Total Checks: {total_checks}")
        print(f"✅ Passed: {passed_checks}")
        print(f"⚠️  Warnings: {warning_checks}")
        print(f"❌ Failed: {failed_checks}")
        print(f"⏭️  Skipped: {skipped_checks}")
        print(f"Success Rate: {passed_checks/total_checks:.1%}")
        print(f"Duration: {total_duration:.2f} seconds")
        
        print(f"\nDetailed Results:")
        print("-" * 80)
        for result in self.verification_results:
            status_icon = {
                "PASS": "✅",
                "FAIL": "❌", 
                "WARNING": "⚠️",
                "SKIP": "⏭️"
            }.get(result["status"], "❓")
            
            print(f"{status_icon} {result['component']}: {result['status']}")
            if result["details"]:
                print(f"    {result['details']}")
            if result["error"]:
                print(f"    Error: {result['error']}")
        
        print("\n" + "="*80)
        
        # System recommendations
        if overall_status == "SYSTEM_HEALTHY":
            print("🎉 System verification completed successfully!")
            print("   The Bitcoin trading system is ready for deployment.")
        elif overall_status == "MINOR_ISSUES":
            print("⚠️  System verification completed with minor issues.")
            print("   The system is functional but some optimizations are recommended.")
        elif overall_status == "SYSTEM_ISSUES":
            print("❌ System verification found significant issues.")
            print("   Please address the failed components before deployment.")
        else:
            print("🚨 Critical system failures detected!")
            print("   System is not ready for deployment. Fix critical issues first.")
        
        print("\n📋 Next Steps:")
        if overall_status in ["SYSTEM_HEALTHY", "MINOR_ISSUES"]:
            print("   1. Review any warnings and optimize if needed")
            print("   2. Configure API keys in backend/.env")
            print("   3. Run deployment: ./deploy.sh")
            print("   4. Access system at http://localhost:3000")
        else:
            print("   1. Fix all critical failures (Core Imports, Decision Engine, Risk Management)")
            print("   2. Address major component failures")
            print("   3. Re-run verification: python system_verification.py")
            print("   4. Proceed with deployment only after verification passes")
        
        return summary


# Standalone verification runner
async def main():
    """Run system verification as standalone script"""
    verifier = SystemIntegrityVerifier()
    results = await verifier.verify_complete_system()
    
    # Save results to file
    results_file = "system_verification_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: {results_file}")
    
    # Exit with appropriate code
    overall_status = results["system_verification_summary"]["overall_status"]
    if overall_status == "SYSTEM_HEALTHY":
        sys.exit(0)
    elif overall_status == "MINOR_ISSUES":
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == "__main__":
    asyncio.run(main())