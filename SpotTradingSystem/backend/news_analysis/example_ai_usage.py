"""
Example usage of Model-Agnostic News Analyzer
Demonstrates how to use different AI providers for news analysis
"""
import asyncio
import sys
import os
from datetime import datetime

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from news_analysis.ai_analyzer import ModelAgnosticNewsAnalyzer
from core.data_models import NewsItem
from ai_providers.factory import AIProviderFactory


def create_sample_news_item() -> NewsItem:
    """Create a sample news item for testing"""
    return NewsItem(
        id="test-001",
        title="Bitcoin Reaches New All-Time High as Institutional Adoption Grows",
        content="""
        Bitcoin has reached a new all-time high of $75,000 as major institutional investors 
        continue to add cryptocurrency to their portfolios. The surge comes after several 
        Fortune 500 companies announced plans to accept Bitcoin as payment and hold it as 
        a treasury asset.
        
        Market analysts attribute the price increase to growing institutional adoption, 
        regulatory clarity in major markets, and increasing retail investor interest. 
        The cryptocurrency has gained over 150% this year, outperforming traditional 
        assets like stocks and gold.
        
        "We're seeing unprecedented institutional demand," said a senior analyst at a 
        major investment firm. "This isn't just speculation anymore - it's becoming 
        a legitimate asset class."
        """,
        source="CryptoNews",
        published_at=datetime.now(),
        url="https://example.com/bitcoin-ath"
    )


async def test_openai_provider():
    """Test OpenAI provider"""
    print("=== Testing OpenAI Provider ===")
    
    try:
        # You need to set your OpenAI API key in environment or config
        analyzer = ModelAgnosticNewsAnalyzer(
            provider_type="openai",
            model="gpt-4",
            # api_key="your-openai-api-key"  # Or set in config/env
        )
        
        news_item = create_sample_news_item()
        analyzed_item = await analyzer.analyze_news_item(news_item)
        
        print(f"Sentiment Score: {analyzed_item.sentiment_score}")
        print(f"Short-term Impact: {analyzed_item.impact_assessment.short_term_impact}")
        print(f"Long-term Impact: {analyzed_item.impact_assessment.long_term_impact}")
        print(f"Reasoning: {analyzed_item.impact_assessment.reasoning[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"OpenAI test failed: {str(e)}")
        return False


async def test_anthropic_provider():
    """Test Anthropic provider"""
    print("\n=== Testing Anthropic Provider ===")
    
    try:
        # You need to set your Anthropic API key
        analyzer = ModelAgnosticNewsAnalyzer(
            provider_type="anthropic",
            model="claude-3-sonnet-20240229",
            # api_key="your-anthropic-api-key"  # Or set in config/env
        )
        
        news_item = create_sample_news_item()
        analyzed_item = await analyzer.analyze_news_item(news_item)
        
        print(f"Sentiment Score: {analyzed_item.sentiment_score}")
        print(f"Short-term Impact: {analyzed_item.impact_assessment.short_term_impact}")
        print(f"Long-term Impact: {analyzed_item.impact_assessment.long_term_impact}")
        print(f"Reasoning: {analyzed_item.impact_assessment.reasoning[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"Anthropic test failed: {str(e)}")
        return False


async def test_google_provider():
    """Test Google AI provider"""
    print("\n=== Testing Google AI Provider ===")
    
    try:
        # You need to set your Google AI API key
        analyzer = ModelAgnosticNewsAnalyzer(
            provider_type="google",
            model="gemini-pro",
            # api_key="your-google-ai-api-key"  # Or set in config/env
        )
        
        news_item = create_sample_news_item()
        analyzed_item = await analyzer.analyze_news_item(news_item)
        
        print(f"Sentiment Score: {analyzed_item.sentiment_score}")
        print(f"Short-term Impact: {analyzed_item.impact_assessment.short_term_impact}")
        print(f"Long-term Impact: {analyzed_item.impact_assessment.long_term_impact}")
        print(f"Reasoning: {analyzed_item.impact_assessment.reasoning[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"Google AI test failed: {str(e)}")
        return False


async def test_fallback_functionality():
    """Test fallback functionality"""
    print("\n=== Testing Fallback Functionality ===")
    
    try:
        # Create analyzer with fallback
        analyzer = ModelAgnosticNewsAnalyzer(
            provider_type="openai",
            model="gpt-4",
            fallback_provider="anthropic",
            # You would need API keys for both providers
        )
        
        # Test provider info
        provider_info = analyzer.get_provider_info()
        print(f"Primary Provider: {provider_info['primary_provider']}")
        print(f"Fallback Provider: {provider_info['fallback_provider']}")
        
        # Test connection to providers
        connection_results = await analyzer.test_providers()
        print(f"Connection Tests: {connection_results}")
        
        return True
        
    except Exception as e:
        print(f"Fallback test failed: {str(e)}")
        return False


async def test_batch_analysis():
    """Test batch analysis with multiple news items"""
    print("\n=== Testing Batch Analysis ===")
    
    try:
        analyzer = ModelAgnosticNewsAnalyzer(
            provider_type="openai",  # Change to your preferred provider
            model="gpt-4"
        )
        
        # Create multiple news items
        news_items = []
        for i in range(3):
            item = create_sample_news_item()
            item.id = f"test-{i:03d}"
            item.title = f"Bitcoin News Item {i+1}"
            news_items.append(item)
        
        # Analyze batch
        analyzed_items = await analyzer.analyze_batch(news_items, max_concurrent=2)
        
        print(f"Analyzed {len(analyzed_items)} news items")
        for item in analyzed_items:
            print(f"  {item.id}: Sentiment={item.sentiment_score}, "
                  f"Impact={item.impact_assessment.short_term_impact:.2f}")
        
        # Generate market summary
        summary = await analyzer.generate_market_summary(analyzed_items)
        print(f"\nMarket Summary:")
        print(f"  Overall Sentiment: {summary['overall_sentiment']}")
        print(f"  Short-term Outlook: {summary['short_term_outlook']}")
        print(f"  AI Provider: {summary['ai_provider']}")
        print(f"  AI Model: {summary['ai_model']}")
        
        return True
        
    except Exception as e:
        print(f"Batch analysis test failed: {str(e)}")
        return False


async def show_supported_providers():
    """Show all supported providers and their models"""
    print("\n=== Supported AI Providers ===")
    
    providers = AIProviderFactory.get_supported_providers()
    
    for provider_type, info in providers.items():
        print(f"\n{info['name']}:")
        print(f"  Type: {provider_type}")
        print(f"  Supported Models: {', '.join(info['supported_models'])}")


async def main():
    """Main example function"""
    print("=== Model-Agnostic News Analyzer Example ===")
    
    # Show supported providers
    await show_supported_providers()
    
    # Note: You need to configure API keys in your environment or config file
    print("\n" + "="*50)
    print("NOTE: To run these tests, you need to configure API keys")
    print("Set them in your .env file or config.py:")
    print("  OPENAI_API_KEY=your-openai-key")
    print("  ANTHROPIC_API_KEY=your-anthropic-key") 
    print("  GOOGLE_API_KEY=your-google-key")
    print("="*50)
    
    # Test different providers (uncomment the ones you have API keys for)
    
    # await test_openai_provider()
    # await test_anthropic_provider()
    # await test_google_provider()
    # await test_fallback_functionality()
    # await test_batch_analysis()
    
    print("\n=== Example completed! ===")
    print("Uncomment the test functions above and configure your API keys to run actual tests.")


if __name__ == "__main__":
    asyncio.run(main())