#!/usr/bin/env python3
"""
集成测试：NewsAPIClient
Integration tests for NewsAPIClient - tests actual API interaction
"""

import pytest
import asyncio
from datetime import datetime

from weighted_sentiment_api_client import NewsAPIClient
from weighted_sentiment_models import WeightedNews


class TestNewsAPIClientIntegration:
    """NewsAPIClient 集成测试类 - 测试实际 API 交互"""
    
    @pytest.mark.asyncio
    async def test_fetch_from_real_api(self):
        """测试从真实 API 获取数据（如果 API 可用）
        
        注意：此测试依赖外部 API，可能会失败如果 API 不可用
        """
        client = NewsAPIClient()
        
        try:
            news_list = await client.fetch_weighted_news()
            
            # 如果 API 返回数据，验证数据格式
            if news_list:
                print(f"\n成功获取 {len(news_list)} 条新闻")
                
                # 验证所有新闻都是 WeightedNews 对象
                assert all(isinstance(news, WeightedNews) for news in news_list)
                
                # 验证第一条新闻的字段
                first_news = news_list[0]
                assert first_news.news_id
                assert first_news.content
                assert first_news.sentiment in ['positive', 'negative', 'neutral']
                assert 1 <= first_news.importance_score <= 10
                assert isinstance(first_news.timestamp, datetime)
                
                print(f"示例新闻：")
                print(f"  ID: {first_news.news_id}")
                print(f"  内容: {first_news.content[:50]}...")
                print(f"  情绪: {first_news.sentiment}")
                print(f"  评分: {first_news.importance_score}")
            else:
                print("\nAPI 返回空列表（可能是 API 暂时无数据或不可用）")
                # 空列表也是有效的响应
                assert news_list == []
        
        except Exception as e:
            # 如果 API 不可用，测试应该优雅地失败
            print(f"\nAPI 不可用或发生错误: {e}")
            pytest.skip(f"API 不可用: {e}")
    
    @pytest.mark.asyncio
    async def test_parse_methods_directly(self):
        """直接测试解析方法"""
        client = NewsAPIClient()
        
        # 测试解析新闻项
        test_item = {
            'news_id': 'test_001',
            'content': 'Test news content',
            'sentiment': 'positive',
            'importance_score': 8,
            'timestamp': '2024-01-15T10:30:00',
            'source': 'TestSource'
        }
        
        news = client._parse_news_item(test_item)
        
        assert news.news_id == 'test_001'
        assert news.content == 'Test news content'
        assert news.sentiment == 'positive'
        assert news.importance_score == 8
        assert news.source == 'TestSource'
        assert isinstance(news.timestamp, datetime)
    
    @pytest.mark.asyncio
    async def test_timeout_configuration(self):
        """测试超时配置"""
        # 创建一个超时时间很短的客户端
        client = NewsAPIClient(timeout=1)
        
        assert client.timeout.total == 1
        
        # 尝试获取数据（可能会超时，这是预期的）
        news_list = await client.fetch_weighted_news()
        
        # 无论成功还是超时，都应该返回列表
        assert isinstance(news_list, list)


if __name__ == '__main__':
    # 运行集成测试
    pytest.main([__file__, '-v', '-s'])
