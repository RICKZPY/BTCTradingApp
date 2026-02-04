"""
Base AI Provider Interface
Abstract base class for all AI providers
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum


class AIProviderType(Enum):
    """Supported AI provider types"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    AZURE_OPENAI = "azure_openai"
    HUGGINGFACE = "huggingface"
    DEEPSEEK = "deepseek"
    DOUBAO = "doubao"  # 字节跳动豆包（原火山方舟）


@dataclass
class AIResponse:
    """Standard response format from AI providers"""
    content: str
    model: str
    provider: str
    tokens_used: Optional[int] = None
    cost: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class AIProviderError(Exception):
    """Base exception for AI provider errors"""
    def __init__(self, message: str, provider: str, error_code: Optional[str] = None):
        self.message = message
        self.provider = provider
        self.error_code = error_code
        super().__init__(f"[{provider}] {message}")


class AIProvider(ABC):
    """Abstract base class for AI providers"""
    
    def __init__(self, api_key: str, model: str, **kwargs):
        """
        Initialize AI provider
        
        Args:
            api_key: API key for the provider
            model: Model name to use
            **kwargs: Additional provider-specific configuration
        """
        self.api_key = api_key
        self.model = model
        self.config = kwargs
        self._validate_config()
    
    @abstractmethod
    def _validate_config(self) -> None:
        """Validate provider configuration"""
        pass
    
    @abstractmethod
    async def generate_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 1000,
        **kwargs
    ) -> AIResponse:
        """
        Generate completion from the AI model
        
        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters
            
        Returns:
            AIResponse with the completion
        """
        pass
    
    @abstractmethod
    async def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 1000,
        **kwargs
    ) -> AIResponse:
        """
        Generate chat completion from the AI model
        
        Args:
            messages: List of chat messages [{"role": "user/assistant/system", "content": "..."}]
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters
            
        Returns:
            AIResponse with the completion
        """
        pass
    
    @abstractmethod
    def get_provider_type(self) -> AIProviderType:
        """Get the provider type"""
        pass
    
    @abstractmethod
    def get_supported_models(self) -> List[str]:
        """Get list of supported models for this provider"""
        pass
    
    @abstractmethod
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Estimate cost for the given token usage
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Estimated cost in USD
        """
        pass
    
    def get_model(self) -> str:
        """Get current model name"""
        return self.model
    
    def set_model(self, model: str) -> None:
        """Set model name"""
        if model not in self.get_supported_models():
            raise AIProviderError(
                f"Model '{model}' not supported by {self.get_provider_type().value}",
                self.get_provider_type().value
            )
        self.model = model
    
    async def test_connection(self) -> bool:
        """
        Test connection to the AI provider
        
        Returns:
            True if connection is successful
        """
        try:
            response = await self.generate_completion(
                "Test connection. Respond with 'OK'.",
                max_tokens=10
            )
            return "OK" in response.content.upper()
        except Exception:
            return False