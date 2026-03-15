#!/usr/bin/env python3
"""
属性测试：OptionTrade 数据验证
Property-based tests for OptionTrade data validation using hypothesis

**Validates: Requirements 8.4, 8.5**
"""

import pytest
from datetime import datetime, timedelta
from hypothesis import given, strategies as st, assume
from weighted_sentiment_models import OptionTrade


# 定义有效的 option_type 策略
valid_option_types = st.sampled_from(["call", "put"])

# 定义有效的正数策略
positive_floats = st.floats(min_value=0.01, max_value=1e6, allow_nan=False, allow_infinity=False)
positive_integers = st.integers(min_value=1, max_value=1000000)

# 定义无效的非正数策略
non_positive_floats = st.floats(max_value=0.0, allow_nan=False, allow_infinity=False)
zero_value = st.just(0.0)
negative_floats = st.floats(max_value=-0.01, allow_nan=False, allow_infinity=False)

# 定义未来时间策略（1小时到1年后）
future_datetimes = st.datetimes(
    min_value=datetime.now() + timedelta(hours=1),
    max_value=datetime.now() + timedelta(days=365)
)

# 定义过去时间策略
past_datetimes = st.datetimes(
    min_value=datetime(2020, 1, 1),
    max_value=datetime.now() - timedelta(seconds=1)
)

# 定义非空字符串策略
non_empty_strings = st.text(min_size=1).filter(lambda s: s.strip())


class TestOptionTradePropertyValidation:
    """属性测试：OptionTrade 数据验证
    
    **Validates: Requirements 8.4, 8.5**
    
    Property 7: Option Trade Validation
    对于任意 OptionTrade 对象，必须满足：
    - strike_price、premium、quantity 为正数
    - expiry_date 在未来
    - option_type 为 "call" 或 "put"
    """
    
    @given(
        instrument_name=non_empty_strings,
        option_type=valid_option_types,
        strike_price=positive_floats,
        premium=positive_floats,
        quantity=positive_floats,
        order_id=st.one_of(st.none(), st.text())
    )
    def test_property_valid_option_trade_always_accepted(
        self, instrument_name, option_type, strike_price, premium, quantity, order_id
    ):
        """属性：所有满足验证规则的期权交易对象都应该被成功创建
        
        **Validates: Requirements 8.4, 8.5**
        
        对于任意满足以下条件的输入：
        - option_type 为 "call" 或 "put"
        - strike_price、premium、quantity 为正数
        - expiry_date 在未来
        
        则 OptionTrade 对象应该被成功创建，不抛出异常
        """
        expiry_date = datetime.now() + timedelta(days=7)
        
        # 创建期权交易对象不应抛出异常
        trade = OptionTrade(
            instrument_name=instrument_name,
            option_type=option_type,
            strike_price=strike_price,
            expiry_date=expiry_date,
            premium=premium,
            quantity=quantity,
            order_id=order_id
        )
        
        # 验证对象属性与输入一致
        assert trade.instrument_name == instrument_name
        assert trade.option_type == option_type
        assert trade.strike_price == strike_price
        assert trade.premium == premium
        assert trade.quantity == quantity
        assert trade.order_id == order_id
        
        # 验证对象满足所有验证规则
        assert trade.option_type in {"call", "put"}
        assert trade.strike_price > 0
        assert trade.premium > 0
        assert trade.quantity > 0
        assert trade.expiry_date > datetime.now()
    
    @given(
        instrument_name=non_empty_strings,
        option_type=st.text().filter(lambda s: s not in {"call", "put"}),
        strike_price=positive_floats,
        premium=positive_floats,
        quantity=positive_floats
    )
    def test_property_invalid_option_type_always_rejected(
        self, instrument_name, option_type, strike_price, premium, quantity
    ):
        """属性：无效的 option_type 总是被拒绝
        
        **Validates: Requirement 8.4**
        
        对于任意不在 {"call", "put"} 中的 option_type 值，
        OptionTrade 对象创建应该抛出 ValueError
        """
        assume(option_type not in {"call", "put"})
        expiry_date = datetime.now() + timedelta(days=7)
        
        with pytest.raises(ValueError, match="option_type 必须是"):
            OptionTrade(
                instrument_name=instrument_name,
                option_type=option_type,
                strike_price=strike_price,
                expiry_date=expiry_date,
                premium=premium,
                quantity=quantity
            )
    
    @given(
        instrument_name=non_empty_strings,
        option_type=valid_option_types,
        strike_price=non_positive_floats,
        premium=positive_floats,
        quantity=positive_floats
    )
    def test_property_non_positive_strike_price_always_rejected(
        self, instrument_name, option_type, strike_price, premium, quantity
    ):
        """属性：非正数的 strike_price 总是被拒绝
        
        **Validates: Requirement 8.4**
        
        对于任意 strike_price <= 0，
        OptionTrade 对象创建应该抛出 ValueError
        """
        expiry_date = datetime.now() + timedelta(days=7)
        
        with pytest.raises(ValueError, match="strike_price 必须为正数"):
            OptionTrade(
                instrument_name=instrument_name,
                option_type=option_type,
                strike_price=strike_price,
                expiry_date=expiry_date,
                premium=premium,
                quantity=quantity
            )
    
    @given(
        instrument_name=non_empty_strings,
        option_type=valid_option_types,
        strike_price=positive_floats,
        premium=non_positive_floats,
        quantity=positive_floats
    )
    def test_property_non_positive_premium_always_rejected(
        self, instrument_name, option_type, strike_price, premium, quantity
    ):
        """属性：非正数的 premium 总是被拒绝
        
        **Validates: Requirement 8.4**
        
        对于任意 premium <= 0，
        OptionTrade 对象创建应该抛出 ValueError
        """
        expiry_date = datetime.now() + timedelta(days=7)
        
        with pytest.raises(ValueError, match="premium 必须为正数"):
            OptionTrade(
                instrument_name=instrument_name,
                option_type=option_type,
                strike_price=strike_price,
                expiry_date=expiry_date,
                premium=premium,
                quantity=quantity
            )
    
    @given(
        instrument_name=non_empty_strings,
        option_type=valid_option_types,
        strike_price=positive_floats,
        premium=positive_floats,
        quantity=non_positive_floats
    )
    def test_property_non_positive_quantity_always_rejected(
        self, instrument_name, option_type, strike_price, premium, quantity
    ):
        """属性：非正数的 quantity 总是被拒绝
        
        **Validates: Requirement 8.4**
        
        对于任意 quantity <= 0，
        OptionTrade 对象创建应该抛出 ValueError
        """
        expiry_date = datetime.now() + timedelta(days=7)
        
        with pytest.raises(ValueError, match="quantity 必须为正数"):
            OptionTrade(
                instrument_name=instrument_name,
                option_type=option_type,
                strike_price=strike_price,
                expiry_date=expiry_date,
                premium=premium,
                quantity=quantity
            )
    
    @given(
        instrument_name=non_empty_strings,
        option_type=valid_option_types,
        strike_price=positive_floats,
        premium=positive_floats,
        quantity=positive_floats,
        expiry_date=past_datetimes
    )
    def test_property_past_expiry_date_always_rejected(
        self, instrument_name, option_type, strike_price, premium, quantity, expiry_date
    ):
        """属性：过去的 expiry_date 总是被拒绝
        
        **Validates: Requirement 8.5**
        
        对于任意 expiry_date <= 当前时间，
        OptionTrade 对象创建应该抛出 ValueError
        """
        with pytest.raises(ValueError, match="expiry_date 必须在未来"):
            OptionTrade(
                instrument_name=instrument_name,
                option_type=option_type,
                strike_price=strike_price,
                expiry_date=expiry_date,
                premium=premium,
                quantity=quantity
            )
    
    @given(
        instrument_name=non_empty_strings,
        option_type=valid_option_types,
        strike_price=positive_floats,
        premium=positive_floats,
        quantity=positive_floats
    )
    def test_property_validate_method_idempotent(
        self, instrument_name, option_type, strike_price, premium, quantity
    ):
        """属性：validate() 方法是幂等的
        
        **Validates: Requirements 8.4, 8.5**
        
        对于任意有效的 OptionTrade 对象，
        多次调用 validate() 方法应该产生相同的结果（不抛出异常）
        """
        expiry_date = datetime.now() + timedelta(days=7)
        
        trade = OptionTrade(
            instrument_name=instrument_name,
            option_type=option_type,
            strike_price=strike_price,
            expiry_date=expiry_date,
            premium=premium,
            quantity=quantity
        )
        
        # 多次调用 validate() 不应抛出异常
        trade.validate()
        trade.validate()
        trade.validate()
        
        # 对象状态不应改变
        assert trade.strike_price == strike_price
        assert trade.premium == premium
        assert trade.quantity == quantity
    
    @given(
        instrument_name=non_empty_strings,
        strike_price=positive_floats,
        premium=positive_floats,
        quantity=positive_floats
    )
    def test_property_both_option_types_equally_valid(
        self, instrument_name, strike_price, premium, quantity
    ):
        """属性：两种 option_type 值都应该被平等接受
        
        **Validates: Requirement 8.4**
        
        对于任意有效的输入，两种 option_type 值（call, put）
        都应该被成功接受，没有偏好
        """
        expiry_date = datetime.now() + timedelta(days=7)
        
        # 测试 call 类型
        call_trade = OptionTrade(
            instrument_name=instrument_name,
            option_type="call",
            strike_price=strike_price,
            expiry_date=expiry_date,
            premium=premium,
            quantity=quantity
        )
        assert call_trade.option_type == "call"
        
        # 测试 put 类型
        put_trade = OptionTrade(
            instrument_name=instrument_name,
            option_type="put",
            strike_price=strike_price,
            expiry_date=expiry_date,
            premium=premium,
            quantity=quantity
        )
        assert put_trade.option_type == "put"
    
    @given(
        instrument_name=non_empty_strings,
        option_type=valid_option_types,
        premium=positive_floats,
        quantity=positive_floats
    )
    def test_property_very_small_positive_values_accepted(
        self, instrument_name, option_type, premium, quantity
    ):
        """属性：非常小的正数值应该被接受
        
        **Validates: Requirement 8.4**
        
        对于任意非常小但为正的 strike_price、premium、quantity，
        OptionTrade 对象应该被成功创建
        """
        expiry_date = datetime.now() + timedelta(days=7)
        very_small_value = 0.00001
        
        trade = OptionTrade(
            instrument_name=instrument_name,
            option_type=option_type,
            strike_price=very_small_value,
            expiry_date=expiry_date,
            premium=premium,
            quantity=quantity
        )
        
        assert trade.strike_price == very_small_value
        assert trade.strike_price > 0
    
    @given(
        instrument_name=non_empty_strings,
        option_type=valid_option_types,
        premium=positive_floats,
        quantity=positive_floats
    )
    def test_property_very_large_positive_values_accepted(
        self, instrument_name, option_type, premium, quantity
    ):
        """属性：非常大的正数值应该被接受
        
        **Validates: Requirement 8.4**
        
        对于任意非常大但有限的 strike_price、premium、quantity，
        OptionTrade 对象应该被成功创建
        """
        expiry_date = datetime.now() + timedelta(days=7)
        very_large_value = 999999.99
        
        trade = OptionTrade(
            instrument_name=instrument_name,
            option_type=option_type,
            strike_price=very_large_value,
            expiry_date=expiry_date,
            premium=premium,
            quantity=quantity
        )
        
        assert trade.strike_price == very_large_value
        assert trade.strike_price > 0
    
    @given(
        instrument_name=non_empty_strings,
        option_type=valid_option_types,
        strike_price=positive_floats,
        premium=positive_floats,
        quantity=positive_floats,
        days_in_future=st.integers(min_value=1, max_value=365)
    )
    def test_property_any_future_expiry_date_accepted(
        self, instrument_name, option_type, strike_price, premium, quantity, days_in_future
    ):
        """属性：任意未来的 expiry_date 都应该被接受
        
        **Validates: Requirement 8.5**
        
        对于任意在未来的 expiry_date（从1天到365天后），
        OptionTrade 对象应该被成功创建
        """
        expiry_date = datetime.now() + timedelta(days=days_in_future)
        
        trade = OptionTrade(
            instrument_name=instrument_name,
            option_type=option_type,
            strike_price=strike_price,
            expiry_date=expiry_date,
            premium=premium,
            quantity=quantity
        )
        
        assert trade.expiry_date > datetime.now()
    
    @given(
        instrument_name=non_empty_strings,
        option_type=valid_option_types,
        strike_price=positive_floats,
        premium=positive_floats,
        quantity=positive_floats
    )
    def test_property_zero_values_always_rejected(
        self, instrument_name, option_type, strike_price, premium, quantity
    ):
        """属性：零值总是被拒绝
        
        **Validates: Requirement 8.4**
        
        对于 strike_price、premium 或 quantity 中的任意零值，
        OptionTrade 对象创建应该抛出 ValueError
        """
        expiry_date = datetime.now() + timedelta(days=7)
        
        # 测试 strike_price = 0
        with pytest.raises(ValueError, match="strike_price 必须为正数"):
            OptionTrade(
                instrument_name=instrument_name,
                option_type=option_type,
                strike_price=0.0,
                expiry_date=expiry_date,
                premium=premium,
                quantity=quantity
            )
        
        # 测试 premium = 0
        with pytest.raises(ValueError, match="premium 必须为正数"):
            OptionTrade(
                instrument_name=instrument_name,
                option_type=option_type,
                strike_price=strike_price,
                expiry_date=expiry_date,
                premium=0.0,
                quantity=quantity
            )
        
        # 测试 quantity = 0
        with pytest.raises(ValueError, match="quantity 必须为正数"):
            OptionTrade(
                instrument_name=instrument_name,
                option_type=option_type,
                strike_price=strike_price,
                expiry_date=expiry_date,
                premium=premium,
                quantity=0.0
            )
    
    @given(
        instrument_name=non_empty_strings,
        option_type=valid_option_types,
        strike_price=positive_floats,
        premium=positive_floats,
        quantity=positive_floats,
        order_id=st.one_of(st.none(), non_empty_strings)
    )
    def test_property_order_id_optional_preserved(
        self, instrument_name, option_type, strike_price, premium, quantity, order_id
    ):
        """属性：可选的 order_id 应该被正确保存
        
        **Validates: Requirements 8.4, 8.5**
        
        对于任意有效的输入和任意 order_id（包括 None），
        创建的 OptionTrade 对象应该保留原始的 order_id 值
        """
        expiry_date = datetime.now() + timedelta(days=7)
        
        trade = OptionTrade(
            instrument_name=instrument_name,
            option_type=option_type,
            strike_price=strike_price,
            expiry_date=expiry_date,
            premium=premium,
            quantity=quantity,
            order_id=order_id
        )
        
        assert trade.order_id == order_id
    
    @given(
        instrument_name=non_empty_strings,
        option_type=valid_option_types,
        strike_price=positive_floats,
        premium=positive_floats,
        quantity=positive_floats
    )
    def test_property_current_time_expiry_rejected(
        self, instrument_name, option_type, strike_price, premium, quantity
    ):
        """属性：当前时间作为 expiry_date 应该被拒绝
        
        **Validates: Requirement 8.5**
        
        对于 expiry_date 等于当前时间（或非常接近），
        OptionTrade 对象创建应该抛出 ValueError
        """
        # 使用当前时间作为到期日
        expiry_date = datetime.now()
        
        with pytest.raises(ValueError, match="expiry_date 必须在未来"):
            OptionTrade(
                instrument_name=instrument_name,
                option_type=option_type,
                strike_price=strike_price,
                expiry_date=expiry_date,
                premium=premium,
                quantity=quantity
            )
    
    @given(
        instrument_name=non_empty_strings,
        option_type=valid_option_types,
        strike_price=positive_integers,
        premium=positive_integers,
        quantity=positive_integers
    )
    def test_property_integer_values_accepted_as_floats(
        self, instrument_name, option_type, strike_price, premium, quantity
    ):
        """属性：整数值应该被接受（作为浮点数）
        
        **Validates: Requirement 8.4**
        
        对于任意正整数的 strike_price、premium、quantity，
        OptionTrade 对象应该被成功创建
        """
        expiry_date = datetime.now() + timedelta(days=7)
        
        trade = OptionTrade(
            instrument_name=instrument_name,
            option_type=option_type,
            strike_price=strike_price,
            expiry_date=expiry_date,
            premium=premium,
            quantity=quantity
        )
        
        assert trade.strike_price == strike_price
        assert trade.premium == premium
        assert trade.quantity == quantity


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
