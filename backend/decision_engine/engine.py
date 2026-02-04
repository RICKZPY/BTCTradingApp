"""
Decision Engine Core
Combines sentiment analysis and technical indicators to generate trading decisions
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
import numpy as np

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.data_models import (
    SentimentScore, TechnicalSignal, Portfolio, TradingDecision, 
    ActionType, RiskLevel, PriceRange, MarketData
)
from decision_engine.risk_parameters import RiskParameters

logger = logging.getLogger(__name__)


@dataclass
class MarketAnalysis:
    """Market analysis combining sentiment and technical data"""
    
    # Input data
    sentiment_score: SentimentScore
    technical_signal: TechnicalSignal
    current_price: float
    portfolio: Portfolio
    
    # Analysis results
    combined_signal_strength: float  # -1 to 1
    overall_confidence: float  # 0 to 1
    market_condition: str  # "bullish", "bearish", "neutral", "volatile"
    risk_assessment: str  # "low", "medium", "high", "critical"
    
    # Supporting data
    sentiment_contribution: float
    technical_contribution: float
    volume_analysis: Optional[Dict[str, float]] = None
    volatility_analysis: Optional[Dict[str, float]] = None
    
    def __post_init__(self):
        """Validate market analysis data"""
        if not -1 <= self.combined_signal_strength <= 1:
            raise ValueError("Combined signal strength must be between -1 and 1")
        
        if not 0 <= self.overall_confidence <= 1:
            raise ValueError("Overall confidence must be between 0 and 1")
        
        if self.market_condition not in ["bullish", "bearish", "neutral", "volatile"]:
            raise ValueError("Market condition must be one of: bullish, bearish, neutral, volatile")
        
        if self.risk_assessment not in ["low", "medium", "high", "critical"]:
            raise ValueError("Risk assessment must be one of: low, medium, high, critical")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'sentiment_score': self.sentiment_score.to_dict(),
            'technical_signal': self.technical_signal.to_dict(),
            'current_price': self.current_price,
            'portfolio': self.portfolio.to_dict(),
            'combined_signal_strength': self.combined_signal_strength,
            'overall_confidence': self.overall_confidence,
            'market_condition': self.market_condition,
            'risk_assessment': self.risk_assessment,
            'sentiment_contribution': self.sentiment_contribution,
            'technical_contribution': self.technical_contribution,
            'volume_analysis': self.volume_analysis,
            'volatility_analysis': self.volatility_analysis
        }


class DecisionEngine:
    """
    Core decision engine that combines sentiment analysis and technical indicators
    to generate trading decisions with risk management
    """
    
    def __init__(self, risk_params: Optional[RiskParameters] = None):
        """
        Initialize decision engine
        
        Args:
            risk_params: Risk management parameters (uses default if None)
        """
        self.risk_params = risk_params or RiskParameters()
        self.last_trade_time: Optional[datetime] = None
        self.daily_loss: float = 0.0
        self.daily_loss_reset_time: datetime = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        logger.info(f"Decision engine initialized with risk parameters: {self.risk_params.to_dict()}")
    
    def _reset_daily_loss_if_needed(self):
        """Reset daily loss counter if it's a new day"""
        current_time = datetime.utcnow()
        if current_time.date() > self.daily_loss_reset_time.date():
            self.daily_loss = 0.0
            self.daily_loss_reset_time = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
            logger.info("Daily loss counter reset for new day")
    
    def _calculate_sentiment_signal(self, sentiment_score: SentimentScore) -> Tuple[float, float]:
        """
        Convert sentiment score to trading signal
        
        Args:
            sentiment_score: Sentiment analysis result
            
        Returns:
            Tuple of (signal_strength, confidence)
        """
        # Convert 0-100 sentiment to -1 to 1 signal
        # 0-40: bearish, 40-60: neutral, 60-100: bullish
        if sentiment_score.sentiment_value <= 40:
            # Bearish sentiment
            signal_strength = -((40 - sentiment_score.sentiment_value) / 40)
        elif sentiment_score.sentiment_value >= 60:
            # Bullish sentiment
            signal_strength = (sentiment_score.sentiment_value - 60) / 40
        else:
            # Neutral sentiment
            signal_strength = (sentiment_score.sentiment_value - 50) / 50 * 0.3  # Weak signal in neutral zone
        
        # Adjust confidence based on sentiment confidence
        adjusted_confidence = sentiment_score.confidence * 0.9  # Slightly reduce confidence
        
        return round(signal_strength, 3), round(adjusted_confidence, 3)
    
    def _combine_signals(self, sentiment_score: SentimentScore, 
                        technical_signal: TechnicalSignal) -> Tuple[float, float, float, float]:
        """
        Combine sentiment and technical signals using weighted average
        
        Args:
            sentiment_score: Sentiment analysis result
            technical_signal: Technical analysis signal
            
        Returns:
            Tuple of (combined_strength, combined_confidence, sentiment_contribution, technical_contribution)
        """
        # Get sentiment signal
        sentiment_strength, sentiment_confidence = self._calculate_sentiment_signal(sentiment_score)
        
        # Technical signal is already in -1 to 1 range
        technical_strength = technical_signal.signal_strength
        technical_confidence = technical_signal.confidence
        
        # Calculate weighted contributions
        sentiment_contribution = sentiment_strength * self.risk_params.sentiment_weight
        technical_contribution = technical_strength * self.risk_params.technical_weight
        
        # Combined signal strength
        combined_strength = sentiment_contribution + technical_contribution
        
        # Combined confidence (weighted average)
        combined_confidence = (
            sentiment_confidence * self.risk_params.sentiment_weight +
            technical_confidence * self.risk_params.technical_weight
        )
        
        # Reduce confidence if signals conflict
        if np.sign(sentiment_strength) != np.sign(technical_strength) and abs(sentiment_strength) > 0.2 and abs(technical_strength) > 0.2:
            combined_confidence *= 0.7  # Reduce confidence by 30% for conflicting signals
            logger.info("Conflicting signals detected - reducing confidence")
        
        return (
            round(combined_strength, 3),
            round(combined_confidence, 3),
            round(sentiment_contribution, 3),
            round(technical_contribution, 3)
        )
    
    def _assess_market_condition(self, combined_strength: float, 
                               technical_signal: TechnicalSignal,
                               volatility: Optional[float] = None) -> str:
        """
        Assess overall market condition
        
        Args:
            combined_strength: Combined signal strength
            technical_signal: Technical analysis signal
            volatility: Market volatility (optional)
            
        Returns:
            Market condition string
        """
        # Check for high volatility
        if volatility and volatility > self.risk_params.max_volatility_threshold:
            return "volatile"
        
        # Assess based on signal strength and technical indicators
        if combined_strength > 0.4:
            return "bullish"
        elif combined_strength < -0.4:
            return "bearish"
        else:
            return "neutral"
    
    def _assess_risk_level(self, combined_confidence: float, market_condition: str,
                          portfolio: Portfolio, current_price: float) -> str:
        """
        Assess risk level for the trading decision
        
        Args:
            combined_confidence: Combined confidence score
            market_condition: Market condition assessment
            portfolio: Current portfolio state
            current_price: Current market price
            
        Returns:
            Risk level string
        """
        risk_factors = []
        
        # Low confidence increases risk
        if combined_confidence < 0.5:
            risk_factors.append("low_confidence")
        
        # Volatile market increases risk
        if market_condition == "volatile":
            risk_factors.append("volatile_market")
        
        # High portfolio risk increases overall risk
        portfolio_risk = abs(portfolio.unrealized_pnl) / portfolio.total_value_usdt if portfolio.total_value_usdt > 0 else 0
        if portfolio_risk > self.risk_params.max_portfolio_risk * 0.8:
            risk_factors.append("high_portfolio_risk")
        
        # Daily loss approaching limit increases risk
        if self.daily_loss > self.risk_params.max_daily_loss * 0.7:
            risk_factors.append("high_daily_loss")
        
        # Determine risk level based on factors
        if len(risk_factors) >= 3:
            return "critical"
        elif len(risk_factors) >= 2:
            return "high"
        elif len(risk_factors) >= 1:
            return "medium"
        else:
            return "low"
    
    def _check_trading_constraints(self, portfolio: Portfolio) -> List[str]:
        """
        Check if trading is allowed based on risk constraints
        
        Args:
            portfolio: Current portfolio state
            
        Returns:
            List of constraint violations (empty if trading is allowed)
        """
        self._reset_daily_loss_if_needed()
        
        violations = []
        
        # Check daily loss limit
        if self.daily_loss >= self.risk_params.max_daily_loss:
            violations.append(f"Daily loss limit exceeded: {self.daily_loss:.2%} >= {self.risk_params.max_daily_loss:.2%}")
        
        # Check portfolio risk limit
        if portfolio.total_value_usdt > 0:
            portfolio_risk = abs(portfolio.unrealized_pnl) / portfolio.total_value_usdt
            if portfolio_risk >= self.risk_params.max_portfolio_risk:
                violations.append(f"Portfolio risk limit exceeded: {portfolio_risk:.2%} >= {self.risk_params.max_portfolio_risk:.2%}")
        
        # Check trade cooldown
        if self.last_trade_time:
            time_since_last_trade = datetime.utcnow() - self.last_trade_time
            cooldown_period = timedelta(minutes=self.risk_params.trade_cooldown_minutes)
            if time_since_last_trade < cooldown_period:
                remaining_cooldown = cooldown_period - time_since_last_trade
                violations.append(f"Trade cooldown active: {remaining_cooldown.total_seconds():.0f} seconds remaining")
        
        return violations
    
    def analyze_market_conditions(self, sentiment_score: SentimentScore,
                                technical_signal: TechnicalSignal,
                                portfolio: Portfolio,
                                current_price: float,
                                market_data: Optional[List[MarketData]] = None) -> MarketAnalysis:
        """
        Analyze market conditions by combining sentiment and technical data
        
        Args:
            sentiment_score: Sentiment analysis result
            technical_signal: Technical analysis signal
            portfolio: Current portfolio state
            current_price: Current market price
            market_data: Optional recent market data for volume/volatility analysis
            
        Returns:
            MarketAnalysis object with comprehensive market assessment
        """
        logger.info(f"Analyzing market conditions - Sentiment: {sentiment_score.sentiment_value}, Technical: {technical_signal.signal_type.value}")
        
        # Combine signals
        combined_strength, combined_confidence, sentiment_contrib, technical_contrib = self._combine_signals(
            sentiment_score, technical_signal
        )
        
        # Analyze volume and volatility if market data is available
        volume_analysis = None
        volatility_analysis = None
        volatility = None
        
        if market_data and len(market_data) > 1:
            # Calculate volume analysis
            volumes = [data.volume for data in market_data[-24:]]  # Last 24 data points
            avg_volume = np.mean(volumes)
            current_volume = market_data[-1].volume
            volume_analysis = {
                "current_volume": current_volume,
                "average_volume": avg_volume,
                "volume_ratio": current_volume / avg_volume if avg_volume > 0 else 1.0
            }
            
            # Calculate volatility analysis
            prices = [data.price for data in market_data[-24:]]
            if len(prices) > 1:
                returns = np.diff(prices) / prices[:-1]
                volatility = np.std(returns)
                volatility_analysis = {
                    "volatility": volatility,
                    "price_range": max(prices) - min(prices),
                    "price_change_24h": (prices[-1] - prices[0]) / prices[0] if prices[0] > 0 else 0
                }
        
        # Assess market condition and risk
        market_condition = self._assess_market_condition(combined_strength, technical_signal, volatility)
        risk_assessment = self._assess_risk_level(combined_confidence, market_condition, portfolio, current_price)
        
        analysis = MarketAnalysis(
            sentiment_score=sentiment_score,
            technical_signal=technical_signal,
            current_price=current_price,
            portfolio=portfolio,
            combined_signal_strength=combined_strength,
            overall_confidence=combined_confidence,
            market_condition=market_condition,
            risk_assessment=risk_assessment,
            sentiment_contribution=sentiment_contrib,
            technical_contribution=technical_contrib,
            volume_analysis=volume_analysis,
            volatility_analysis=volatility_analysis
        )
        
        logger.info(f"Market analysis completed - Combined strength: {combined_strength}, Confidence: {combined_confidence}, Condition: {market_condition}")
        
        return analysis
    
    def generate_trading_decision(self, analysis: MarketAnalysis) -> TradingDecision:
        """
        Generate trading decision based on market analysis
        
        Args:
            analysis: Market analysis result
            
        Returns:
            TradingDecision with recommended action and parameters
        """
        logger.info("Generating trading decision from market analysis")
        
        # Check trading constraints
        constraint_violations = self._check_trading_constraints(analysis.portfolio)
        if constraint_violations:
            logger.warning(f"Trading constraints violated: {constraint_violations}")
            return self._create_hold_decision(
                analysis.current_price,
                f"Trading blocked due to constraints: {'; '.join(constraint_violations)}",
                RiskLevel.HIGH
            )
        
        # Check minimum confidence threshold
        if analysis.overall_confidence < self.risk_params.min_confidence_threshold:
            logger.info(f"Confidence too low for trading: {analysis.overall_confidence} < {self.risk_params.min_confidence_threshold}")
            return self._create_hold_decision(
                analysis.current_price,
                f"Insufficient confidence for trading: {analysis.overall_confidence:.2%} < {self.risk_params.min_confidence_threshold:.2%}",
                RiskLevel.MEDIUM
            )
        
        # Check for critical risk conditions
        if analysis.risk_assessment == "critical":
            logger.warning("Critical risk conditions detected - recommending HOLD")
            return self._create_hold_decision(
                analysis.current_price,
                "Critical risk conditions detected - avoiding new positions",
                RiskLevel.CRITICAL
            )
        
        # Determine action based on signal strength
        if analysis.combined_signal_strength > 0.3:
            action = ActionType.BUY
        elif analysis.combined_signal_strength < -0.3:
            action = ActionType.SELL
        else:
            return self._create_hold_decision(
                analysis.current_price,
                f"Signal strength too weak for action: {analysis.combined_signal_strength}",
                self._map_risk_assessment_to_level(analysis.risk_assessment)
            )
        
        # Calculate position size
        suggested_amount = self.calculate_position_size(analysis, action)
        
        # Calculate price range
        price_range = self._calculate_price_range(analysis.current_price, action)
        
        # Generate reasoning
        reasoning = self._generate_decision_reasoning(analysis, action, suggested_amount)
        
        # Map risk assessment to risk level
        risk_level = self._map_risk_assessment_to_level(analysis.risk_assessment)
        
        decision = TradingDecision(
            action=action,
            confidence=analysis.overall_confidence,
            suggested_amount=suggested_amount,
            price_range=price_range,
            reasoning=reasoning,
            risk_level=risk_level
        )
        
        logger.info(f"Trading decision generated: {action.value} {suggested_amount:.4f} BTC at confidence {analysis.overall_confidence:.2%}")
        
        return decision
    
    def calculate_position_size(self, analysis: MarketAnalysis, action: ActionType) -> float:
        """
        Calculate appropriate position size based on risk parameters and market analysis
        
        Args:
            analysis: Market analysis result
            action: Intended trading action
            
        Returns:
            Position size as percentage of portfolio
        """
        # Base position size based on confidence
        if analysis.overall_confidence >= self.risk_params.high_confidence_threshold:
            base_size = self.risk_params.max_position_size
        else:
            # Scale position size with confidence
            confidence_ratio = (analysis.overall_confidence - self.risk_params.min_confidence_threshold) / \
                             (self.risk_params.high_confidence_threshold - self.risk_params.min_confidence_threshold)
            base_size = self.risk_params.min_position_size + \
                       (self.risk_params.max_position_size - self.risk_params.min_position_size) * confidence_ratio
        
        # Adjust for signal strength
        signal_adjustment = abs(analysis.combined_signal_strength)
        adjusted_size = base_size * signal_adjustment
        
        # Adjust for risk level
        risk_multipliers = {
            "low": 1.0,
            "medium": 0.8,
            "high": 0.6,
            "critical": 0.3
        }
        risk_adjusted_size = adjusted_size * risk_multipliers[analysis.risk_assessment]
        
        # Ensure within bounds
        final_size = max(self.risk_params.min_position_size, 
                        min(self.risk_params.max_position_size, risk_adjusted_size))
        
        logger.debug(f"Position size calculation: base={base_size:.3f}, signal_adj={adjusted_size:.3f}, risk_adj={risk_adjusted_size:.3f}, final={final_size:.3f}")
        
        return round(final_size, 4)
    
    def _calculate_price_range(self, current_price: float, action: ActionType) -> PriceRange:
        """
        Calculate acceptable price range for the trading decision
        
        Args:
            current_price: Current market price
            action: Trading action
            
        Returns:
            PriceRange object with min and max acceptable prices
        """
        # Price tolerance based on action type
        if action == ActionType.BUY:
            # For buying, allow slightly higher prices
            min_price = current_price * 0.995  # 0.5% below current
            max_price = current_price * 1.01   # 1% above current
        elif action == ActionType.SELL:
            # For selling, allow slightly lower prices
            min_price = current_price * 0.99   # 1% below current
            max_price = current_price * 1.005  # 0.5% above current
        else:  # HOLD
            min_price = current_price * 0.99
            max_price = current_price * 1.01
        
        return PriceRange(min_price=min_price, max_price=max_price)
    
    def _generate_decision_reasoning(self, analysis: MarketAnalysis, 
                                   action: ActionType, suggested_amount: float) -> str:
        """
        Generate human-readable reasoning for the trading decision
        
        Args:
            analysis: Market analysis result
            action: Trading action
            suggested_amount: Suggested position size
            
        Returns:
            Reasoning string
        """
        reasoning_parts = []
        
        # Overall signal assessment
        reasoning_parts.append(f"Combined signal strength: {analysis.combined_signal_strength:.3f} ({action.value} signal)")
        reasoning_parts.append(f"Overall confidence: {analysis.overall_confidence:.2%}")
        
        # Sentiment contribution
        sentiment_direction = "positive" if analysis.sentiment_contribution > 0 else "negative" if analysis.sentiment_contribution < 0 else "neutral"
        reasoning_parts.append(f"Sentiment analysis: {sentiment_direction} ({analysis.sentiment_score.sentiment_value:.1f}/100)")
        
        # Technical contribution
        technical_direction = analysis.technical_signal.signal_type.value.lower()
        reasoning_parts.append(f"Technical analysis: {technical_direction} signal ({analysis.technical_signal.signal_strength:.3f})")
        
        # Market condition
        reasoning_parts.append(f"Market condition: {analysis.market_condition}")
        
        # Risk assessment
        reasoning_parts.append(f"Risk level: {analysis.risk_assessment}")
        
        # Position sizing rationale
        reasoning_parts.append(f"Position size: {suggested_amount:.2%} of portfolio")
        
        # Contributing indicators
        if analysis.technical_signal.contributing_indicators:
            indicators = ", ".join(analysis.technical_signal.contributing_indicators)
            reasoning_parts.append(f"Key technical indicators: {indicators}")
        
        return "; ".join(reasoning_parts)
    
    def _create_hold_decision(self, current_price: float, reasoning: str, risk_level: RiskLevel) -> TradingDecision:
        """
        Create a HOLD trading decision
        
        Args:
            current_price: Current market price
            reasoning: Reasoning for the hold decision
            risk_level: Risk level assessment
            
        Returns:
            TradingDecision with HOLD action
        """
        return TradingDecision(
            action=ActionType.HOLD,
            confidence=0.5,  # Neutral confidence for hold decisions
            suggested_amount=0.0,
            price_range=PriceRange(min_price=current_price * 0.99, max_price=current_price * 1.01),
            reasoning=reasoning,
            risk_level=risk_level
        )
    
    def _map_risk_assessment_to_level(self, risk_assessment: str) -> RiskLevel:
        """Map risk assessment string to RiskLevel enum"""
        mapping = {
            "low": RiskLevel.LOW,
            "medium": RiskLevel.MEDIUM,
            "high": RiskLevel.HIGH,
            "critical": RiskLevel.CRITICAL
        }
        return mapping.get(risk_assessment, RiskLevel.MEDIUM)
    
    def update_trade_history(self, executed_trade: bool, pnl: Optional[float] = None):
        """
        Update trade history and daily loss tracking
        
        Args:
            executed_trade: Whether a trade was actually executed
            pnl: Profit/loss from the trade (if completed)
        """
        if executed_trade:
            self.last_trade_time = datetime.utcnow()
            logger.info(f"Trade history updated - Last trade: {self.last_trade_time}")
            
            if pnl is not None and pnl < 0:
                self.daily_loss += abs(pnl)
                logger.info(f"Daily loss updated: {self.daily_loss:.4f}")
    
    def get_engine_status(self) -> Dict[str, Any]:
        """
        Get current engine status and statistics
        
        Returns:
            Dictionary with engine status information
        """
        self._reset_daily_loss_if_needed()
        
        return {
            "risk_parameters": self.risk_params.to_dict(),
            "last_trade_time": self.last_trade_time.isoformat() if self.last_trade_time else None,
            "daily_loss": self.daily_loss,
            "daily_loss_limit": self.risk_params.max_daily_loss,
            "daily_loss_remaining": max(0, self.risk_params.max_daily_loss - self.daily_loss),
            "trading_allowed": len(self._check_trading_constraints(Portfolio(0, 0, 0, 0))) == 0,
            "engine_initialized": True
        }