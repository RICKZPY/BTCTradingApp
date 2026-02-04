#!/usr/bin/env python3
"""
Test the Bitcoin Trading System API
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import json

from api.main import app

# Create test client
client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Bitcoin Trading System API"
    assert data["version"] == "1.0.0"


def test_health_simple():
    """Test simple health check"""
    with patch('api.main.trading_system', None):
        response = client.get("/api/v1/health/simple")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data


def test_health_liveness():
    """Test liveness probe"""
    response = client.get("/api/v1/health/liveness")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"


@patch('api.main.trading_system')
def test_system_status_unavailable(mock_system):
    """Test system status when trading system is unavailable"""
    mock_system = None
    
    response = client.get("/api/v1/system/status")
    assert response.status_code == 503
    data = response.json()
    assert data["success"] == False
    assert "not available" in data["message"]


@patch('api.main.trading_system')
def test_portfolio_unavailable(mock_system):
    """Test portfolio when trading system is unavailable"""
    mock_system = None
    
    response = client.get("/api/v1/trading/portfolio")
    assert response.status_code == 503


@patch('api.main.trading_system')
def test_market_data(mock_system):
    """Test market data endpoint"""
    # Mock trading system
    mock_system.analysis_cache = {
        'market_data': {
            'symbol': 'BTCUSDT',
            'price': 45000.0,
            'volume': 1000.0,
            'timestamp': '2024-01-01T00:00:00'
        }
    }
    
    response = client.get("/api/v1/trading/market-data/BTCUSDT")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert data["data"]["symbol"] == "BTCUSDT"
    assert data["data"]["price"] == 45000.0


@patch('api.main.trading_system')
def test_analysis_current(mock_system):
    """Test current analysis endpoint"""
    # Mock trading system with analysis cache
    mock_system.analysis_cache = {
        'sentiment_data': {
            'average_sentiment': 0.5,
            'key_topics': ['bitcoin', 'price'],
            'impact_assessment': {'short_term': 0.7}
        },
        'technical_data': {
            'signals': [{
                'type': 'BUY',
                'strength': 0.8,
                'confidence': 0.9,
                'indicators': {'rsi': 30}
            }]
        }
    }
    
    response = client.get("/api/v1/analysis/current")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert data["sentiment"] is not None
    assert data["technical"] is not None
    assert data["decision"] is not None


def test_order_history():
    """Test order history endpoint"""
    with patch('api.main.trading_system') as mock_system:
        mock_system.order_manager = Mock()
        
        response = client.get("/api/v1/trading/orders")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "data" in data
        assert "orders" in data["data"]


def test_place_order_validation():
    """Test order placement validation"""
    # Test invalid order (LIMIT without price)
    order_data = {
        "symbol": "BTCUSDT",
        "side": "BUY",
        "type": "LIMIT",
        "quantity": 0.1
        # Missing price for LIMIT order
    }
    
    with patch('api.main.trading_system') as mock_system:
        mock_system.order_manager = Mock()
        
        response = client.post("/api/v1/trading/orders", json=order_data)
        assert response.status_code == 400
        data = response.json()
        assert "Price is required for LIMIT orders" in data["message"]


def test_trigger_analysis():
    """Test analysis trigger endpoint"""
    with patch('api.main.trading_system') as mock_system:
        mock_system.message_queue = Mock()
        mock_system.message_queue.enqueue_simple = Mock()
        
        response = client.post("/api/v1/analysis/trigger", json={})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "triggered" in data["message"]


def test_system_control():
    """Test system control endpoint"""
    with patch('api.main.trading_system') as mock_system:
        mock_system.start = Mock()
        mock_system.stop = Mock()
        
        # Test start
        response = client.post("/api/v1/system/control", json={"action": "start"})
        assert response.status_code == 200
        
        # Test invalid action
        response = client.post("/api/v1/system/control", json={"action": "invalid"})
        assert response.status_code == 400


def test_api_documentation():
    """Test API documentation endpoints"""
    # Test OpenAPI docs
    response = client.get("/docs")
    assert response.status_code == 200
    
    # Test ReDoc
    response = client.get("/redoc")
    assert response.status_code == 200
    
    # Test OpenAPI JSON
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert data["info"]["title"] == "Bitcoin Trading System API"


def run_tests():
    """Run all tests"""
    print("Running Bitcoin Trading System API Tests")
    print("=" * 50)
    
    test_functions = [
        test_root_endpoint,
        test_health_simple,
        test_health_liveness,
        test_system_status_unavailable,
        test_portfolio_unavailable,
        test_market_data,
        test_analysis_current,
        test_order_history,
        test_place_order_validation,
        test_trigger_analysis,
        test_system_control,
        test_api_documentation
    ]
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            print(f"Running {test_func.__name__}...", end=" ")
            test_func()
            print("✓ PASSED")
            passed += 1
        except Exception as e:
            print(f"✗ FAILED: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"Tests completed: {passed} passed, {failed} failed")
    
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)