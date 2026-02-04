"""
Simple test script for the new AI provider system
"""
import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_providers.factory import AIProviderFactory
from ai_providers.base import AIProviderError


async def test_provider_factory():
    """Test the AI provider factory"""
    print("=== Testing AI Provider Factory ===")
    
    # Test getting supported providers
    providers = AIProviderFactory.get_supported_providers()
    print(f"Supported providers: {list(providers.keys())}")
    
    for provider_type, info in providers.items():
        print(f"\n{info['name']}:")
        print(f"  Models: {', '.join(info['supported_models'][:3])}...")  # Show first 3 models
    
    return True


async def test_openai_provider_creation():
    """Test creating OpenAI provider"""
    print("\n=== Testing OpenAI Provider Creation ===")
    
    try:
        provider = AIProviderFactory.create_provider(
            provider_type="openai",
            api_key="test-key-123",
            model="gpt-4"
        )
        
        print(f"✓ Created OpenAI provider: {provider.get_provider_type().value}")
        print(f"✓ Model: {provider.get_model()}")
        print(f"✓ Supported models: {len(provider.get_supported_models())} models")
        
        # Test cost estimation
        cost = provider.estimate_cost(1000, 500)
        print(f"✓ Cost estimation for 1K input + 500 output tokens: ${cost:.4f}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error creating OpenAI provider: {str(e)}")
        return False


async def test_anthropic_provider_creation():
    """Test creating Anthropic provider"""
    print("\n=== Testing Anthropic Provider Creation ===")
    
    try:
        provider = AIProviderFactory.create_provider(
            provider_type="anthropic",
            api_key="test-key-123",
            model="claude-3-sonnet-20240229"
        )
        
        print(f"✓ Created Anthropic provider: {provider.get_provider_type().value}")
        print(f"✓ Model: {provider.get_model()}")
        print(f"✓ Supported models: {len(provider.get_supported_models())} models")
        
        # Test cost estimation
        cost = provider.estimate_cost(1000, 500)
        print(f"✓ Cost estimation for 1K input + 500 output tokens: ${cost:.4f}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error creating Anthropic provider: {str(e)}")
        return False


async def test_google_provider_creation():
    """Test creating Google provider"""
    print("\n=== Testing Google Provider Creation ===")
    
    try:
        provider = AIProviderFactory.create_provider(
            provider_type="google",
            api_key="test-key-123",
            model="gemini-pro"
        )
        
        print(f"✓ Created Google provider: {provider.get_provider_type().value}")
        print(f"✓ Model: {provider.get_model()}")
        print(f"✓ Supported models: {len(provider.get_supported_models())} models")
        
        # Test cost estimation
        cost = provider.estimate_cost(1000, 500)
        print(f"✓ Cost estimation for 1K input + 500 output tokens: ${cost:.4f}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error creating Google provider: {str(e)}")
        return False


async def test_deepseek_provider_creation():
    """Test creating Deepseek provider"""
    print("\n=== Testing Deepseek Provider Creation ===")
    
    try:
        provider = AIProviderFactory.create_provider(
            provider_type="deepseek",
            api_key="test-key-123",
            model="deepseek-chat"
        )
        
        print(f"✓ Created Deepseek provider: {provider.get_provider_type().value}")
        print(f"✓ Model: {provider.get_model()}")
        print(f"✓ Supported models: {len(provider.get_supported_models())} models")
        
        # Test cost estimation
        cost = provider.estimate_cost(1000, 500)
        print(f"✓ Cost estimation for 1K input + 500 output tokens: ${cost:.4f}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error creating Deepseek provider: {str(e)}")
        return False


async def test_doubao_provider_creation():
    """Test creating Doubao provider"""
    print("\n=== Testing Doubao Provider Creation ===")
    
    try:
        provider = AIProviderFactory.create_provider(
            provider_type="doubao",
            api_key="test-key-123",
            model="doubao-lite-4k"
        )
        
        print(f"✓ Created Doubao provider: {provider.get_provider_type().value}")
        print(f"✓ Model: {provider.get_model()}")
        print(f"✓ Supported models: {len(provider.get_supported_models())} models")
        
        # Test cost estimation
        cost = provider.estimate_cost(1000, 500)
        print(f"✓ Cost estimation for 1K input + 500 output tokens: ${cost:.4f}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error creating Doubao provider: {str(e)}")
        return False


async def test_error_handling():
    """Test error handling"""
    print("\n=== Testing Error Handling ===")
    
    # Test unsupported provider
    try:
        AIProviderFactory.create_provider(
            provider_type="unsupported",
            api_key="test-key",
            model="test-model"
        )
        print("✗ Should have raised error for unsupported provider")
        return False
    except AIProviderError as e:
        print(f"✓ Correctly caught error for unsupported provider: {e.message}")
    
    # Test invalid model
    try:
        AIProviderFactory.create_provider(
            provider_type="openai",
            api_key="test-key",
            model="invalid-model"
        )
        print("✗ Should have raised error for invalid model")
        return False
    except AIProviderError as e:
        print(f"✓ Correctly caught error for invalid model: {e.message}")
    
    # Test missing API key
    try:
        AIProviderFactory.create_provider(
            provider_type="openai",
            api_key="",
            model="gpt-4"
        )
        print("✗ Should have raised error for missing API key")
        return False
    except AIProviderError as e:
        print(f"✓ Correctly caught error for missing API key: {e.message}")
    
    return True


async def test_config_creation():
    """Test creating provider from config"""
    print("\n=== Testing Config-Based Creation ===")
    
    config = {
        "provider": "openai",
        "api_key": "test-key-123",
        "model": "gpt-4",
        "organization": "test-org"
    }
    
    try:
        provider = AIProviderFactory.create_from_config(config)
        print(f"✓ Created provider from config: {provider.get_provider_type().value}")
        print(f"✓ Model: {provider.get_model()}")
        return True
    except Exception as e:
        print(f"✗ Error creating provider from config: {str(e)}")
        return False


async def main():
    """Main test function"""
    print("=== AI Provider System Test ===")
    print("Testing the new model-agnostic AI provider system...\n")
    
    tests = [
        test_provider_factory,
        test_openai_provider_creation,
        test_anthropic_provider_creation,
        test_google_provider_creation,
        test_deepseek_provider_creation,
        test_doubao_provider_creation,
        test_error_handling,
        test_config_creation
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {str(e)}")
            results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print(f"\n=== Test Summary ===")
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! The AI provider system is working correctly.")
        print("\nNext steps:")
        print("1. Configure your API keys in the .env file")
        print("2. Set AI_PROVIDER to your preferred provider (openai, anthropic, google)")
        print("3. Use ModelAgnosticNewsAnalyzer in your application")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)