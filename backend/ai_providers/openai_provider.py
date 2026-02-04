"""
OpenAI Provider Implementation
"""
import asyncio
from typing import Dict, Any, Optional, List
import openai

from .base import AIProvider, AIResponse, AIProviderError, AIProviderType


class OpenAIProvider(AIProvider):
    """OpenAI provider implementation"""
    
    # Model pricing per 1K tokens (input, output) in USD
    MODEL_PRICING = {
        "gpt-4": (0.03, 0.06),
        "gpt-4-32k": (0.06, 0.12),
        "gpt-4-turbo": (0.01, 0.03),
        "gpt-4-turbo-preview": (0.01, 0.03),
        "gpt-3.5-turbo": (0.0015, 0.002),
        "gpt-3.5-turbo-16k": (0.003, 0.004),
    }
    
    def __init__(self, api_key: str, model: str = "gpt-4", **kwargs):
        """
        Initialize OpenAI provider
        
        Args:
            api_key: OpenAI API key
            model: Model name (default: gpt-4)
            **kwargs: Additional configuration (base_url, organization, etc.)
        """
        super().__init__(api_key, model, **kwargs)
        
        # Set OpenAI API key
        openai.api_key = api_key
        
        # Set organization if provided
        if "organization" in kwargs:
            openai.organization = kwargs["organization"]
    
    def _validate_config(self) -> None:
        """Validate OpenAI configuration"""
        if not self.api_key:
            raise AIProviderError("OpenAI API key is required", "openai")
        
        if self.model not in self.get_supported_models():
            raise AIProviderError(f"Model '{self.model}' not supported", "openai")
    
    async def generate_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 1000,
        **kwargs
    ) -> AIResponse:
        """Generate completion using OpenAI"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        return await self.generate_chat_completion(
            messages, temperature, max_tokens, **kwargs
        )
    
    async def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 1000,
        **kwargs
    ) -> AIResponse:
        """Generate chat completion using OpenAI"""
        try:
            # Use the older OpenAI API format for version 0.27.10
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            content = response.choices[0].message.content
            usage = response.get('usage', {})
            
            return AIResponse(
                content=content,
                model=self.model,
                provider="openai",
                tokens_used=usage.get('total_tokens'),
                cost=self._calculate_cost(usage) if usage else None,
                metadata={
                    "finish_reason": response.choices[0].get('finish_reason'),
                    "prompt_tokens": usage.get('prompt_tokens'),
                    "completion_tokens": usage.get('completion_tokens'),
                }
            )
            
        except openai.error.OpenAIError as e:
            raise AIProviderError(f"OpenAI API error: {str(e)}", "openai", getattr(e, 'code', None))
        except Exception as e:
            raise AIProviderError(f"Unexpected error: {str(e)}", "openai")
    
    def get_provider_type(self) -> AIProviderType:
        """Get provider type"""
        return AIProviderType.OPENAI
    
    def get_supported_models(self) -> List[str]:
        """Get supported OpenAI models"""
        return list(self.MODEL_PRICING.keys())
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost for OpenAI API usage"""
        if self.model not in self.MODEL_PRICING:
            return 0.0
        
        input_price, output_price = self.MODEL_PRICING[self.model]
        return (input_tokens / 1000 * input_price) + (output_tokens / 1000 * output_price)
    
    def _calculate_cost(self, usage) -> float:
        """Calculate actual cost from usage"""
        if not usage or self.model not in self.MODEL_PRICING:
            return 0.0
        
        input_price, output_price = self.MODEL_PRICING[self.model]
        prompt_tokens = usage.get('prompt_tokens', 0)
        completion_tokens = usage.get('completion_tokens', 0)
        return (prompt_tokens / 1000 * input_price) + (completion_tokens / 1000 * output_price)