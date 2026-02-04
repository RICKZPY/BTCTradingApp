"""
Backtesting API routes
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import only what we need to avoid dependency issues
try:
    from backtesting.engine import BacktestEngine
    from core.data_models import MarketData
    BACKTESTING_AVAILABLE = True
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"Backtesting not available: {e}")
    BACKTESTING_AVAILABLE = False

logger = logging.getLogger(__name__)

router = APIRouter()


class BacktestRequest(BaseModel):
    """Backtest request model"""
    symbol: str = "BTCUSDT"
    days: int = 30
    initial_capital: float = 10000.0
    max_position_size: float = 0.1
    stop_loss_percentage: float = 0.05
    take_profit_percentage: float = 0.15
    min_confidence_threshold: float = 0.7
    sentiment_weight: float = 0.4
    technical_weight: float = 0.6
    strategy_name: str = "Default Strategy"


class BacktestResponse(BaseModel):
    """Backtest response model"""
    success: bool
    message: str
    timestamp: datetime = None
    data: Optional[Dict[str, Any]] = None
    
    def __init__(self, **data):
        if 'timestamp' not in data:
            data['timestamp'] = datetime.utcnow()
        super().__init__(**data)


@router.post("/run", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest):
    """
    Run backtesting with specified parameters
    
    Args:
        request: Backtest configuration
        
    Returns:
        Backtest results with performance metrics
    """
    if not BACKTESTING_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Backtesting functionality is not available due to missing dependencies"
        )
    
    try:
        logger.info(f"Starting backtest for {request.symbol} with {request.days} days")
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=request.days)
        
        # Generate sample historical data (in production, this would come from a data provider)
        historical_data = _generate_sample_market_data(request.symbol, start_date, end_date)
        
        # Create backtest engine
        engine = BacktestEngine(initial_capital=request.initial_capital)
        
        # Strategy configuration
        strategy_config = {
            'risk_parameters': {
                'max_position_size': request.max_position_size,
                'stop_loss_percentage': request.stop_loss_percentage,
                'take_profit_percentage': request.take_profit_percentage,
                'min_confidence_threshold': request.min_confidence_threshold,
                'sentiment_weight': request.sentiment_weight,
                'technical_weight': request.technical_weight
            }
        }
        
        # Run backtest
        result = engine.run_backtest(
            start_date=start_date,
            end_date=end_date,
            strategy_config=strategy_config,
            historical_data=historical_data,
            strategy_name=request.strategy_name
        )
        
        # Convert result to API format
        metrics = result.performance_metrics
        
        response_data = {
            'backtest_id': result.backtest_id,
            'strategy_name': result.strategy_name,
            'performance_metrics': {
                'total_return': metrics.total_return,
                'annualized_return': metrics.annualized_return,
                'total_trades': metrics.total_trades,
                'winning_trades': metrics.winning_trades,
                'losing_trades': metrics.losing_trades,
                'win_rate': metrics.win_rate,
                'sharpe_ratio': metrics.sharpe_ratio,
                'max_drawdown': metrics.max_drawdown,
                'max_drawdown_duration': metrics.max_drawdown_duration,
                'volatility': metrics.volatility,
                'average_win': metrics.average_win,
                'average_loss': metrics.average_loss,
                'profit_factor': metrics.profit_factor,
                'largest_win': metrics.largest_win,
                'largest_loss': metrics.largest_loss,
                'initial_capital': metrics.initial_capital,
                'final_capital': metrics.final_capital,
                'peak_capital': metrics.peak_capital,
                'calmar_ratio': metrics.calmar_ratio,
                'sortino_ratio': metrics.sortino_ratio,
                'duration_days': metrics.duration_days
            },
            'trades': [trade.to_dict() for trade in result.trades],
            'equity_curve': [
                {'timestamp': timestamp.isoformat(), 'value': value}
                for timestamp, value in result.equity_curve
            ],
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'data_points': len(historical_data)
        }
        
        logger.info(f"Backtest completed: {len(result.trades)} trades, "
                   f"{metrics.total_return:.2%} return")
        
        return BacktestResponse(
            success=True,
            message="Backtest completed successfully",
            data=response_data
        )
        
    except Exception as e:
        logger.error(f"Error running backtest: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to run backtest: {str(e)}"
        )


@router.get("/status")
async def get_backtest_status():
    """
    Get backtesting engine status
    
    Returns:
        Backtesting engine status and capabilities
    """
    if not BACKTESTING_AVAILABLE:
        return {
            "success": False,
            "message": "Backtesting functionality is not available",
            "data": {
                "available": False,
                "reason": "Missing dependencies"
            }
        }
    
    try:
        # Create a temporary engine to get status
        engine = BacktestEngine()
        status = engine.get_engine_status()
        
        return {
            "success": True,
            "message": "Backtest engine status retrieved successfully",
            "data": {
                **status,
                "available": True,
                "supported_symbols": ["BTCUSDT", "ETHUSDT", "ADAUSDT"],
                "max_backtest_days": 365,
                "min_backtest_days": 1
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting backtest status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get backtest status: {str(e)}"
        )


def _generate_sample_market_data(symbol: str, start_date: datetime, end_date: datetime):
    """
    Generate sample market data for backtesting
    In production, this would fetch real historical data
    """
    if not BACKTESTING_AVAILABLE:
        return []
    
    data = []
    current_date = start_date
    base_price = 45000.0  # Starting price for BTCUSDT
    
    # Generate hourly data points
    while current_date <= end_date:
        # Simple random walk with some trend
        price_change = (hash(str(current_date)) % 1000 - 500) / 100  # -5 to +5 USD change
        base_price += price_change
        base_price = max(base_price, 1000.0)  # Minimum price floor
        
        volume = 1000 + (hash(str(current_date + timedelta(minutes=1))) % 500)  # Random volume
        
        data.append(MarketData(
            symbol=symbol,
            timestamp=current_date,
            price=base_price,
            volume=volume,
            source="backtest_generator"
        ))
        
        current_date += timedelta(hours=1)  # Hourly data
    
    logger.info(f"Generated {len(data)} market data points for {symbol}")
    return data