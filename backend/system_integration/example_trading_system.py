#!/usr/bin/env python3
"""
Example usage of the integrated trading system
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
import asyncio
from datetime import datetime

from system_integration.trading_system_integration import TradingSystemIntegration, TradingSystemConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main function to run the trading system"""
    logger.info("Starting Bitcoin Trading System")
    logger.info("="*60)
    
    # Create custom configuration
    config = TradingSystemConfig(
        market_data_interval=30,  # 30 seconds for demo
        news_collection_interval=120,  # 2 minutes for demo
        technical_analysis_interval=60,  # 1 minute for demo
        decision_interval=90,  # 1.5 minutes for demo
        min_confidence_threshold=0.6,
        max_position_size=0.05,  # 5% for demo
        stop_loss_percentage=0.015  # 1.5% for demo
    )
    
    # Initialize trading system
    trading_system = TradingSystemIntegration(config)
    
    try:
        # Start the system
        await trading_system.start()
        
        # Display system status
        status = trading_system.get_system_status()
        logger.info("System Status:")
        logger.info(f"  System State: {status['system_coordinator']['system_state']}")
        logger.info(f"  Components: {status['system_coordinator']['components']['total']}")
        logger.info(f"  Processors: {status['trading_system']['processors']}")
        
        # Run for a demo period (or forever)
        logger.info("Trading system is running...")
        logger.info("Press Ctrl+C to stop")
        
        # For demo, run for 5 minutes then stop
        # For production, use: await trading_system.run_forever()
        await asyncio.sleep(300)  # 5 minutes
        
        logger.info("Demo period completed, stopping system...")
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, stopping system...")
    except Exception as e:
        logger.error(f"System error: {e}")
    finally:
        await trading_system.stop()
        logger.info("Trading system stopped")


if __name__ == "__main__":
    asyncio.run(main())