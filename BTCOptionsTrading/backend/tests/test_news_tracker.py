#!/usr/bin/env python3
"""
单元测试：NewsTracker 组件
Unit tests for NewsTracker component
"""

import pytest
import asyncio
import os
import tempfile
from datetime import datetime
from pathlib import Path

from weighted_sentiment_news_tracker import NewsTracker
from weighted_sentiment_models import WeightedNews


@pytest.fixture
def temp_db():
    """创建临时数据库用于测试"""
    # 创建临时文件
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    yield path
    
    # 清理临时文件
    try:
        os.unlink(path)
    except:
        pass


@pytest.fixture
def tracker(temp_db):
    """创建 NewsTracker 实例"""
    return NewsTracker(db_path=temp_db)


@pytest.fixture
def sample_news():
    """创建示例新闻列表"""
    return [
        WeightedNews(
            news_id="news_001",
            content="Major BTC announcement",
            sentiment="positive",
            importance_score=9,
            timestamp=datetime.now()
        ),
        WeightedNews(
            news_id="news_002",
            content="Minor update",
            sentiment="neutral",
            importance_score=5,
            timestamp=datetime.now()
        ),
        WeightedNews(
            news_id="news_003",
            content="Important market change",
            sentiment="negative",
            importance_score=8,
            timestamp=datetime.now()
        ),
        WeightedNews(
            news_id="news_004",
            content="Regulatory news",
            sentiment="negative",
            importance_score=7,
            timestamp=datetime.now()
        ),
        WeightedNews(
            news_id="news_005",
            content="Low importance update",
            sentiment="neutral",
            importance_score=6,
            timestamp=datetime.now()
        )
    ]


class TestNewsDatabaseInitialization:
    """测试数据库初始化"""
    
    def test_database_creation(self, temp_db):
        """测试数据库文件创建"""
        tracker = NewsTracker(db_path=temp_db)
        assert os.path.exists(temp_db)
    
    def test_table_creation(self, tracker, temp_db):
        """测试表结构创建"""
        import sqlite3
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='news_history'
        """)
        result = cursor.fetchone()
        assert result is not None
        assert result[0] == 'news_history'
        
        conn.close()
    
    def test_index_creation(self, tracker, temp_db):
        """测试索引创建"""
        import sqlite3
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # 检查索引是否存在
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index' AND name='idx_news_timestamp'
        """)
        result = cursor.fetchone()
        assert result is not None
        assert result[0] == 'idx_news_timestamp'
        
        conn.close()


class TestNewsIdentification:
    """测试新闻识别逻辑"""
    
    @pytest.mark.asyncio
    async def test_identify_new_high_score_news(self, tracker, sample_news):
        """测试识别新的高分新闻"""
        # 第一次识别应该返回所有评分 >= 7 的新闻
        new_news = await tracker.identify_new_news(sample_news)
        
        # 应该识别出 3 条新闻（评分 9, 8, 7）
        assert len(new_news) == 3
        
        # 验证所有识别出的新闻评分 >= 7
        for news in new_news:
            assert news.importance_score >= 7
        
        # 验证具体的新闻 ID
        news_ids = {news.news_id for news in new_news}
        assert news_ids == {"news_001", "news_003", "news_004"}
    
    @pytest.mark.asyncio
    async def test_score_threshold_boundary(self, tracker):
        """测试评分阈值边界情况（6, 7, 8）"""
        news_list = [
            WeightedNews(
                news_id=f"news_{score}",
                content=f"News with score {score}",
                sentiment="neutral",
                importance_score=score,
                timestamp=datetime.now()
            )
            for score in [6, 7, 8]
        ]
        
        new_news = await tracker.identify_new_news(news_list)
        
        # 应该只识别出评分 7 和 8 的新闻
        assert len(new_news) == 2
        
        news_ids = {news.news_id for news in new_news}
        assert news_ids == {"news_7", "news_8"}
    
    @pytest.mark.asyncio
    async def test_empty_news_list(self, tracker):
        """测试空新闻列表"""
        new_news = await tracker.identify_new_news([])
        assert len(new_news) == 0
    
    @pytest.mark.asyncio
    async def test_no_duplicate_identification(self, tracker, sample_news):
        """测试不会重复识别同一新闻"""
        # 第一次识别
        new_news_1 = await tracker.identify_new_news(sample_news)
        assert len(new_news_1) == 3
        
        # 更新历史
        await tracker.update_history(sample_news)
        
        # 第二次识别应该返回空列表
        new_news_2 = await tracker.identify_new_news(sample_news)
        assert len(new_news_2) == 0


class TestNewsHistoryUpdate:
    """测试新闻历史更新"""
    
    @pytest.mark.asyncio
    async def test_update_history(self, tracker, sample_news):
        """测试更新新闻历史"""
        # 更新历史
        await tracker.update_history(sample_news)
        
        # 验证所有新闻都已保存
        for news in sample_news:
            is_processed = await tracker.is_news_processed(news.news_id)
            assert is_processed is True
    
    @pytest.mark.asyncio
    async def test_update_empty_list(self, tracker):
        """测试更新空列表"""
        # 不应该抛出异常
        await tracker.update_history([])
        
        count = tracker.get_history_count()
        assert count == 0
    
    @pytest.mark.asyncio
    async def test_duplicate_update_ignored(self, tracker, sample_news):
        """测试重复更新被忽略"""
        # 第一次更新
        await tracker.update_history(sample_news)
        count_1 = tracker.get_history_count()
        
        # 第二次更新相同的新闻
        await tracker.update_history(sample_news)
        count_2 = tracker.get_history_count()
        
        # 数量应该相同（重复插入被忽略）
        assert count_1 == count_2
        assert count_1 == len(sample_news)


class TestNewsProcessedCheck:
    """测试新闻处理状态检查"""
    
    @pytest.mark.asyncio
    async def test_is_news_processed_false(self, tracker):
        """测试未处理的新闻"""
        is_processed = await tracker.is_news_processed("nonexistent_news")
        assert is_processed is False
    
    @pytest.mark.asyncio
    async def test_is_news_processed_true(self, tracker, sample_news):
        """测试已处理的新闻"""
        # 更新历史
        await tracker.update_history(sample_news)
        
        # 检查第一条新闻
        is_processed = await tracker.is_news_processed(sample_news[0].news_id)
        assert is_processed is True


class TestHistoryCount:
    """测试历史记录计数"""
    
    def test_initial_count_zero(self, tracker):
        """测试初始计数为 0"""
        count = tracker.get_history_count()
        assert count == 0
    
    @pytest.mark.asyncio
    async def test_count_after_update(self, tracker, sample_news):
        """测试更新后的计数"""
        await tracker.update_history(sample_news)
        
        count = tracker.get_history_count()
        assert count == len(sample_news)


class TestClearHistory:
    """测试清空历史记录"""
    
    @pytest.mark.asyncio
    async def test_clear_history(self, tracker, sample_news):
        """测试清空历史记录"""
        # 添加一些数据
        await tracker.update_history(sample_news)
        assert tracker.get_history_count() > 0
        
        # 清空历史
        tracker.clear_history()
        
        # 验证已清空
        count = tracker.get_history_count()
        assert count == 0


class TestIntegrationScenarios:
    """测试集成场景"""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self, tracker, sample_news):
        """测试完整工作流程"""
        # 1. 第一次检查：识别所有高分新闻
        new_news = await tracker.identify_new_news(sample_news)
        assert len(new_news) == 3
        
        # 2. 更新历史
        await tracker.update_history(sample_news)
        
        # 3. 第二次检查：不应该有新新闻
        new_news = await tracker.identify_new_news(sample_news)
        assert len(new_news) == 0
        
        # 4. 添加新的新闻
        new_sample = [
            WeightedNews(
                news_id="news_006",
                content="Another important news",
                sentiment="positive",
                importance_score=9,
                timestamp=datetime.now()
            )
        ]
        
        # 5. 第三次检查：应该识别出新新闻
        new_news = await tracker.identify_new_news(new_sample)
        assert len(new_news) == 1
        assert new_news[0].news_id == "news_006"
    
    @pytest.mark.asyncio
    async def test_mixed_scores_workflow(self, tracker):
        """测试混合评分的工作流程"""
        # 创建包含各种评分的新闻
        news_list = [
            WeightedNews(
                news_id=f"news_{i}",
                content=f"News {i}",
                sentiment="neutral",
                importance_score=i,
                timestamp=datetime.now()
            )
            for i in range(1, 11)  # 评分 1-10
        ]
        
        # 识别高分新闻
        new_news = await tracker.identify_new_news(news_list)
        
        # 应该识别出评分 7, 8, 9, 10 的新闻
        assert len(new_news) == 4
        
        # 验证所有评分 >= 7
        for news in new_news:
            assert news.importance_score >= 7


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
