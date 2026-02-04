"""
Deepseek Provider Implementation
"""
import asyncio
from typing import Dict, Any, Optional, List
import httpx

from .base import AIProvider, AIResponse, AIProviderError, AIProviderType


class DeepseekProvider(AIProvider):
    """Deepseek AI provider implementation"""
    
    # Model pricing per 1K tokens (input, output) in USD
    # Deepseek pricing is very competitive
    MODEL_PRICING = {
        "deepseek-chat": (0.0001, 0.0002),  # 非常便宜的价格
        "deepseek-coder": (0.0001, 0.0002),
        "deepseek-v2": (0.00014, 0.00028),
        "deepseek-v2.5": (0.00014, 0.00028),
    }
    
    def __init__(self, api_key: str, model: str = "deepseek-chat", **kwargs):
        """
        Initialize Deepseek provider
        
        Args:
            api_key: Deepseek API key
            model: Model name (default: deepseek-chat)
            **kwargs: Additional configuration
        """
        super().__init__(api_key, model, **kwargs)
        self.base_url = kwargs.get("base_url", "https://api.deepseek.com")
    
    def _validate_config(self) -> None:
        """Validate Deepseek configuration"""
        if not self.api_key:
            raise AIProviderError("Deepseek API key is required", "deepseek")
        
        if self.model not in self.get_supported_models():
            raise AIProviderError(f"Model '{self.model}' not supported", "deepseek")
    
    async def generate_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 1000,
        **kwargs
    ) -> AIResponse:
        """Generate completion using Deepseek"""
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
        """Generate chat completion using Deepseek"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Prepare request body
            body = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": False
            }
            
            # Add system prompt if provided
            if "system" in kwargs:
                # Insert system message at the beginning
                messages_with_system = [{"role": "system", "content": kwargs["system"]}] + messages
                body["messages"] = messages_with_system
            
            # Add other parameters
            for key, value in kwargs.items():
                if key not in ["system"]:
                    body[key] = value
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/v1/chat/completions",
                    headers=headers,
                    json=body,
                    timeout=60.0
                )
                
                if response.status_code != 200:
                    error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                    error_message = error_data.get("error", {}).get("message", f"HTTP {response.status_code}")
                    raise AIProviderError(f"Deepseek API error: {error_message}", "deepseek", str(response.status_code))
                
                data = response.json()
                
                # Extract content from response
                content = ""
                if data.get("choices") and len(data["choices"]) > 0:
                    content = data["choices"][0].get("message", {}).get("content", "")
                
                # Calculate tokens and cost
                usage = data.get("usage", {})
                input_tokens = usage.get("prompt_tokens", 0)
                output_tokens = usage.get("completion_tokens", 0)
                total_tokens = usage.get("total_tokens", input_tokens + output_tokens)
                cost = self.estimate_cost(input_tokens, output_tokens)
                
                return AIResponse(
                    content=content,
                    model=self.model,
                    provider="deepseek",
                    tokens_used=total_tokens,
                    cost=cost,
                    metadata={
                        "finish_reason": data.get("choices", [{}])[0].get("finish_reason"),
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                    }
                )
                
        except httpx.RequestError as e:
            raise AIProviderError(f"Network error: {str(e)}", "deepseek")
        except Exception as e:
            if isinstance(e, AIProviderError):
                raise
            raise AIProviderError(f"Unexpected error: {str(e)}", "deepseek")
    
    def get_provider_type(self) -> AIProviderType:
        """Get provider type"""
        return AIProviderType.DEEPSEEK
    
    def get_supported_models(self) -> List[str]:
        """Get supported Deepseek models"""
        return list(self.MODEL_PRICING.keys())
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost for Deepseek API usage"""
        if self.model not in self.MODEL_PRICING:
            return 0.0
        
        input_price, output_price = self.MODEL_PRICING[self.model]
        return (input_tokens / 1000 * input_price) + (output_tokens / 1000 * output_price)