"""
Tests for AI Providers
"""
import pytest
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_providers.base import AIProvider, AIResponse, AIProviderError, AIProviderType
from ai_providers.openai_provider import OpenAIProvider
from ai_providers.anthropic_provider import AnthropicProvider
from ai_providers.google_provider import GoogleProvider
from ai_providers.deepseek_provider import DeepseekProvider
from ai_providers.doubao_provider import DoubaoProvider
from ai_providers.factory import AIProviderFactory


class TestAIProviderFactory:
    """Test AI provider factory"""
    
    def test_get_supported_providers(self):
        """Test getting supported providers"""
        providers = AIProviderFactory.get_supported_providers()
        
        assert "openai" in providers
        assert "anthropic" in providers
        assert "google" in providers
        assert "deepseek" in providers
        assert "doubao" in providers
        
        # Check structure
        for provider_type, info in providers.items():
            assert "name" in info
            assert "supported_models" in info
            assert "class" in info
    
    def test_create_openai_provider(self):
        """Test creating OpenAI provider"""
        provider = AIProviderFactory.create_provider(
            provider_type="openai",
            api_key="test-key",
            model="gpt-4"
        )
        
        assert isinstance(provider, OpenAIProvider)
        assert provider.get_provider_type() == AIProviderType.OPENAI
        assert provider.get_model() == "gpt-4"
    
    def test_create_anthropic_provider(self):
        """Test creating Anthropic provider"""
        provider = AIProviderFactory.create_provider(
            provider_type="anthropic",
            api_key="test-key",
            model="claude-3-sonnet-20240229"
        )
        
        assert isinstance(provider, AnthropicProvider)
        assert provider.get_provider_type() == AIProviderType.ANTHROPIC
        assert provider.get_model() == "claude-3-sonnet-20240229"
    
    def test_create_google_provider(self):
        """Test creating Google provider"""
        provider = AIProviderFactory.create_provider(
            provider_type="google",
            api_key="test-key",
            model="gemini-pro"
        )
        
        assert isinstance(provider, GoogleProvider)
        assert provider.get_provider_type() == AIProviderType.GOOGLE
        assert provider.get_model() == "gemini-pro"
    
    def test_create_deepseek_provider(self):
        """Test creating Deepseek provider"""
        provider = AIProviderFactory.create_provider(
            provider_type="deepseek",
            api_key="test-key",
            model="deepseek-chat"
        )
        
        assert isinstance(provider, DeepseekProvider)
        assert provider.get_provider_type() == AIProviderType.DEEPSEEK
        assert provider.get_model() == "deepseek-chat"
    
    def test_create_doubao_provider(self):
        """Test creating Doubao provider"""
        provider = AIProviderFactory.create_provider(
            provider_type="doubao",
            api_key="test-key",
            model="doubao-lite-4k"
        )
        
        assert isinstance(provider, DoubaoProvider)
        assert provider.get_provider_type() == AIProviderType.DOUBAO
        assert provider.get_model() == "doubao-lite-4k"
    
    def test_unsupported_provider(self):
        """Test creating unsupported provider"""
        with pytest.raises(AIProviderError):
            AIProviderFactory.create_provider(
                provider_type="unsupported",
                api_key="test-key",
                model="test-model"
            )
    
    def test_create_from_config(self):
        """Test creating provider from config"""
        config = {
            "provider": "openai",
            "api_key": "test-key",
            "model": "gpt-4",
            "organization": "test-org"
        }
        
        provider = AIProviderFactory.create_from_config(config)
        
        assert isinstance(provider, OpenAIProvider)
        assert provider.get_model() == "gpt-4"
    
    def test_create_from_config_missing_keys(self):
        """Test creating provider from config with missing keys"""
        config = {
            "provider": "openai",
            # Missing api_key and model
        }
        
        with pytest.raises(AIProviderError):
            AIProviderFactory.create_from_config(config)


class TestOpenAIProvider:
    """Test OpenAI provider"""
    
    def test_initialization(self):
        """Test OpenAI provider initialization"""
        provider = OpenAIProvider(api_key="test-key", model="gpt-4")
        
        assert provider.api_key == "test-key"
        assert provider.model == "gpt-4"
        assert provider.get_provider_type() == AIProviderType.OPENAI
    
    def test_supported_models(self):
        """Test getting supported models"""
        provider = OpenAIProvider(api_key="test-key", model="gpt-4")
        models = provider.get_supported_models()
        
        assert "gpt-4" in models
        assert "gpt-3.5-turbo" in models
        assert isinstance(models, list)
    
    def test_cost_estimation(self):
        """Test cost estimation"""
        provider = OpenAIProvider(api_key="test-key", model="gpt-4")
        
        # Test with known pricing
        cost = provider.estimate_cost(1000, 1000)  # 1K input, 1K output tokens
        assert cost > 0
        assert isinstance(cost, float)
    
    def test_invalid_model(self):
        """Test initialization with invalid model"""
        with pytest.raises(AIProviderError):
            OpenAIProvider(api_key="test-key", model="invalid-model")
    
    def test_missing_api_key(self):
        """Test initialization without API key"""
        with pytest.raises(AIProviderError):
            OpenAIProvider(api_key="", model="gpt-4")


class TestAnthropicProvider:
    """Test Anthropic provider"""
    
    def test_initialization(self):
        """Test Anthropic provider initialization"""
        provider = AnthropicProvider(api_key="test-key", model="claude-3-sonnet-20240229")
        
        assert provider.api_key == "test-key"
        assert provider.model == "claude-3-sonnet-20240229"
        assert provider.get_provider_type() == AIProviderType.ANTHROPIC
    
    def test_supported_models(self):
        """Test getting supported models"""
        provider = AnthropicProvider(api_key="test-key", model="claude-3-sonnet-20240229")
        models = provider.get_supported_models()
        
        assert "claude-3-sonnet-20240229" in models
        assert "claude-3-opus-20240229" in models
        assert isinstance(models, list)
    
    def test_cost_estimation(self):
        """Test cost estimation"""
        provider = AnthropicProvider(api_key="test-key", model="claude-3-sonnet-20240229")
        
        cost = provider.estimate_cost(1000, 1000)
        assert cost > 0
        assert isinstance(cost, float)


class TestGoogleProvider:
    """Test Google provider"""
    
    def test_initialization(self):
        """Test Google provider initialization"""
        provider = GoogleProvider(api_key="test-key", model="gemini-pro")
        
        assert provider.api_key == "test-key"
        assert provider.model == "gemini-pro"
        assert provider.get_provider_type() == AIProviderType.GOOGLE
    
    def test_supported_models(self):
        """Test getting supported models"""
        provider = GoogleProvider(api_key="test-key", model="gemini-pro")
        models = provider.get_supported_models()
        
        assert "gemini-pro" in models
        assert "gemini-1.5-pro" in models
        assert isinstance(models, list)
    
    def test_cost_estimation(self):
        """Test cost estimation"""
        provider = GoogleProvider(api_key="test-key", model="gemini-pro")
        
        cost = provider.estimate_cost(1000, 1000)
        assert cost > 0
        assert isinstance(cost, float)


class TestDeepseekProvider:
    """Test Deepseek provider"""
    
    def test_initialization(self):
        """Test Deepseek provider initialization"""
        provider = DeepseekProvider(api_key="test-key", model="deepseek-chat")
        
        assert provider.api_key == "test-key"
        assert provider.model == "deepseek-chat"
        assert provider.get_provider_type() == AIProviderType.DEEPSEEK
    
    def test_supported_models(self):
        """Test getting supported models"""
        provider = DeepseekProvider(api_key="test-key", model="deepseek-chat")
        models = provider.get_supported_models()
        
        assert "deepseek-chat" in models
        assert "deepseek-coder" in models
        assert isinstance(models, list)
    
    def test_cost_estimation(self):
        """Test cost estimation"""
        provider = DeepseekProvider(api_key="test-key", model="deepseek-chat")
        
        cost = provider.estimate_cost(1000, 1000)
        assert cost > 0
        assert isinstance(cost, float)
    
    def test_invalid_model(self):
        """Test initialization with invalid model"""
        with pytest.raises(AIProviderError):
            DeepseekProvider(api_key="test-key", model="invalid-model")
    
    def test_missing_api_key(self):
        """Test initialization without API key"""
        with pytest.raises(AIProviderError):
            DeepseekProvider(api_key="", model="deepseek-chat")


class TestDoubaoProvider:
    """Test Doubao provider"""
    
    def test_initialization(self):
        """Test Doubao provider initialization"""
        provider = DoubaoProvider(api_key="test-key", model="doubao-lite-4k")
        
        assert provider.api_key == "test-key"
        assert provider.model == "doubao-lite-4k"
        assert provider.get_provider_type() == AIProviderType.DOUBAO
    
    def test_supported_models(self):
        """Test getting supported models"""
        provider = DoubaoProvider(api_key="test-key", model="doubao-lite-4k")
        models = provider.get_supported_models()
        
        assert "doubao-lite-4k" in models
        assert "doubao-pro-4k" in models
        assert isinstance(models, list)
    
    def test_cost_estimation(self):
        """Test cost estimation"""
        provider = DoubaoProvider(api_key="test-key", model="doubao-lite-4k")
        
        cost = provider.estimate_cost(1000, 1000)
        assert cost > 0
        assert isinstance(cost, float)
    
    def test_invalid_model(self):
        """Test initialization with invalid model"""
        with pytest.raises(AIProviderError):
            DoubaoProvider(api_key="test-key", model="invalid-model")
    
    def test_missing_api_key(self):
        """Test initialization without API key"""
        with pytest.raises(AIProviderError):
            DoubaoProvider(api_key="", model="doubao-lite-4k")


class TestAIResponse:
    """Test AI response data structure"""
    
    def test_ai_response_creation(self):
        """Test creating AI response"""
        response = AIResponse(
            content="Test response",
            model="gpt-4",
            provider="openai",
            tokens_used=100,
            cost=0.01,
            metadata={"test": "data"}
        )
        
        assert response.content == "Test response"
        assert response.model == "gpt-4"
        assert response.provider == "openai"
        assert response.tokens_used == 100
        assert response.cost == 0.01
        assert response.metadata["test"] == "data"


class TestAIProviderError:
    """Test AI provider error"""
    
    def test_error_creation(self):
        """Test creating AI provider error"""
        error = AIProviderError("Test error", "openai", "test_code")
        
        assert error.message == "Test error"
        assert error.provider == "openai"
        assert error.error_code == "test_code"
        assert str(error) == "[openai] Test error"


if __name__ == "__main__":
    pytest.main([__file__])