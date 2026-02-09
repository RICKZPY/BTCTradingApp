"""
Deribit连接器测试
测试与Deribit API的交互功能
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from src.connectors.deribit_connector import DeribitConnector, RateLimiter
from src.core.models import OptionContract, OptionType, MarketData
from src.core.exceptions import APIConnectionError


class TestRateLimiter:
    """测试限流器"""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_allows_requests_within_limit(self):
        """测试限流器允许限制内的请求"""
        limiter = RateLimiter(max_requests=5, time_window=1)
        
        # 应该能够快速发送5个请求
        start_time = asyncio.get_event_loop().time()
        for _ in range(5):
            await limiter.acquire()
        end_time = asyncio.get_event_loop().time()
        
        # 应该在很短时间内完成
        assert end_time - start_time < 0.1
    
    @pytest.mark.asyncio
    async def test_rate_limiter_blocks_excess_requests(self):
        """测试限流器阻止超限请求"""
        limiter = RateLimiter(max_requests=3, time_window=1)
        
        # 发送3个请求
        for _ in range(3):
            await limiter.acquire()
        
        # 第4个请求应该被延迟
        start_time = asyncio.get_event_loop().time()
        await limiter.acquire()
        end_time = asyncio.get_event_loop().time()
        
        # 应该至少等待接近1秒
        assert end_time - start_time >= 0.9


class TestDeribitConnector:
    """测试Deribit连接器"""
    
    @pytest.fixture
    def connector(self):
        """创建连接器实例"""
        return DeribitConnector()
    
    @pytest.mark.asyncio
    async def test_connector_initialization(self, connector):
        """测试连接器初始化"""
        assert connector.base_url is not None
        assert connector.client is not None
        assert connector.rate_limiter is not None
        assert connector.access_token is None
    
    @pytest.mark.asyncio
    async def test_parse_option_contract(self, connector):
        """测试解析期权合约数据"""
        mock_data = {
            "instrument_name": "BTC-25DEC26-50000-C",
            "base_currency": "BTC",
            "option_type": "call",
            "strike": 50000,
            "expiration_timestamp": 1735084800000,  # 2024-12-25
            "mark_price": 2500,
            "best_bid_price": 2450,
            "best_ask_price": 2550,
            "last_price": 2500,
            "mark_iv": 80,  # 80%
            "greeks": {
                "delta": 0.6,
                "gamma": 0.001,
                "theta": -10.5,
                "vega": 25.0,
                "rho": 15.0
            },
            "open_interest": 100,
            "stats": {"volume": 50}
        }
        
        contract = connector._parse_option_contract(mock_data)
        
        assert contract.instrument_name == "BTC-25DEC26-50000-C"
        assert contract.underlying == "BTC"
        assert contract.option_type == OptionType.CALL
        assert contract.strike_price == Decimal("50000")
        assert contract.current_price == Decimal("2500")
        assert contract.implied_volatility == 0.8  # 转换为小数
        assert contract.delta == 0.6
        assert contract.open_interest == 100
    
    @pytest.mark.asyncio
    async def test_request_with_mock_response(self, connector):
        """测试API请求（使用模拟响应）"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"test": "data"}
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch.object(connector.client, 'post', return_value=mock_response) as mock_post:
            # 将mock_post设置为异步函数
            async def async_post(*args, **kwargs):
                return mock_response
            mock_post.side_effect = async_post
            
            result = await connector._request("test_method", {"param": "value"})
            
            assert result == {"test": "data"}
            assert mock_post.called
    
    @pytest.mark.asyncio
    async def test_request_handles_api_error(self, connector):
        """测试API请求处理错误"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {"message": "Test error"}
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch.object(connector.client, 'post', return_value=mock_response) as mock_post:
            async def async_post(*args, **kwargs):
                return mock_response
            mock_post.side_effect = async_post
            
            with pytest.raises(APIConnectionError, match="Test error"):
                await connector._request("test_method")
    
    @pytest.mark.asyncio
    async def test_get_options_chain_with_mock(self, connector):
        """测试获取期权链（使用模拟数据）"""
        mock_instruments = [
            {
                "instrument_name": "BTC-25DEC26-50000-C",
                "base_currency": "BTC",
                "option_type": "call",
                "strike": 50000,
                "expiration_timestamp": 1735084800000,
                "mark_price": 2500,
                "best_bid_price": 2450,
                "best_ask_price": 2550,
                "last_price": 2500,
                "mark_iv": 80,
                "greeks": {"delta": 0.6, "gamma": 0.001, "theta": -10.5, "vega": 25.0, "rho": 15.0},
                "open_interest": 100,
                "stats": {"volume": 50}
            }
        ]
        
        # 创建异步mock函数
        async def mock_request(*args, **kwargs):
            return mock_instruments
        
        with patch.object(connector, '_request', side_effect=mock_request):
            contracts = await connector.get_options_chain("BTC")
            
            assert len(contracts) == 1
            assert contracts[0].instrument_name == "BTC-25DEC26-50000-C"
            assert contracts[0].option_type == OptionType.CALL
    
    @pytest.mark.asyncio
    async def test_get_real_time_data_with_mock(self, connector):
        """测试获取实时数据（使用模拟数据）"""
        mock_ticker = {
            "last_price": 45000,
            "best_bid_price": 44950,
            "best_ask_price": 45050,
            "stats": {"volume": 1000}
        }
        
        # 创建异步mock函数
        async def mock_request(*args, **kwargs):
            return mock_ticker
        
        with patch.object(connector, '_request', side_effect=mock_request):
            market_data = await connector.get_real_time_data(["BTC-PERPETUAL"])
            
            assert "BTC-PERPETUAL" in market_data
            data = market_data["BTC-PERPETUAL"]
            assert data.price == Decimal("45000")
            assert data.bid == Decimal("44950")
            assert data.ask == Decimal("45050")
            assert data.volume == 1000
    
    @pytest.mark.asyncio
    async def test_connector_close(self, connector):
        """测试连接器关闭"""
        with patch.object(connector.client, 'aclose') as mock_close:
            async def async_close():
                pass
            mock_close.side_effect = async_close
            
            await connector.close()
            assert mock_close.called


class TestDeribitConnectorIntegration:
    """集成测试（需要实际API连接，标记为可选）"""
    
    @pytest.mark.skip(reason="Requires actual API connection")
    @pytest.mark.asyncio
    async def test_real_api_connection(self):
        """测试真实API连接"""
        connector = DeribitConnector()
        
        try:
            # 测试获取期权链
            contracts = await connector.get_options_chain("BTC")
            assert len(contracts) > 0
            
            # 验证合约数据
            contract = contracts[0]
            assert contract.instrument_name is not None
            assert contract.strike_price > 0
            assert contract.option_type in [OptionType.CALL, OptionType.PUT]
            
        finally:
            await connector.close()
