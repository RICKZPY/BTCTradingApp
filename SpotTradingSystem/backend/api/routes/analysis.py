"""
Analysis API routes
"""
import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.models import (
    AnalysisResponse, SentimentAnalysis, TechnicalSignal, TradingDecision
)
from system_integration.trading_system_integration import TradingSystemIntegration

logger = logging.getLogger(__name__)

router = APIRouter()


def get_trading_system() -> TradingSystemIntegration:
    """Get trading system instance"""
    from api.main import trading_system
    if trading_system is None:
        raise HTTPException(
            status_code=503,
            detail="Trading system is not available"
        )
    return trading_system


@router.get("/current", response_model=AnalysisResponse)
async def get_current_analysis():
    """
    Get current analysis results (sentiment, technical, decision)
    
    Returns:
        Current analysis data from all modules
    """
    try:
        system = get_trading_system()
        
        # Get cached analysis data
        sentiment_data = system.analysis_cache.get('sentiment_data')
        technical_data = system.analysis_cache.get('technical_data')
        
        # Convert to API models
        sentiment = None
        if sentiment_data:
            sentiment = SentimentAnalysis(
                sentiment_score=sentiment_data.get('average_sentiment', 0.0),
                confidence=0.8,  # Default confidence
                key_topics=sentiment_data.get('key_topics', []),
                impact_assessment=sentiment_data.get('impact_assessment', {}),
                timestamp=datetime.utcnow()
            )
        
        technical = None
        if technical_data and technical_data.get('signals'):
            signals = technical_data['signals']
            if signals:
                signal = signals[0]  # Get first signal
                technical = TechnicalSignal(
                    signal_type=signal.get('type', 'HOLD'),
                    strength=signal.get('strength', 0.5),
                    confidence=signal.get('confidence', 0.5),
                    indicators=signal.get('indicators', {}),
                    timestamp=datetime.utcnow()
                )
        
        # Generate mock decision if we have analysis data
        decision = None
        if sentiment or technical:
            decision = TradingDecision(
                action="HOLD",  # Default action
                symbol="BTCUSDT",
                quantity=None,
                confidence=0.5,
                reasoning="Analysis in progress",
                sentiment_data=sentiment,
                technical_data=technical,
                timestamp=datetime.utcnow()
            )
            
            # Determine action based on analysis
            if sentiment and technical:
                if sentiment.sentiment_score > 0.3 and technical.strength > 0.6:
                    decision.action = "BUY"
                    decision.quantity = 0.1
                    decision.confidence = min(sentiment.confidence, technical.confidence)
                    decision.reasoning = "Positive sentiment and strong technical signals"
                elif sentiment.sentiment_score < -0.3 and technical.strength > 0.6:
                    decision.action = "SELL"
                    decision.quantity = 0.1
                    decision.confidence = min(sentiment.confidence, technical.confidence)
                    decision.reasoning = "Negative sentiment and strong technical signals"
        
        return AnalysisResponse(
            message="Current analysis retrieved successfully",
            sentiment=sentiment,
            technical=technical,
            decision=decision
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current analysis: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get current analysis: {str(e)}"
        )


@router.get("/sentiment", response_model=SentimentAnalysis)
async def get_sentiment_analysis():
    """
    Get current sentiment analysis
    
    Returns:
        Latest sentiment analysis results
    """
    try:
        system = get_trading_system()
        
        sentiment_data = system.analysis_cache.get('sentiment_data')
        
        if not sentiment_data:
            # Return neutral sentiment if no data
            return SentimentAnalysis(
                sentiment_score=0.0,
                confidence=0.0,
                key_topics=[],
                impact_assessment={},
                timestamp=datetime.utcnow()
            )
        
        return SentimentAnalysis(
            sentiment_score=sentiment_data.get('average_sentiment', 0.0),
            confidence=0.8,
            key_topics=sentiment_data.get('key_topics', []),
            impact_assessment=sentiment_data.get('impact_assessment', {}),
            timestamp=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sentiment analysis: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get sentiment analysis: {str(e)}"
        )


@router.get("/technical", response_model=TechnicalSignal)
async def get_technical_analysis():
    """
    Get current technical analysis
    
    Returns:
        Latest technical analysis signals
    """
    try:
        system = get_trading_system()
        
        technical_data = system.analysis_cache.get('technical_data')
        
        if not technical_data or not technical_data.get('signals'):
            # Return neutral signal if no data
            return TechnicalSignal(
                signal_type="HOLD",
                strength=0.5,
                confidence=0.0,
                indicators={},
                timestamp=datetime.utcnow()
            )
        
        signals = technical_data['signals']
        signal = signals[0]  # Get first signal
        
        return TechnicalSignal(
            signal_type=signal.get('type', 'HOLD'),
            strength=signal.get('strength', 0.5),
            confidence=signal.get('confidence', 0.5),
            indicators=signal.get('indicators', {}),
            timestamp=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting technical analysis: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get technical analysis: {str(e)}"
        )


@router.get("/decision")
async def get_trading_decision():
    """
    Get latest trading decision
    
    Returns:
        Latest trading decision from the decision engine
    """
    try:
        system = get_trading_system()
        
        # Get the last decision time and analysis data
        last_decision_time = system.last_decision_time
        sentiment_data = system.analysis_cache.get('sentiment_data')
        technical_data = system.analysis_cache.get('technical_data')
        
        if not last_decision_time:
            return {
                "success": True,
                "message": "No trading decisions made yet",
                "decision": None,
                "last_decision_time": None
            }
        
        # Create decision based on cached analysis
        decision = TradingDecision(
            action="HOLD",
            symbol="BTCUSDT",
            quantity=None,
            confidence=0.5,
            reasoning="Based on latest analysis",
            timestamp=last_decision_time
        )
        
        # Add analysis data if available
        if sentiment_data:
            decision.sentiment_data = SentimentAnalysis(
                sentiment_score=sentiment_data.get('average_sentiment', 0.0),
                confidence=0.8,
                key_topics=sentiment_data.get('key_topics', []),
                impact_assessment=sentiment_data.get('impact_assessment', {}),
                timestamp=last_decision_time
            )
        
        if technical_data and technical_data.get('signals'):
            signal = technical_data['signals'][0]
            decision.technical_data = TechnicalSignal(
                signal_type=signal.get('type', 'HOLD'),
                strength=signal.get('strength', 0.5),
                confidence=signal.get('confidence', 0.5),
                indicators=signal.get('indicators', {}),
                timestamp=last_decision_time
            )
        
        return {
            "success": True,
            "message": "Trading decision retrieved successfully",
            "decision": decision,
            "last_decision_time": last_decision_time.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trading decision: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get trading decision: {str(e)}"
        )


@router.post("/trigger")
async def trigger_analysis():
    """
    Manually trigger analysis processes
    
    Returns:
        Trigger confirmation
    """
    try:
        system = get_trading_system()
        
        # Trigger data collection
        await system.message_queue.enqueue_simple(
            "data_collection",
            {'type': 'market_data'},
            priority=1
        )
        
        await system.message_queue.enqueue_simple(
            "data_collection",
            {'type': 'news_data'},
            priority=1
        )
        
        return {
            "success": True,
            "message": "Analysis processes triggered successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering analysis: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger analysis: {str(e)}"
        )


@router.get("/history")
async def get_analysis_history(
    analysis_type: Optional[str] = Query(None, description="Type of analysis (sentiment, technical, decision)"),
    limit: int = Query(50, ge=1, le=1000, description="Number of records to return")
):
    """
    Get historical analysis data
    
    Args:
        analysis_type: Type of analysis to retrieve
        limit: Maximum number of records
        
    Returns:
        Historical analysis data
    """
    try:
        # This would typically query a database or time series store
        # For now, return mock historical data
        
        history = []
        for i in range(min(limit, 10)):  # Return up to 10 mock records
            timestamp = datetime.utcnow().replace(hour=datetime.utcnow().hour - i)
            
            if not analysis_type or analysis_type == "sentiment":
                history.append({
                    "type": "sentiment",
                    "timestamp": timestamp.isoformat(),
                    "data": {
                        "sentiment_score": 0.3 + (i * 0.1),
                        "confidence": 0.8,
                        "key_topics": ["bitcoin", "price", "market"]
                    }
                })
            
            if not analysis_type or analysis_type == "technical":
                history.append({
                    "type": "technical",
                    "timestamp": timestamp.isoformat(),
                    "data": {
                        "signal_type": "BUY" if i % 2 == 0 else "SELL",
                        "strength": 0.6 + (i * 0.05),
                        "confidence": 0.7,
                        "indicators": {"rsi": 45 + i, "macd": "bullish"}
                    }
                })
        
        return {
            "success": True,
            "message": f"Retrieved {len(history)} historical records",
            "data": history,
            "total_count": len(history)
        }
        
    except Exception as e:
        logger.error(f"Error getting analysis history: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get analysis history: {str(e)}"
        )