"""
AI Provider Factory
Factory class for creating AI provider instances
"""
from typing import Dict, Any, Optional
import logging

from .base import AIProvider, AIProviderType, AIProviderError
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .google_provider import GoogleProvider
from .deepseek_provider import DeepseekProvider
from .doubao_provider import DoubaoProvider

logger = logging.getLogger(__name__)


class AIProviderFactory:
    """Factory for creating AI provider instances"""
    
    _providers = {
        AIProviderType.OPENAI: OpenAIProvider,
        AIProviderType.ANTHROPIC: AnthropicProvider,
        AIProviderType.GOOGLE: GoogleProvider,
        AIProviderType.DEEPSEEK: DeepseekProvider,
        AIProviderType.DOUBAO: DoubaoProvider,
    }
    
    @classmethod
    def create_provider(
        self,
        provider_type: str,
        api_key: str,
        model: str,
        **kwargs
    ) -> AIProvider:
        """
        Create an AI provider instance
        
        Args:
            provider_type: Type of provider ("openai", "anthropic", "google")
            api_key: API key for the provider
            model: Model name to use
            **kwargs: Additional provider-specific configuration
            
        Returns:
            AIProvider instance
            
        Raises:
            AIProviderError: If provider type is not supported
        """
        try:
            provider_enum = AIProviderType(provider_type.lower())
        except ValueError:
            supported_types = [t.value for t in AIProviderType]
            raise AIProviderError(
                f"Unsupported provider type '{provider_type}'. Supported types: {supported_types}",
                "factory"
            )
        
        if provider_enum not in self._providers:
            raise AIProviderError(
                f"Provider '{provider_type}' not implemented yet",
                "factory"
            )
        
        provider_class = self._providers[provider_enum]
        
        try:
            return provider_class(api_key=api_key, model=model, **kwargs)
        except Exception as e:
            logger.error(f"Failed to create {provider_type} provider: {str(e)}")
            raise AIProviderError(
                f"Failed to create {provider_type} provider: {str(e)}",
                "factory"
            )
    
    @classmethod
    def get_supported_providers(cls) -> Dict[str, Dict[str, Any]]:
        """
        Get information about supported providers
        
        Returns:
            Dictionary with provider information
        """
        info = {}
        
        for provider_type, provider_class in cls._providers.items():
            # Create a temporary instance to get model info
            try:
                temp_instance = provider_class("dummy_key", "dummy_model")
                models = temp_instance.get_supported_models()
            except:
                models = []
            
            info[provider_type.value] = {
                "name": provider_type.value.title(),
                "supported_models": models,
                "class": provider_class.__name__
            }
        
        return info
    
    @classmethod
    def create_from_config(cls, config: Dict[str, Any]) -> AIProvider:
        """
        Create provider from configuration dictionary
        
        Args:
            config: Configuration dictionary with keys:
                - provider: Provider type
                - api_key: API key
                - model: Model name
                - **other provider-specific options
                
        Returns:
            AIProvider instance
        """
        required_keys = ["provider", "api_key", "model"]
        missing_keys = [key for key in required_keys if key not in config]
        
        if missing_keys:
            raise AIProviderError(
                f"Missing required configuration keys: {missing_keys}",
                "factory"
            )
        
        provider_type = config.pop("provider")
        api_key = config.pop("api_key")
        model = config.pop("model")
        
        return cls.create_provider(
            provider_type=provider_type,
            api_key=api_key,
            model=model,
            **config
        )
    
    @classmethod
    async def test_provider_connection(
        cls,
        provider_type: str,
        api_key: str,
        model: str,
        **kwargs
    ) -> bool:
        """
        Test connection to a provider
        
        Args:
            provider_type: Type of provider
            api_key: API key
            model: Model name
            **kwargs: Additional configuration
            
        Returns:
            True if connection is successful
        """
        try:
            provider = cls.create_provider(provider_type, api_key, model, **kwargs)
            return await provider.test_connection()
        except Exception as e:
            logger.error(f"Connection test failed for {provider_type}: {str(e)}")
            return False