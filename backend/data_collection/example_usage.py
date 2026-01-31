"""
Example usage of the Data Collection System

This script demonstrates how to use the data collection framework
to collect data from various sources.
"""

import asyncio
from data_collection.manager import DataCollectionManager
from data_collection.adapters.news_collector import NewsDataCollector
from data_collection.adapters.market_collector import MarketDataCollector


async def example_basic_usage():
    """Example of basic data collection usage"""
    print("=== Basic Data Collection Example ===")
    
    # Create individual collectors
    news_collector = NewsDataCollector(sources=['coindesk'], max_articles_per_source=5)
    market_collector = MarketDataCollector(pairs=['BTC/USDT'])
    
    # Test connections
    print("Testing connections...")
    news_valid = await news_collector.validate_connection()
    market_valid = await market_collector.validate_connection()
    
    print(f"News collector connection: {'✓' if news_valid else '✗'}")
    print(f"Market collector connection: {'✓' if market_valid else '✗'}")
    
    # Collect data
    if news_valid:
        print("\nCollecting news data...")
        news_data = await news_collector.safe_collect()
        print(f"Collected {len(news_data)} news items")
        
        if news_data:
            print(f"Sample news item: {news_data[0].title[:100]}...")
    
    if market_valid:
        print("\nCollecting market data...")
        market_data = await market_collector.safe_collect()
        print(f"Collected {len(market_data)} market data points")
        
        if market_data:
            print(f"Sample market data: {market_data[0].symbol} = ${market_data[0].price}")
    
    # Clean up
    await news_collector.close()
    await market_collector.close()


async def example_manager_usage():
    """Example of using the DataCollectionManager"""
    print("\n=== Data Collection Manager Example ===")
    
    # Create manager
    manager = DataCollectionManager()
    
    # Initialize (this registers all collectors)
    await manager.initialize()
    
    # Test all collectors
    print("Testing all collector connections...")
    test_results = await manager.test_collectors()
    
    for collector_name, is_valid in test_results.items():
        status = "✓" if is_valid else "✗"
        print(f"{collector_name}: {status}")
    
    # Force collect from all sources once
    print("\nForce collecting from all sources...")
    results = await manager.force_collect_all()
    
    for collector_name, item_count in results.items():
        print(f"{collector_name}: {item_count} items collected")
    
    # Get system status
    print("\nSystem status:")
    status = await manager.get_system_status()
    print(f"System running: {status.get('system_running', False)}")
    print(f"Active collectors: {status.get('scheduler', {}).get('active_collectors', 0)}")
    
    # Clean up
    await manager.stop()


async def example_queue_usage():
    """Example of queue-based data processing"""
    print("\n=== Queue-Based Processing Example ===")
    
    from data_collection.queue_manager import DataQueueManager
    
    # Create queue manager
    queue_manager = DataQueueManager()
    
    # Define a simple processor
    async def process_news_data(item):
        print(f"Processing news item: {item.get('data', {}).get('title', 'Unknown')[:50]}...")
    
    async def process_market_data(item):
        data = item.get('data', {})
        print(f"Processing market data: {data.get('symbol', 'Unknown')} = ${data.get('price', 0)}")
    
    # Register processors
    queue_manager.register_processor(queue_manager.NEWS_QUEUE, process_news_data)
    queue_manager.register_processor(queue_manager.MARKET_QUEUE, process_market_data)
    
    # Get queue statistics
    stats = await queue_manager.get_queue_stats()
    print("Queue statistics:")
    for queue_name, queue_stats in stats.items():
        if isinstance(queue_stats, dict):
            print(f"  {queue_name}: {queue_stats.get('length', 0)} items")


if __name__ == "__main__":
    print("Bitcoin Trading System - Data Collection Examples")
    print("=" * 50)
    
    # Run examples
    asyncio.run(example_basic_usage())
    asyncio.run(example_manager_usage())
    asyncio.run(example_queue_usage())
    
    print("\n" + "=" * 50)
    print("Examples completed!")
    print("\nNote: These examples require proper API keys and network connectivity.")
    print("Configure your .env file with the necessary API credentials to test with real data.")