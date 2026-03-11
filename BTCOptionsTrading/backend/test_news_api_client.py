#!/usr/bin/env python3
"""
单元测试：NewsAPIClient
Unit tests for NewsAPIClient class
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import MagicMock, patch
import aiohttp

from weighted_sentiment_api_client import NewsAPIClient
from weighted_sentiment_models import WeightedNews


# Python 3.7 兼容：创建 AsyncMock
class AsyncMock(MagicMock):
    """异步 Mock 对象（Python 3.7 兼容）"""
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)
    
    def __await__(self):
        return self().__await__()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *args):
        return None


class TestNewsAPIClient:
    """NewsAPIClient 单元测试类"""
    
    def test_init(self):
        """测试客户端初始化"""
        client = NewsAPIClient()
        assert client.api_url == "http://43.106.51.106:5002/api/weighted-sentiment/news"
        assert client.timeout.total == 30
        
        # 测试自定义参数
        custom_client = NewsAPIClient(
            api_url="https://custom.api.com/news",
            timeout=60
        )
        assert custom_client.api_url == "https://custom.api.com/news"
        assert custom_client.timeout.total == 60
    
    @pytest.mark.asyncio
    async def test_fetch_weighted_news_success(self):
        """测试成功获取新闻数据"""
        client = NewsAPIClient()
        
        # 模拟 API 响应数据
        mock_response_data = [
            {
                'news_id': 'news_001',
                'content': 'Bitcoin reaches new high',
                'sentiment': 'positive',
                'importance_score': 9,
                'timestamp': '2024-01-15T10:30:00',
                'source': 'CoinDesk'
            },
            {
                'news_id': 'news_002',
                'content': 'Market volatility increases',
                'sentiment': 'neutral',
                'importance_score': 7,
                'timestamp': '2024-01-15T11:00:00'
            }
        ]
        
        # 模拟 aiohttp 响应
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_response_data)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('weighted_sentiment_api_client.aiohttp.ClientSession', return_value=mock_session):
            news_list = await client.fetch_weighted_news()
        
        # 验证结果
        assert len(news_list) == 2
        assert all(isinstance(news, WeightedNews) for news in news_list)
        
        # 验证第一条新闻
        assert news_list[0].news_id == 'news_001'
        assert news_list[0].content == 'Bitcoin reaches new high'
        assert news_list[0].sentiment == 'positive'
        assert news_list[0].importance_score == 9
        assert news_list[0].source == 'CoinDesk'
        
        # 验证第二条新闻
        assert news_list[1].news_id == 'news_002'
        assert news_list[1].importance_score == 7
    
    @pytest.mark.asyncio
    async def test_fetch_weighted_news_http_error(self):
        """测试 HTTP 错误响应"""
        client = NewsAPIClient()
        
        # 模拟 HTTP 错误响应
        mock_response = MagicMock()
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value="Internal Server Error")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('weighted_sentiment_api_client.aiohttp.ClientSession', return_value=mock_session):
            news_list = await client.fetch_weighted_news()
        
        # 验证返回空列表
        assert news_list == []
    
    @pytest.mark.asyncio
    async def test_fetch_weighted_news_timeout(self):
        """测试请求超时"""
        client = NewsAPIClient(timeout=1)
        
        # 模拟超时异常
        mock_response = MagicMock()
        mock_response.__aenter__ = AsyncMock(side_effect=asyncio.TimeoutError())
        
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('weighted_sentiment_api_client.aiohttp.ClientSession', return_value=mock_session):
            news_list = await client.fetch_weighted_news()
        
        # 验证返回空列表
        assert news_list == []
    
    @pytest.mark.asyncio
    async def test_fetch_weighted_news_connection_error(self):
        """测试连接错误"""
        client = NewsAPIClient()
        
        # 模拟连接错误
        mock_session = MagicMock()
        mock_session.get = MagicMock(
            side_effect=aiohttp.ClientConnectorError(
                connection_key=None,
                os_error=OSError("Connection refused")
            )
        )
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('weighted_sentiment_api_client.aiohttp.ClientSession', return_value=mock_session):
            news_list = await client.fetch_weighted_news()
        
        # 验证返回空列表
        assert news_list == []
    
    @pytest.mark.asyncio
    async def test_fetch_weighted_news_json_parse_error(self):
        """测试 JSON 解析错误"""
        client = NewsAPIClient()
        
        # 模拟 JSON 解析错误
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            side_effect=aiohttp.ContentTypeError(
                request_info=None,
                history=None,
                message="Invalid JSON"
            )
        )
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('weighted_sentiment_api_client.aiohttp.ClientSession', return_value=mock_session):
            news_list = await client.fetch_weighted_news()
        
        # 验证返回空列表
        assert news_list == []
    
    @pytest.mark.asyncio
    async def test_fetch_weighted_news_invalid_response_format(self):
        """测试无效的响应格式（非列表）"""
        client = NewsAPIClient()
        
        # 模拟非列表响应
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={'error': 'Invalid format'})
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('weighted_sentiment_api_client.aiohttp.ClientSession', return_value=mock_session):
            news_list = await client.fetch_weighted_news()
        
        # 验证返回空列表
        assert news_list == []
    
    @pytest.mark.asyncio
    async def test_fetch_weighted_news_skip_invalid_items(self):
        """测试跳过无效新闻项"""
        client = NewsAPIClient()
        
        # 模拟包含有效和无效新闻项的响应
        mock_response_data = [
            {
                'news_id': 'news_001',
                'content': 'Valid news',
                'sentiment': 'positive',
                'importance_score': 8,
                'timestamp': '2024-01-15T10:30:00'
            },
            {
                # 缺少 news_id 字段
                'content': 'Invalid news',
                'sentiment': 'neutral',
                'importance_score': 7,
                'timestamp': '2024-01-15T11:00:00'
            },
            {
                'news_id': 'news_003',
                'content': 'Another valid news',
                'sentiment': 'negative',
                'importance_score': 9,
                'timestamp': '2024-01-15T12:00:00'
            }
        ]
        
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_response_data)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('weighted_sentiment_api_client.aiohttp.ClientSession', return_value=mock_session):
            news_list = await client.fetch_weighted_news()
        
        # 验证只返回有效的新闻项
        assert len(news_list) == 2
        assert news_list[0].news_id == 'news_001'
        assert news_list[1].news_id == 'news_003'
    
    def test_parse_news_item_success(self):
        """测试成功解析新闻项"""
        client = NewsAPIClient()
        
        item = {
            'news_id': 'news_001',
            'content': 'Test news',
            'sentiment': 'positive',
            'importance_score': 8,
            'timestamp': '2024-01-15T10:30:00',
            'source': 'TestSource'
        }
        
        news = client._parse_news_item(item)
        
        assert news.news_id == 'news_001'
        assert news.content == 'Test news'
        assert news.sentiment == 'positive'
        assert news.importance_score == 8
        assert news.source == 'TestSource'
        assert isinstance(news.timestamp, datetime)
    
    def test_parse_news_item_missing_field(self):
        """测试缺少必需字段"""
        client = NewsAPIClient()
        
        item = {
            'news_id': 'news_001',
            'content': 'Test news',
            # 缺少 sentiment 字段
            'importance_score': 8,
            'timestamp': '2024-01-15T10:30:00'
        }
        
        with pytest.raises(KeyError):
            client._parse_news_item(item)
    
    def test_parse_news_item_invalid_score(self):
        """测试无效的重要性评分"""
        client = NewsAPIClient()
        
        item = {
            'news_id': 'news_001',
            'content': 'Test news',
            'sentiment': 'positive',
            'importance_score': 15,  # 超出范围
            'timestamp': '2024-01-15T10:30:00'
        }
        
        with pytest.raises(ValueError):
            client._parse_news_item(item)
    
    def test_parse_timestamp_iso_format(self):
        """测试解析 ISO 8601 格式时间戳"""
        client = NewsAPIClient()
        
        # 测试标准 ISO 格式
        timestamp = client._parse_timestamp('2024-01-15T10:30:00')
        assert isinstance(timestamp, datetime)
        assert timestamp.year == 2024
        assert timestamp.month == 1
        assert timestamp.day == 15
        
        # 测试带 Z 的 ISO 格式
        timestamp_z = client._parse_timestamp('2024-01-15T10:30:00Z')
        assert isinstance(timestamp_z, datetime)
    
    def test_parse_timestamp_unix_format(self):
        """测试解析 Unix 时间戳"""
        client = NewsAPIClient()
        
        # Unix 时间戳（秒）
        unix_timestamp = 1705318200  # 2024-01-15 10:30:00 UTC
        timestamp = client._parse_timestamp(unix_timestamp)
        assert isinstance(timestamp, datetime)
    
    def test_parse_timestamp_datetime_object(self):
        """测试已经是 datetime 对象的时间戳"""
        client = NewsAPIClient()
        
        dt = datetime(2024, 1, 15, 10, 30, 0)
        timestamp = client._parse_timestamp(dt)
        assert timestamp == dt
    
    def test_parse_timestamp_invalid(self):
        """测试无效的时间戳格式"""
        client = NewsAPIClient()
        
        with pytest.raises(ValueError):
            client._parse_timestamp('invalid-timestamp')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
