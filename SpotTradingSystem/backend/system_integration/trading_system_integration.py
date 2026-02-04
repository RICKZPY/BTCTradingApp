"""
Trading System Integration
Integrates all trading system modules with event-driven architecture
"""
import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from system_integration.event_bus import EventBus, Event, EventType
from system_integration.message_queue import MessageQueue, Message, MessagePriority, MessageProcessor, ProcessingResult, MessageStatus
from system_integration.task_scheduler import TaskScheduler
from system_integration.system_coordinator import SystemCoordinator

# Import trading system modules
from data_collection.scheduler import DataCollectionScheduler
from news_analysis.analyzer import NewsAnalyzer
from technical_analysis.engine import TechnicalAnalysisEngine
from decision_engine.engine import DecisionEngine
from risk_management.risk_manager import RiskManager
from trading_execution.order_manager import OrderManager
from trading_execution.position_manager import PositionManager

logger = logging.getLogger(__name__)


@dataclass
class TradingSystemConfig:
    """Trading system configuration"""
    # Data collection intervals
    market_data_interval: int = 60  # seconds
    news_collection_interval: int = 300  # 5 minutes
    
    # Analysis intervals
    technical_analysis_interval: int = 120  # 2 minutes
    news_analysis_batch_size: int = 10
    
    # Decision making
    decision_interval: int = 180  # 3 minutes
    min_confidence_threshold: float = 0.7
    
    # Risk management
    max_position_size: float = 0.1  # 10% of portfolio
    stop_loss_percentage: float = 0.02  # 2%
    
    # Trading execution
    order_timeout: int = 300  # 5 minutes
    max_slippage: float = 0.001  # 0.1%


class DataCollectionProcessor(MessageProcessor):
    """Processes data collection messages"""
    
    def __init__(self, event_bus: EventBus, data_scheduler: DataCollectionScheduler):
        super().__init__("data_collection_processor")
        self.event_bus = event_bus
        self.data_scheduler = data_scheduler
    
    async def process(self, message: Message) -> ProcessingResult:
        """Process data collection message"""
        try:
            payload = message.payload
            collection_type = payload.get('type')
            
            if collection_type == 'market_data':
                # Collect market data
                market_data = await self.data_scheduler.collect_market_data()
                
                # Publish market data event
                await self.event_bus.publish_new(
                    EventType.PRICE_UPDATE,
                    "data_collection",
                    {
                        'symbol': market_data.get('symbol', 'BTCUSDT'),
                        'price': market_data.get('price'),
                        'volume': market_data.get('volume'),
                        'timestamp': datetime.utcnow().isoformat()
                    }
                )
                
            elif collection_type == 'news_data':
                # Collect news data
                news_items = await self.data_scheduler.collect_news_data()
                
                # Publish news data event
                await self.event_bus.publish_new(
                    EventType.NEWS_UPDATE,
                    "data_collection",
                    {
                        'news_count': len(news_items),
                        'news_items': [item.to_dict() for item in news_items[:5]],  # First 5 items
                        'timestamp': datetime.utcnow().isoformat()
                    }
                )
            
            return ProcessingResult(
                message_id=message.message_id,
                status=MessageStatus.COMPLETED,
                result=f"Collected {collection_type}",
                processing_time=0.5
            )
            
        except Exception as e:
            logger.error(f"Data collection processing failed: {e}")
            return ProcessingResult(
                message_id=message.message_id,
                status=MessageStatus.FAILED,
                error=str(e),
                processing_time=0.1
            )


class AnalysisProcessor(MessageProcessor):
    """Processes analysis messages"""
    
    def __init__(self, event_bus: EventBus, news_analyzer: NewsAnalyzer, 
                 technical_engine: TechnicalAnalysisEngine):
        super().__init__("analysis_processor")
        self.event_bus = event_bus
        self.news_analyzer = news_analyzer
        self.technical_engine = technical_engine
    
    async def process(self, message: Message) -> ProcessingResult:
        """Process analysis message"""
        try:
            payload = message.payload
            analysis_type = payload.get('type')
            
            if analysis_type == 'news_analysis':
                # Analyze news sentiment
                news_items = payload.get('news_items', [])
                
                analysis_results = []
                for news_item in news_items:
                    result = await self.news_analyzer.analyze_news_item(news_item)
                    analysis_results.append(result)
                
                # Publish sentiment analysis event
                await self.event_bus.publish_new(
                    EventType.SENTIMENT_UPDATE,
                    "news_analysis",
                    {
                        'analysis_count': len(analysis_results),
                        'average_sentiment': sum(r.sentiment_score for r in analysis_results) / len(analysis_results) if analysis_results else 0,
                        'results': [r.to_dict() for r in analysis_results],
                        'timestamp': datetime.utcnow().isoformat()
                    }
                )
                
            elif analysis_type == 'technical_analysis':
                # Perform technical analysis
                market_data = payload.get('market_data', [])
                
                signals = self.technical_engine.generate_signals(market_data)
                
                # Publish technical analysis event
                await self.event_bus.publish_new(
                    EventType.SIGNAL_GENERATED,
                    "technical_analysis",
                    {
                        'signals': [s.to_dict() for s in signals],
                        'signal_count': len(signals),
                        'timestamp': datetime.utcnow().isoformat()
                    }
                )
            
            return ProcessingResult(
                message_id=message.message_id,
                status=MessageStatus.COMPLETED,
                result=f"Completed {analysis_type}",
                processing_time=1.0
            )
            
        except Exception as e:
            logger.error(f"Analysis processing failed: {e}")
            return ProcessingResult(
                message_id=message.message_id,
                status=MessageStatus.FAILED,
                error=str(e),
                processing_time=0.1
            )


class DecisionProcessor(MessageProcessor):
    """Processes trading decision messages"""
    
    def __init__(self, event_bus: EventBus, decision_engine: DecisionEngine, 
                 risk_manager: RiskManager):
        super().__init__("decision_processor")
        self.event_bus = event_bus
        self.decision_engine = decision_engine
        self.risk_manager = risk_manager
    
    async def process(self, message: Message) -> ProcessingResult:
        """Process trading decision message"""
        try:
            payload = message.payload
            
            # Get analysis data
            sentiment_data = payload.get('sentiment_data')
            technical_data = payload.get('technical_data')
            market_data = payload.get('market_data')
            
            # Make trading decision
            decision = await self.decision_engine.make_decision(
                sentiment_data, technical_data, market_data
            )
            
            if decision and decision.action != 'HOLD':
                # Validate decision with risk manager
                risk_assessment = await self.risk_manager.assess_trade_risk(decision)
                
                if risk_assessment.approved:
                    # Publish trading decision event
                    await self.event_bus.publish_new(
                        EventType.TRADING_DECISION,
                        "decision_engine",
                        {
                            'decision': decision.to_dict(),
                            'risk_assessment': risk_assessment.to_dict(),
                            'timestamp': datetime.utcnow().isoformat()
                        }
                    )
                else:
                    logger.warning(f"Trade rejected by risk manager: {risk_assessment.rejection_reason}")
            
            return ProcessingResult(
                message_id=message.message_id,
                status=MessageStatus.COMPLETED,
                result=f"Decision: {decision.action if decision else 'HOLD'}",
                processing_time=0.8
            )
            
        except Exception as e:
            logger.error(f"Decision processing failed: {e}")
            return ProcessingResult(
                message_id=message.message_id,
                status=MessageStatus.FAILED,
                error=str(e),
                processing_time=0.1
            )


class ExecutionProcessor(MessageProcessor):
    """Processes trade execution messages"""
    
    def __init__(self, event_bus: EventBus, order_manager: OrderManager, 
                 position_manager: PositionManager):
        super().__init__("execution_processor")
        self.event_bus = event_bus
        self.order_manager = order_manager
        self.position_manager = position_manager
    
    async def process(self, message: Message) -> ProcessingResult:
        """Process trade execution message"""
        try:
            payload = message.payload
            decision = payload.get('decision')
            
            if not decision:
                return ProcessingResult(
                    message_id=message.message_id,
                    status=MessageStatus.FAILED,
                    error="No trading decision provided",
                    processing_time=0.1
                )
            
            # Execute trade
            order_result = await self.order_manager.execute_trade(decision)
            
            # Update position
            if order_result.status == 'FILLED':
                await self.position_manager.update_position(order_result)
                
                # Publish execution event
                await self.event_bus.publish_new(
                    EventType.TRADE_EXECUTED,
                    "trading_execution",
                    {
                        'order_result': order_result.to_dict(),
                        'position_update': True,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                )
            else:
                logger.warning(f"Order not filled: {order_result.status}")
            
            return ProcessingResult(
                message_id=message.message_id,
                status=MessageStatus.COMPLETED,
                result=f"Order {order_result.status}",
                processing_time=2.0
            )
            
        except Exception as e:
            logger.error(f"Execution processing failed: {e}")
            return ProcessingResult(
                message_id=message.message_id,
                status=MessageStatus.FAILED,
                error=str(e),
                processing_time=0.1
            )


class TradingSystemIntegration:
    """
    Main trading system integration class
    Coordinates all trading system components through event-driven architecture
    """
    
    def __init__(self, config: TradingSystemConfig = None):
        """Initialize trading system integration"""
        self.config = config or TradingSystemConfig()
        
        # System coordinator
        self.coordinator = SystemCoordinator()
        
        # Get core components
        self.event_bus = self.coordinator.event_bus
        self.message_queue = self.coordinator.message_queue
        self.task_scheduler = self.coordinator.task_scheduler
        
        # Trading system components
        self.data_scheduler = None
        self.news_analyzer = None
        self.technical_engine = None
        self.decision_engine = None
        self.risk_manager = None
        self.order_manager = None
        self.position_manager = None
        
        # Message processors
        self.processors = {}
        
        # System state
        self.analysis_cache = {}
        self.last_decision_time = None
        
        logger.info("Trading system integration initialized")
    
    async def initialize_components(self):
        """Initialize all trading system components"""
        try:
            # Initialize trading components
            self.data_scheduler = DataCollectionScheduler()
            self.news_analyzer = NewsAnalyzer()
            self.technical_engine = TechnicalAnalysisEngine()
            self.decision_engine = DecisionEngine()
            self.risk_manager = RiskManager()
            self.order_manager = OrderManager()
            self.position_manager = PositionManager()
            
            # Register components with coordinator
            self.coordinator.register_component("data_scheduler", self.data_scheduler)
            self.coordinator.register_component("news_analyzer", self.news_analyzer)
            self.coordinator.register_component("technical_engine", self.technical_engine)
            self.coordinator.register_component("decision_engine", self.decision_engine)
            self.coordinator.register_component("risk_manager", self.risk_manager)
            self.coordinator.register_component("order_manager", self.order_manager)
            self.coordinator.register_component("position_manager", self.position_manager)
            
            # Initialize message processors
            self.processors['data_collection'] = DataCollectionProcessor(
                self.event_bus, self.data_scheduler
            )
            self.processors['analysis'] = AnalysisProcessor(
                self.event_bus, self.news_analyzer, self.technical_engine
            )
            self.processors['decision'] = DecisionProcessor(
                self.event_bus, self.decision_engine, self.risk_manager
            )
            self.processors['execution'] = ExecutionProcessor(
                self.event_bus, self.order_manager, self.position_manager
            )
            
            # Register processors with message queue
            for queue_name, processor in self.processors.items():
                self.message_queue.register_processor(queue_name, processor)
            
            logger.info("All trading system components initialized")
            
        except Exception as e:
            logger.error(f"Component initialization failed: {e}")
            raise
    
    def setup_event_handlers(self):
        """Setup event handlers for trading system events"""
        # Handle price updates
        self.event_bus.subscribe(
            {EventType.PRICE_UPDATE},
            self._handle_price_update,
            async_handler=True
        )
        
        # Handle news updates
        self.event_bus.subscribe(
            {EventType.NEWS_UPDATE},
            self._handle_news_update,
            async_handler=True
        )
        
        # Handle sentiment updates
        self.event_bus.subscribe(
            {EventType.SENTIMENT_UPDATE},
            self._handle_sentiment_update,
            async_handler=True
        )
        
        # Handle signal generation
        self.event_bus.subscribe(
            {EventType.SIGNAL_GENERATED},
            self._handle_signal_generated,
            async_handler=True
        )
        
        # Handle trading decisions
        self.event_bus.subscribe(
            {EventType.TRADING_DECISION},
            self._handle_trading_decision,
            async_handler=True
        )
        
        # Handle trade execution
        self.event_bus.subscribe(
            {EventType.TRADE_EXECUTED},
            self._handle_trade_executed,
            async_handler=True
        )
    
    async def _handle_price_update(self, event: Event):
        """Handle price update events"""
        try:
            # Cache market data for analysis
            self.analysis_cache['market_data'] = event.data
            
            # Trigger technical analysis
            await self.message_queue.enqueue_simple(
                "analysis",
                {
                    'type': 'technical_analysis',
                    'market_data': [event.data]
                },
                MessagePriority.NORMAL
            )
            
        except Exception as e:
            logger.error(f"Error handling price update: {e}")
    
    async def _handle_news_update(self, event: Event):
        """Handle news update events"""
        try:
            news_items = event.data.get('news_items', [])
            
            if news_items:
                # Trigger news analysis
                await self.message_queue.enqueue_simple(
                    "analysis",
                    {
                        'type': 'news_analysis',
                        'news_items': news_items
                    },
                    MessagePriority.HIGH
                )
            
        except Exception as e:
            logger.error(f"Error handling news update: {e}")
    
    async def _handle_sentiment_update(self, event: Event):
        """Handle sentiment analysis updates"""
        try:
            # Cache sentiment data
            self.analysis_cache['sentiment_data'] = event.data
            
            # Check if we have enough data for decision making
            await self._check_decision_trigger()
            
        except Exception as e:
            logger.error(f"Error handling sentiment update: {e}")
    
    async def _handle_signal_generated(self, event: Event):
        """Handle technical signal generation"""
        try:
            # Cache technical data
            self.analysis_cache['technical_data'] = event.data
            
            # Check if we have enough data for decision making
            await self._check_decision_trigger()
            
        except Exception as e:
            logger.error(f"Error handling signal generation: {e}")
    
    async def _check_decision_trigger(self):
        """Check if we should trigger decision making"""
        try:
            # Check if we have both sentiment and technical data
            has_sentiment = 'sentiment_data' in self.analysis_cache
            has_technical = 'technical_data' in self.analysis_cache
            has_market = 'market_data' in self.analysis_cache
            
            # Check time since last decision
            now = datetime.utcnow()
            time_since_last = None
            if self.last_decision_time:
                time_since_last = (now - self.last_decision_time).total_seconds()
            
            # Trigger decision if we have data and enough time has passed
            if (has_sentiment and has_technical and has_market and 
                (time_since_last is None or time_since_last >= self.config.decision_interval)):
                
                await self.message_queue.enqueue_simple(
                    "decision",
                    {
                        'sentiment_data': self.analysis_cache.get('sentiment_data'),
                        'technical_data': self.analysis_cache.get('technical_data'),
                        'market_data': self.analysis_cache.get('market_data')
                    },
                    MessagePriority.HIGH
                )
                
                self.last_decision_time = now
            
        except Exception as e:
            logger.error(f"Error checking decision trigger: {e}")
    
    async def _handle_trading_decision(self, event: Event):
        """Handle trading decision events"""
        try:
            decision = event.data.get('decision')
            
            if decision and decision.get('action') != 'HOLD':
                # Trigger trade execution
                await self.message_queue.enqueue_simple(
                    "execution",
                    {
                        'decision': decision
                    },
                    MessagePriority.CRITICAL
                )
            
        except Exception as e:
            logger.error(f"Error handling trading decision: {e}")
    
    async def _handle_trade_executed(self, event: Event):
        """Handle trade execution events"""
        try:
            order_result = event.data.get('order_result')
            logger.info(f"Trade executed: {order_result}")
            
            # Could trigger additional actions like notifications, logging, etc.
            
        except Exception as e:
            logger.error(f"Error handling trade execution: {e}")
    
    def setup_scheduled_tasks(self):
        """Setup scheduled tasks for data collection and system maintenance"""
        # Market data collection
        self.task_scheduler.schedule_interval(
            name="market_data_collection",
            task_func=self._collect_market_data,
            interval_seconds=self.config.market_data_interval,
            description="Collect market data",
            tags=["data_collection", "market"]
        )
        
        # News data collection
        self.task_scheduler.schedule_interval(
            name="news_data_collection",
            task_func=self._collect_news_data,
            interval_seconds=self.config.news_collection_interval,
            description="Collect news data",
            tags=["data_collection", "news"]
        )
        
        # Portfolio monitoring
        self.task_scheduler.schedule_interval(
            name="portfolio_monitoring",
            task_func=self._monitor_portfolio,
            interval_seconds=300,  # 5 minutes
            description="Monitor portfolio and positions",
            tags=["monitoring", "portfolio"]
        )
    
    async def _collect_market_data(self):
        """Scheduled task to collect market data"""
        try:
            await self.message_queue.enqueue_simple(
                "data_collection",
                {'type': 'market_data'},
                MessagePriority.NORMAL
            )
        except Exception as e:
            logger.error(f"Market data collection task failed: {e}")
    
    async def _collect_news_data(self):
        """Scheduled task to collect news data"""
        try:
            await self.message_queue.enqueue_simple(
                "data_collection",
                {'type': 'news_data'},
                MessagePriority.NORMAL
            )
        except Exception as e:
            logger.error(f"News data collection task failed: {e}")
    
    async def _monitor_portfolio(self):
        """Scheduled task to monitor portfolio"""
        try:
            if self.position_manager:
                portfolio = await self.position_manager.get_portfolio_summary()
                
                # Publish portfolio update event
                await self.event_bus.publish_new(
                    EventType.PORTFOLIO_UPDATE,
                    "portfolio_monitor",
                    {
                        'portfolio': portfolio.to_dict() if portfolio else {},
                        'timestamp': datetime.utcnow().isoformat()
                    }
                )
        except Exception as e:
            logger.error(f"Portfolio monitoring task failed: {e}")
    
    async def start(self):
        """Start the trading system"""
        try:
            logger.info("Starting trading system...")
            
            # Initialize components
            await self.initialize_components()
            
            # Setup event handlers
            self.setup_event_handlers()
            
            # Setup scheduled tasks
            self.setup_scheduled_tasks()
            
            # Start system coordinator
            await self.coordinator.startup()
            
            logger.info("Trading system started successfully")
            
        except Exception as e:
            logger.error(f"Trading system startup failed: {e}")
            raise
    
    async def stop(self):
        """Stop the trading system"""
        try:
            logger.info("Stopping trading system...")
            
            # Stop system coordinator
            await self.coordinator.shutdown()
            
            logger.info("Trading system stopped successfully")
            
        except Exception as e:
            logger.error(f"Trading system shutdown failed: {e}")
            raise
    
    async def run_forever(self):
        """Run the trading system indefinitely"""
        try:
            await self.start()
            await self.coordinator.run_forever()
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Trading system error: {e}")
        finally:
            await self.stop()
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        coordinator_status = self.coordinator.get_system_status()
        
        return {
            'trading_system': {
                'config': {
                    'market_data_interval': self.config.market_data_interval,
                    'news_collection_interval': self.config.news_collection_interval,
                    'decision_interval': self.config.decision_interval,
                    'min_confidence_threshold': self.config.min_confidence_threshold
                },
                'analysis_cache': {
                    'has_market_data': 'market_data' in self.analysis_cache,
                    'has_sentiment_data': 'sentiment_data' in self.analysis_cache,
                    'has_technical_data': 'technical_data' in self.analysis_cache
                },
                'last_decision_time': self.last_decision_time.isoformat() if self.last_decision_time else None,
                'processors': list(self.processors.keys())
            },
            'system_coordinator': coordinator_status
        }