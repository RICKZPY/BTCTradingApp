"""
Risk Manager
Comprehensive risk assessment and management for trading decisions
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

from core.data_models import (
    TradingDecision, Portfolio, Position, RiskLevel, ActionType, MarketData
)
from decision_engine.risk_parameters import RiskParameters

logger = logging.getLogger(__name__)


class RiskCategory(Enum):
    """Risk category classifications"""
    MARKET_RISK = "market_risk"
    LIQUIDITY_RISK = "liquidity_risk"
    CONCENTRATION_RISK = "concentration_risk"
    VOLATILITY_RISK = "volatility_risk"
    DRAWDOWN_RISK = "drawdown_risk"
    OPERATIONAL_RISK = "operational_risk"


@dataclass
class RiskFactor:
    """Individual risk factor assessment"""
    category: RiskCategory
    name: str
    score: float  # 0 to 1 (0 = no risk, 1 = maximum risk)
    impact: float  # 0 to 1 (potential impact on portfolio)
    description: str
    mitigation_suggestions: List[str]


@dataclass
class RiskAssessment:
    """Comprehensive risk assessment for a trading decision"""
    
    # Overall risk metrics
    overall_risk_score: float  # 0 to 100
    risk_level: RiskLevel
    max_loss_potential: float  # Maximum potential loss in USDT
    recommended_position_size: float  # Recommended position size (0 to 1)
    
    # Individual risk factors
    risk_factors: List[RiskFactor]
    
    # Risk breakdown by category
    market_risk_score: float
    liquidity_risk_score: float
    concentration_risk_score: float
    volatility_risk_score: float
    drawdown_risk_score: float
    operational_risk_score: float
    
    # Portfolio impact
    portfolio_risk_before: float  # Portfolio risk before trade
    portfolio_risk_after: float   # Portfolio risk after trade
    risk_change: float           # Change in portfolio risk
    
    # Recommendations
    risk_mitigation_actions: List[str]
    position_adjustments: Dict[str, float]
    
    # Metadata
    assessment_timestamp: datetime
    confidence: float  # Confidence in risk assessment (0 to 1)
    
    def __post_init__(self):
        """Validate risk assessment data"""
        if not 0 <= self.overall_risk_score <= 100:
            raise ValueError("Overall risk score must be between 0 and 100")
        
        if not 0 <= self.recommended_position_size <= 1:
            raise ValueError("Recommended position size must be between 0 and 1")
        
        if self.max_loss_potential < 0:
            raise ValueError("Max loss potential cannot be negative")
        
        for score in [self.market_risk_score, self.liquidity_risk_score, 
                     self.concentration_risk_score, self.volatility_risk_score,
                     self.drawdown_risk_score, self.operational_risk_score]:
            if not 0 <= score <= 1:
                raise ValueError("Individual risk scores must be between 0 and 1")
        
        if not 0 <= self.confidence <= 1:
            raise ValueError("Confidence must be between 0 and 1")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'overall_risk_score': self.overall_risk_score,
            'risk_level': self.risk_level.value,
            'max_loss_potential': self.max_loss_potential,
            'recommended_position_size': self.recommended_position_size,
            'risk_factors': [
                {
                    'category': rf.category.value,
                    'name': rf.name,
                    'score': rf.score,
                    'impact': rf.impact,
                    'description': rf.description,
                    'mitigation_suggestions': rf.mitigation_suggestions
                }
                for rf in self.risk_factors
            ],
            'market_risk_score': self.market_risk_score,
            'liquidity_risk_score': self.liquidity_risk_score,
            'concentration_risk_score': self.concentration_risk_score,
            'volatility_risk_score': self.volatility_risk_score,
            'drawdown_risk_score': self.drawdown_risk_score,
            'operational_risk_score': self.operational_risk_score,
            'portfolio_risk_before': self.portfolio_risk_before,
            'portfolio_risk_after': self.portfolio_risk_after,
            'risk_change': self.risk_change,
            'risk_mitigation_actions': self.risk_mitigation_actions,
            'position_adjustments': self.position_adjustments,
            'assessment_timestamp': self.assessment_timestamp.isoformat(),
            'confidence': self.confidence
        }


class RiskManager:
    """
    Comprehensive risk manager for trading operations
    """
    
    def __init__(self, risk_params: Optional[RiskParameters] = None):
        """
        Initialize risk manager
        
        Args:
            risk_params: Risk management parameters
        """
        self.risk_params = risk_params or RiskParameters()
        self.trade_history: List[Dict] = []
        self.daily_loss: float = 0.0
        self.max_drawdown: float = 0.0
        self.peak_portfolio_value: float = 0.0
        
        logger.info("Risk manager initialized")
    
    def _calculate_market_risk(self, decision: TradingDecision, portfolio: Portfolio,
                             market_data: Optional[List[MarketData]] = None) -> RiskFactor:
        """
        Calculate market risk factor
        
        Args:
            decision: Trading decision to assess
            portfolio: Current portfolio
            market_data: Optional market data for volatility analysis
            
        Returns:
            Market risk factor
        """
        # Base market risk from decision confidence
        base_risk = 1 - decision.confidence
        
        # Adjust for market volatility if available
        volatility_adjustment = 0.0
        if market_data and len(market_data) > 1:
            prices = [data.price for data in market_data[-24:]]  # Last 24 periods
            if len(prices) > 1:
                returns = np.diff(prices) / prices[:-1]
                volatility = np.std(returns)
                volatility_adjustment = min(0.5, volatility * 10)  # Scale volatility
        
        # Adjust for position size
        size_adjustment = decision.suggested_amount * 0.3  # Larger positions = higher risk
        
        risk_score = min(1.0, base_risk + volatility_adjustment + size_adjustment)
        
        # Calculate potential impact
        position_value = decision.suggested_amount * portfolio.total_value_usdt
        impact = min(1.0, position_value / portfolio.total_value_usdt)
        
        mitigation_suggestions = []
        if risk_score > 0.7:
            mitigation_suggestions.extend([
                "Reduce position size",
                "Use tighter stop losses",
                "Consider market timing"
            ])
        
        return RiskFactor(
            category=RiskCategory.MARKET_RISK,
            name="Market Risk",
            score=risk_score,
            impact=impact,
            description=f"Risk from market movements and price volatility (confidence: {decision.confidence:.1%})",
            mitigation_suggestions=mitigation_suggestions
        )
    
    def _calculate_liquidity_risk(self, decision: TradingDecision, portfolio: Portfolio,
                                market_data: Optional[List[MarketData]] = None) -> RiskFactor:
        """
        Calculate liquidity risk factor
        
        Args:
            decision: Trading decision to assess
            portfolio: Current portfolio
            market_data: Optional market data for volume analysis
            
        Returns:
            Liquidity risk factor
        """
        # Base liquidity risk
        base_risk = 0.2  # Assume moderate base liquidity risk for crypto
        
        # Adjust for trading volume if available
        volume_adjustment = 0.0
        if market_data:
            recent_volumes = [data.volume for data in market_data[-6:]]  # Last 6 periods
            if recent_volumes:
                avg_volume = np.mean(recent_volumes)
                if avg_volume < self.risk_params.min_volume_threshold:
                    volume_adjustment = 0.4  # High liquidity risk for low volume
                elif avg_volume > self.risk_params.min_volume_threshold * 2:
                    volume_adjustment = -0.1  # Lower liquidity risk for high volume
        
        # Adjust for position size relative to typical volume
        size_adjustment = 0.0
        if market_data and decision.suggested_amount > 0:
            position_value = decision.suggested_amount * portfolio.total_value_usdt
            # Estimate if position is large relative to market
            if position_value > 100000:  # Large position
                size_adjustment = 0.2
        
        risk_score = max(0.0, min(1.0, base_risk + volume_adjustment + size_adjustment))
        
        # Impact based on position size
        impact = min(1.0, decision.suggested_amount * 2)
        
        mitigation_suggestions = []
        if risk_score > 0.6:
            mitigation_suggestions.extend([
                "Split large orders into smaller chunks",
                "Use limit orders instead of market orders",
                "Monitor order book depth"
            ])
        
        return RiskFactor(
            category=RiskCategory.LIQUIDITY_RISK,
            name="Liquidity Risk",
            score=risk_score,
            impact=impact,
            description="Risk from insufficient market liquidity affecting order execution",
            mitigation_suggestions=mitigation_suggestions
        )
    
    def _calculate_concentration_risk(self, decision: TradingDecision, 
                                    portfolio: Portfolio) -> RiskFactor:
        """
        Calculate concentration risk factor
        
        Args:
            decision: Trading decision to assess
            portfolio: Current portfolio
            
        Returns:
            Concentration risk factor
        """
        # Calculate current BTC concentration
        btc_value = portfolio.btc_balance * (portfolio.positions[0].current_price if portfolio.positions else 45000)
        current_btc_ratio = btc_value / portfolio.total_value_usdt if portfolio.total_value_usdt > 0 else 0
        
        # Calculate concentration after trade
        if decision.action == ActionType.BUY:
            additional_btc_value = decision.suggested_amount * portfolio.total_value_usdt
            new_btc_ratio = (btc_value + additional_btc_value) / portfolio.total_value_usdt
        elif decision.action == ActionType.SELL:
            reduced_btc_value = decision.suggested_amount * portfolio.total_value_usdt
            new_btc_ratio = max(0, (btc_value - reduced_btc_value) / portfolio.total_value_usdt)
        else:
            new_btc_ratio = current_btc_ratio
        
        # Risk increases with concentration
        concentration_risk = new_btc_ratio ** 2  # Quadratic increase in risk
        
        # Impact based on change in concentration
        concentration_change = abs(new_btc_ratio - current_btc_ratio)
        impact = min(1.0, concentration_change * 3)
        
        mitigation_suggestions = []
        if concentration_risk > 0.6:
            mitigation_suggestions.extend([
                "Diversify into other assets",
                "Reduce position size",
                "Consider hedging strategies"
            ])
        
        return RiskFactor(
            category=RiskCategory.CONCENTRATION_RISK,
            name="Concentration Risk",
            score=concentration_risk,
            impact=impact,
            description=f"Risk from portfolio concentration (BTC ratio: {new_btc_ratio:.1%})",
            mitigation_suggestions=mitigation_suggestions
        )
    
    def _calculate_volatility_risk(self, decision: TradingDecision, portfolio: Portfolio,
                                 market_data: Optional[List[MarketData]] = None) -> RiskFactor:
        """
        Calculate volatility risk factor
        
        Args:
            decision: Trading decision to assess
            portfolio: Current portfolio
            market_data: Optional market data for volatility calculation
            
        Returns:
            Volatility risk factor
        """
        # Base volatility risk for crypto
        base_risk = 0.4
        
        # Calculate actual volatility if market data available
        volatility_multiplier = 1.0
        if market_data and len(market_data) > 1:
            prices = [data.price for data in market_data[-24:]]  # Last 24 periods
            if len(prices) > 1:
                returns = np.diff(prices) / prices[:-1]
                volatility = np.std(returns)
                # Normalize volatility (typical crypto daily volatility ~0.03-0.08)
                normalized_volatility = min(1.0, volatility / 0.05)
                volatility_multiplier = 0.5 + normalized_volatility
        
        # Adjust for position size
        size_multiplier = 1 + decision.suggested_amount
        
        risk_score = min(1.0, base_risk * volatility_multiplier * size_multiplier)
        
        # Impact based on position size and volatility
        impact = min(1.0, decision.suggested_amount * volatility_multiplier)
        
        mitigation_suggestions = []
        if risk_score > 0.7:
            mitigation_suggestions.extend([
                "Use smaller position sizes during high volatility",
                "Implement tighter stop losses",
                "Consider volatility-based position sizing"
            ])
        
        return RiskFactor(
            category=RiskCategory.VOLATILITY_RISK,
            name="Volatility Risk",
            score=risk_score,
            impact=impact,
            description="Risk from price volatility and sudden market movements",
            mitigation_suggestions=mitigation_suggestions
        )
    
    def _calculate_drawdown_risk(self, decision: TradingDecision, 
                               portfolio: Portfolio) -> RiskFactor:
        """
        Calculate drawdown risk factor
        
        Args:
            decision: Trading decision to assess
            portfolio: Current portfolio
            
        Returns:
            Drawdown risk factor
        """
        # Current drawdown
        current_drawdown = abs(portfolio.unrealized_pnl) / portfolio.total_value_usdt if portfolio.total_value_usdt > 0 else 0
        
        # Potential additional drawdown from new position
        position_value = decision.suggested_amount * portfolio.total_value_usdt
        potential_loss = position_value * self.risk_params.stop_loss_percentage
        potential_drawdown = (abs(portfolio.unrealized_pnl) + potential_loss) / portfolio.total_value_usdt
        
        # Risk increases with drawdown
        drawdown_risk = min(1.0, potential_drawdown / self.risk_params.max_daily_loss)
        
        # Impact based on potential drawdown increase
        drawdown_increase = potential_drawdown - current_drawdown
        impact = min(1.0, drawdown_increase * 5)
        
        mitigation_suggestions = []
        if drawdown_risk > 0.6:
            mitigation_suggestions.extend([
                "Reduce position sizes",
                "Take partial profits on existing positions",
                "Implement stricter stop losses"
            ])
        
        return RiskFactor(
            category=RiskCategory.DRAWDOWN_RISK,
            name="Drawdown Risk",
            score=drawdown_risk,
            impact=impact,
            description=f"Risk of portfolio drawdown (current: {current_drawdown:.1%}, potential: {potential_drawdown:.1%})",
            mitigation_suggestions=mitigation_suggestions
        )
    
    def _calculate_operational_risk(self, decision: TradingDecision, 
                                  portfolio: Portfolio) -> RiskFactor:
        """
        Calculate operational risk factor
        
        Args:
            decision: Trading decision to assess
            portfolio: Current portfolio
            
        Returns:
            Operational risk factor
        """
        # Base operational risk for automated trading
        base_risk = 0.15
        
        # Increase risk for larger positions (more impact if something goes wrong)
        size_adjustment = decision.suggested_amount * 0.2
        
        # Increase risk if confidence is low (more likely to be wrong)
        confidence_adjustment = (1 - decision.confidence) * 0.3
        
        risk_score = min(1.0, base_risk + size_adjustment + confidence_adjustment)
        
        # Impact based on position size
        impact = min(1.0, decision.suggested_amount * 1.5)
        
        mitigation_suggestions = []
        if risk_score > 0.5:
            mitigation_suggestions.extend([
                "Implement additional validation checks",
                "Use limit orders with appropriate buffers",
                "Monitor execution closely"
            ])
        
        return RiskFactor(
            category=RiskCategory.OPERATIONAL_RISK,
            name="Operational Risk",
            score=risk_score,
            impact=impact,
            description="Risk from system failures, execution errors, or technical issues",
            mitigation_suggestions=mitigation_suggestions
        )
    
    def assess_trade_risk(self, decision: TradingDecision, portfolio: Portfolio,
                         market_data: Optional[List[MarketData]] = None) -> RiskAssessment:
        """
        Perform comprehensive risk assessment for a trading decision
        
        Args:
            decision: Trading decision to assess
            portfolio: Current portfolio state
            market_data: Optional recent market data
            
        Returns:
            Comprehensive risk assessment
        """
        logger.info(f"Assessing risk for {decision.action.value} decision")
        
        # Calculate individual risk factors
        risk_factors = [
            self._calculate_market_risk(decision, portfolio, market_data),
            self._calculate_liquidity_risk(decision, portfolio, market_data),
            self._calculate_concentration_risk(decision, portfolio),
            self._calculate_volatility_risk(decision, portfolio, market_data),
            self._calculate_drawdown_risk(decision, portfolio),
            self._calculate_operational_risk(decision, portfolio)
        ]
        
        # Extract risk scores by category
        market_risk_score = next(rf.score for rf in risk_factors if rf.category == RiskCategory.MARKET_RISK)
        liquidity_risk_score = next(rf.score for rf in risk_factors if rf.category == RiskCategory.LIQUIDITY_RISK)
        concentration_risk_score = next(rf.score for rf in risk_factors if rf.category == RiskCategory.CONCENTRATION_RISK)
        volatility_risk_score = next(rf.score for rf in risk_factors if rf.category == RiskCategory.VOLATILITY_RISK)
        drawdown_risk_score = next(rf.score for rf in risk_factors if rf.category == RiskCategory.DRAWDOWN_RISK)
        operational_risk_score = next(rf.score for rf in risk_factors if rf.category == RiskCategory.OPERATIONAL_RISK)
        
        # Calculate weighted overall risk score
        risk_weights = {
            RiskCategory.MARKET_RISK: 0.25,
            RiskCategory.LIQUIDITY_RISK: 0.15,
            RiskCategory.CONCENTRATION_RISK: 0.20,
            RiskCategory.VOLATILITY_RISK: 0.20,
            RiskCategory.DRAWDOWN_RISK: 0.15,
            RiskCategory.OPERATIONAL_RISK: 0.05
        }
        
        weighted_risk = sum(rf.score * rf.impact * risk_weights[rf.category] for rf in risk_factors)
        overall_risk_score = min(100.0, weighted_risk * 100)
        
        # Determine risk level
        if overall_risk_score >= 75:
            risk_level = RiskLevel.CRITICAL
        elif overall_risk_score >= 50:
            risk_level = RiskLevel.HIGH
        elif overall_risk_score >= 25:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
        
        # Calculate maximum loss potential
        position_value = decision.suggested_amount * portfolio.total_value_usdt
        max_loss_potential = position_value * self.risk_params.stop_loss_percentage
        
        # Calculate recommended position size based on risk
        risk_adjustment = 1 - (overall_risk_score / 100) * 0.5  # Reduce size by up to 50% for high risk
        recommended_position_size = decision.suggested_amount * risk_adjustment
        
        # Calculate portfolio risk before and after
        portfolio_risk_before = abs(portfolio.unrealized_pnl) / portfolio.total_value_usdt if portfolio.total_value_usdt > 0 else 0
        portfolio_risk_after = (abs(portfolio.unrealized_pnl) + max_loss_potential) / portfolio.total_value_usdt if portfolio.total_value_usdt > 0 else 0
        risk_change = portfolio_risk_after - portfolio_risk_before
        
        # Generate risk mitigation actions
        risk_mitigation_actions = []
        high_risk_factors = [rf for rf in risk_factors if rf.score > 0.6]
        for rf in high_risk_factors:
            risk_mitigation_actions.extend(rf.mitigation_suggestions)
        
        # Remove duplicates
        risk_mitigation_actions = list(set(risk_mitigation_actions))
        
        # Generate position adjustments
        position_adjustments = {
            "size_adjustment": risk_adjustment,
            "stop_loss_tightening": 1.0 + (overall_risk_score / 100) * 0.5,  # Tighten stop loss for higher risk
            "confidence_requirement": decision.confidence + (overall_risk_score / 100) * 0.2  # Require higher confidence for risky trades
        }
        
        # Assessment confidence based on data availability
        confidence = 0.8
        if not market_data:
            confidence -= 0.2
        if len(portfolio.positions) == 0:
            confidence -= 0.1
        
        assessment = RiskAssessment(
            overall_risk_score=overall_risk_score,
            risk_level=risk_level,
            max_loss_potential=max_loss_potential,
            recommended_position_size=recommended_position_size,
            risk_factors=risk_factors,
            market_risk_score=market_risk_score,
            liquidity_risk_score=liquidity_risk_score,
            concentration_risk_score=concentration_risk_score,
            volatility_risk_score=volatility_risk_score,
            drawdown_risk_score=drawdown_risk_score,
            operational_risk_score=operational_risk_score,
            portfolio_risk_before=portfolio_risk_before,
            portfolio_risk_after=portfolio_risk_after,
            risk_change=risk_change,
            risk_mitigation_actions=risk_mitigation_actions,
            position_adjustments=position_adjustments,
            assessment_timestamp=datetime.utcnow(),
            confidence=confidence
        )
        
        logger.info(f"Risk assessment completed: {risk_level.value} risk ({overall_risk_score:.1f}/100)")
        
        return assessment
    
    def validate_trade(self, decision: TradingDecision, portfolio: Portfolio,
                      risk_assessment: Optional[RiskAssessment] = None) -> Tuple[bool, List[str]]:
        """
        Validate if a trade should be executed based on risk assessment
        
        Args:
            decision: Trading decision to validate
            portfolio: Current portfolio state
            risk_assessment: Optional pre-calculated risk assessment
            
        Returns:
            Tuple of (is_valid, violation_reasons)
        """
        violations = []
        
        # Perform risk assessment if not provided
        if risk_assessment is None:
            risk_assessment = self.assess_trade_risk(decision, portfolio)
        
        # Check overall risk level
        if risk_assessment.risk_level == RiskLevel.CRITICAL:
            violations.append("Critical risk level detected")
        
        # Check maximum loss potential
        if risk_assessment.max_loss_potential > portfolio.total_value_usdt * self.risk_params.max_daily_loss:
            violations.append(f"Potential loss exceeds daily limit: ${risk_assessment.max_loss_potential:.2f}")
        
        # Check portfolio risk increase
        if risk_assessment.risk_change > self.risk_params.max_portfolio_risk * 0.5:
            violations.append(f"Portfolio risk increase too large: {risk_assessment.risk_change:.2%}")
        
        # Check position size limits
        if decision.suggested_amount > self.risk_params.max_position_size:
            violations.append(f"Position size exceeds limit: {decision.suggested_amount:.2%} > {self.risk_params.max_position_size:.2%}")
        
        # Check individual risk factors
        for rf in risk_assessment.risk_factors:
            if rf.score > 0.8 and rf.impact > 0.7:
                violations.append(f"High {rf.name.lower()}: {rf.score:.1%}")
        
        is_valid = len(violations) == 0
        
        if not is_valid:
            logger.warning(f"Trade validation failed: {violations}")
        else:
            logger.info("Trade validation passed")
        
        return is_valid, violations
    
    def calculate_stop_loss(self, entry_price: float, action: ActionType,
                          risk_tolerance: Optional[float] = None) -> float:
        """
        Calculate appropriate stop loss price
        
        Args:
            entry_price: Entry price for the position
            action: Trading action (BUY or SELL)
            risk_tolerance: Optional custom risk tolerance (uses default if None)
            
        Returns:
            Stop loss price
        """
        risk_pct = risk_tolerance or self.risk_params.stop_loss_percentage
        
        if action == ActionType.BUY:
            # For long positions, stop loss is below entry price
            stop_loss = entry_price * (1 - risk_pct)
        elif action == ActionType.SELL:
            # For short positions, stop loss is above entry price
            stop_loss = entry_price * (1 + risk_pct)
        else:
            # For HOLD, return entry price
            stop_loss = entry_price
        
        logger.debug(f"Calculated stop loss: ${stop_loss:.2f} for {action.value} at ${entry_price:.2f}")
        
        return stop_loss
    
    def monitor_portfolio_risk(self, portfolio: Portfolio,
                             market_data: Optional[List[MarketData]] = None) -> Dict[str, Any]:
        """
        Monitor overall portfolio risk status
        
        Args:
            portfolio: Current portfolio state
            market_data: Optional recent market data
            
        Returns:
            Portfolio risk status dictionary
        """
        # Calculate current portfolio metrics
        total_value = portfolio.total_value_usdt
        unrealized_pnl = portfolio.unrealized_pnl
        current_drawdown = abs(unrealized_pnl) / total_value if total_value > 0 else 0
        
        # Update peak portfolio value
        if total_value > self.peak_portfolio_value:
            self.peak_portfolio_value = total_value
        
        # Calculate maximum drawdown
        if self.peak_portfolio_value > 0:
            max_drawdown_current = (self.peak_portfolio_value - total_value) / self.peak_portfolio_value
            self.max_drawdown = max(self.max_drawdown, max_drawdown_current)
        
        # Calculate portfolio volatility if market data available
        portfolio_volatility = 0.0
        if market_data and len(market_data) > 1:
            # Estimate portfolio volatility based on BTC volatility (simplified)
            prices = [data.price for data in market_data[-24:]]
            if len(prices) > 1:
                returns = np.diff(prices) / prices[:-1]
                btc_volatility = np.std(returns)
                # Scale by BTC exposure
                btc_exposure = portfolio.btc_balance * prices[-1] / total_value if total_value > 0 else 0
                portfolio_volatility = btc_volatility * btc_exposure
        
        # Risk status assessment
        risk_alerts = []
        
        if current_drawdown > self.risk_params.max_daily_loss * 0.8:
            risk_alerts.append("Approaching daily loss limit")
        
        if self.max_drawdown > self.risk_params.max_portfolio_risk:
            risk_alerts.append("Maximum drawdown exceeded")
        
        if portfolio_volatility > self.risk_params.max_volatility_threshold:
            risk_alerts.append("High portfolio volatility")
        
        # Overall risk level
        if len(risk_alerts) >= 2:
            overall_risk = "HIGH"
        elif len(risk_alerts) >= 1:
            overall_risk = "MEDIUM"
        else:
            overall_risk = "LOW"
        
        return {
            "overall_risk_level": overall_risk,
            "current_drawdown": current_drawdown,
            "max_drawdown": self.max_drawdown,
            "portfolio_volatility": portfolio_volatility,
            "daily_loss": self.daily_loss,
            "daily_loss_limit": self.risk_params.max_daily_loss,
            "risk_alerts": risk_alerts,
            "total_value": total_value,
            "unrealized_pnl": unrealized_pnl,
            "peak_value": self.peak_portfolio_value,
            "monitoring_timestamp": datetime.utcnow().isoformat()
        }
    
    def update_trade_outcome(self, realized_pnl: float, trade_successful: bool):
        """
        Update risk manager with trade outcome
        
        Args:
            realized_pnl: Realized profit/loss from the trade
            trade_successful: Whether the trade was successful
        """
        # Update daily loss if trade was a loss
        if realized_pnl < 0:
            self.daily_loss += abs(realized_pnl)
        
        # Record trade in history
        trade_record = {
            "timestamp": datetime.utcnow(),
            "pnl": realized_pnl,
            "successful": trade_successful,
            "daily_loss_after": self.daily_loss
        }
        self.trade_history.append(trade_record)
        
        # Keep only recent trade history (last 100 trades)
        if len(self.trade_history) > 100:
            self.trade_history = self.trade_history[-100:]
        
        logger.info(f"Trade outcome updated: PnL=${realized_pnl:.2f}, Success={trade_successful}")
    
    def get_risk_manager_status(self) -> Dict[str, Any]:
        """
        Get current risk manager status and statistics
        
        Returns:
            Risk manager status dictionary
        """
        # Calculate recent performance metrics
        recent_trades = self.trade_history[-20:] if len(self.trade_history) >= 20 else self.trade_history
        
        if recent_trades:
            win_rate = sum(1 for trade in recent_trades if trade["successful"]) / len(recent_trades)
            avg_pnl = np.mean([trade["pnl"] for trade in recent_trades])
            total_pnl = sum(trade["pnl"] for trade in recent_trades)
        else:
            win_rate = 0.0
            avg_pnl = 0.0
            total_pnl = 0.0
        
        return {
            "risk_parameters": self.risk_params.to_dict(),
            "daily_loss": self.daily_loss,
            "max_drawdown": self.max_drawdown,
            "peak_portfolio_value": self.peak_portfolio_value,
            "total_trades": len(self.trade_history),
            "recent_win_rate": win_rate,
            "recent_avg_pnl": avg_pnl,
            "recent_total_pnl": total_pnl,
            "status_timestamp": datetime.utcnow().isoformat()
        }