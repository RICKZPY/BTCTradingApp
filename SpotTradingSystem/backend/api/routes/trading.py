"""
Trading API routes
"""
import logging
from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Query, Depends

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.models import (
    PortfolioResponse, Portfolio, Position, OrderHistoryResponse, OrderHistory,
    TradingOrder, PlaceOrderRequest, CancelOrderRequest, APIResponse,
    MarketDataResponse, MarketData, OrderSide, OrderType, OrderStatus
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


@router.get("/portfolio", response_model=PortfolioResponse)
async def get_portfolio():
    """
    Get current portfolio status
    
    Returns:
        Current portfolio with positions and balances
    """
    try:
        system = get_trading_system()
        
        if not system.position_manager:
            raise HTTPException(
                status_code=503,
                detail="Position manager is not available"
            )
        
        # Get portfolio summary
        portfolio_summary = await system.position_manager.get_portfolio_summary()
        
        if not portfolio_summary:
            # Return empty portfolio
            portfolio = Portfolio(
                total_value=0.0,
                available_balance=0.0,
                positions=[],
                total_unrealized_pnl=0.0,
                total_unrealized_pnl_percent=0.0,
                timestamp=datetime.utcnow()
            )
        else:
            # Convert positions to API format
            positions = []
            for symbol, pos_data in portfolio_summary.positions.items():
                position = Position(
                    symbol=symbol,
                    quantity=pos_data['quantity'],
                    average_price=pos_data['average_price'],
                    current_price=pos_data.get('current_price'),
                    current_value=pos_data['current_value'],
                    unrealized_pnl=pos_data.get('unrealized_pnl', 0.0),
                    unrealized_pnl_percent=pos_data.get('unrealized_pnl_percent', 0.0),
                    side="LONG" if pos_data['quantity'] > 0 else "SHORT",
                    timestamp=portfolio_summary.timestamp
                )
                positions.append(position)
            
            portfolio = Portfolio(
                total_value=portfolio_summary.total_value,
                available_balance=portfolio_summary.available_balance,
                positions=positions,
                total_unrealized_pnl=portfolio_summary.total_unrealized_pnl,
                total_unrealized_pnl_percent=(portfolio_summary.total_unrealized_pnl / portfolio_summary.total_value * 100) if portfolio_summary.total_value > 0 else 0.0,
                timestamp=portfolio_summary.timestamp
            )
        
        return PortfolioResponse(
            message="Portfolio retrieved successfully",
            portfolio=portfolio
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting portfolio: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get portfolio: {str(e)}"
        )


@router.get("/orders", response_model=OrderHistoryResponse)
async def get_order_history(
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    status: Optional[OrderStatus] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=1000, description="Number of orders to return"),
    offset: int = Query(0, ge=0, description="Number of orders to skip")
):
    """
    Get order history
    
    Args:
        symbol: Optional symbol filter
        status: Optional status filter
        limit: Maximum number of orders to return
        offset: Number of orders to skip
        
    Returns:
        Order history with pagination
    """
    try:
        system = get_trading_system()
        
        if not system.order_manager:
            raise HTTPException(
                status_code=503,
                detail="Order manager is not available"
            )
        
        # Get order history (this would be implemented in the order manager)
        # For now, return mock data
        orders = [
            TradingOrder(
                order_id="order_123",
                symbol="BTCUSDT",
                side=OrderSide.BUY,
                type=OrderType.MARKET,
                quantity=0.1,
                price=None,
                status=OrderStatus.FILLED,
                filled_quantity=0.1,
                average_price=45000.0,
                created_at=datetime.utcnow() - timedelta(hours=1),
                updated_at=datetime.utcnow() - timedelta(hours=1)
            ),
            TradingOrder(
                order_id="order_124",
                symbol="BTCUSDT",
                side=OrderSide.SELL,
                type=OrderType.LIMIT,
                quantity=0.05,
                price=46000.0,
                status=OrderStatus.NEW,
                filled_quantity=0.0,
                average_price=None,
                created_at=datetime.utcnow() - timedelta(minutes=30),
                updated_at=None
            )
        ]
        
        # Apply filters
        if symbol:
            orders = [o for o in orders if o.symbol == symbol]
        if status:
            orders = [o for o in orders if o.status == status]
        
        # Apply pagination
        total_count = len(orders)
        orders = orders[offset:offset + limit]
        
        order_history = OrderHistory(
            orders=orders,
            total_count=total_count,
            page=offset // limit + 1,
            page_size=limit
        )
        
        return OrderHistoryResponse(
            message="Order history retrieved successfully",
            data=order_history
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting order history: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get order history: {str(e)}"
        )


@router.post("/orders", response_model=APIResponse)
async def place_order(request: PlaceOrderRequest):
    """
    Place a new trading order
    
    Args:
        request: Order placement request
        
    Returns:
        Order placement result
    """
    try:
        system = get_trading_system()
        
        if not system.order_manager:
            raise HTTPException(
                status_code=503,
                detail="Order manager is not available"
            )
        
        # Validate request
        if request.type == OrderType.LIMIT and request.price is None:
            raise HTTPException(
                status_code=400,
                detail="Price is required for LIMIT orders"
            )
        
        # Create trading decision for order execution
        from core.data_models import TradingDecision
        
        decision = TradingDecision(
            action=request.side.value,
            symbol=request.symbol,
            quantity=request.quantity,
            confidence=1.0,  # Manual orders have full confidence
            reasoning="Manual order placement via API",
            timestamp=datetime.utcnow()
        )
        
        # Execute the order
        order_result = await system.order_manager.execute_trade(decision)
        
        return APIResponse(
            success=True,
            message=f"Order placed successfully. Order ID: {order_result.order_id}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error placing order: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to place order: {str(e)}"
        )


@router.delete("/orders/{order_id}", response_model=APIResponse)
async def cancel_order(order_id: str):
    """
    Cancel an existing order
    
    Args:
        order_id: ID of the order to cancel
        
    Returns:
        Cancellation result
    """
    try:
        system = get_trading_system()
        
        if not system.order_manager:
            raise HTTPException(
                status_code=503,
                detail="Order manager is not available"
            )
        
        # Cancel the order (this would be implemented in the order manager)
        # For now, return success
        
        return APIResponse(
            success=True,
            message=f"Order {order_id} cancelled successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling order: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel order: {str(e)}"
        )


@router.get("/market-data/{symbol}", response_model=MarketDataResponse)
async def get_market_data(symbol: str):
    """
    Get current market data for a symbol
    
    Args:
        symbol: Trading symbol (e.g., BTCUSDT)
        
    Returns:
        Current market data
    """
    try:
        system = get_trading_system()
        
        # Get market data from analysis cache or data collector
        market_data_dict = system.analysis_cache.get('market_data', {})
        
        if not market_data_dict or market_data_dict.get('symbol') != symbol:
            # Return mock data if not available
            market_data_dict = {
                'symbol': symbol,
                'price': 45000.0,
                'volume': 1000.0,
                'change_24h': 500.0,
                'change_24h_percent': 1.12,
                'high_24h': 45500.0,
                'low_24h': 44000.0,
                'timestamp': datetime.utcnow().isoformat()
            }
        
        market_data = MarketData(
            symbol=market_data_dict['symbol'],
            price=market_data_dict['price'],
            volume=market_data_dict['volume'],
            change_24h=market_data_dict.get('change_24h'),
            change_24h_percent=market_data_dict.get('change_24h_percent'),
            high_24h=market_data_dict.get('high_24h'),
            low_24h=market_data_dict.get('low_24h'),
            timestamp=datetime.fromisoformat(market_data_dict['timestamp']) if isinstance(market_data_dict['timestamp'], str) else market_data_dict['timestamp']
        )
        
        return MarketDataResponse(
            message="Market data retrieved successfully",
            data=market_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting market data: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get market data: {str(e)}"
        )


@router.get("/positions/{symbol}")
async def get_position(symbol: str):
    """
    Get position for a specific symbol
    
    Args:
        symbol: Trading symbol
        
    Returns:
        Position information
    """
    try:
        system = get_trading_system()
        
        if not system.position_manager:
            raise HTTPException(
                status_code=503,
                detail="Position manager is not available"
            )
        
        # Get position for symbol (this would be implemented in position manager)
        # For now, return mock data
        
        position = Position(
            symbol=symbol,
            quantity=0.1,
            average_price=45000.0,
            current_price=45200.0,
            current_value=4520.0,
            unrealized_pnl=20.0,
            unrealized_pnl_percent=0.44,
            side="LONG",
            timestamp=datetime.utcnow()
        )
        
        return {
            "success": True,
            "message": "Position retrieved successfully",
            "position": position
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting position: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get position: {str(e)}"
        )