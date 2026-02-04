#!/usr/bin/env python3
"""
Strategy Manager
Handles custom trading strategy creation, validation, and execution
"""
import ast
import logging
import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
import importlib.util
import sys
import tempfile
import traceback

logger = logging.getLogger(__name__)

@dataclass
class StrategyInfo:
    """Strategy metadata"""
    id: str
    name: str
    description: str
    author: str
    version: str
    created_at: datetime
    updated_at: datetime
    tags: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

@dataclass
class Strategy:
    """Complete strategy definition"""
    info: StrategyInfo
    code: str
    parameters: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'info': self.info.to_dict(),
            'code': self.code,
            'parameters': self.parameters
        }

class StrategyValidator:
    """Validates strategy code for security and correctness"""
    
    ALLOWED_IMPORTS = {
        'numpy', 'np', 'pandas', 'pd', 'math', 'datetime', 'typing',
        'dataclasses', 'enum', 'collections', 'itertools', 'functools'
    }
    
    FORBIDDEN_FUNCTIONS = {
        'exec', 'eval', 'compile', '__import__', 'open', 'file',
        'input', 'raw_input', 'reload', 'vars', 'dir', 'globals', 'locals'
    }
    
    REQUIRED_METHODS = {
        'generate_signal', 'get_parameters', 'get_info'
    }
    
    def validate_syntax(self, code: str) -> Tuple[bool, Optional[str]]:
        """Validate Python syntax"""
        try:
            ast.parse(code)
            return True, None
        except SyntaxError as e:
            return False, f"Syntax error: {str(e)}"
    
    def validate_imports(self, code: str) -> Tuple[bool, Optional[str]]:
        """Validate that only allowed imports are used"""
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name not in self.ALLOWED_IMPORTS:
                            return False, f"Forbidden import: {alias.name}"
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module not in self.ALLOWED_IMPORTS:
                        return False, f"Forbidden import: {node.module}"
            return True, None
        except Exception as e:
            return False, f"Import validation error: {str(e)}"
    
    def validate_functions(self, code: str) -> Tuple[bool, Optional[str]]:
        """Validate that forbidden functions are not used"""
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in self.FORBIDDEN_FUNCTIONS:
                            return False, f"Forbidden function: {node.func.id}"
            return True, None
        except Exception as e:
            return False, f"Function validation error: {str(e)}"
    
    def validate_structure(self, code: str) -> Tuple[bool, Optional[str]]:
        """Validate that required methods are present"""
        try:
            tree = ast.parse(code)
            
            # Find class definition
            strategy_class = None
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    strategy_class = node
                    break
            
            if not strategy_class:
                return False, "No strategy class found. Must define a class that inherits from BaseStrategy."
            
            # Check for required methods
            method_names = {node.name for node in strategy_class.body if isinstance(node, ast.FunctionDef)}
            missing_methods = self.REQUIRED_METHODS - method_names
            
            if missing_methods:
                return False, f"Missing required methods: {', '.join(missing_methods)}"
            
            return True, None
        except Exception as e:
            return False, f"Structure validation error: {str(e)}"
    
    def validate_code(self, code: str) -> Tuple[bool, List[str]]:
        """Comprehensive code validation"""
        errors = []
        
        # Syntax validation
        valid, error = self.validate_syntax(code)
        if not valid:
            errors.append(error)
            return False, errors  # Can't continue if syntax is invalid
        
        # Import validation
        valid, error = self.validate_imports(code)
        if not valid:
            errors.append(error)
        
        # Function validation
        valid, error = self.validate_functions(code)
        if not valid:
            errors.append(error)
        
        # Structure validation
        valid, error = self.validate_structure(code)
        if not valid:
            errors.append(error)
        
        return len(errors) == 0, errors

class StrategyManager:
    """Manages custom trading strategies"""
    
    def __init__(self, strategies_dir: str = "strategies"):
        """Initialize strategy manager"""
        self.strategies_dir = strategies_dir
        self.validator = StrategyValidator()
        self.strategies: Dict[str, Strategy] = {}
        
        # Create strategies directory if it doesn't exist
        os.makedirs(self.strategies_dir, exist_ok=True)
        
        # Load existing strategies
        self.load_strategies()
        
        logger.info(f"Strategy manager initialized with {len(self.strategies)} strategies")
    
    def load_strategies(self):
        """Load all strategies from disk"""
        try:
            for filename in os.listdir(self.strategies_dir):
                if filename.endswith('.json'):
                    strategy_path = os.path.join(self.strategies_dir, filename)
                    try:
                        with open(strategy_path, 'r', encoding='utf-8') as f:
                            strategy_data = json.load(f)
                        
                        # Convert to Strategy object
                        info_data = strategy_data['info']
                        info = StrategyInfo(
                            id=info_data['id'],
                            name=info_data['name'],
                            description=info_data['description'],
                            author=info_data['author'],
                            version=info_data['version'],
                            created_at=datetime.fromisoformat(info_data['created_at']),
                            updated_at=datetime.fromisoformat(info_data['updated_at']),
                            tags=info_data['tags']
                        )
                        
                        strategy = Strategy(
                            info=info,
                            code=strategy_data['code'],
                            parameters=strategy_data['parameters']
                        )
                        
                        self.strategies[strategy.info.id] = strategy
                        logger.debug(f"Loaded strategy: {strategy.info.name}")
                        
                    except Exception as e:
                        logger.error(f"Error loading strategy {filename}: {e}")
                        
        except Exception as e:
            logger.error(f"Error loading strategies: {e}")
    
    def save_strategy(self, strategy: Strategy):
        """Save strategy to disk"""
        try:
            strategy_path = os.path.join(self.strategies_dir, f"{strategy.info.id}.json")
            with open(strategy_path, 'w', encoding='utf-8') as f:
                json.dump(strategy.to_dict(), f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved strategy: {strategy.info.name}")
            
        except Exception as e:
            logger.error(f"Error saving strategy {strategy.info.id}: {e}")
            raise
    
    def create_strategy(self, name: str, description: str, code: str, 
                       parameters: Dict[str, Any], author: str = "User",
                       tags: List[str] = None) -> Tuple[bool, str, Optional[Strategy]]:
        """Create a new strategy"""
        try:
            # Validate code
            valid, errors = self.validator.validate_code(code)
            if not valid:
                return False, f"Code validation failed: {'; '.join(errors)}", None
            
            # Create strategy info
            strategy_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            info = StrategyInfo(
                id=strategy_id,
                name=name,
                description=description,
                author=author,
                version="1.0.0",
                created_at=now,
                updated_at=now,
                tags=tags or []
            )
            
            # Create strategy
            strategy = Strategy(
                info=info,
                code=code,
                parameters=parameters
            )
            
            # Test strategy execution
            test_result, test_error = self.test_strategy(strategy)
            if not test_result:
                return False, f"Strategy test failed: {test_error}", None
            
            # Save strategy
            self.strategies[strategy_id] = strategy
            self.save_strategy(strategy)
            
            return True, "Strategy created successfully", strategy
            
        except Exception as e:
            logger.error(f"Error creating strategy: {e}")
            return False, f"Error creating strategy: {str(e)}", None
    
    def update_strategy(self, strategy_id: str, name: str = None, description: str = None,
                       code: str = None, parameters: Dict[str, Any] = None,
                       tags: List[str] = None) -> Tuple[bool, str, Optional[Strategy]]:
        """Update an existing strategy"""
        try:
            if strategy_id not in self.strategies:
                return False, "Strategy not found", None
            
            strategy = self.strategies[strategy_id]
            
            # Update fields if provided
            if name is not None:
                strategy.info.name = name
            if description is not None:
                strategy.info.description = description
            if code is not None:
                # Validate new code
                valid, errors = self.validator.validate_code(code)
                if not valid:
                    return False, f"Code validation failed: {'; '.join(errors)}", None
                
                # Test new code
                test_strategy = Strategy(strategy.info, code, strategy.parameters)
                test_result, test_error = self.test_strategy(test_strategy)
                if not test_result:
                    return False, f"Strategy test failed: {test_error}", None
                
                strategy.code = code
            
            if parameters is not None:
                strategy.parameters = parameters
            if tags is not None:
                strategy.info.tags = tags
            
            # Update timestamp
            strategy.info.updated_at = datetime.utcnow()
            
            # Save updated strategy
            self.save_strategy(strategy)
            
            return True, "Strategy updated successfully", strategy
            
        except Exception as e:
            logger.error(f"Error updating strategy: {e}")
            return False, f"Error updating strategy: {str(e)}", None
    
    def delete_strategy(self, strategy_id: str) -> Tuple[bool, str]:
        """Delete a strategy"""
        try:
            if strategy_id not in self.strategies:
                return False, "Strategy not found"
            
            # Remove from memory
            strategy = self.strategies.pop(strategy_id)
            
            # Remove from disk
            strategy_path = os.path.join(self.strategies_dir, f"{strategy_id}.json")
            if os.path.exists(strategy_path):
                os.remove(strategy_path)
            
            logger.info(f"Deleted strategy: {strategy.info.name}")
            return True, "Strategy deleted successfully"
            
        except Exception as e:
            logger.error(f"Error deleting strategy: {e}")
            return False, f"Error deleting strategy: {str(e)}"
    
    def get_strategy(self, strategy_id: str) -> Optional[Strategy]:
        """Get a strategy by ID"""
        return self.strategies.get(strategy_id)
    
    def list_strategies(self) -> List[Dict[str, Any]]:
        """List all strategies"""
        return [strategy.to_dict() for strategy in self.strategies.values()]
    
    def test_strategy(self, strategy: Strategy) -> Tuple[bool, Optional[str]]:
        """Test strategy execution in a safe environment"""
        try:
            # Create a temporary module
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                # Add base strategy class and required imports
                base_code = '''
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class MarketData:
    symbol: str
    price: float
    volume: float
    timestamp: datetime
    source: str = "test"

class BaseStrategy:
    """Base class for trading strategies"""
    
    def __init__(self, parameters: Dict[str, Any] = None):
        self.parameters = parameters or {}
    
    def generate_signal(self, market_data: List[MarketData], 
                       sentiment_score: float = 0.5,
                       technical_indicators: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate trading signal - must be implemented by subclass"""
        raise NotImplementedError("Subclass must implement generate_signal method")
    
    def get_parameters(self) -> Dict[str, Any]:
        """Get strategy parameters"""
        return self.parameters
    
    def get_info(self) -> Dict[str, Any]:
        """Get strategy information"""
        return {
            "name": getattr(self, 'name', 'Unknown Strategy'),
            "description": getattr(self, 'description', 'No description'),
            "version": getattr(self, 'version', '1.0.0')
        }

'''
                f.write(base_code)
                f.write('\n\n')
                f.write(strategy.code)
                f.write('\n\n')
                
                # Add test code
                test_code = '''
# Test the strategy
if __name__ == "__main__":
    # Find the strategy class
    import inspect
    strategy_class = None
    for name, obj in globals().items():
        if (inspect.isclass(obj) and 
            issubclass(obj, BaseStrategy) and 
            obj != BaseStrategy):
            strategy_class = obj
            break
    
    if strategy_class is None:
        raise Exception("No strategy class found")
    
    # Test instantiation
    strategy_instance = strategy_class()
    
    # Test required methods
    info = strategy_instance.get_info()
    params = strategy_instance.get_parameters()
    
    # Test signal generation with sample data
    sample_data = [
        MarketData("BTCUSDT", 45000.0, 100.0, datetime.now()),
        MarketData("BTCUSDT", 45100.0, 110.0, datetime.now()),
        MarketData("BTCUSDT", 45200.0, 120.0, datetime.now()),
    ]
    
    signal = strategy_instance.generate_signal(sample_data)
    
    print("Strategy test passed successfully")
'''
                f.write(test_code)
                temp_file = f.name
            
            # Execute the test
            try:
                spec = importlib.util.spec_from_file_location("test_strategy", temp_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                return True, None
                
            except Exception as e:
                return False, str(e)
            
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Error testing strategy: {e}")
            return False, f"Test execution error: {str(e)}"
    
    def get_strategy_templates(self) -> List[Dict[str, Any]]:
        """Get predefined strategy templates"""
        templates = [
            {
                "id": "sma_crossover",
                "name": "Simple Moving Average Crossover",
                "description": "Classic SMA crossover strategy with customizable periods",
                "code": '''class SMAStrategy(BaseStrategy):
    """Simple Moving Average Crossover Strategy"""
    
    def __init__(self, parameters=None):
        super().__init__(parameters)
        self.name = "SMA Crossover Strategy"
        self.description = "Buy when short SMA crosses above long SMA, sell when below"
        self.version = "1.0.0"
        
        # Default parameters
        self.short_period = self.parameters.get('short_period', 10)
        self.long_period = self.parameters.get('long_period', 20)
        self.min_confidence = self.parameters.get('min_confidence', 0.6)
    
    def generate_signal(self, market_data, sentiment_score=0.5, technical_indicators=None):
        if len(market_data) < self.long_period:
            return {"action": "HOLD", "confidence": 0.0, "reasoning": "Insufficient data"}
        
        # Calculate SMAs
        prices = [data.price for data in market_data[-self.long_period:]]
        short_sma = np.mean(prices[-self.short_period:])
        long_sma = np.mean(prices)
        
        # Generate signal
        if short_sma > long_sma:
            confidence = min(0.9, 0.5 + (short_sma - long_sma) / long_sma)
            if confidence >= self.min_confidence:
                return {
                    "action": "BUY",
                    "confidence": confidence,
                    "reasoning": f"Short SMA ({short_sma:.2f}) > Long SMA ({long_sma:.2f})"
                }
        elif short_sma < long_sma:
            confidence = min(0.9, 0.5 + (long_sma - short_sma) / long_sma)
            if confidence >= self.min_confidence:
                return {
                    "action": "SELL", 
                    "confidence": confidence,
                    "reasoning": f"Short SMA ({short_sma:.2f}) < Long SMA ({long_sma:.2f})"
                }
        
        return {"action": "HOLD", "confidence": 0.5, "reasoning": "No clear signal"}''',
                "parameters": {
                    "short_period": 10,
                    "long_period": 20,
                    "min_confidence": 0.6
                },
                "tags": ["technical", "sma", "crossover", "beginner"]
            },
            {
                "id": "rsi_strategy",
                "name": "RSI Momentum Strategy",
                "description": "RSI-based momentum strategy with overbought/oversold signals",
                "code": '''class RSIStrategy(BaseStrategy):
    """RSI Momentum Strategy"""
    
    def __init__(self, parameters=None):
        super().__init__(parameters)
        self.name = "RSI Momentum Strategy"
        self.description = "Buy when RSI is oversold, sell when overbought"
        self.version = "1.0.0"
        
        self.rsi_period = self.parameters.get('rsi_period', 14)
        self.oversold_threshold = self.parameters.get('oversold_threshold', 30)
        self.overbought_threshold = self.parameters.get('overbought_threshold', 70)
        self.min_confidence = self.parameters.get('min_confidence', 0.7)
    
    def calculate_rsi(self, prices):
        """Calculate RSI indicator"""
        if len(prices) < self.rsi_period + 1:
            return 50.0  # Neutral RSI
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-self.rsi_period:])
        avg_loss = np.mean(losses[-self.rsi_period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def generate_signal(self, market_data, sentiment_score=0.5, technical_indicators=None):
        if len(market_data) < self.rsi_period + 1:
            return {"action": "HOLD", "confidence": 0.0, "reasoning": "Insufficient data for RSI"}
        
        prices = [data.price for data in market_data]
        rsi = self.calculate_rsi(prices)
        
        # Incorporate sentiment
        sentiment_factor = (sentiment_score - 0.5) * 0.2  # -0.1 to +0.1 adjustment
        
        if rsi <= self.oversold_threshold:
            confidence = min(0.95, 0.7 + (self.oversold_threshold - rsi) / 100 + sentiment_factor)
            if confidence >= self.min_confidence:
                return {
                    "action": "BUY",
                    "confidence": confidence,
                    "reasoning": f"RSI oversold: {rsi:.1f} <= {self.oversold_threshold}"
                }
        elif rsi >= self.overbought_threshold:
            confidence = min(0.95, 0.7 + (rsi - self.overbought_threshold) / 100 - sentiment_factor)
            if confidence >= self.min_confidence:
                return {
                    "action": "SELL",
                    "confidence": confidence,
                    "reasoning": f"RSI overbought: {rsi:.1f} >= {self.overbought_threshold}"
                }
        
        return {"action": "HOLD", "confidence": 0.5, "reasoning": f"RSI neutral: {rsi:.1f}"}''',
                "parameters": {
                    "rsi_period": 14,
                    "oversold_threshold": 30,
                    "overbought_threshold": 70,
                    "min_confidence": 0.7
                },
                "tags": ["technical", "rsi", "momentum", "intermediate"]
            },
            {
                "id": "sentiment_strategy",
                "name": "Sentiment-Based Strategy",
                "description": "Trading strategy based on market sentiment analysis",
                "code": '''class SentimentStrategy(BaseStrategy):
    """Sentiment-Based Trading Strategy"""
    
    def __init__(self, parameters=None):
        super().__init__(parameters)
        self.name = "Sentiment Strategy"
        self.description = "Trade based on market sentiment with trend confirmation"
        self.version = "1.0.0"
        
        self.sentiment_threshold = self.parameters.get('sentiment_threshold', 0.6)
        self.trend_period = self.parameters.get('trend_period', 5)
        self.min_confidence = self.parameters.get('min_confidence', 0.65)
    
    def calculate_trend(self, prices):
        """Calculate price trend direction"""
        if len(prices) < self.trend_period:
            return 0.0
        
        recent_prices = prices[-self.trend_period:]
        trend = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]
        return trend
    
    def generate_signal(self, market_data, sentiment_score=0.5, technical_indicators=None):
        if len(market_data) < self.trend_period:
            return {"action": "HOLD", "confidence": 0.0, "reasoning": "Insufficient data"}
        
        prices = [data.price for data in market_data]
        trend = self.calculate_trend(prices)
        
        # Normalize sentiment score (0-1 to -1 to 1)
        sentiment_signal = (sentiment_score - 0.5) * 2
        
        # Combine sentiment and trend
        if sentiment_signal > 0.2 and trend > 0:  # Positive sentiment + uptrend
            confidence = min(0.9, self.min_confidence + abs(sentiment_signal) * 0.3)
            return {
                "action": "BUY",
                "confidence": confidence,
                "reasoning": f"Positive sentiment ({sentiment_score:.2f}) + uptrend ({trend:.3f})"
            }
        elif sentiment_signal < -0.2 and trend < 0:  # Negative sentiment + downtrend
            confidence = min(0.9, self.min_confidence + abs(sentiment_signal) * 0.3)
            return {
                "action": "SELL",
                "confidence": confidence,
                "reasoning": f"Negative sentiment ({sentiment_score:.2f}) + downtrend ({trend:.3f})"
            }
        
        return {
            "action": "HOLD", 
            "confidence": 0.4,
            "reasoning": f"Mixed signals: sentiment={sentiment_score:.2f}, trend={trend:.3f}"
        }''',
                "parameters": {
                    "sentiment_threshold": 0.6,
                    "trend_period": 5,
                    "min_confidence": 0.65
                },
                "tags": ["sentiment", "trend", "advanced"]
            }
        ]
        
        return templates

# Global strategy manager instance
strategy_manager = StrategyManager()