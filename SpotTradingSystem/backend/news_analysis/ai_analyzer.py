"""
Model-Agnostic News Analyzer
Uses configurable AI providers for sentiment analysis and impact assessment
"""
import asyncio
import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.data_models import NewsItem, SentimentScore, ImpactAssessment
from config import settings
from ai_providers.factory import AIProviderFactory
from ai_providers.base import AIProvider, AIProviderError
from news_analysis.cache import AnalysisCache
from news_analysis.impact_assessor import ImpactAssessor, HumanReviewManager

logger = logging.getLogger(__name__)


class ModelAgnosticNewsAnalyzer:
    """
    Model-agnostic news analyzer that can use different AI providers
    """
    
    def __init__(self, 
                 provider_type: Optional[str] = None,
                 model: Optional[str] = None,
                 api_key: Optional[str] = None,
                 fallback_provider: Optional[str] = None,
                 **provider_kwargs):
        """
        Initialize the model-agnostic news analyzer
        
        Args:
            provider_type: AI provider type (openai, anthropic, google)
            model: Model name to use
            api_key: API key (if not provided, will use from settings)
            fallback_provider: Fallback provider if primary fails
            **provider_kwargs: Additional provider-specific configuration
        """
        # Use settings defaults if not provided
        self.provider_type = provider_type or settings.api.ai_provider
        self.model = model or settings.api.ai_model
        self.fallback_provider = fallback_provider or settings.api.ai_fallback_provider
        self.fallback_model = settings.api.ai_fallback_model
        
        # Get API key based on provider
        if not api_key:
            api_key = self._get_api_key_for_provider(self.provider_type)
        
        # Create primary provider
        try:
            self.primary_provider = AIProviderFactory.create_provider(
                provider_type=self.provider_type,
                api_key=api_key,
                model=self.model,
                **provider_kwargs
            )
            logger.info(f"Initialized primary AI provider: {self.provider_type} with model {self.model}")
        except Exception as e:
            logger.error(f"Failed to initialize primary provider {self.provider_type}: {str(e)}")
            raise
        
        # Create fallback provider if specified
        self.fallback_provider_instance = None
        if self.fallback_provider:
            try:
                fallback_api_key = self._get_api_key_for_provider(self.fallback_provider)
                fallback_model = self.fallback_model or self._get_default_model_for_provider(self.fallback_provider)
                
                self.fallback_provider_instance = AIProviderFactory.create_provider(
                    provider_type=self.fallback_provider,
                    api_key=fallback_api_key,
                    model=fallback_model,
                    **provider_kwargs
                )
                logger.info(f"Initialized fallback AI provider: {self.fallback_provider} with model {fallback_model}")
            except Exception as e:
                logger.warning(f"Failed to initialize fallback provider {self.fallback_provider}: {str(e)}")
        
        # Initialize other components
        self.cache = AnalysisCache()
        self.impact_assessor = ImpactAssessor()
        self.review_manager = HumanReviewManager()
        
        # Analysis prompts
        self.sentiment_prompt = """
        Analyze the sentiment of the following news article about Bitcoin/cryptocurrency and provide:
        1. A sentiment score from 0-100 (0=very negative, 50=neutral, 100=very positive)
        2. Confidence level from 0-1 (how confident you are in this assessment)
        3. Key factors that influenced your sentiment assessment (list of strings)
        
        Focus specifically on how this news might affect Bitcoin price and market sentiment.
        
        Article: {content}
        
        Respond in JSON format:
        {{
            "sentiment_value": <0-100>,
            "confidence": <0-1>,
            "key_factors": ["factor1", "factor2", ...]
        }}
        """
        
        self.impact_prompt = """
        Assess the potential impact of this news article on Bitcoin price:
        1. Short-term impact (1-7 days): -1 (very negative) to 1 (very positive)
        2. Long-term impact (1-3 months): -1 (very negative) to 1 (very positive)
        3. Impact confidence: 0-1 (how confident you are in this assessment)
        4. Reasoning: explain your assessment
        
        Consider factors like:
        - Regulatory changes
        - Institutional adoption
        - Technical developments
        - Market sentiment shifts
        - Macroeconomic factors
        
        Article: {content}
        
        Respond in JSON format:
        {{
            "short_term_impact": <-1 to 1>,
            "long_term_impact": <-1 to 1>,
            "impact_confidence": <0-1>,
            "reasoning": "detailed explanation"
        }}
        """
    
    def _get_api_key_for_provider(self, provider_type: str) -> str:
        """Get API key for the specified provider from settings"""
        key_mapping = {
            "openai": settings.api.openai_api_key,
            "anthropic": settings.api.anthropic_api_key,
            "google": settings.api.google_api_key,
            "deepseek": settings.api.deepseek_api_key,
            "doubao": settings.api.doubao_api_key,
        }
        
        api_key = key_mapping.get(provider_type.lower())
        if not api_key:
            raise AIProviderError(f"No API key configured for provider '{provider_type}'", provider_type)
        
        return api_key
    
    def _get_default_model_for_provider(self, provider_type: str) -> str:
        """Get default model for the specified provider"""
        default_models = {
            "openai": "gpt-4",
            "anthropic": "claude-3-sonnet-20240229",
            "google": "gemini-pro",
            "deepseek": "deepseek-chat",
            "doubao": "doubao-lite-4k",
        }
        
        return default_models.get(provider_type.lower(), "gpt-4")
    
    async def _call_ai_with_fallback(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Call AI provider with fallback support
        
        Args:
            prompt: User prompt
            system_prompt: System prompt
            
        Returns:
            AI response content
        """
        # Try primary provider first
        try:
            response = await self.primary_provider.generate_completion(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=settings.api.ai_temperature,
                max_tokens=settings.api.ai_max_tokens
            )
            logger.debug(f"Primary provider ({self.provider_type}) succeeded. Cost: ${response.cost:.4f}")
            return response.content
        except Exception as e:
            logger.warning(f"Primary provider ({self.provider_type}) failed: {str(e)}")
            
            # Try fallback provider if available
            if self.fallback_provider_instance:
                try:
                    response = await self.fallback_provider_instance.generate_completion(
                        prompt=prompt,
                        system_prompt=system_prompt,
                        temperature=settings.api.ai_temperature,
                        max_tokens=settings.api.ai_max_tokens
                    )
                    logger.info(f"Fallback provider ({self.fallback_provider}) succeeded. Cost: ${response.cost:.4f}")
                    return response.content
                except Exception as fallback_error:
                    logger.error(f"Fallback provider ({self.fallback_provider}) also failed: {str(fallback_error)}")
            
            # If both providers fail, raise the original error
            raise e
    
    async def analyze_sentiment(self, content: str) -> SentimentScore:
        """
        Analyze sentiment of news content using configured AI provider
        
        Args:
            content: News article content
            
        Returns:
            SentimentScore object with analysis results
        """
        # Check cache first
        cache_key = f"sentiment_{hash(content)}_{self.provider_type}_{self.model}"
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            logger.info("Retrieved sentiment analysis from cache")
            return SentimentScore.from_dict(cached_result)
        
        try:
            system_prompt = "You are a financial analyst specializing in cryptocurrency market sentiment analysis."
            prompt = self.sentiment_prompt.format(content=content[:4000])  # Limit content length
            
            result_text = await self._call_ai_with_fallback(prompt, system_prompt)
            
            # Parse JSON response
            try:
                result_data = json.loads(result_text)
            except json.JSONDecodeError:
                # Fallback: extract JSON from response if wrapped in other text
                import re
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    result_data = json.loads(json_match.group())
                else:
                    raise ValueError("Could not parse JSON from AI response")
            
            sentiment_score = SentimentScore(
                sentiment_value=float(result_data['sentiment_value']),
                confidence=float(result_data['confidence']),
                key_factors=result_data['key_factors']
            )
            
            # Cache the result
            await self.cache.set(cache_key, sentiment_score.to_dict(), ttl=3600)  # Cache for 1 hour
            
            logger.info(f"Sentiment analysis completed: score={sentiment_score.sentiment_value}, confidence={sentiment_score.confidence}")
            return sentiment_score
            
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {str(e)}")
            # Return neutral sentiment with low confidence as fallback
            return SentimentScore(
                sentiment_value=50.0,
                confidence=0.1,
                key_factors=["analysis_failed"]
            )
    
    async def assess_bitcoin_impact(self, content: str) -> ImpactAssessment:
        """
        Assess the potential impact of news on Bitcoin price
        
        Args:
            content: News article content
            
        Returns:
            ImpactAssessment object with impact analysis
        """
        # Check cache first
        cache_key = f"impact_{hash(content)}_{self.provider_type}_{self.model}"
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            logger.info("Retrieved impact assessment from cache")
            return ImpactAssessment.from_dict(cached_result)
        
        try:
            system_prompt = "You are a cryptocurrency market analyst specializing in Bitcoin price impact assessment."
            prompt = self.impact_prompt.format(content=content[:4000])
            
            result_text = await self._call_ai_with_fallback(prompt, system_prompt)
            
            # Parse JSON response
            try:
                result_data = json.loads(result_text)
            except json.JSONDecodeError:
                # Fallback: extract JSON from response if wrapped in other text
                import re
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    result_data = json.loads(json_match.group())
                else:
                    raise ValueError("Could not parse JSON from AI response")
            
            impact_assessment = ImpactAssessment(
                short_term_impact=float(result_data['short_term_impact']),
                long_term_impact=float(result_data['long_term_impact']),
                impact_confidence=float(result_data['impact_confidence']),
                reasoning=result_data['reasoning']
            )
            
            # Cache the result
            await self.cache.set(cache_key, impact_assessment.to_dict(), ttl=3600)  # Cache for 1 hour
            
            logger.info(f"Impact assessment completed: short_term={impact_assessment.short_term_impact}, long_term={impact_assessment.long_term_impact}")
            return impact_assessment
            
        except Exception as e:
            logger.error(f"Error in impact assessment: {str(e)}")
            # Return neutral impact with low confidence as fallback
            return ImpactAssessment(
                short_term_impact=0.0,
                long_term_impact=0.0,
                impact_confidence=0.1,
                reasoning="Impact assessment failed due to technical error"
            )
    
    async def analyze_news_item(self, news_item: NewsItem, use_advanced_impact: bool = True) -> NewsItem:
        """
        Perform complete analysis on a news item (sentiment + impact)
        
        Args:
            news_item: NewsItem to analyze
            use_advanced_impact: Whether to use advanced impact assessment algorithm
            
        Returns:
            NewsItem with sentiment_score and impact_assessment populated
        """
        try:
            # Combine title and content for analysis
            full_content = f"{news_item.title}\n\n{news_item.content}"
            
            # Perform sentiment analysis
            sentiment_task = self.analyze_sentiment(full_content)
            
            # Choose impact assessment method
            if use_advanced_impact:
                # Use advanced impact assessor
                impact_task = self.impact_assessor.assess_impact(news_item)
            else:
                # Use AI-based impact assessment
                impact_task = self.assess_bitcoin_impact(full_content)
            
            sentiment_score, impact_assessment = await asyncio.gather(
                sentiment_task, impact_task
            )
            
            # Update the news item
            news_item.sentiment_score = sentiment_score.sentiment_value
            news_item.impact_assessment = impact_assessment
            
            # Check for anomalous results and add to review queue if needed
            if self.impact_assessor.detect_anomalous_results(news_item):
                self.review_manager.add_for_review(
                    news_item, 
                    "Anomalous analysis results detected - requires human review"
                )
            
            logger.info(f"Completed analysis for news item: {news_item.id}")
            return news_item
            
        except Exception as e:
            logger.error(f"Error analyzing news item {news_item.id}: {str(e)}")
            # Set default values on error
            news_item.sentiment_score = 50.0
            news_item.impact_assessment = ImpactAssessment(
                short_term_impact=0.0,
                long_term_impact=0.0,
                impact_confidence=0.1,
                reasoning="Analysis failed due to technical error"
            )
            return news_item
    
    async def analyze_batch(self, news_items: List[NewsItem], max_concurrent: int = 5) -> List[NewsItem]:
        """
        Analyze multiple news items in batches with concurrency control
        
        Args:
            news_items: List of NewsItem objects to analyze
            max_concurrent: Maximum number of concurrent analyses
            
        Returns:
            List of analyzed NewsItem objects
        """
        if not news_items:
            return []
        
        logger.info(f"Starting batch analysis of {len(news_items)} news items using {self.provider_type}")
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def analyze_with_semaphore(item: NewsItem) -> NewsItem:
            async with semaphore:
                return await self.analyze_news_item(item)
        
        # Process all items concurrently with limit
        analyzed_items = await asyncio.gather(
            *[analyze_with_semaphore(item) for item in news_items],
            return_exceptions=True
        )
        
        # Filter out exceptions and log errors
        results = []
        for i, result in enumerate(analyzed_items):
            if isinstance(result, Exception):
                logger.error(f"Error analyzing item {i}: {str(result)}")
                # Add original item with default values
                item = news_items[i]
                item.sentiment_score = 50.0
                item.impact_assessment = ImpactAssessment(
                    short_term_impact=0.0,
                    long_term_impact=0.0,
                    impact_confidence=0.1,
                    reasoning="Analysis failed due to technical error"
                )
                results.append(item)
            else:
                results.append(result)
        
        logger.info(f"Completed batch analysis of {len(results)} news items")
        return results
    
    async def generate_market_summary(self, news_items: List[NewsItem], time_window_hours: int = 24) -> Dict[str, Any]:
        """
        Generate a market sentiment summary from recent news items
        
        Args:
            news_items: List of analyzed news items
            time_window_hours: Time window to consider for summary
            
        Returns:
            Dictionary containing market summary
        """
        if not news_items:
            return {
                "overall_sentiment": 50.0,
                "sentiment_confidence": 0.0,
                "short_term_outlook": 0.0,
                "long_term_outlook": 0.0,
                "total_articles": 0,
                "key_themes": [],
                "summary_timestamp": datetime.utcnow().isoformat(),
                "ai_provider": self.provider_type,
                "ai_model": self.model
            }
        
        # Filter news items within time window
        cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)
        recent_items = [
            item for item in news_items 
            if item.published_at >= cutoff_time and item.sentiment_score is not None
        ]
        
        if not recent_items:
            return {
                "overall_sentiment": 50.0,
                "sentiment_confidence": 0.0,
                "short_term_outlook": 0.0,
                "long_term_outlook": 0.0,
                "total_articles": 0,
                "key_themes": [],
                "summary_timestamp": datetime.utcnow().isoformat(),
                "ai_provider": self.provider_type,
                "ai_model": self.model
            }
        
        # Calculate weighted averages
        total_weight = 0
        weighted_sentiment = 0
        weighted_short_impact = 0
        weighted_long_impact = 0
        
        for item in recent_items:
            if item.impact_assessment:
                weight = item.impact_assessment.impact_confidence
                total_weight += weight
                weighted_sentiment += item.sentiment_score * weight
                weighted_short_impact += item.impact_assessment.short_term_impact * weight
                weighted_long_impact += item.impact_assessment.long_term_impact * weight
        
        if total_weight > 0:
            overall_sentiment = weighted_sentiment / total_weight
            short_term_outlook = weighted_short_impact / total_weight
            long_term_outlook = weighted_long_impact / total_weight
            sentiment_confidence = min(total_weight / len(recent_items), 1.0)
        else:
            overall_sentiment = sum(item.sentiment_score for item in recent_items) / len(recent_items)
            short_term_outlook = 0.0
            long_term_outlook = 0.0
            sentiment_confidence = 0.5
        
        return {
            "overall_sentiment": round(overall_sentiment, 2),
            "sentiment_confidence": round(sentiment_confidence, 2),
            "short_term_outlook": round(short_term_outlook, 2),
            "long_term_outlook": round(long_term_outlook, 2),
            "total_articles": len(recent_items),
            "key_themes": [],  # Would need additional analysis to extract themes
            "summary_timestamp": datetime.utcnow().isoformat(),
            "ai_provider": self.provider_type,
            "ai_model": self.model
        }
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the current AI provider configuration"""
        return {
            "primary_provider": self.provider_type,
            "primary_model": self.model,
            "fallback_provider": self.fallback_provider,
            "fallback_model": self.fallback_model,
            "supported_providers": AIProviderFactory.get_supported_providers()
        }
    
    async def test_providers(self) -> Dict[str, bool]:
        """Test connection to all configured providers"""
        results = {}
        
        # Test primary provider
        try:
            results["primary"] = await self.primary_provider.test_connection()
        except Exception as e:
            logger.error(f"Primary provider test failed: {str(e)}")
            results["primary"] = False
        
        # Test fallback provider if configured
        if self.fallback_provider_instance:
            try:
                results["fallback"] = await self.fallback_provider_instance.test_connection()
            except Exception as e:
                logger.error(f"Fallback provider test failed: {str(e)}")
                results["fallback"] = False
        
        return results