"""
Example usage of the News Analysis module
"""
import asyncio
from datetime import datetime
from backend.core.data_models import NewsItem, generate_id
from backend.news_analysis import NewsAnalyzer


async def main():
    """Example usage of the news analysis module"""
    
    # Initialize the news analyzer
    analyzer = NewsAnalyzer()
    
    # Create sample news items
    sample_news = [
        NewsItem(
            id=generate_id(),
            title="Bitcoin ETF Approved by SEC",
            content="The Securities and Exchange Commission has approved the first Bitcoin ETF, marking a significant milestone for cryptocurrency adoption in traditional finance.",
            source="CoinDesk",
            published_at=datetime.utcnow(),
            url="https://example.com/btc-etf-approved"
        ),
        NewsItem(
            id=generate_id(),
            title="Major Bank Announces Bitcoin Trading Services",
            content="A leading global bank announced it will offer Bitcoin trading services to institutional clients, signaling growing acceptance of cryptocurrency in traditional banking.",
            source="Reuters",
            published_at=datetime.utcnow(),
            url="https://example.com/bank-btc-trading"
        ),
        NewsItem(
            id=generate_id(),
            title="Bitcoin Network Experiences High Transaction Fees",
            content="Bitcoin transaction fees have spiked to multi-month highs due to increased network congestion, raising concerns about scalability.",
            source="CoinTelegraph",
            published_at=datetime.utcnow(),
            url="https://example.com/btc-high-fees"
        )
    ]
    
    print("Starting news analysis...")
    
    # Analyze news items in batch
    analyzed_items = await analyzer.analyze_batch(sample_news, max_concurrent=2)
    
    # Display results
    for item in analyzed_items:
        print(f"\n--- Analysis Results for: {item.title} ---")
        print(f"Sentiment Score: {item.sentiment_score}")
        if item.impact_assessment:
            print(f"Short-term Impact: {item.impact_assessment.short_term_impact}")
            print(f"Long-term Impact: {item.impact_assessment.long_term_impact}")
            print(f"Confidence: {item.impact_assessment.impact_confidence}")
            print(f"Reasoning: {item.impact_assessment.reasoning}")
    
    # Generate market summary
    market_summary = await analyzer.generate_market_summary(analyzed_items)
    print(f"\n--- Market Summary ---")
    print(f"Overall Sentiment: {market_summary['overall_sentiment']}")
    print(f"Short-term Outlook: {market_summary['short_term_outlook']}")
    print(f"Long-term Outlook: {market_summary['long_term_outlook']}")
    print(f"Total Articles: {market_summary['total_articles']}")
    
    # Check for items needing review
    review_queue = analyzer.get_review_queue()
    if review_queue:
        print(f"\n--- Items Needing Human Review: {len(review_queue)} ---")
        for review_item in review_queue:
            print(f"- {review_item['news_item'].title}: {review_item['reason']}")
    
    # Get analysis statistics
    stats = analyzer.get_analysis_statistics(analyzed_items)
    print(f"\n--- Analysis Statistics ---")
    print(f"Total Analyzed: {stats['total_analyzed']}")
    if 'impact_statistics' in stats:
        impact_stats = stats['impact_statistics']
        print(f"Average Short-term Impact: {impact_stats.get('average_short_term_impact', 'N/A')}")
        print(f"Average Long-term Impact: {impact_stats.get('average_long_term_impact', 'N/A')}")
        print(f"Anomaly Rate: {impact_stats.get('anomaly_rate', 'N/A')}")


if __name__ == "__main__":
    asyncio.run(main())