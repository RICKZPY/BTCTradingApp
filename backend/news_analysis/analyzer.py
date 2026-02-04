"""
News Analyzer implementation using OpenAI GPT-4 for sentiment analysis
"""
import asyncio
import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import openai
from openai import AsyncOpenAI

from backend.core.data_models import NewsItem, SentimentScore, ImpactAssessment
from backend.config import settings
from .cache import AnalysisCache
from .impact_assessor import ImpactAssessor, HumanReviewManager

logger = logging.getLogger(__name__)


class NewsAnalyzer:
    """
    News analyzer using OpenAI GPT-4 for sentiment analysis and impact assessment
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the news analyzer
        
        Args:
            api_key: OpenAI API key, defaults to settings.api.openai_api_key
        """
        self.api_key = api_key or settings.api.openai_api_key
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.client = AsyncOpenAI(api_key=self.api_key)
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
    
    async def analyze_sentiment(self, content: str) -> SentimentScore:
        """
        Analyze sentiment of news content using GPT-4
        
        Args:
            content: News article content
            
        Returns:
            SentimentScore object with analysis results
        """
        # Check cache first
        cache_key = f"sentiment_{hash(content)}"
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            logger.info("Retrieved sentiment analysis from cache")
            return SentimentScore.from_dict(cached_result)
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a financial analyst specializing in cryptocurrency market sentiment analysis."},
                    {"role": "user", "content": self.sentiment_prompt.format(content=content[:4000])}  # Limit content length
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            result_text = response.choices[0].message.content.strip()
            
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
                    raise ValueError("Could not parse JSON from GPT-4 response")
            
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
        cache_key = f"impact_{hash(content)}"
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            logger.info("Retrieved impact assessment from cache")
            return ImpactAssessment.from_dict(cached_result)
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a cryptocurrency market analyst specializing in Bitcoin price impact assessment."},
                    {"role": "user", "content": self.impact_prompt.format(content=content[:4000])}
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            result_text = response.choices[0].message.content.strip()
            
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
                    raise ValueError("Could not parse JSON from GPT-4 response")
            
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
                # Use GPT-4 based impact assessment
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
        
        logger.info(f"Starting batch analysis of {len(news_items)} news items")
        
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
                "summary_timestamp": datetime.utcnow().isoformat()
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
                "summary_timestamp": datetime.utcnow().isoformat()
            }
        
        # Calculate weighted averages
        total_weight = 0
        weighted_sentiment = 0
        weighted_short_impact = 0
        weighted_long_impact = 0
        all_key_factors = []
        
        for item in recent_items:
            if item.impact_assessment:
                weight = item.impact_assessment.impact_confidence
                total_weight += weight
                weighted_sentiment += item.sentiment_score * weight
                weighted_short_impact += item.impact_assessment.short_term_impact * weight
                weighted_long_impact += item.impact_assessment.long_term_impact * weight
                
                # Collect key factors (assuming they exist in sentiment analysis)
                # This would need to be stored separately or retrieved from cache
        
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
            "summary_timestamp": datetime.utcnow().isoformat()
        }
    
    def detect_anomalous_results(self, news_item: NewsItem) -> bool:
        """
        Detect if analysis results are anomalous and need human review
        
        Args:
            news_item: Analyzed news item
            
        Returns:
            True if results are anomalous and need review
        """
        if not news_item.sentiment_score or not news_item.impact_assessment:
            return True
        
        # Check for extreme values with low confidence
        if news_item.impact_assessment.impact_confidence < 0.3:
            if (abs(news_item.impact_assessment.short_term_impact) > 0.8 or 
                abs(news_item.impact_assessment.long_term_impact) > 0.8):
                return True
        
        # Check for contradictory sentiment and impact
        sentiment_normalized = (news_item.sentiment_score - 50) / 50  # Convert to -1 to 1 scale
        if (sentiment_normalized > 0.5 and news_item.impact_assessment.short_term_impact < -0.5) or \
           (sentiment_normalized < -0.5 and news_item.impact_assessment.short_term_impact > 0.5):
            return True
        
        # Check for very short reasoning
        if len(news_item.impact_assessment.reasoning) < 50:
            return True
        
        return False
    
    def get_review_queue(self) -> List[Dict[str, Any]]:
        """
        Get items pending human review
        
        Returns:
            List of items in review queue
        """
        return self.review_manager.get_review_queue()
    
    def mark_item_reviewed(self, news_item_id: str, reviewer_notes: str = ""):
        """
        Mark an item as reviewed by human
        
        Args:
            news_item_id: ID of the reviewed news item
            reviewer_notes: Optional notes from reviewer
        """
        self.review_manager.mark_reviewed(news_item_id, reviewer_notes)
    
    def get_analysis_statistics(self, news_items: List[NewsItem]) -> Dict[str, Any]:
        """
        Get comprehensive analysis statistics
        
        Args:
            news_items: List of analyzed news items
            
        Returns:
            Dictionary with analysis statistics
        """
        impact_stats = self.impact_assessor.get_impact_statistics(news_items)
        review_stats = self.review_manager.get_review_statistics()
        
        return {
            "impact_statistics": impact_stats,
            "review_statistics": review_stats,
            "total_analyzed": len([item for item in news_items if item.sentiment_score is not None])
        }