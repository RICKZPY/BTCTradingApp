"""
Advanced impact assessment algorithms for news analysis
Implements short-term and long-term impact evaluation with anomaly detection
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncio
import json
from enum import Enum

from backend.core.data_models import NewsItem, ImpactAssessment
from backend.config import settings

logger = logging.getLogger(__name__)


class ImpactTimeframe(Enum):
    """Impact assessment timeframes"""
    SHORT_TERM = "short_term"  # 1-7 days
    LONG_TERM = "long_term"    # 1-3 months


class NewsCategory(Enum):
    """News categories for impact assessment"""
    REGULATORY = "regulatory"
    INSTITUTIONAL = "institutional"
    TECHNICAL = "technical"
    MARKET = "market"
    MACROECONOMIC = "macroeconomic"
    SOCIAL = "social"
    UNKNOWN = "unknown"


@dataclass
class ImpactFactors:
    """Factors that influence impact assessment"""
    regulatory_weight: float = 0.3
    institutional_weight: float = 0.25
    technical_weight: float = 0.2
    market_weight: float = 0.15
    macro_weight: float = 0.1


@dataclass
class AnomalyThresholds:
    """Thresholds for detecting anomalous analysis results"""
    min_confidence: float = 0.3
    max_impact_without_confidence: float = 0.8
    min_reasoning_length: int = 50
    sentiment_impact_contradiction_threshold: float = 0.5


class ImpactAssessor:
    """
    Advanced impact assessment engine for news analysis
    """
    
    def __init__(self):
        """Initialize the impact assessor"""
        self.impact_factors = ImpactFactors()
        self.anomaly_thresholds = AnomalyThresholds()
        
        # Keywords for categorizing news
        self.category_keywords = {
            NewsCategory.REGULATORY: [
                'regulation', 'regulatory', 'sec', 'cftc', 'government', 'ban', 'legal',
                'compliance', 'law', 'policy', 'central bank', 'fed', 'treasury'
            ],
            NewsCategory.INSTITUTIONAL: [
                'institutional', 'bank', 'corporation', 'company', 'investment',
                'fund', 'etf', 'adoption', 'partnership', 'integration', 'enterprise'
            ],
            NewsCategory.TECHNICAL: [
                'blockchain', 'mining', 'hash rate', 'difficulty', 'upgrade',
                'fork', 'protocol', 'network', 'transaction', 'scalability', 'lightning'
            ],
            NewsCategory.MARKET: [
                'price', 'trading', 'volume', 'market', 'exchange', 'liquidity',
                'volatility', 'bull', 'bear', 'rally', 'crash', 'correction'
            ],
            NewsCategory.MACROECONOMIC: [
                'inflation', 'interest rate', 'gdp', 'recession', 'economy',
                'dollar', 'currency', 'monetary policy', 'fiscal', 'unemployment'
            ],
            NewsCategory.SOCIAL: [
                'twitter', 'social media', 'sentiment', 'retail', 'community',
                'influencer', 'celebrity', 'public opinion', 'mainstream'
            ]
        }
    
    def categorize_news(self, news_item: NewsItem) -> NewsCategory:
        """
        Categorize news item based on content keywords
        
        Args:
            news_item: News item to categorize
            
        Returns:
            NewsCategory enum value
        """
        content_lower = f"{news_item.title} {news_item.content}".lower()
        
        category_scores = {}
        for category, keywords in self.category_keywords.items():
            score = sum(1 for keyword in keywords if keyword in content_lower)
            if score > 0:
                category_scores[category] = score
        
        if not category_scores:
            return NewsCategory.UNKNOWN
        
        # Return category with highest score
        return max(category_scores, key=category_scores.get)
    
    def calculate_base_impact(self, news_item: NewsItem, category: NewsCategory) -> Tuple[float, float]:
        """
        Calculate base impact scores based on news category and content
        
        Args:
            news_item: News item to assess
            category: News category
            
        Returns:
            Tuple of (short_term_impact, long_term_impact)
        """
        # Base impact multipliers by category
        category_multipliers = {
            NewsCategory.REGULATORY: (0.8, 0.9),      # High impact, especially long-term
            NewsCategory.INSTITUTIONAL: (0.6, 0.8),   # Medium-high impact
            NewsCategory.TECHNICAL: (0.4, 0.7),       # Lower short-term, higher long-term
            NewsCategory.MARKET: (0.9, 0.5),          # High short-term, lower long-term
            NewsCategory.MACROECONOMIC: (0.7, 0.8),   # High impact both timeframes
            NewsCategory.SOCIAL: (0.5, 0.3),          # Medium short-term, low long-term
            NewsCategory.UNKNOWN: (0.3, 0.3)          # Low impact for unknown
        }
        
        short_mult, long_mult = category_multipliers[category]
        
        # Adjust based on sentiment if available
        sentiment_adjustment = 0.0
        if news_item.sentiment_score is not None:
            # Convert sentiment (0-100) to impact scale (-1 to 1)
            sentiment_normalized = (news_item.sentiment_score - 50) / 50
            sentiment_adjustment = sentiment_normalized * 0.5  # Max 0.5 adjustment
        
        # Calculate base impacts
        short_term_impact = sentiment_adjustment * short_mult
        long_term_impact = sentiment_adjustment * long_mult
        
        # Ensure values are within bounds
        short_term_impact = max(-1.0, min(1.0, short_term_impact))
        long_term_impact = max(-1.0, min(1.0, long_term_impact))
        
        return short_term_impact, long_term_impact
    
    def assess_impact_confidence(self, news_item: NewsItem, category: NewsCategory) -> float:
        """
        Assess confidence in impact assessment
        
        Args:
            news_item: News item to assess
            category: News category
            
        Returns:
            Confidence score (0-1)
        """
        confidence = 0.5  # Base confidence
        
        # Adjust based on category (some categories are easier to assess)
        category_confidence = {
            NewsCategory.REGULATORY: 0.8,
            NewsCategory.INSTITUTIONAL: 0.7,
            NewsCategory.TECHNICAL: 0.6,
            NewsCategory.MARKET: 0.9,
            NewsCategory.MACROECONOMIC: 0.7,
            NewsCategory.SOCIAL: 0.4,
            NewsCategory.UNKNOWN: 0.2
        }
        
        confidence = category_confidence[category]
        
        # Adjust based on content quality
        content_length = len(news_item.content)
        if content_length > 1000:
            confidence += 0.1
        elif content_length < 200:
            confidence -= 0.2
        
        # Adjust based on source reliability (simplified)
        reliable_sources = ['coindesk', 'cointelegraph', 'reuters', 'bloomberg', 'wsj']
        if any(source in news_item.source.lower() for source in reliable_sources):
            confidence += 0.1
        
        # Adjust based on recency
        hours_old = (datetime.utcnow() - news_item.published_at).total_seconds() / 3600
        if hours_old < 6:
            confidence += 0.1
        elif hours_old > 48:
            confidence -= 0.1
        
        return max(0.0, min(1.0, confidence))
    
    def generate_impact_reasoning(self, news_item: NewsItem, category: NewsCategory, 
                                short_impact: float, long_impact: float) -> str:
        """
        Generate reasoning for impact assessment
        
        Args:
            news_item: News item
            category: News category
            short_impact: Short-term impact score
            long_impact: Long-term impact score
            
        Returns:
            Reasoning string
        """
        reasoning_parts = []
        
        # Category-based reasoning
        category_reasoning = {
            NewsCategory.REGULATORY: "Regulatory developments typically have significant and lasting impact on Bitcoin adoption and price.",
            NewsCategory.INSTITUTIONAL: "Institutional involvement often signals mainstream acceptance and can drive sustained price movements.",
            NewsCategory.TECHNICAL: "Technical developments may have limited immediate impact but can significantly affect long-term value proposition.",
            NewsCategory.MARKET: "Market-related news typically has immediate price impact but may not affect long-term fundamentals.",
            NewsCategory.MACROECONOMIC: "Macroeconomic factors influence Bitcoin as both a risk asset and inflation hedge.",
            NewsCategory.SOCIAL: "Social sentiment can drive short-term price movements but has limited long-term impact.",
            NewsCategory.UNKNOWN: "Impact assessment is uncertain due to unclear news categorization."
        }
        
        reasoning_parts.append(category_reasoning[category])
        
        # Impact direction reasoning
        if short_impact > 0.3:
            reasoning_parts.append("Expected positive short-term price impact due to favorable market sentiment.")
        elif short_impact < -0.3:
            reasoning_parts.append("Expected negative short-term price impact due to unfavorable market conditions.")
        else:
            reasoning_parts.append("Limited short-term price impact expected.")
        
        if long_impact > 0.3:
            reasoning_parts.append("Positive long-term implications for Bitcoin adoption and value.")
        elif long_impact < -0.3:
            reasoning_parts.append("Negative long-term implications for Bitcoin ecosystem.")
        else:
            reasoning_parts.append("Neutral long-term impact on Bitcoin fundamentals.")
        
        # Add sentiment-based reasoning if available
        if news_item.sentiment_score is not None:
            if news_item.sentiment_score > 70:
                reasoning_parts.append("Highly positive sentiment supports bullish price expectations.")
            elif news_item.sentiment_score < 30:
                reasoning_parts.append("Negative sentiment may pressure prices in the near term.")
        
        return " ".join(reasoning_parts)
    
    async def assess_impact(self, news_item: NewsItem) -> ImpactAssessment:
        """
        Perform comprehensive impact assessment on a news item
        
        Args:
            news_item: News item to assess
            
        Returns:
            ImpactAssessment object
        """
        try:
            # Categorize the news
            category = self.categorize_news(news_item)
            
            # Calculate base impact scores
            short_impact, long_impact = self.calculate_base_impact(news_item, category)
            
            # Assess confidence
            confidence = self.assess_impact_confidence(news_item, category)
            
            # Generate reasoning
            reasoning = self.generate_impact_reasoning(news_item, category, short_impact, long_impact)
            
            # Create impact assessment
            impact_assessment = ImpactAssessment(
                short_term_impact=short_impact,
                long_term_impact=long_impact,
                impact_confidence=confidence,
                reasoning=reasoning
            )
            
            logger.info(f"Impact assessment completed for news item {news_item.id}: "
                       f"category={category.value}, short={short_impact:.2f}, long={long_impact:.2f}, confidence={confidence:.2f}")
            
            return impact_assessment
            
        except Exception as e:
            logger.error(f"Error in impact assessment for news item {news_item.id}: {str(e)}")
            # Return neutral assessment on error
            return ImpactAssessment(
                short_term_impact=0.0,
                long_term_impact=0.0,
                impact_confidence=0.1,
                reasoning="Impact assessment failed due to technical error"
            )
    
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
        
        impact = news_item.impact_assessment
        
        # Check for extreme values with low confidence
        if impact.impact_confidence < self.anomaly_thresholds.min_confidence:
            if (abs(impact.short_term_impact) > self.anomaly_thresholds.max_impact_without_confidence or 
                abs(impact.long_term_impact) > self.anomaly_thresholds.max_impact_without_confidence):
                logger.warning(f"Anomaly detected: High impact with low confidence for news item {news_item.id}")
                return True
        
        # Check for contradictory sentiment and impact
        sentiment_normalized = (news_item.sentiment_score - 50) / 50  # Convert to -1 to 1 scale
        threshold = self.anomaly_thresholds.sentiment_impact_contradiction_threshold
        
        if ((sentiment_normalized > threshold and impact.short_term_impact < -threshold) or 
            (sentiment_normalized < -threshold and impact.short_term_impact > threshold)):
            logger.warning(f"Anomaly detected: Contradictory sentiment and impact for news item {news_item.id}")
            return True
        
        # Check for very short reasoning
        if len(impact.reasoning) < self.anomaly_thresholds.min_reasoning_length:
            logger.warning(f"Anomaly detected: Insufficient reasoning for news item {news_item.id}")
            return True
        
        return False
    
    async def assess_batch_impact(self, news_items: List[NewsItem]) -> List[NewsItem]:
        """
        Assess impact for multiple news items
        
        Args:
            news_items: List of news items to assess
            
        Returns:
            List of news items with impact assessments
        """
        if not news_items:
            return []
        
        logger.info(f"Starting batch impact assessment for {len(news_items)} news items")
        
        # Process items concurrently
        tasks = [self.assess_impact(item) for item in news_items]
        impact_assessments = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Update news items with assessments
        results = []
        for i, (item, assessment) in enumerate(zip(news_items, impact_assessments)):
            if isinstance(assessment, Exception):
                logger.error(f"Error assessing impact for item {i}: {str(assessment)}")
                # Set default assessment
                item.impact_assessment = ImpactAssessment(
                    short_term_impact=0.0,
                    long_term_impact=0.0,
                    impact_confidence=0.1,
                    reasoning="Impact assessment failed due to technical error"
                )
            else:
                item.impact_assessment = assessment
            
            results.append(item)
        
        logger.info(f"Completed batch impact assessment for {len(results)} news items")
        return results
    
    def get_impact_statistics(self, news_items: List[NewsItem]) -> Dict[str, Any]:
        """
        Generate statistics about impact assessments
        
        Args:
            news_items: List of analyzed news items
            
        Returns:
            Dictionary with impact statistics
        """
        if not news_items:
            return {}
        
        # Filter items with impact assessments
        assessed_items = [item for item in news_items if item.impact_assessment]
        
        if not assessed_items:
            return {"total_items": len(news_items), "assessed_items": 0}
        
        # Calculate statistics
        short_impacts = [item.impact_assessment.short_term_impact for item in assessed_items]
        long_impacts = [item.impact_assessment.long_term_impact for item in assessed_items]
        confidences = [item.impact_assessment.impact_confidence for item in assessed_items]
        
        # Categorize items
        categories = [self.categorize_news(item) for item in assessed_items]
        category_counts = {}
        for category in categories:
            category_counts[category.value] = category_counts.get(category.value, 0) + 1
        
        # Detect anomalies
        anomalous_count = sum(1 for item in assessed_items if self.detect_anomalous_results(item))
        
        return {
            "total_items": len(news_items),
            "assessed_items": len(assessed_items),
            "average_short_term_impact": sum(short_impacts) / len(short_impacts),
            "average_long_term_impact": sum(long_impacts) / len(long_impacts),
            "average_confidence": sum(confidences) / len(confidences),
            "category_distribution": category_counts,
            "anomalous_results": anomalous_count,
            "anomaly_rate": anomalous_count / len(assessed_items) if assessed_items else 0
        }


class HumanReviewManager:
    """
    Manager for handling items that need human review
    """
    
    def __init__(self):
        """Initialize the human review manager"""
        self.review_queue = []
        self.reviewed_items = {}
    
    def add_for_review(self, news_item: NewsItem, reason: str):
        """
        Add a news item to the human review queue
        
        Args:
            news_item: News item that needs review
            reason: Reason for requiring review
        """
        review_entry = {
            "news_item": news_item,
            "reason": reason,
            "added_at": datetime.utcnow(),
            "status": "pending"
        }
        self.review_queue.append(review_entry)
        logger.info(f"Added news item {news_item.id} to human review queue: {reason}")
    
    def get_review_queue(self) -> List[Dict[str, Any]]:
        """
        Get items pending human review
        
        Returns:
            List of items in review queue
        """
        return [item for item in self.review_queue if item["status"] == "pending"]
    
    def mark_reviewed(self, news_item_id: str, reviewer_notes: str = ""):
        """
        Mark an item as reviewed
        
        Args:
            news_item_id: ID of the reviewed news item
            reviewer_notes: Optional notes from reviewer
        """
        for item in self.review_queue:
            if item["news_item"].id == news_item_id:
                item["status"] = "reviewed"
                item["reviewed_at"] = datetime.utcnow()
                item["reviewer_notes"] = reviewer_notes
                self.reviewed_items[news_item_id] = item
                logger.info(f"Marked news item {news_item_id} as reviewed")
                break
    
    def get_review_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the review process
        
        Returns:
            Dictionary with review statistics
        """
        pending_count = len(self.get_review_queue())
        reviewed_count = len(self.reviewed_items)
        total_count = len(self.review_queue)
        
        return {
            "pending_reviews": pending_count,
            "completed_reviews": reviewed_count,
            "total_items": total_count,
            "review_completion_rate": reviewed_count / total_count if total_count > 0 else 0
        }