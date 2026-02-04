"""
Google AI Provider Implementation
"""
import asyncio
from typing import Dict, Any, Optional, List
import httpx

from .base import AIProvider, AIResponse, AIProviderError, AIProviderType


class GoogleProvider(AIProvider):
    """Google AI (Gemini) provider implementation"""
    
    # Model pricing per 1K tokens (input, output) in USD
    MODEL_PRICING = {
        "gemini-pro": (0.0005, 0.0015),
        "gemini-pro-vision": (0.0005, 0.0015),
        "gemini-1.5-pro": (0.0035, 0.0105),
        "gemini-1.5-flash": (0.00035, 0.00105),
    }
    
    def __init__(self, api_key: str, model: str = "gemini-pro", **kwargs):
        """
        Initialize Google AI provider
        
        Args:
            api_key: Google AI API key
            model: Model name (default: gemini-pro)
            **kwargs: Additional configuration
        """
        super().__init__(api_key, model, **kwargs)
        self.base_url = kwargs.get("base_url", "https://generativelanguage.googleapis.com")
    
    def _validate_config(self) -> None:
        """Validate Google AI configuration"""
        if not self.api_key:
            raise AIProviderError("Google AI API key is required", "google")
        
        if self.model not in self.get_supported_models():
            raise AIProviderError(f"Model '{self.model}' not supported", "google")
    
    async def generate_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 1000,
        **kwargs
    ) -> AIResponse:
        """Generate completion using Google AI"""
        # Combine system prompt and user prompt
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        try:
            body = {
                "contents": [
                    {
                        "parts": [
                            {"text": full_prompt}
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens,
                }
            }
            
            # Add other parameters
            for key, value in kwargs.items():
                if key in ["topP", "topK", "candidateCount"]:
                    body["generationConfig"][key] = value
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/v1beta/models/{self.model}:generateContent",
                    params={"key": self.api_key},
                    json=body,
                    timeout=60.0
                )
                
                if response.status_code != 200:
                    error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                    error_message = error_data.get("error", {}).get("message", f"HTTP {response.status_code}")
                    raise AIProviderError(f"Google AI API error: {error_message}", "google", str(response.status_code))
                
                data = response.json()
                
                # Extract content from response
                content = ""
                if data.get("candidates") and len(data["candidates"]) > 0:
                    candidate = data["candidates"][0]
                    if candidate.get("content", {}).get("parts"):
                        content = candidate["content"]["parts"][0].get("text", "")
                
                # Google AI doesn't provide token usage in the response
                # We'll estimate based on content length
                estimated_input_tokens = len(full_prompt) // 4  # Rough estimation
                estimated_output_tokens = len(content) // 4
                total_tokens = estimated_input_tokens + estimated_output_tokens
                cost = self.estimate_cost(estimated_input_tokens, estimated_output_tokens)
                
                return AIResponse(
                    content=content,
                    model=self.model,
                    provider="google",
                    tokens_used=total_tokens,
                    cost=cost,
                    metadata={
                        "finish_reason": data.get("candidates", [{}])[0].get("finishReason"),
                        "estimated_input_tokens": estimated_input_tokens,
                        "estimated_output_tokens": estimated_output_tokens,
                    }
                )
                
        except httpx.RequestError as e:
            raise AIProviderError(f"Network error: {str(e)}", "google")
        except Exception as e:
            if isinstance(e, AIProviderError):
                raise
            raise AIProviderError(f"Unexpected error: {str(e)}", "google")
    
    async def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 1000,
        **kwargs
    ) -> AIResponse:
        """Generate chat completion using Google AI"""
        # Convert messages to Google AI format
        contents = []
        system_prompt = None
        
        for message in messages:
            role = message["role"]
            content = message["content"]
            
            if role == "system":
                system_prompt = content
            elif role == "user":
                contents.append({
                    "role": "user",
                    "parts": [{"text": content}]
                })
            elif role == "assistant":
                contents.append({
                    "role": "model",
                    "parts": [{"text": content}]
                })
        
        # If we have a system prompt, prepend it to the first user message
        if system_prompt and contents:
            first_user_content = contents[0]["parts"][0]["text"]
            contents[0]["parts"][0]["text"] = f"{system_prompt}\n\n{first_user_content}"
        
        try:
            body = {
                "contents": contents,
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens,
                }
            }
            
            # Add other parameters
            for key, value in kwargs.items():
                if key in ["topP", "topK", "candidateCount"]:
                    body["generationConfig"][key] = value
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/v1beta/models/{self.model}:generateContent",
                    params={"key": self.api_key},
                    json=body,
                    timeout=60.0
                )
                
                if response.status_code != 200:
                    error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                    error_message = error_data.get("error", {}).get("message", f"HTTP {response.status_code}")
                    raise AIProviderError(f"Google AI API error: {error_message}", "google", str(response.status_code))
                
                data = response.json()
                
                # Extract content from response
                content = ""
                if data.get("candidates") and len(data["candidates"]) > 0:
                    candidate = data["candidates"][0]
                    if candidate.get("content", {}).get("parts"):
                        content = candidate["content"]["parts"][0].get("text", "")
                
                # Estimate tokens
                total_input_text = " ".join([msg["content"] for msg in messages])
                estimated_input_tokens = len(total_input_text) // 4
                estimated_output_tokens = len(content) // 4
                total_tokens = estimated_input_tokens + estimated_output_tokens
                cost = self.estimate_cost(estimated_input_tokens, estimated_output_tokens)
                
                return AIResponse(
                    content=content,
                    model=self.model,
                    provider="google",
                    tokens_used=total_tokens,
                    cost=cost,
                    metadata={
                        "finish_reason": data.get("candidates", [{}])[0].get("finishReason"),
                        "estimated_input_tokens": estimated_input_tokens,
                        "estimated_output_tokens": estimated_output_tokens,
                    }
                )
                
        except httpx.RequestError as e:
            raise AIProviderError(f"Network error: {str(e)}", "google")
        except Exception as e:
            if isinstance(e, AIProviderError):
                raise
            raise AIProviderError(f"Unexpected error: {str(e)}", "google")
    
    def get_provider_type(self) -> AIProviderType:
        """Get provider type"""
        return AIProviderType.GOOGLE
    
    def get_supported_models(self) -> List[str]:
        """Get supported Google AI models"""
        return list(self.MODEL_PRICING.keys())
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost for Google AI API usage"""
        if self.model not in self.MODEL_PRICING:
            return 0.0
        
        input_price, output_price = self.MODEL_PRICING[self.model]
        return (input_tokens / 1000 * input_price) + (output_tokens / 1000 * output_price)