#!/usr/bin/env python3
"""
单元测试：WeightedNews 数据类
Unit tests for WeightedNews dataclass
"""

import pytest
from datetime import datetime
from weighted_sentiment_models import WeightedNews


class TestWeightedNewsValidation:
    """测试 WeightedNews 数据验证"""
    
    def test_valid_news_creation(self):
        """测试创建有效的新闻对象"""
        news = WeightedNews(
            news_id="news_001",
            content="Bitcoin reaches new high",
            sentiment="positive",
            importance_score=8,
            timestamp=datetime.now(),
            source="CoinDesk"
        )
        assert news.news_id == "news_001"
        assert news.sentiment == "positive"
        assert news.importance_score == 8
    
    def test_valid_news_without_source(self):
        """测试创建没有来源的有效新闻对象"""
        news = WeightedNews(
            news_id="news_002",
            content="Market update",
            sentiment="neutral",
            importance_score=5,
            timestamp=datetime.now()
        )
        assert news.source is None
    
    def test_empty_news_id_raises_error(self):
        """测试空 news_id 抛出错误"""
        with pytest.raises(ValueError, match="news_id 不能为空"):
            WeightedNews(
                news_id="",
                content="Test content",
                sentiment="positive",
                importance_score=5,
                timestamp=datetime.now()
            )
    
    def test_whitespace_news_id_raises_error(self):
        """测试仅包含空格的 news_id 抛出错误"""
        with pytest.raises(ValueError, match="news_id 不能为空"):
            WeightedNews(
                news_id="   ",
                content="Test content",
                sentiment="positive",
                importance_score=5,
                timestamp=datetime.now()
            )
    
    def test_importance_score_below_range_raises_error(self):
        """测试 importance_score 低于范围抛出错误"""
        with pytest.raises(ValueError, match="importance_score 必须在 1-10 范围内"):
            WeightedNews(
                news_id="news_003",
                content="Test content",
                sentiment="positive",
                importance_score=0,
                timestamp=datetime.now()
            )
    
    def test_importance_score_above_range_raises_error(self):
        """测试 importance_score 高于范围抛出错误"""
        with pytest.raises(ValueError, match="importance_score 必须在 1-10 范围内"):
            WeightedNews(
                news_id="news_004",
                content="Test content",
                sentiment="positive",
                importance_score=11,
                timestamp=datetime.now()
            )
    
    def test_importance_score_boundary_values(self):
        """测试 importance_score 边界值（1 和 10）"""
        # 测试最小值
        news_min = WeightedNews(
            news_id="news_005",
            content="Test content",
            sentiment="positive",
            importance_score=1,
            timestamp=datetime.now()
        )
        assert news_min.importance_score == 1
        
        # 测试最大值
        news_max = WeightedNews(
            news_id="news_006",
            content="Test content",
            sentiment="positive",
            importance_score=10,
            timestamp=datetime.now()
        )
        assert news_max.importance_score == 10
    
    def test_invalid_sentiment_raises_error(self):
        """测试无效的 sentiment 值抛出错误"""
        with pytest.raises(ValueError, match="sentiment 必须是"):
            WeightedNews(
                news_id="news_007",
                content="Test content",
                sentiment="bullish",  # 无效值
                importance_score=5,
                timestamp=datetime.now()
            )
    
    def test_all_valid_sentiments(self):
        """测试所有有效的 sentiment 值"""
        valid_sentiments = ["positive", "negative", "neutral"]
        
        for sentiment in valid_sentiments:
            news = WeightedNews(
                news_id=f"news_{sentiment}",
                content="Test content",
                sentiment=sentiment,
                importance_score=5,
                timestamp=datetime.now()
            )
            assert news.sentiment == sentiment
    
    def test_importance_score_non_integer_raises_error(self):
        """测试非整数的 importance_score 抛出错误"""
        with pytest.raises(ValueError, match="importance_score 必须是整数"):
            WeightedNews(
                news_id="news_008",
                content="Test content",
                sentiment="positive",
                importance_score=5.5,  # 浮点数
                timestamp=datetime.now()
            )
    
    def test_validate_method_can_be_called_explicitly(self):
        """测试可以显式调用 validate 方法"""
        news = WeightedNews(
            news_id="news_009",
            content="Test content",
            sentiment="positive",
            importance_score=7,
            timestamp=datetime.now()
        )
        # 不应抛出异常
        news.validate()
    
    def test_high_score_news_threshold(self):
        """测试高分新闻阈值（评分 >= 7）"""
        # 评分 6 - 不是高分新闻
        news_6 = WeightedNews(
            news_id="news_010",
            content="Test content",
            sentiment="positive",
            importance_score=6,
            timestamp=datetime.now()
        )
        assert news_6.importance_score < 7
        
        # 评分 7 - 是高分新闻
        news_7 = WeightedNews(
            news_id="news_011",
            content="Test content",
            sentiment="positive",
            importance_score=7,
            timestamp=datetime.now()
        )
        assert news_7.importance_score >= 7
        
        # 评分 8 - 是高分新闻
        news_8 = WeightedNews(
            news_id="news_012",
            content="Test content",
            sentiment="positive",
            importance_score=8,
            timestamp=datetime.now()
        )
        assert news_8.importance_score >= 7


if __name__ == "__main__":
    pytest.main([__file__, "-v"])



class TestOptionTradeValidation:
    """测试 OptionTrade 数据验证"""
    
    def test_valid_call_option_creation(self):
        """测试创建有效的看涨期权对象"""
        from weighted_sentiment_models import OptionTrade
        from datetime import timedelta
        
        future_date = datetime.now() + timedelta(days=7)
        option = OptionTrade(
            instrument_name="BTC-31DEC23-40000-C",
            option_type="call",
            strike_price=40000.0,
            expiry_date=future_date,
            premium=500.0,
            quantity=0.1,
            order_id="order_123"
        )
        assert option.option_type == "call"
        assert option.strike_price == 40000.0
        assert option.premium == 500.0
        assert option.quantity == 0.1
    
    def test_valid_put_option_creation(self):
        """测试创建有效的看跌期权对象"""
        from weighted_sentiment_models import OptionTrade
        from datetime import timedelta
        
        future_date = datetime.now() + timedelta(days=7)
        option = OptionTrade(
            instrument_name="BTC-31DEC23-40000-P",
            option_type="put",
            strike_price=40000.0,
            expiry_date=future_date,
            premium=500.0,
            quantity=0.1
        )
        assert option.option_type == "put"
        assert option.order_id is None
    
    def test_invalid_option_type_raises_error(self):
        """测试无效的 option_type 抛出错误"""
        from weighted_sentiment_models import OptionTrade
        from datetime import timedelta
        
        future_date = datetime.now() + timedelta(days=7)
        with pytest.raises(ValueError, match="option_type 必须是"):
            OptionTrade(
                instrument_name="BTC-31DEC23-40000-C",
                option_type="invalid",
                strike_price=40000.0,
                expiry_date=future_date,
                premium=500.0,
                quantity=0.1
            )
    
    def test_negative_strike_price_raises_error(self):
        """测试负数 strike_price 抛出错误"""
        from weighted_sentiment_models import OptionTrade
        from datetime import timedelta
        
        future_date = datetime.now() + timedelta(days=7)
        with pytest.raises(ValueError, match="strike_price 必须为正数"):
            OptionTrade(
                instrument_name="BTC-31DEC23-40000-C",
                option_type="call",
                strike_price=-40000.0,
                expiry_date=future_date,
                premium=500.0,
                quantity=0.1
            )
    
    def test_zero_strike_price_raises_error(self):
        """测试零 strike_price 抛出错误"""
        from weighted_sentiment_models import OptionTrade
        from datetime import timedelta
        
        future_date = datetime.now() + timedelta(days=7)
        with pytest.raises(ValueError, match="strike_price 必须为正数"):
            OptionTrade(
                instrument_name="BTC-31DEC23-40000-C",
                option_type="call",
                strike_price=0,
                expiry_date=future_date,
                premium=500.0,
                quantity=0.1
            )
    
    def test_negative_premium_raises_error(self):
        """测试负数 premium 抛出错误"""
        from weighted_sentiment_models import OptionTrade
        from datetime import timedelta
        
        future_date = datetime.now() + timedelta(days=7)
        with pytest.raises(ValueError, match="premium 必须为正数"):
            OptionTrade(
                instrument_name="BTC-31DEC23-40000-C",
                option_type="call",
                strike_price=40000.0,
                expiry_date=future_date,
                premium=-500.0,
                quantity=0.1
            )
    
    def test_zero_premium_raises_error(self):
        """测试零 premium 抛出错误"""
        from weighted_sentiment_models import OptionTrade
        from datetime import timedelta
        
        future_date = datetime.now() + timedelta(days=7)
        with pytest.raises(ValueError, match="premium 必须为正数"):
            OptionTrade(
                instrument_name="BTC-31DEC23-40000-C",
                option_type="call",
                strike_price=40000.0,
                expiry_date=future_date,
                premium=0,
                quantity=0.1
            )
    
    def test_negative_quantity_raises_error(self):
        """测试负数 quantity 抛出错误"""
        from weighted_sentiment_models import OptionTrade
        from datetime import timedelta
        
        future_date = datetime.now() + timedelta(days=7)
        with pytest.raises(ValueError, match="quantity 必须为正数"):
            OptionTrade(
                instrument_name="BTC-31DEC23-40000-C",
                option_type="call",
                strike_price=40000.0,
                expiry_date=future_date,
                premium=500.0,
                quantity=-0.1
            )
    
    def test_zero_quantity_raises_error(self):
        """测试零 quantity 抛出错误"""
        from weighted_sentiment_models import OptionTrade
        from datetime import timedelta
        
        future_date = datetime.now() + timedelta(days=7)
        with pytest.raises(ValueError, match="quantity 必须为正数"):
            OptionTrade(
                instrument_name="BTC-31DEC23-40000-C",
                option_type="call",
                strike_price=40000.0,
                expiry_date=future_date,
                premium=500.0,
                quantity=0
            )
    
    def test_past_expiry_date_raises_error(self):
        """测试过去的 expiry_date 抛出错误"""
        from weighted_sentiment_models import OptionTrade
        from datetime import timedelta
        
        past_date = datetime.now() - timedelta(days=1)
        with pytest.raises(ValueError, match="expiry_date 必须在未来"):
            OptionTrade(
                instrument_name="BTC-31DEC23-40000-C",
                option_type="call",
                strike_price=40000.0,
                expiry_date=past_date,
                premium=500.0,
                quantity=0.1
            )
    
    def test_current_time_expiry_date_raises_error(self):
        """测试当前时间的 expiry_date 抛出错误"""
        from weighted_sentiment_models import OptionTrade
        
        # 使用当前时间（应该失败，因为必须在未来）
        current_time = datetime.now()
        with pytest.raises(ValueError, match="expiry_date 必须在未来"):
            OptionTrade(
                instrument_name="BTC-31DEC23-40000-C",
                option_type="call",
                strike_price=40000.0,
                expiry_date=current_time,
                premium=500.0,
                quantity=0.1
            )
    
    def test_non_numeric_strike_price_raises_error(self):
        """测试非数字的 strike_price 抛出错误"""
        from weighted_sentiment_models import OptionTrade
        from datetime import timedelta
        
        future_date = datetime.now() + timedelta(days=7)
        with pytest.raises(ValueError, match="strike_price 必须是数字"):
            OptionTrade(
                instrument_name="BTC-31DEC23-40000-C",
                option_type="call",
                strike_price="40000",  # 字符串
                expiry_date=future_date,
                premium=500.0,
                quantity=0.1
            )
    
    def test_non_numeric_premium_raises_error(self):
        """测试非数字的 premium 抛出错误"""
        from weighted_sentiment_models import OptionTrade
        from datetime import timedelta
        
        future_date = datetime.now() + timedelta(days=7)
        with pytest.raises(ValueError, match="premium 必须是数字"):
            OptionTrade(
                instrument_name="BTC-31DEC23-40000-C",
                option_type="call",
                strike_price=40000.0,
                expiry_date=future_date,
                premium="500",  # 字符串
                quantity=0.1
            )
    
    def test_non_numeric_quantity_raises_error(self):
        """测试非数字的 quantity 抛出错误"""
        from weighted_sentiment_models import OptionTrade
        from datetime import timedelta
        
        future_date = datetime.now() + timedelta(days=7)
        with pytest.raises(ValueError, match="quantity 必须是数字"):
            OptionTrade(
                instrument_name="BTC-31DEC23-40000-C",
                option_type="call",
                strike_price=40000.0,
                expiry_date=future_date,
                premium=500.0,
                quantity="0.1"  # 字符串
            )
    
    def test_non_datetime_expiry_date_raises_error(self):
        """测试非 datetime 的 expiry_date 抛出错误"""
        from weighted_sentiment_models import OptionTrade
        
        with pytest.raises(ValueError, match="expiry_date 必须是 datetime 对象"):
            OptionTrade(
                instrument_name="BTC-31DEC23-40000-C",
                option_type="call",
                strike_price=40000.0,
                expiry_date="2023-12-31",  # 字符串
                premium=500.0,
                quantity=0.1
            )
    
    def test_validate_method_can_be_called_explicitly(self):
        """测试可以显式调用 validate 方法"""
        from weighted_sentiment_models import OptionTrade
        from datetime import timedelta
        
        future_date = datetime.now() + timedelta(days=7)
        option = OptionTrade(
            instrument_name="BTC-31DEC23-40000-C",
            option_type="call",
            strike_price=40000.0,
            expiry_date=future_date,
            premium=500.0,
            quantity=0.1
        )
        # 不应抛出异常
        option.validate()
    
    def test_integer_values_accepted_for_numeric_fields(self):
        """测试数字字段接受整数值"""
        from weighted_sentiment_models import OptionTrade
        from datetime import timedelta
        
        future_date = datetime.now() + timedelta(days=7)
        option = OptionTrade(
            instrument_name="BTC-31DEC23-40000-C",
            option_type="call",
            strike_price=40000,  # 整数
            expiry_date=future_date,
            premium=500,  # 整数
            quantity=1  # 整数
        )
        assert option.strike_price == 40000
        assert option.premium == 500
        assert option.quantity == 1
    
    def test_small_positive_values_accepted(self):
        """测试接受小的正数值"""
        from weighted_sentiment_models import OptionTrade
        from datetime import timedelta
        
        future_date = datetime.now() + timedelta(days=7)
        option = OptionTrade(
            instrument_name="BTC-31DEC23-40000-C",
            option_type="call",
            strike_price=0.01,
            expiry_date=future_date,
            premium=0.01,
            quantity=0.01
        )
        assert option.strike_price == 0.01
        assert option.premium == 0.01
        assert option.quantity == 0.01
    
    def test_both_option_types_valid(self):
        """测试两种期权类型都有效"""
        from weighted_sentiment_models import OptionTrade
        from datetime import timedelta
        
        future_date = datetime.now() + timedelta(days=7)
        
        # 测试 call
        call_option = OptionTrade(
            instrument_name="BTC-31DEC23-40000-C",
            option_type="call",
            strike_price=40000.0,
            expiry_date=future_date,
            premium=500.0,
            quantity=0.1
        )
        assert call_option.option_type == "call"
        
        # 测试 put
        put_option = OptionTrade(
            instrument_name="BTC-31DEC23-40000-P",
            option_type="put",
            strike_price=40000.0,
            expiry_date=future_date,
            premium=500.0,
            quantity=0.1
        )
        assert put_option.option_type == "put"



class TestStraddleTradeResultValidation:
    """测试 StraddleTradeResult 数据验证"""
    
    def test_valid_successful_straddle_result(self):
        """测试创建有效的成功跨式交易结果"""
        from weighted_sentiment_models import StraddleTradeResult, OptionTrade
        from datetime import timedelta
        
        future_date = datetime.now() + timedelta(days=7)
        call_option = OptionTrade(
            instrument_name="BTC-31DEC23-40000-C",
            option_type="call",
            strike_price=40000.0,
            expiry_date=future_date,
            premium=500.0,
            quantity=0.1
        )
        put_option = OptionTrade(
            instrument_name="BTC-31DEC23-40000-P",
            option_type="put",
            strike_price=40000.0,
            expiry_date=future_date,
            premium=480.0,
            quantity=0.1
        )
        
        result = StraddleTradeResult(
            success=True,
            news_id="news_001",
            trade_time=datetime.now(),
            spot_price=40000.0,
            call_option=call_option,
            put_option=put_option,
            total_cost=980.0
        )
        
        assert result.success is True
        assert result.news_id == "news_001"
        assert result.total_cost == 980.0
        assert result.call_option is not None
        assert result.put_option is not None
    
    def test_valid_failed_straddle_result(self):
        """测试创建有效的失败跨式交易结果"""
        from weighted_sentiment_models import StraddleTradeResult
        
        result = StraddleTradeResult(
            success=False,
            news_id="news_002",
            trade_time=datetime.now(),
            spot_price=40000.0,
            call_option=None,
            put_option=None,
            total_cost=0.0,
            error_message="Failed to find suitable options"
        )
        
        assert result.success is False
        assert result.error_message == "Failed to find suitable options"
    
    def test_successful_result_without_call_option_raises_error(self):
        """测试成功结果缺少 call_option 抛出错误"""
        from weighted_sentiment_models import StraddleTradeResult, OptionTrade
        from datetime import timedelta
        
        future_date = datetime.now() + timedelta(days=7)
        put_option = OptionTrade(
            instrument_name="BTC-31DEC23-40000-P",
            option_type="put",
            strike_price=40000.0,
            expiry_date=future_date,
            premium=480.0,
            quantity=0.1
        )
        
        with pytest.raises(ValueError, match="成功的交易必须包含 call_option"):
            StraddleTradeResult(
                success=True,
                news_id="news_003",
                trade_time=datetime.now(),
                spot_price=40000.0,
                call_option=None,
                put_option=put_option,
                total_cost=480.0
            )
    
    def test_successful_result_without_put_option_raises_error(self):
        """测试成功结果缺少 put_option 抛出错误"""
        from weighted_sentiment_models import StraddleTradeResult, OptionTrade
        from datetime import timedelta
        
        future_date = datetime.now() + timedelta(days=7)
        call_option = OptionTrade(
            instrument_name="BTC-31DEC23-40000-C",
            option_type="call",
            strike_price=40000.0,
            expiry_date=future_date,
            premium=500.0,
            quantity=0.1
        )
        
        with pytest.raises(ValueError, match="成功的交易必须包含 put_option"):
            StraddleTradeResult(
                success=True,
                news_id="news_004",
                trade_time=datetime.now(),
                spot_price=40000.0,
                call_option=call_option,
                put_option=None,
                total_cost=500.0
            )
    
    def test_failed_result_without_error_message_raises_error(self):
        """测试失败结果缺少 error_message 抛出错误"""
        from weighted_sentiment_models import StraddleTradeResult
        
        with pytest.raises(ValueError, match="失败的交易必须提供 error_message"):
            StraddleTradeResult(
                success=False,
                news_id="news_005",
                trade_time=datetime.now(),
                spot_price=40000.0,
                call_option=None,
                put_option=None,
                total_cost=0.0,
                error_message=None
            )
    
    def test_negative_total_cost_raises_error(self):
        """测试负数 total_cost 抛出错误"""
        from weighted_sentiment_models import StraddleTradeResult, OptionTrade
        from datetime import timedelta
        
        future_date = datetime.now() + timedelta(days=7)
        call_option = OptionTrade(
            instrument_name="BTC-31DEC23-40000-C",
            option_type="call",
            strike_price=40000.0,
            expiry_date=future_date,
            premium=500.0,
            quantity=0.1
        )
        put_option = OptionTrade(
            instrument_name="BTC-31DEC23-40000-P",
            option_type="put",
            strike_price=40000.0,
            expiry_date=future_date,
            premium=480.0,
            quantity=0.1
        )
        
        with pytest.raises(ValueError, match="total_cost 必须为正数"):
            StraddleTradeResult(
                success=True,
                news_id="news_006",
                trade_time=datetime.now(),
                spot_price=40000.0,
                call_option=call_option,
                put_option=put_option,
                total_cost=-980.0
            )
    
    def test_zero_total_cost_raises_error(self):
        """测试零 total_cost 抛出错误（成功交易时）"""
        from weighted_sentiment_models import StraddleTradeResult, OptionTrade
        from datetime import timedelta
        
        future_date = datetime.now() + timedelta(days=7)
        call_option = OptionTrade(
            instrument_name="BTC-31DEC23-40000-C",
            option_type="call",
            strike_price=40000.0,
            expiry_date=future_date,
            premium=500.0,
            quantity=0.1
        )
        put_option = OptionTrade(
            instrument_name="BTC-31DEC23-40000-P",
            option_type="put",
            strike_price=40000.0,
            expiry_date=future_date,
            premium=480.0,
            quantity=0.1
        )
        
        with pytest.raises(ValueError, match="total_cost 必须为正数"):
            StraddleTradeResult(
                success=True,
                news_id="news_007",
                trade_time=datetime.now(),
                spot_price=40000.0,
                call_option=call_option,
                put_option=put_option,
                total_cost=0.0
            )
    
    def test_negative_spot_price_raises_error(self):
        """测试负数 spot_price 抛出错误"""
        from weighted_sentiment_models import StraddleTradeResult
        
        with pytest.raises(ValueError, match="spot_price 必须为正数"):
            StraddleTradeResult(
                success=False,
                news_id="news_008",
                trade_time=datetime.now(),
                spot_price=-40000.0,
                call_option=None,
                put_option=None,
                total_cost=0.0,
                error_message="Test error"
            )
    
    def test_zero_spot_price_raises_error(self):
        """测试零 spot_price 抛出错误"""
        from weighted_sentiment_models import StraddleTradeResult
        
        with pytest.raises(ValueError, match="spot_price 必须为正数"):
            StraddleTradeResult(
                success=False,
                news_id="news_009",
                trade_time=datetime.now(),
                spot_price=0.0,
                call_option=None,
                put_option=None,
                total_cost=0.0,
                error_message="Test error"
            )
    
    def test_validate_method_can_be_called_explicitly(self):
        """测试可以显式调用 validate 方法"""
        from weighted_sentiment_models import StraddleTradeResult
        
        result = StraddleTradeResult(
            success=False,
            news_id="news_010",
            trade_time=datetime.now(),
            spot_price=40000.0,
            call_option=None,
            put_option=None,
            total_cost=0.0,
            error_message="Test error"
        )
        # 不应抛出异常
        result.validate()


class TestTradeRecordValidation:
    """测试 TradeRecord 数据验证"""
    
    def test_valid_successful_trade_record(self):
        """测试创建有效的成功交易记录"""
        from weighted_sentiment_models import TradeRecord
        
        record = TradeRecord(
            id=1,
            news_id="news_001",
            news_content="Bitcoin reaches new high",
            sentiment="positive",
            importance_score=8,
            trade_time=datetime.now(),
            spot_price=40000.0,
            call_instrument="BTC-31DEC23-40000-C",
            call_strike=40000.0,
            call_premium=500.0,
            put_instrument="BTC-31DEC23-40000-P",
            put_strike=40000.0,
            put_premium=480.0,
            total_cost=980.0,
            success=True
        )
        
        assert record.id == 1
        assert record.news_id == "news_001"
        assert record.importance_score == 8
        assert record.success is True
    
    def test_valid_failed_trade_record(self):
        """测试创建有效的失败交易记录"""
        from weighted_sentiment_models import TradeRecord
        
        record = TradeRecord(
            id=2,
            news_id="news_002",
            news_content="Market update",
            sentiment="neutral",
            importance_score=7,
            trade_time=datetime.now(),
            spot_price=40000.0,
            call_instrument="",
            call_strike=0.0,
            call_premium=0.0,
            put_instrument="",
            put_strike=0.0,
            put_premium=0.0,
            total_cost=0.0,
            success=False,
            error_message="Failed to find suitable options"
        )
        
        assert record.success is False
        assert record.error_message == "Failed to find suitable options"
    
    def test_importance_score_below_range_raises_error(self):
        """测试 importance_score 低于范围抛出错误"""
        from weighted_sentiment_models import TradeRecord
        
        with pytest.raises(ValueError, match="importance_score 必须在 1-10 范围内"):
            TradeRecord(
                id=3,
                news_id="news_003",
                news_content="Test content",
                sentiment="positive",
                importance_score=0,
                trade_time=datetime.now(),
                spot_price=40000.0,
                call_instrument="BTC-31DEC23-40000-C",
                call_strike=40000.0,
                call_premium=500.0,
                put_instrument="BTC-31DEC23-40000-P",
                put_strike=40000.0,
                put_premium=480.0,
                total_cost=980.0,
                success=True
            )
    
    def test_importance_score_above_range_raises_error(self):
        """测试 importance_score 高于范围抛出错误"""
        from weighted_sentiment_models import TradeRecord
        
        with pytest.raises(ValueError, match="importance_score 必须在 1-10 范围内"):
            TradeRecord(
                id=4,
                news_id="news_004",
                news_content="Test content",
                sentiment="positive",
                importance_score=11,
                trade_time=datetime.now(),
                spot_price=40000.0,
                call_instrument="BTC-31DEC23-40000-C",
                call_strike=40000.0,
                call_premium=500.0,
                put_instrument="BTC-31DEC23-40000-P",
                put_strike=40000.0,
                put_premium=480.0,
                total_cost=980.0,
                success=True
            )
    
    def test_invalid_sentiment_raises_error(self):
        """测试无效的 sentiment 值抛出错误"""
        from weighted_sentiment_models import TradeRecord
        
        with pytest.raises(ValueError, match="sentiment 必须是"):
            TradeRecord(
                id=5,
                news_id="news_005",
                news_content="Test content",
                sentiment="bullish",
                importance_score=8,
                trade_time=datetime.now(),
                spot_price=40000.0,
                call_instrument="BTC-31DEC23-40000-C",
                call_strike=40000.0,
                call_premium=500.0,
                put_instrument="BTC-31DEC23-40000-P",
                put_strike=40000.0,
                put_premium=480.0,
                total_cost=980.0,
                success=True
            )
    
    def test_negative_spot_price_raises_error(self):
        """测试负数 spot_price 抛出错误"""
        from weighted_sentiment_models import TradeRecord
        
        with pytest.raises(ValueError, match="spot_price 必须为正数"):
            TradeRecord(
                id=6,
                news_id="news_006",
                news_content="Test content",
                sentiment="positive",
                importance_score=8,
                trade_time=datetime.now(),
                spot_price=-40000.0,
                call_instrument="BTC-31DEC23-40000-C",
                call_strike=40000.0,
                call_premium=500.0,
                put_instrument="BTC-31DEC23-40000-P",
                put_strike=40000.0,
                put_premium=480.0,
                total_cost=980.0,
                success=True
            )
    
    def test_negative_call_strike_raises_error(self):
        """测试负数 call_strike 抛出错误（成功交易时）"""
        from weighted_sentiment_models import TradeRecord
        
        with pytest.raises(ValueError, match="call_strike 必须为正数"):
            TradeRecord(
                id=7,
                news_id="news_007",
                news_content="Test content",
                sentiment="positive",
                importance_score=8,
                trade_time=datetime.now(),
                spot_price=40000.0,
                call_instrument="BTC-31DEC23-40000-C",
                call_strike=-40000.0,
                call_premium=500.0,
                put_instrument="BTC-31DEC23-40000-P",
                put_strike=40000.0,
                put_premium=480.0,
                total_cost=980.0,
                success=True
            )
    
    def test_negative_call_premium_raises_error(self):
        """测试负数 call_premium 抛出错误（成功交易时）"""
        from weighted_sentiment_models import TradeRecord
        
        with pytest.raises(ValueError, match="call_premium 必须为正数"):
            TradeRecord(
                id=8,
                news_id="news_008",
                news_content="Test content",
                sentiment="positive",
                importance_score=8,
                trade_time=datetime.now(),
                spot_price=40000.0,
                call_instrument="BTC-31DEC23-40000-C",
                call_strike=40000.0,
                call_premium=-500.0,
                put_instrument="BTC-31DEC23-40000-P",
                put_strike=40000.0,
                put_premium=480.0,
                total_cost=980.0,
                success=True
            )
    
    def test_negative_put_strike_raises_error(self):
        """测试负数 put_strike 抛出错误（成功交易时）"""
        from weighted_sentiment_models import TradeRecord
        
        with pytest.raises(ValueError, match="put_strike 必须为正数"):
            TradeRecord(
                id=9,
                news_id="news_009",
                news_content="Test content",
                sentiment="positive",
                importance_score=8,
                trade_time=datetime.now(),
                spot_price=40000.0,
                call_instrument="BTC-31DEC23-40000-C",
                call_strike=40000.0,
                call_premium=500.0,
                put_instrument="BTC-31DEC23-40000-P",
                put_strike=-40000.0,
                put_premium=480.0,
                total_cost=980.0,
                success=True
            )
    
    def test_negative_put_premium_raises_error(self):
        """测试负数 put_premium 抛出错误（成功交易时）"""
        from weighted_sentiment_models import TradeRecord
        
        with pytest.raises(ValueError, match="put_premium 必须为正数"):
            TradeRecord(
                id=10,
                news_id="news_010",
                news_content="Test content",
                sentiment="positive",
                importance_score=8,
                trade_time=datetime.now(),
                spot_price=40000.0,
                call_instrument="BTC-31DEC23-40000-C",
                call_strike=40000.0,
                call_premium=500.0,
                put_instrument="BTC-31DEC23-40000-P",
                put_strike=40000.0,
                put_premium=-480.0,
                total_cost=980.0,
                success=True
            )
    
    def test_negative_total_cost_raises_error(self):
        """测试负数 total_cost 抛出错误（成功交易时）"""
        from weighted_sentiment_models import TradeRecord
        
        with pytest.raises(ValueError, match="total_cost 必须为正数"):
            TradeRecord(
                id=11,
                news_id="news_011",
                news_content="Test content",
                sentiment="positive",
                importance_score=8,
                trade_time=datetime.now(),
                spot_price=40000.0,
                call_instrument="BTC-31DEC23-40000-C",
                call_strike=40000.0,
                call_premium=500.0,
                put_instrument="BTC-31DEC23-40000-P",
                put_strike=40000.0,
                put_premium=480.0,
                total_cost=-980.0,
                success=True
            )
    
    def test_all_valid_sentiments(self):
        """测试所有有效的 sentiment 值"""
        from weighted_sentiment_models import TradeRecord
        
        valid_sentiments = ["positive", "negative", "neutral"]
        
        for sentiment in valid_sentiments:
            record = TradeRecord(
                id=12,
                news_id=f"news_{sentiment}",
                news_content="Test content",
                sentiment=sentiment,
                importance_score=8,
                trade_time=datetime.now(),
                spot_price=40000.0,
                call_instrument="BTC-31DEC23-40000-C",
                call_strike=40000.0,
                call_premium=500.0,
                put_instrument="BTC-31DEC23-40000-P",
                put_strike=40000.0,
                put_premium=480.0,
                total_cost=980.0,
                success=True
            )
            assert record.sentiment == sentiment
    
    def test_validate_method_can_be_called_explicitly(self):
        """测试可以显式调用 validate 方法"""
        from weighted_sentiment_models import TradeRecord
        
        record = TradeRecord(
            id=13,
            news_id="news_013",
            news_content="Test content",
            sentiment="positive",
            importance_score=8,
            trade_time=datetime.now(),
            spot_price=40000.0,
            call_instrument="BTC-31DEC23-40000-C",
            call_strike=40000.0,
            call_premium=500.0,
            put_instrument="BTC-31DEC23-40000-P",
            put_strike=40000.0,
            put_premium=480.0,
            total_cost=980.0,
            success=True
        )
        # 不应抛出异常
        record.validate()
    
    def test_failed_trade_allows_zero_prices(self):
        """测试失败的交易允许零价格"""
        from weighted_sentiment_models import TradeRecord
        
        # 失败的交易不验证价格字段
        record = TradeRecord(
            id=14,
            news_id="news_014",
            news_content="Test content",
            sentiment="positive",
            importance_score=8,
            trade_time=datetime.now(),
            spot_price=40000.0,
            call_instrument="",
            call_strike=0.0,
            call_premium=0.0,
            put_instrument="",
            put_strike=0.0,
            put_premium=0.0,
            total_cost=0.0,
            success=False,
            error_message="Test error"
        )
        assert record.success is False
