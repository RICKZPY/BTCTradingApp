#!/usr/bin/env python3
"""
属性测试：WeightedNews 数据验证
Property-based tests for WeightedNews data validation using hypothesis

**Validates: Requirements 8.1, 8.2, 8.3**
"""

import pytest
from datetime import datetime, timedelta
from hypothesis import given, strategies as st, assume
from weighted_sentiment_models import WeightedNews


# 定义有效的情绪值策略
valid_sentiments = st.sampled_from(["positive", "negative", "neutral"])

# 定义有效的 importance_score 策略（1-10）
valid_scores = st.integers(min_value=1, max_value=10)

# 定义无效的 importance_score 策略（范围外）
invalid_scores_below = st.integers(max_value=0)
invalid_scores_above = st.integers(min_value=11)

# 定义非空字符串策略
non_empty_strings = st.text(min_size=1).filter(lambda s: s.strip())

# 定义空或仅空格字符串策略
empty_or_whitespace_strings = st.one_of(
    st.just(""),
    st.text(min_size=1, max_size=10).filter(lambda s: not s.strip())
)


class TestWeightedNewsPropertyValidation:
    """属性测试：WeightedNews 数据验证完整性
    
    **Validates: Requirements 8.1, 8.2, 8.3**
    
    Property 6: Data Validation Completeness
    对于任意 WeightedNews 对象，必须满足：
    - importance_score 在 1-10 范围内
    - sentiment 为有效值之一
    - news_id 非空
    """
    
    @given(
        news_id=non_empty_strings,
        content=st.text(),
        sentiment=valid_sentiments,
        importance_score=valid_scores,
        source=st.one_of(st.none(), st.text())
    )
    def test_property_valid_news_always_accepted(
        self, news_id, content, sentiment, importance_score, source
    ):
        """属性：所有满足验证规则的新闻对象都应该被成功创建
        
        **Validates: Requirements 8.1, 8.2, 8.3**
        
        对于任意满足以下条件的输入：
        - news_id 非空
        - importance_score 在 1-10 范围内
        - sentiment 为有效值之一
        
        则 WeightedNews 对象应该被成功创建，不抛出异常
        """
        # 创建新闻对象不应抛出异常
        news = WeightedNews(
            news_id=news_id,
            content=content,
            sentiment=sentiment,
            importance_score=importance_score,
            timestamp=datetime.now(),
            source=source
        )
        
        # 验证对象属性与输入一致
        assert news.news_id == news_id
        assert news.content == content
        assert news.sentiment == sentiment
        assert news.importance_score == importance_score
        assert news.source == source
        
        # 验证对象满足所有验证规则
        assert news.news_id.strip()  # news_id 非空
        assert 1 <= news.importance_score <= 10  # 评分在范围内
        assert news.sentiment in {"positive", "negative", "neutral"}  # 情绪有效
    
    @given(
        news_id=empty_or_whitespace_strings,
        content=st.text(),
        sentiment=valid_sentiments,
        importance_score=valid_scores
    )
    def test_property_empty_news_id_always_rejected(
        self, news_id, content, sentiment, importance_score
    ):
        """属性：空或仅空格的 news_id 总是被拒绝
        
        **Validates: Requirement 8.3**
        
        对于任意空字符串或仅包含空格的 news_id，
        WeightedNews 对象创建应该抛出 ValueError
        """
        with pytest.raises(ValueError, match="news_id 不能为空"):
            WeightedNews(
                news_id=news_id,
                content=content,
                sentiment=sentiment,
                importance_score=importance_score,
                timestamp=datetime.now()
            )
    
    @given(
        news_id=non_empty_strings,
        content=st.text(),
        sentiment=valid_sentiments,
        importance_score=invalid_scores_below
    )
    def test_property_score_below_range_always_rejected(
        self, news_id, content, sentiment, importance_score
    ):
        """属性：低于范围的 importance_score 总是被拒绝
        
        **Validates: Requirement 8.1**
        
        对于任意 importance_score <= 0，
        WeightedNews 对象创建应该抛出 ValueError
        """
        with pytest.raises(ValueError, match="importance_score 必须在 1-10 范围内"):
            WeightedNews(
                news_id=news_id,
                content=content,
                sentiment=sentiment,
                importance_score=importance_score,
                timestamp=datetime.now()
            )
    
    @given(
        news_id=non_empty_strings,
        content=st.text(),
        sentiment=valid_sentiments,
        importance_score=invalid_scores_above
    )
    def test_property_score_above_range_always_rejected(
        self, news_id, content, sentiment, importance_score
    ):
        """属性：高于范围的 importance_score 总是被拒绝
        
        **Validates: Requirement 8.1**
        
        对于任意 importance_score >= 11，
        WeightedNews 对象创建应该抛出 ValueError
        """
        with pytest.raises(ValueError, match="importance_score 必须在 1-10 范围内"):
            WeightedNews(
                news_id=news_id,
                content=content,
                sentiment=sentiment,
                importance_score=importance_score,
                timestamp=datetime.now()
            )
    
    @given(
        news_id=non_empty_strings,
        content=st.text(),
        sentiment=st.text().filter(lambda s: s not in {"positive", "negative", "neutral"}),
        importance_score=valid_scores
    )
    def test_property_invalid_sentiment_always_rejected(
        self, news_id, content, sentiment, importance_score
    ):
        """属性：无效的 sentiment 值总是被拒绝
        
        **Validates: Requirement 8.2**
        
        对于任意不在 {"positive", "negative", "neutral"} 中的 sentiment 值，
        WeightedNews 对象创建应该抛出 ValueError
        """
        # 确保 sentiment 确实不是有效值
        assume(sentiment not in {"positive", "negative", "neutral"})
        
        with pytest.raises(ValueError, match="sentiment 必须是"):
            WeightedNews(
                news_id=news_id,
                content=content,
                sentiment=sentiment,
                importance_score=importance_score,
                timestamp=datetime.now()
            )
    
    @given(
        news_id=non_empty_strings,
        content=st.text(),
        sentiment=valid_sentiments,
        importance_score=st.floats(min_value=1.0, max_value=10.0).filter(
            lambda x: not x.is_integer()
        )
    )
    def test_property_non_integer_score_always_rejected(
        self, news_id, content, sentiment, importance_score
    ):
        """属性：非整数的 importance_score 总是被拒绝
        
        **Validates: Requirement 8.1**
        
        对于任意浮点数（非整数）的 importance_score，
        WeightedNews 对象创建应该抛出 ValueError
        """
        with pytest.raises(ValueError, match="importance_score 必须是整数"):
            WeightedNews(
                news_id=news_id,
                content=content,
                sentiment=sentiment,
                importance_score=importance_score,
                timestamp=datetime.now()
            )
    
    @given(
        news_id=non_empty_strings,
        content=st.text(),
        sentiment=valid_sentiments,
        importance_score=valid_scores
    )
    def test_property_validate_method_idempotent(
        self, news_id, content, sentiment, importance_score
    ):
        """属性：validate() 方法是幂等的
        
        **Validates: Requirements 8.1, 8.2, 8.3**
        
        对于任意有效的 WeightedNews 对象，
        多次调用 validate() 方法应该产生相同的结果（不抛出异常）
        """
        news = WeightedNews(
            news_id=news_id,
            content=content,
            sentiment=sentiment,
            importance_score=importance_score,
            timestamp=datetime.now()
        )
        
        # 多次调用 validate() 不应抛出异常
        news.validate()
        news.validate()
        news.validate()
        
        # 对象状态不应改变
        assert news.news_id == news_id
        assert news.importance_score == importance_score
        assert news.sentiment == sentiment
    
    @given(
        news_id=non_empty_strings,
        content=st.text(),
        importance_score=valid_scores
    )
    def test_property_all_sentiments_equally_valid(
        self, news_id, content, importance_score
    ):
        """属性：所有有效的 sentiment 值都应该被平等接受
        
        **Validates: Requirement 8.2**
        
        对于任意有效的输入，三种 sentiment 值（positive, negative, neutral）
        都应该被成功接受，没有偏好
        """
        valid_sentiments_list = ["positive", "negative", "neutral"]
        
        for sentiment in valid_sentiments_list:
            news = WeightedNews(
                news_id=news_id,
                content=content,
                sentiment=sentiment,
                importance_score=importance_score,
                timestamp=datetime.now()
            )
            assert news.sentiment == sentiment
    
    @given(
        news_id=non_empty_strings,
        content=st.text(),
        sentiment=valid_sentiments
    )
    def test_property_boundary_scores_always_valid(
        self, news_id, content, sentiment
    ):
        """属性：边界值（1 和 10）总是有效的
        
        **Validates: Requirement 8.1**
        
        对于任意有效的输入，importance_score 的边界值 1 和 10
        都应该被成功接受
        """
        # 测试最小边界值 1
        news_min = WeightedNews(
            news_id=news_id,
            content=content,
            sentiment=sentiment,
            importance_score=1,
            timestamp=datetime.now()
        )
        assert news_min.importance_score == 1
        
        # 测试最大边界值 10
        news_max = WeightedNews(
            news_id=news_id + "_max",  # 确保不同的 news_id
            content=content,
            sentiment=sentiment,
            importance_score=10,
            timestamp=datetime.now()
        )
        assert news_max.importance_score == 10
    
    @given(
        news_id=non_empty_strings,
        content=st.text(),
        sentiment=valid_sentiments,
        importance_score=valid_scores,
        timestamp_offset_hours=st.integers(min_value=-1000, max_value=1000)
    )
    def test_property_timestamp_preserved(
        self, news_id, content, sentiment, importance_score, timestamp_offset_hours
    ):
        """属性：timestamp 值应该被正确保存
        
        **Validates: Requirements 8.1, 8.2, 8.3**
        
        对于任意有效的输入和任意 timestamp，
        创建的 WeightedNews 对象应该保留原始的 timestamp 值
        """
        timestamp = datetime.now() + timedelta(hours=timestamp_offset_hours)
        
        news = WeightedNews(
            news_id=news_id,
            content=content,
            sentiment=sentiment,
            importance_score=importance_score,
            timestamp=timestamp
        )
        
        assert news.timestamp == timestamp


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])

