"""
Anthropic Provider Implementation
"""
import asyncio
from typing import Dict, Any, Optional, List
import httpx

from .base import AIProvider, AIResponse, AIProviderError, AIProviderType


class AnthropicProvider(AIProvider):
    """Anthropic (Claude) provider implementation"""
    
    # Model pricing per 1K tokens (input, output) in USD
    MODEL_PRICING = {
        "claude-3-opus-20240229": (0.015, 0.075),
        "claude-3-sonnet-20240229": (0.003, 0.015),
        "claude-3-haiku-20240307": (0.00025, 0.00125),
        "claude-2.1": (0.008, 0.024),
        "claude-2.0": (0.008, 0.024),
        "claude-instant-1.2": (0.0008, 0.0024),
    }
    
    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229", **kwargs):
        """
        Initialize Anthropic provider
        
        Args:
            api_key: Anthropic API key
            model: Model name (default: claude-3-sonnet-20240229)
            **kwargs: Additional configuration
        """
        super().__init__(api_key, model, **kwargs)
        self.base_url = kwargs.get("base_url", "https://api.anthropic.com")
        self.version = kwargs.get("version", "2023-06-01")
    
    def _validate_config(self) -> None:
        """Validate Anthropic configuration"""
        if not self.api_key:
            raise AIProviderError("Anthropic API key is required", "anthropic")
        
        if self.model not in self.get_supported_models():
            raise AIProviderError(f"Model '{self.model}' not supported", "anthropic")
    
    async def generate_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 1000,
        **kwargs
    ) -> AIResponse:
        """Generate completion using Anthropic"""
        messages = [{"role": "user", "content": prompt}]
        return await self.generate_chat_completion(
            messages, temperature, max_tokens, system=system_prompt, **kwargs
        )
    
    async def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 1000,
        **kwargs
    ) -> AIResponse:
        """Generate chat completion using Anthropic"""
        try:
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": self.version,
                "content-type": "application/json"
            }
            
            # Prepare request body
            body = {
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages
            }
            
            # Add system prompt if provided
            if "system" in kwargs:
                body["system"] = kwargs["system"]
            
            # Add other parameters
            for key, value in kwargs.items():
                if key not in ["system"]:
                    body[key] = value
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/v1/messages",
                    headers=headers,
                    json=body,
                    timeout=60.0
                )
                
                if response.status_code != 200:
                    error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                    error_message = error_data.get("error", {}).get("message", f"HTTP {response.status_code}")
                    raise AIProviderError(f"Anthropic API error: {error_message}", "anthropic", str(response.status_code))
                
                data = response.json()
                
                # Extract content from response
                content = ""
                if data.get("content") and len(data["content"]) > 0:
                    content = data["content"][0].get("text", "")
                
                # Calculate tokens and cost
                input_tokens = data.get("usage", {}).get("input_tokens", 0)
                output_tokens = data.get("usage", {}).get("output_tokens", 0)
                total_tokens = input_tokens + output_tokens
                cost = self.estimate_cost(input_tokens, output_tokens)
                
                return AIResponse(
                    content=content,
                    model=self.model,
                    provider="anthropic",
                    tokens_used=total_tokens,
                    cost=cost,
                    metadata={
                        "stop_reason": data.get("stop_reason"),
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                    }
                )
                
        except httpx.RequestError as e:
            raise AIProviderError(f"Network error: {str(e)}", "anthropic")
        except Exception as e:
            if isinstance(e, AIProviderError):
                raise
            raise AIProviderError(f"Unexpected error: {str(e)}", "anthropic")
    
    def get_provider_type(self) -> AIProviderType:
        """Get provider type"""
        return AIProviderType.ANTHROPIC
    
    def get_supported_models(self) -> List[str]:
        """Get supported Anthropic models"""
        return list(self.MODEL_PRICING.keys())
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost for Anthropic API usage"""
        if self.model not in self.MODEL_PRICING:
            return 0.0
        
        input_price, output_price = self.MODEL_PRICING[self.model]
        return (input_tokens / 1000 * input_price) + (output_tokens / 1000 * output_price)