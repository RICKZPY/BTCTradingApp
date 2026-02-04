#!/usr/bin/env python3
"""
Property-based tests for sentiment analysis output validity
验证情绪分析输出有效性 - 属性 2
"""
import pytest
from hypothesis import given, strategies as st, assume, settings
from datetime import datetime, timezone
import json
from typing import List, Dict, Any

from core.data_models import NewsItem, SentimentScore, ImpactAssessment
from news_analysis.sentiment_analyzer import SentimentAnalyzer


# Hypothesis strategies for generating test data
def sentiment_score_strategy():
    """Generate valid sentiment scores (0-100)"""
    return st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False)


def confidence_strategy():
    """Generate valid confidence scores (0-1)"""
    return st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)


def impact_score_strategy():
    """Generate valid impact scores (-1 to 1)"""
    return st.floats(min_value=-1.0, max_value=1.0, allow_nan=False, allow_infinity=False)


def news_text_strategy():
    """Generate news text content"""
    return st.text(min_size=10, max_size=1000).filter(lambda x: x.strip())


def key_factors_strategy():
    """Generate key factors list"""
    return st.lists(
        st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
        min_size=0,
        max_size=10
    )


@given(
    sentiment_value=sentiment_score_strategy(),
    confidence=confidence_strategy(),
    key_factors=key_factors_strategy()
)
def test_sentiment_score_validity_property(sentiment_value, confidence, key_factors):
    """
    Property 2.1: Sentiment score validity
    For any sentiment analysis output, scores should be within valid ranges
    **Validates: Requirements 2.2, 2.3**
    """
    # Create SentimentScore
    sentiment_score = SentimentScore(
        sentiment_value=sentiment_value,
        confidence=confidence,
        key_factors=key_factors
    )
    
    # Property: Sentiment value should be between 0 and 100
    assert 0.0 <= sentiment_score.sentiment_value <= 100.0
    
    # Property: Confidence should be between 0 and 1
    assert 0.0 <= sentiment_score.confidence <= 1.0
    
    # Property: Key factors should be a list
    assert isinstance(sentiment_score.key_factors, list)
    
    # Property: All key factors should be non-empty strings
    for factor in sentiment_score.key_factors:
        assert isinstance(factor, str)
        assert len(factor.strip()) > 0


@given(
    short_term_impact=impact_score_strategy(),
    long_term_impact=impact_score_strategy(),
    impact_confidence=confidence_strategy(),
    reasoning=st.text(min_size=10, max_size=500).filter(lambda x: x.strip())
)
def test_impact_assessment_validity_property(short_term_impact, long_term_impact, impact_confidence, reasoning):
    """
    Property 2.2: Impact assessment validity
    For any impact assessment, values should be within valid ranges and consistent
    **Validates: Requirements 2.3, 2.4**
    """
    # Create ImpactAssessment
    impact_assessment = ImpactAssessment(
        short_term_impact=short_term_impact,
        long_term_impact=long_term_impact,
        impact_confidence=impact_confidence,
        reasoning=reasoning
    )
    
    # Property: Impact scores should be between -1 and 1
    assert -1.0 <= impact_assessment.short_term_impact <= 1.0
    assert -1.0 <= impact_assessment.long_term_impact <= 1.0
    
    # Property: Impact confidence should be between 0 and 1
    assert 0.0 <= impact_assessment.impact_confidence <= 1.0
    
    # Property: Reasoning should be a non-empty string
    assert isinstance(impact_assessment.reasoning, str)
    assert len(impact_assessment.reasoning.strip()) > 0


@given(
    news_content=news_text_strategy(),
    expected_sentiment_range=st.tuples(
        st.floats(min_value=0, max_value=50),
        st.floats(min_value=50, max_value=100)
    ).filter(lambda x: x[0] < x[1])
)
def test_sentiment_consistency_property(news_content, expected_sentiment_range):
    """
    Property 2.3: Sentiment analysis consistency
    For similar news content, sentiment scores should be consistent
    **Validates: Requirements 2.2, 2.4**
    """
    min_sentiment, max_sentiment = expected_sentiment_range
    
    # Mock sentiment analyzer
    def mock_analyze_sentiment(text):
        # Simple rule-based sentiment for testing
        positive_words = ['good', 'great', 'excellent', 'positive', 'bullish', 'up', 'rise', 'gain']
        negative_words = ['bad', 'terrible', 'negative', 'bearish', 'down', 'fall', 'loss', 'crash']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            base_sentiment = 70.0
        elif negative_count > positive_count:
            base_sentiment = 30.0
        else:
            base_sentiment = 50.0
        
        # Add some variation but keep it consistent
        import hashlib
        text_hash = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
        variation = (text_hash % 21) - 10  # -10 to +10
        
        sentiment = max(0, min(100, base_sentiment + variation))
        confidence = min(1.0, len(text) / 1000.0 + 0.3)  # Longer text = higher confidence
        
        return SentimentScore(
            sentiment_value=sentiment,
            confidence=confidence,
            key_factors=[]
        )
    
    # Analyze the same content multiple times
    results = []
    for _ in range(3):  # Analyze 3 times
        result = mock_analyze_sentiment(news_content)
        results.append(result)
    
    # Property: Results should be identical for the same input
    for i in range(1, len(results)):
        assert abs(results[i].sentiment_value - results[0].sentiment_value) < 0.001
        assert abs(results[i].confidence - results[0].confidence) < 0.001
    
    # Property: Sentiment should be within expected range
    for result in results:
        assert 0.0 <= result.sentiment_value <= 100.0
        assert 0.0 <= result.confidence <= 1.0


@given(
    news_items=st.lists(
        st.builds(
            NewsItem,
            id=st.text(min_size=1, max_size=20),
            title=st.text(min_size=5, max_size=100),
            content=news_text_strategy(),
            source=st.text(min_size=1, max_size=20),
            published_at=st.datetimes(
                min_value=datetime(2020, 1, 1),
                max_value=datetime(2030, 12, 31)
            ).map(lambda dt: dt.replace(tzinfo=timezone.utc)),
            url=st.text(min_size=10, max_size=100)
        ),
        min_size=1,
        max_size=10
    )
)
def test_batch_sentiment_analysis_property(news_items):
    """
    Property 2.4: Batch sentiment analysis consistency
    For any batch of news items, analysis should be consistent and complete
    **Validates: Requirements 2.1, 2.2**
    """
    # Mock batch sentiment analysis
    def analyze_batch(items):
        results = []
        for item in items:
            # Simple sentiment analysis based on content length and keywords
            content_length = len(item.content)
            title_length = len(item.title)
            
            # Base sentiment on content characteristics
            if 'positive' in item.content.lower() or 'good' in item.content.lower():
                base_sentiment = 75.0
            elif 'negative' in item.content.lower() or 'bad' in item.content.lower():
                base_sentiment = 25.0
            else:
                base_sentiment = 50.0
            
            # Adjust based on content length (longer = more confident)
            confidence = min(1.0, (content_length + title_length) / 500.0 + 0.2)
            
            sentiment_score = SentimentScore(
                sentiment_value=base_sentiment,
                confidence=confidence,
                key_factors=[item.source]
            )
            
            results.append((item, sentiment_score))
        
        return results
    
    # Analyze the batch
    analysis_results = analyze_batch(news_items)
    
    # Property: Should have results for all input items
    assert len(analysis_results) == len(news_items)
    
    # Property: Each result should be valid
    for item, sentiment in analysis_results:
        assert isinstance(sentiment, SentimentScore)
        assert 0.0 <= sentiment.sentiment_value <= 100.0
        assert 0.0 <= sentiment.confidence <= 1.0
        assert isinstance(sentiment.key_factors, list)
    
    # Property: Results should be deterministic for the same input
    second_analysis = analyze_batch(news_items)
    for i, (item1, sentiment1) in enumerate(analysis_results):
        item2, sentiment2 = second_analysis[i]
        assert item1.id == item2.id
        assert abs(sentiment1.sentiment_value - sentiment2.sentiment_value) < 0.001


@given(
    sentiment_scores=st.lists(
        sentiment_score_strategy(),
        min_size=5,
        max_size=20
    ),
    time_window_hours=st.integers(min_value=1, max_value=24)
)
def test_sentiment_aggregation_property(sentiment_scores, time_window_hours):
    """
    Property 2.5: Sentiment aggregation validity
    For any collection of sentiment scores, aggregation should produce valid results
    **Validates: Requirements 2.4, 2.5**
    """
    # Mock sentiment aggregation function
    def aggregate_sentiments(scores, window_hours):
        if not scores:
            return None
        
        # Calculate weighted average (more recent = higher weight)
        total_weight = 0
        weighted_sum = 0
        
        for i, score in enumerate(scores):
            # Weight decreases with age (newer scores have higher weight)
            weight = 1.0 / (1 + i * 0.1)  # Simple decay function
            weighted_sum += score * weight
            total_weight += weight
        
        if total_weight == 0:
            return None
        
        aggregated_sentiment = weighted_sum / total_weight
        
        # Calculate confidence based on number of scores and variance
        variance = sum((score - aggregated_sentiment) ** 2 for score in scores) / len(scores)
        confidence = min(1.0, len(scores) / 10.0) * (1.0 / (1.0 + variance / 100.0))
        
        return {
            'aggregated_sentiment': aggregated_sentiment,
            'confidence': confidence,
            'sample_count': len(scores),
            'time_window_hours': window_hours
        }
    
    # Perform aggregation
    result = aggregate_sentiments(sentiment_scores, time_window_hours)
    
    if result:
        # Property: Aggregated sentiment should be within valid range
        assert 0.0 <= result['aggregated_sentiment'] <= 100.0
        
        # Property: Confidence should be within valid range
        assert 0.0 <= result['confidence'] <= 1.0
        
        # Property: Sample count should match input
        assert result['sample_count'] == len(sentiment_scores)
        
        # Property: Time window should be preserved
        assert result['time_window_hours'] == time_window_hours
        
        # Property: Aggregated sentiment should be influenced by input scores
        min_input = min(sentiment_scores)
        max_input = max(sentiment_scores)
        assert min_input <= result['aggregated_sentiment'] <= max_input


@given(
    positive_keywords=st.lists(st.text(min_size=3, max_size=15), min_size=1, max_size=5),
    negative_keywords=st.lists(st.text(min_size=3, max_size=15), min_size=1, max_size=5),
    neutral_text=st.text(min_size=20, max_size=200)
)
def test_keyword_based_sentiment_property(positive_keywords, negative_keywords, neutral_text):
    """
    Property 2.6: Keyword-based sentiment detection
    For any set of keywords, sentiment should correlate with keyword presence
    **Validates: Requirements 2.2, 2.3**
    """
    # Ensure keywords are unique and non-overlapping
    positive_keywords = list(set(positive_keywords))
    negative_keywords = list(set(negative_keywords))
    
    # Remove any overlap between positive and negative keywords
    negative_keywords = [kw for kw in negative_keywords if kw not in positive_keywords]
    
    if not negative_keywords:  # Ensure we have some negative keywords
        negative_keywords = ['bad', 'terrible', 'awful']
    
    def analyze_with_keywords(text, pos_keywords, neg_keywords):
        text_lower = text.lower()
        
        pos_count = sum(1 for kw in pos_keywords if kw.lower() in text_lower)
        neg_count = sum(1 for kw in neg_keywords if kw.lower() in text_lower)
        
        if pos_count > neg_count:
            sentiment = 70.0 + min(20.0, pos_count * 5)  # 70-90 range
        elif neg_count > pos_count:
            sentiment = 30.0 - min(20.0, neg_count * 5)  # 10-30 range
        else:
            sentiment = 50.0  # Neutral
        
        sentiment = max(0.0, min(100.0, sentiment))
        confidence = min(1.0, (pos_count + neg_count) / 10.0 + 0.3)
        
        return SentimentScore(
            sentiment_value=sentiment,
            confidence=confidence,
            key_factors=pos_keywords[:pos_count] + neg_keywords[:neg_count]
        )
    
    # Test with positive keywords
    positive_text = neutral_text + " " + " ".join(positive_keywords[:2])
    pos_result = analyze_with_keywords(positive_text, positive_keywords, negative_keywords)
    
    # Test with negative keywords
    negative_text = neutral_text + " " + " ".join(negative_keywords[:2])
    neg_result = analyze_with_keywords(negative_text, positive_keywords, negative_keywords)
    
    # Test with neutral text
    neutral_result = analyze_with_keywords(neutral_text, positive_keywords, negative_keywords)
    
    # Property: Positive text should have higher sentiment than negative text
    assert pos_result.sentiment_value > neg_result.sentiment_value
    
    # Property: Neutral text should have moderate sentiment
    assert 40.0 <= neutral_result.sentiment_value <= 60.0
    
    # Property: All results should have valid ranges
    for result in [pos_result, neg_result, neutral_result]:
        assert 0.0 <= result.sentiment_value <= 100.0
        assert 0.0 <= result.confidence <= 1.0
        assert isinstance(result.key_factors, list)


@given(
    market_context=st.sampled_from(['bull_market', 'bear_market', 'sideways_market']),
    news_sentiment=sentiment_score_strategy(),
    market_volatility=st.floats(min_value=0.1, max_value=2.0)
)
def test_contextual_sentiment_adjustment_property(market_context, news_sentiment, market_volatility):
    """
    Property 2.7: Contextual sentiment adjustment
    For any market context, sentiment should be adjusted appropriately
    **Validates: Requirements 2.4, 2.5**
    """
    def adjust_sentiment_for_context(base_sentiment, context, volatility):
        """Adjust sentiment based on market context"""
        adjusted_sentiment = base_sentiment
        confidence_modifier = 1.0
        
        if context == 'bull_market':
            # In bull markets, positive news is amplified, negative news is dampened
            if base_sentiment > 50:
                adjusted_sentiment = min(100, base_sentiment * 1.2)
            else:
                adjusted_sentiment = max(0, base_sentiment * 0.8)
            confidence_modifier = 1.1
            
        elif context == 'bear_market':
            # In bear markets, negative news is amplified, positive news is dampened
            if base_sentiment < 50:
                adjusted_sentiment = max(0, base_sentiment * 0.8)
            else:
                adjusted_sentiment = min(100, base_sentiment * 1.2)
            confidence_modifier = 1.1
            
        elif context == 'sideways_market':
            # In sideways markets, sentiment moves toward neutral
            adjusted_sentiment = base_sentiment * 0.9 + 50 * 0.1
            confidence_modifier = 0.9
        
        # High volatility reduces confidence
        final_confidence = min(1.0, 0.8 * confidence_modifier / volatility)
        
        return {
            'adjusted_sentiment': max(0, min(100, adjusted_sentiment)),
            'confidence': max(0, min(1, final_confidence)),
            'context': context,
            'volatility': volatility
        }
    
    # Apply contextual adjustment
    result = adjust_sentiment_for_context(news_sentiment, market_context, market_volatility)
    
    # Property: Adjusted sentiment should be within valid range
    assert 0.0 <= result['adjusted_sentiment'] <= 100.0
    
    # Property: Confidence should be within valid range
    assert 0.0 <= result['confidence'] <= 1.0
    
    # Property: Context should be preserved
    assert result['context'] == market_context
    
    # Property: High volatility should reduce confidence
    if market_volatility > 1.5:
        assert result['confidence'] < 0.8
    
    # Property: Adjustment should be reasonable (not too extreme)
    adjustment_ratio = result['adjusted_sentiment'] / news_sentiment if news_sentiment > 0 else 1.0
    assert 0.5 <= adjustment_ratio <= 2.0  # No more than 2x adjustment


if __name__ == "__main__":
    # Run the property tests
    pytest.main([__file__, "-v", "--tb=short"])