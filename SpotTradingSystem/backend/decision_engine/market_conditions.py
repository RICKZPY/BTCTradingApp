"""
Market Conditions Assessment
Evaluates market conditions to determine if trading is appropriate
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
import numpy as np
from enum import Enum

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.data_models import MarketData, NewsItem, TechnicalSignal, SentimentScore

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """Market regime classifications"""
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    SIDEWAYS = "sideways"
    VOLATILE = "volatile"
    LOW_VOLUME = "low_volume"
    BREAKOUT = "breakout"
    REVERSAL = "reversal"


class TradingRecommendation(Enum):
    """Trading recommendations based on market conditions"""
    FAVORABLE = "favorable"
    CAUTIOUS = "cautious"
    AVOID = "avoid"
    WAIT = "wait"


@dataclass
class MarketConditionAssessment:
    """Comprehensive market condition assessment"""
    
    # Market regime
    primary_regime: MarketRegime
    secondary_regimes: List[MarketRegime]
    regime_confidence: float  # 0 to 1
    
    # Trading recommendation
    trading_recommendation: TradingRecommendation
    recommendation_reasoning: str
    
    # Market metrics
    volatility_score: float  # 0 to 1 (0 = low volatility, 1 = high volatility)
    volume_score: float  # 0 to 1 (0 = low volume, 1 = high volume)
    trend_strength: float  # -1 to 1 (-1 = strong downtrend, 1 = strong uptrend)
    momentum_score: float  # -1 to 1 (-1 = strong bearish momentum, 1 = strong bullish momentum)
    
    # Risk factors
    risk_factors: List[str]
    opportunity_factors: List[str]
    
    # Timing assessment
    entry_timing_score: float  # 0 to 1 (0 = poor timing, 1 = excellent timing)
    exit_timing_score: float  # 0 to 1 (0 = poor timing, 1 = excellent timing)
    
    # Supporting data
    analysis_timestamp: datetime
    data_quality_score: float  # 0 to 1 (quality of underlying data)
    
    def __post_init__(self):
        """Validate market condition assessment"""
        if not 0 <= self.regime_confidence <= 1:
            raise ValueError("Regime confidence must be between 0 and 1")
        
        if not 0 <= self.volatility_score <= 1:
            raise ValueError("Volatility score must be between 0 and 1")
        
        if not 0 <= self.volume_score <= 1:
            raise ValueError("Volume score must be between 0 and 1")
        
        if not -1 <= self.trend_strength <= 1:
            raise ValueError("Trend strength must be between -1 and 1")
        
        if not -1 <= self.momentum_score <= 1:
            raise ValueError("Momentum score must be between -1 and 1")
        
        if not 0 <= self.entry_timing_score <= 1:
            raise ValueError("Entry timing score must be between 0 and 1")
        
        if not 0 <= self.exit_timing_score <= 1:
            raise ValueError("Exit timing score must be between 0 and 1")
        
        if not 0 <= self.data_quality_score <= 1:
            raise ValueError("Data quality score must be between 0 and 1")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'primary_regime': self.primary_regime.value,
            'secondary_regimes': [regime.value for regime in self.secondary_regimes],
            'regime_confidence': self.regime_confidence,
            'trading_recommendation': self.trading_recommendation.value,
            'recommendation_reasoning': self.recommendation_reasoning,
            'volatility_score': self.volatility_score,
            'volume_score': self.volume_score,
            'trend_strength': self.trend_strength,
            'momentum_score': self.momentum_score,
            'risk_factors': self.risk_factors,
            'opportunity_factors': self.opportunity_factors,
            'entry_timing_score': self.entry_timing_score,
            'exit_timing_score': self.exit_timing_score,
            'analysis_timestamp': self.analysis_timestamp.isoformat(),
            'data_quality_score': self.data_quality_score
        }


class MarketConditionEvaluator:
    """
    Evaluates market conditions to determine if trading is appropriate
    """
    
    def __init__(self, 
                 volatility_threshold: float = 0.05,
                 volume_threshold: float = 1000000,
                 trend_lookback_hours: int = 24,
                 momentum_lookback_hours: int = 6):
        """
        Initialize market condition evaluator
        
        Args:
            volatility_threshold: Threshold for high volatility (default 5%)
            volume_threshold: Minimum volume threshold
            trend_lookback_hours: Hours to look back for trend analysis
            momentum_lookback_hours: Hours to look back for momentum analysis
        """
        self.volatility_threshold = volatility_threshold
        self.volume_threshold = volume_threshold
        self.trend_lookback_hours = trend_lookback_hours
        self.momentum_lookback_hours = momentum_lookback_hours
        
        logger.info(f"Market condition evaluator initialized with volatility_threshold={volatility_threshold}")
    
    def _calculate_volatility_metrics(self, market_data: List[MarketData]) -> Dict[str, float]:
        """
        Calculate volatility metrics from market data
        
        Args:
            market_data: List of market data points
            
        Returns:
            Dictionary with volatility metrics
        """
        if len(market_data) < 2:
            return {
                'volatility': 0.0,
                'price_range': 0.0,
                'volatility_score': 0.0
            }
        
        prices = [data.price for data in market_data]
        
        # Calculate returns
        returns = np.diff(prices) / prices[:-1]
        
        # Calculate volatility (standard deviation of returns)
        volatility = np.std(returns) if len(returns) > 0 else 0.0
        
        # Calculate price range
        price_range = (max(prices) - min(prices)) / np.mean(prices) if np.mean(prices) > 0 else 0.0
        
        # Normalize volatility score (0 to 1)
        volatility_score = min(1.0, volatility / self.volatility_threshold)
        
        return {
            'volatility': volatility,
            'price_range': price_range,
            'volatility_score': volatility_score
        }
    
    def _calculate_volume_metrics(self, market_data: List[MarketData]) -> Dict[str, float]:
        """
        Calculate volume metrics from market data
        
        Args:
            market_data: List of market data points
            
        Returns:
            Dictionary with volume metrics
        """
        if not market_data:
            return {
                'average_volume': 0.0,
                'current_volume': 0.0,
                'volume_trend': 0.0,
                'volume_score': 0.0
            }
        
        volumes = [data.volume for data in market_data]
        current_volume = volumes[-1] if volumes else 0.0
        average_volume = np.mean(volumes) if volumes else 0.0
        
        # Calculate volume trend (recent vs historical)
        if len(volumes) >= 6:
            recent_volume = np.mean(volumes[-6:])  # Last 6 periods
            historical_volume = np.mean(volumes[:-6])  # Earlier periods
            volume_trend = (recent_volume - historical_volume) / historical_volume if historical_volume > 0 else 0.0
        else:
            volume_trend = 0.0
        
        # Normalize volume score
        volume_score = min(1.0, current_volume / self.volume_threshold) if self.volume_threshold > 0 else 1.0
        
        return {
            'average_volume': average_volume,
            'current_volume': current_volume,
            'volume_trend': volume_trend,
            'volume_score': volume_score
        }
    
    def _calculate_trend_strength(self, market_data: List[MarketData]) -> float:
        """
        Calculate trend strength from market data
        
        Args:
            market_data: List of market data points
            
        Returns:
            Trend strength (-1 to 1)
        """
        if len(market_data) < 3:
            return 0.0
        
        prices = [data.price for data in market_data]
        
        # Calculate linear regression slope
        x = np.arange(len(prices))
        slope, _ = np.polyfit(x, prices, 1)
        
        # Normalize slope to trend strength
        price_mean = np.mean(prices)
        if price_mean > 0:
            trend_strength = slope / price_mean * len(prices)  # Scale by number of periods
            trend_strength = max(-1.0, min(1.0, trend_strength))  # Clamp to [-1, 1]
        else:
            trend_strength = 0.0
        
        return trend_strength
    
    def _calculate_momentum_score(self, market_data: List[MarketData]) -> float:
        """
        Calculate momentum score from recent market data
        
        Args:
            market_data: List of market data points
            
        Returns:
            Momentum score (-1 to 1)
        """
        if len(market_data) < 2:
            return 0.0
        
        prices = [data.price for data in market_data]
        
        # Calculate rate of change
        if len(prices) >= 6:
            recent_price = prices[-1]
            earlier_price = prices[-6]  # 6 periods ago
            roc = (recent_price - earlier_price) / earlier_price if earlier_price > 0 else 0.0
        else:
            recent_price = prices[-1]
            earlier_price = prices[0]
            roc = (recent_price - earlier_price) / earlier_price if earlier_price > 0 else 0.0
        
        # Normalize to momentum score
        momentum_score = max(-1.0, min(1.0, roc * 10))  # Scale and clamp
        
        return momentum_score
    
    def _identify_market_regime(self, volatility_score: float, volume_score: float,
                              trend_strength: float, momentum_score: float) -> Tuple[MarketRegime, List[MarketRegime], float]:
        """
        Identify primary and secondary market regimes
        
        Args:
            volatility_score: Volatility score (0 to 1)
            volume_score: Volume score (0 to 1)
            trend_strength: Trend strength (-1 to 1)
            momentum_score: Momentum score (-1 to 1)
            
        Returns:
            Tuple of (primary_regime, secondary_regimes, confidence)
        """
        regimes = []
        regime_scores = {}
        
        # Trending regimes
        if abs(trend_strength) > 0.3:
            if trend_strength > 0:
                regimes.append(MarketRegime.TRENDING_UP)
                regime_scores[MarketRegime.TRENDING_UP] = abs(trend_strength)
            else:
                regimes.append(MarketRegime.TRENDING_DOWN)
                regime_scores[MarketRegime.TRENDING_DOWN] = abs(trend_strength)
        
        # Volatile regime
        if volatility_score > 0.7:
            regimes.append(MarketRegime.VOLATILE)
            regime_scores[MarketRegime.VOLATILE] = volatility_score
        
        # Low volume regime
        if volume_score < 0.3:
            regimes.append(MarketRegime.LOW_VOLUME)
            regime_scores[MarketRegime.LOW_VOLUME] = 1 - volume_score
        
        # Sideways regime
        if abs(trend_strength) < 0.2 and volatility_score < 0.5:
            regimes.append(MarketRegime.SIDEWAYS)
            regime_scores[MarketRegime.SIDEWAYS] = 1 - abs(trend_strength)
        
        # Breakout regime (high volume + momentum)
        if volume_score > 0.7 and abs(momentum_score) > 0.5:
            regimes.append(MarketRegime.BREAKOUT)
            regime_scores[MarketRegime.BREAKOUT] = (volume_score + abs(momentum_score)) / 2
        
        # Reversal regime (momentum opposite to trend)
        if abs(trend_strength) > 0.3 and abs(momentum_score) > 0.3:
            if np.sign(trend_strength) != np.sign(momentum_score):
                regimes.append(MarketRegime.REVERSAL)
                regime_scores[MarketRegime.REVERSAL] = (abs(trend_strength) + abs(momentum_score)) / 2
        
        # Determine primary regime
        if regimes:
            primary_regime = max(regimes, key=lambda r: regime_scores.get(r, 0))
            secondary_regimes = [r for r in regimes if r != primary_regime]
            confidence = regime_scores.get(primary_regime, 0.5)
        else:
            primary_regime = MarketRegime.SIDEWAYS
            secondary_regimes = []
            confidence = 0.3
        
        return primary_regime, secondary_regimes, confidence
    
    def _assess_trading_recommendation(self, primary_regime: MarketRegime,
                                     secondary_regimes: List[MarketRegime],
                                     volatility_score: float,
                                     volume_score: float,
                                     sentiment_score: Optional[SentimentScore] = None) -> Tuple[TradingRecommendation, str]:
        """
        Assess trading recommendation based on market conditions
        
        Args:
            primary_regime: Primary market regime
            secondary_regimes: Secondary market regimes
            volatility_score: Volatility score
            volume_score: Volume score
            sentiment_score: Optional sentiment analysis
            
        Returns:
            Tuple of (recommendation, reasoning)
        """
        risk_factors = []
        opportunity_factors = []
        
        # Analyze primary regime
        if primary_regime == MarketRegime.TRENDING_UP:
            opportunity_factors.append("Strong uptrend")
        elif primary_regime == MarketRegime.TRENDING_DOWN:
            opportunity_factors.append("Clear downtrend for short positions")
        elif primary_regime == MarketRegime.VOLATILE:
            risk_factors.append("High volatility increases risk")
        elif primary_regime == MarketRegime.LOW_VOLUME:
            risk_factors.append("Low volume reduces liquidity")
        elif primary_regime == MarketRegime.BREAKOUT:
            opportunity_factors.append("Breakout pattern detected")
        elif primary_regime == MarketRegime.REVERSAL:
            opportunity_factors.append("Potential reversal opportunity")
        elif primary_regime == MarketRegime.SIDEWAYS:
            risk_factors.append("Sideways market lacks clear direction")
        
        # Analyze secondary regimes
        for regime in secondary_regimes:
            if regime == MarketRegime.VOLATILE:
                risk_factors.append("Secondary volatility concern")
            elif regime == MarketRegime.LOW_VOLUME:
                risk_factors.append("Volume concerns")
        
        # Volume and volatility factors
        if volume_score < 0.3:
            risk_factors.append("Insufficient trading volume")
        elif volume_score > 0.8:
            opportunity_factors.append("High trading volume")
        
        if volatility_score > 0.8:
            risk_factors.append("Excessive volatility")
        elif volatility_score < 0.2:
            opportunity_factors.append("Low volatility environment")
        
        # Sentiment factors
        if sentiment_score:
            if sentiment_score.sentiment_value > 70 and sentiment_score.confidence > 0.7:
                opportunity_factors.append("Positive market sentiment")
            elif sentiment_score.sentiment_value < 30 and sentiment_score.confidence > 0.7:
                risk_factors.append("Negative market sentiment")
        
        # Determine recommendation
        risk_count = len(risk_factors)
        opportunity_count = len(opportunity_factors)
        
        if opportunity_count >= 2 and risk_count <= 1:
            recommendation = TradingRecommendation.FAVORABLE
            reasoning = f"Favorable conditions: {', '.join(opportunity_factors)}"
        elif risk_count >= 2:
            recommendation = TradingRecommendation.AVOID
            reasoning = f"Avoid trading: {', '.join(risk_factors)}"
        elif opportunity_count >= 1 and risk_count <= 1:
            recommendation = TradingRecommendation.CAUTIOUS
            reasoning = f"Proceed with caution: {', '.join(opportunity_factors + risk_factors)}"
        else:
            recommendation = TradingRecommendation.WAIT
            reasoning = "Mixed signals - wait for clearer conditions"
        
        return recommendation, reasoning
    
    def _calculate_timing_scores(self, primary_regime: MarketRegime,
                               trend_strength: float,
                               momentum_score: float,
                               volatility_score: float) -> Tuple[float, float]:
        """
        Calculate entry and exit timing scores
        
        Args:
            primary_regime: Primary market regime
            trend_strength: Trend strength
            momentum_score: Momentum score
            volatility_score: Volatility score
            
        Returns:
            Tuple of (entry_timing_score, exit_timing_score)
        """
        # Entry timing factors
        entry_factors = []
        
        if primary_regime in [MarketRegime.TRENDING_UP, MarketRegime.TRENDING_DOWN]:
            entry_factors.append(abs(trend_strength))
        
        if primary_regime == MarketRegime.BREAKOUT:
            entry_factors.append(0.8)  # Breakouts are good entry points
        
        if abs(momentum_score) > 0.5:
            entry_factors.append(abs(momentum_score))
        
        if volatility_score < 0.5:  # Lower volatility is better for entry
            entry_factors.append(1 - volatility_score)
        
        # Exit timing factors
        exit_factors = []
        
        if primary_regime == MarketRegime.REVERSAL:
            exit_factors.append(0.9)  # Reversals are good exit points
        
        if volatility_score > 0.7:  # High volatility suggests exit
            exit_factors.append(volatility_score)
        
        if primary_regime == MarketRegime.SIDEWAYS:
            exit_factors.append(0.6)  # Sideways markets suggest taking profits
        
        # Calculate scores
        entry_timing_score = np.mean(entry_factors) if entry_factors else 0.3
        exit_timing_score = np.mean(exit_factors) if exit_factors else 0.3
        
        return min(1.0, entry_timing_score), min(1.0, exit_timing_score)
    
    def _assess_data_quality(self, market_data: List[MarketData],
                           news_items: Optional[List[NewsItem]] = None) -> float:
        """
        Assess the quality of input data for analysis
        
        Args:
            market_data: Market data points
            news_items: Optional news items
            
        Returns:
            Data quality score (0 to 1)
        """
        quality_factors = []
        
        # Market data quality
        if market_data:
            # Check data recency
            latest_data = max(market_data, key=lambda x: x.timestamp)
            data_age = datetime.utcnow() - latest_data.timestamp
            if data_age.total_seconds() < 3600:  # Less than 1 hour old
                quality_factors.append(1.0)
            elif data_age.total_seconds() < 7200:  # Less than 2 hours old
                quality_factors.append(0.8)
            else:
                quality_factors.append(0.5)
            
            # Check data completeness
            if len(market_data) >= 24:  # At least 24 data points
                quality_factors.append(1.0)
            elif len(market_data) >= 12:
                quality_factors.append(0.7)
            else:
                quality_factors.append(0.4)
            
            # Check for data gaps
            timestamps = [data.timestamp for data in market_data]
            timestamps.sort()
            gaps = []
            for i in range(1, len(timestamps)):
                gap = (timestamps[i] - timestamps[i-1]).total_seconds()
                gaps.append(gap)
            
            if gaps:
                avg_gap = np.mean(gaps)
                max_gap = max(gaps)
                if max_gap < avg_gap * 3:  # No large gaps
                    quality_factors.append(1.0)
                else:
                    quality_factors.append(0.6)
        else:
            quality_factors.append(0.0)
        
        # News data quality (if provided)
        if news_items:
            recent_news = [item for item in news_items 
                          if (datetime.utcnow() - item.published_at).total_seconds() < 86400]  # Last 24 hours
            if len(recent_news) >= 5:
                quality_factors.append(0.8)
            elif len(recent_news) >= 2:
                quality_factors.append(0.6)
            else:
                quality_factors.append(0.4)
        
        return np.mean(quality_factors) if quality_factors else 0.3
    
    def evaluate_market_conditions(self, 
                                 market_data: List[MarketData],
                                 sentiment_score: Optional[SentimentScore] = None,
                                 technical_signal: Optional[TechnicalSignal] = None,
                                 news_items: Optional[List[NewsItem]] = None) -> MarketConditionAssessment:
        """
        Evaluate comprehensive market conditions
        
        Args:
            market_data: Recent market data
            sentiment_score: Optional sentiment analysis
            technical_signal: Optional technical analysis signal
            news_items: Optional recent news items
            
        Returns:
            MarketConditionAssessment with comprehensive analysis
        """
        logger.info(f"Evaluating market conditions with {len(market_data)} data points")
        
        # Filter data by time windows
        current_time = datetime.utcnow()
        trend_cutoff = current_time - timedelta(hours=self.trend_lookback_hours)
        momentum_cutoff = current_time - timedelta(hours=self.momentum_lookback_hours)
        
        trend_data = [data for data in market_data if data.timestamp >= trend_cutoff]
        momentum_data = [data for data in market_data if data.timestamp >= momentum_cutoff]
        
        # Calculate metrics
        volatility_metrics = self._calculate_volatility_metrics(trend_data)
        volume_metrics = self._calculate_volume_metrics(trend_data)
        trend_strength = self._calculate_trend_strength(trend_data)
        momentum_score = self._calculate_momentum_score(momentum_data)
        
        # Identify market regime
        primary_regime, secondary_regimes, regime_confidence = self._identify_market_regime(
            volatility_metrics['volatility_score'],
            volume_metrics['volume_score'],
            trend_strength,
            momentum_score
        )
        
        # Assess trading recommendation
        trading_recommendation, recommendation_reasoning = self._assess_trading_recommendation(
            primary_regime,
            secondary_regimes,
            volatility_metrics['volatility_score'],
            volume_metrics['volume_score'],
            sentiment_score
        )
        
        # Calculate timing scores
        entry_timing_score, exit_timing_score = self._calculate_timing_scores(
            primary_regime,
            trend_strength,
            momentum_score,
            volatility_metrics['volatility_score']
        )
        
        # Assess data quality
        data_quality_score = self._assess_data_quality(market_data, news_items)
        
        # Identify risk and opportunity factors
        risk_factors = []
        opportunity_factors = []
        
        if volatility_metrics['volatility_score'] > 0.7:
            risk_factors.append("High volatility")
        
        if volume_metrics['volume_score'] < 0.3:
            risk_factors.append("Low trading volume")
        
        if abs(trend_strength) > 0.5:
            if trend_strength > 0:
                opportunity_factors.append("Strong uptrend")
            else:
                opportunity_factors.append("Strong downtrend")
        
        if primary_regime == MarketRegime.BREAKOUT:
            opportunity_factors.append("Breakout pattern")
        
        if data_quality_score < 0.5:
            risk_factors.append("Poor data quality")
        
        assessment = MarketConditionAssessment(
            primary_regime=primary_regime,
            secondary_regimes=secondary_regimes,
            regime_confidence=regime_confidence,
            trading_recommendation=trading_recommendation,
            recommendation_reasoning=recommendation_reasoning,
            volatility_score=volatility_metrics['volatility_score'],
            volume_score=volume_metrics['volume_score'],
            trend_strength=trend_strength,
            momentum_score=momentum_score,
            risk_factors=risk_factors,
            opportunity_factors=opportunity_factors,
            entry_timing_score=entry_timing_score,
            exit_timing_score=exit_timing_score,
            analysis_timestamp=current_time,
            data_quality_score=data_quality_score
        )
        
        logger.info(f"Market condition assessment completed: {primary_regime.value}, recommendation: {trading_recommendation.value}")
        
        return assessment
    
    def is_suitable_for_trading(self, assessment: MarketConditionAssessment) -> bool:
        """
        Determine if market conditions are suitable for trading
        
        Args:
            assessment: Market condition assessment
            
        Returns:
            True if conditions are suitable for trading
        """
        # Check trading recommendation
        if assessment.trading_recommendation == TradingRecommendation.AVOID:
            return False
        
        # Check data quality
        if assessment.data_quality_score < 0.4:
            return False
        
        # Check for critical risk factors
        critical_risks = ["Excessive volatility", "Insufficient trading volume", "Poor data quality"]
        if any(risk in assessment.risk_factors for risk in critical_risks):
            return False
        
        # Check regime confidence
        if assessment.regime_confidence < 0.3:
            return False
        
        return True
    
    def get_dynamic_strategy_adjustments(self, assessment: MarketConditionAssessment) -> Dict[str, Any]:
        """
        Get dynamic strategy adjustments based on market conditions
        
        Args:
            assessment: Market condition assessment
            
        Returns:
            Dictionary with strategy adjustment recommendations
        """
        adjustments = {
            "position_size_multiplier": 1.0,
            "stop_loss_adjustment": 1.0,
            "take_profit_adjustment": 1.0,
            "confidence_threshold_adjustment": 0.0,
            "recommended_timeframe": "normal",
            "special_instructions": []
        }
        
        # Adjust based on volatility
        if assessment.volatility_score > 0.7:
            adjustments["position_size_multiplier"] *= 0.7  # Reduce position size
            adjustments["stop_loss_adjustment"] *= 1.5  # Wider stop loss
            adjustments["confidence_threshold_adjustment"] += 0.1  # Higher confidence required
            adjustments["special_instructions"].append("High volatility - reduce risk")
        
        # Adjust based on volume
        if assessment.volume_score < 0.4:
            adjustments["position_size_multiplier"] *= 0.8  # Reduce position size
            adjustments["recommended_timeframe"] = "longer"
            adjustments["special_instructions"].append("Low volume - use longer timeframes")
        
        # Adjust based on trend strength
        if abs(assessment.trend_strength) > 0.6:
            adjustments["take_profit_adjustment"] *= 1.3  # Wider take profit in strong trends
            adjustments["special_instructions"].append("Strong trend - let profits run")
        
        # Adjust based on regime
        if assessment.primary_regime == MarketRegime.VOLATILE:
            adjustments["position_size_multiplier"] *= 0.6
            adjustments["confidence_threshold_adjustment"] += 0.15
            adjustments["special_instructions"].append("Volatile regime - extra caution")
        elif assessment.primary_regime == MarketRegime.BREAKOUT:
            adjustments["position_size_multiplier"] *= 1.2  # Increase position size for breakouts
            adjustments["special_instructions"].append("Breakout detected - opportunity for larger position")
        
        return adjustments