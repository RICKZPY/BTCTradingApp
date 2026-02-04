#!/usr/bin/env python3
"""
Property-based tests for data models
验证数据持久化完整性 - 属性 9
"""
import pytest
from hypothesis import given, strategies as st, assume
from datetime import datetime, timezone
import json
from decimal import Decimal

from core.data_models import (
    NewsItem, MarketData, Position, Portfolio, SentimentScore,
    ImpactAssessment, TechnicalSignal, PriceRange, TradingDecision,
    OrderResult, TradingRecord, ActionType, SignalType, RiskLevel,
    OrderStatus, PriceType, serialize_to_json, deserialize_from_json
)


# Hypothesis strategies for generating test data
def text_strategy(min_size=1, max_size=100):
    """Generate non-empty text strings"""
    return st.text(min_size=min_size, max_size=max_size).filter(lambda x: x.strip())


def positive_float_strategy(min_value=0.01, max_value=1000000):
    """Generate positive float values"""
    return st.floats(min_value=min_value, max_value=max_value, allow_nan=False, allow_infinity=False)


def percentage_strategy():
    """Generate percentage values (0-100)"""
    return st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False)


def confidence_strategy():
    """Generate confidence values (0-1)"""
    return st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False)


def impact_strategy():
    """Generate impact values (-1 to 1)"""
    return st.floats(min_value=-1, max_value=1, allow_nan=False, allow_infinity=False)


def datetime_strategy():
    """Generate datetime objects"""
    return st.datetimes(
        min_value=datetime(2020, 1, 1),
        max_value=datetime(2030, 12, 31)
    ).map(lambda dt: dt.replace(tzinfo=timezone.utc))


# Property tests for NewsItem
@given(
    id=text_strategy(),
    title=text_strategy(),
    content=text_strategy(),
    source=text_strategy(),
    published_at=datetime_strategy(),
    url=text_strategy(),
    sentiment_score=st.one_of(st.none(), percentage_strategy())
)
def test_news_item_serialization_roundtrip(id, title, content, source, published_at, url, sentiment_score):
    """
    Property 9.1: NewsItem serialization round trip
    For any valid NewsItem, serializing then deserializing should produce an equivalent object
    **Validates: Requirements 9.1, 9.2**
    """
    # Create NewsItem
    news_item = NewsItem(
        id=id,
        title=title,
        content=content,
        source=source,
        published_at=published_at,
        url=url,
        sentiment_score=sentiment_score
    )
    
    # Serialize to dict and back
    dict_data = news_item.to_dict()
    restored_item = NewsItem.from_dict(dict_data)
    
    # Verify equivalence
    assert restored_item.id == news_item.id
    assert restored_item.title == news_item.title
    assert restored_item.content == news_item.content
    assert restored_item.source == news_item.source
    assert restored_item.published_at == news_item.published_at
    assert restored_item.url == news_item.url
    assert restored_item.sentiment_score == news_item.sentiment_score


@given(
    symbol=text_strategy(),
    price=positive_float_strategy(),
    volume=st.floats(min_value=0, max_value=1000000, allow_nan=False, allow_infinity=False),
    timestamp=datetime_strategy(),
    source=text_strategy()
)
def test_market_data_serialization_roundtrip(symbol, price, volume, timestamp, source):
    """
    Property 9.2: MarketData serialization round trip
    For any valid MarketData, serializing then deserializing should produce an equivalent object
    **Validates: Requirements 9.1, 9.2**
    """
    # Create MarketData
    market_data = MarketData(
        symbol=symbol,
        price=price,
        volume=volume,
        timestamp=timestamp,
        source=source
    )
    
    # Serialize to dict and back
    dict_data = market_data.to_dict()
    restored_data = MarketData.from_dict(dict_data)
    
    # Verify equivalence
    assert restored_data.symbol == market_data.symbol
    assert restored_data.price == market_data.price
    assert restored_data.volume == market_data.volume
    assert restored_data.timestamp == market_data.timestamp
    assert restored_data.source == market_data.source


@given(
    symbol=text_strategy(),
    amount=st.floats(min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False).filter(lambda x: x != 0),
    entry_price=positive_float_strategy(),
    current_price=positive_float_strategy(),
    pnl=st.floats(min_value=-10000, max_value=10000, allow_nan=False, allow_infinity=False),
    entry_time=datetime_strategy()
)
def test_position_serialization_roundtrip(symbol, amount, entry_price, current_price, pnl, entry_time):
    """
    Property 9.3: Position serialization round trip
    For any valid Position, serializing then deserializing should produce an equivalent object
    **Validates: Requirements 9.1, 9.2**
    """
    # Create Position
    position = Position(
        symbol=symbol,
        amount=amount,
        entry_price=entry_price,
        current_price=current_price,
        pnl=pnl,
        entry_time=entry_time
    )
    
    # Serialize to dict and back
    dict_data = position.to_dict()
    restored_position = Position.from_dict(dict_data)
    
    # Verify equivalence
    assert restored_position.symbol == position.symbol
    assert restored_position.amount == position.amount
    assert restored_position.entry_price == position.entry_price
    assert restored_position.current_price == position.current_price
    assert restored_position.pnl == position.pnl
    assert restored_position.entry_time == position.entry_time


@given(
    btc_balance=st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False),
    usdt_balance=st.floats(min_value=0, max_value=100000, allow_nan=False, allow_infinity=False),
    total_value_usdt=st.floats(min_value=0, max_value=200000, allow_nan=False, allow_infinity=False),
    unrealized_pnl=st.floats(min_value=-10000, max_value=10000, allow_nan=False, allow_infinity=False)
)
def test_portfolio_serialization_roundtrip(btc_balance, usdt_balance, total_value_usdt, unrealized_pnl):
    """
    Property 9.4: Portfolio serialization round trip
    For any valid Portfolio, serializing then deserializing should produce an equivalent object
    **Validates: Requirements 9.1, 9.2**
    """
    # Create Portfolio
    portfolio = Portfolio(
        btc_balance=btc_balance,
        usdt_balance=usdt_balance,
        total_value_usdt=total_value_usdt,
        unrealized_pnl=unrealized_pnl
    )
    
    # Serialize to dict and back
    dict_data = portfolio.to_dict()
    restored_portfolio = Portfolio.from_dict(dict_data)
    
    # Verify equivalence
    assert restored_portfolio.btc_balance == portfolio.btc_balance
    assert restored_portfolio.usdt_balance == portfolio.usdt_balance
    assert restored_portfolio.total_value_usdt == portfolio.total_value_usdt
    assert restored_portfolio.unrealized_pnl == portfolio.unrealized_pnl
    assert len(restored_portfolio.positions) == len(portfolio.positions)


@given(
    sentiment_value=percentage_strategy(),
    confidence=confidence_strategy(),
    key_factors=st.lists(text_strategy(), min_size=0, max_size=5)
)
def test_sentiment_score_serialization_roundtrip(sentiment_value, confidence, key_factors):
    """
    Property 9.5: SentimentScore serialization round trip
    For any valid SentimentScore, serializing then deserializing should produce an equivalent object
    **Validates: Requirements 9.1, 9.2**
    """
    # Create SentimentScore
    sentiment_score = SentimentScore(
        sentiment_value=sentiment_value,
        confidence=confidence,
        key_factors=key_factors
    )
    
    # Serialize to dict and back
    dict_data = sentiment_score.to_dict()
    restored_score = SentimentScore.from_dict(dict_data)
    
    # Verify equivalence
    assert restored_score.sentiment_value == sentiment_score.sentiment_value
    assert restored_score.confidence == sentiment_score.confidence
    assert restored_score.key_factors == sentiment_score.key_factors


@given(
    short_term_impact=impact_strategy(),
    long_term_impact=impact_strategy(),
    impact_confidence=confidence_strategy(),
    reasoning=text_strategy()
)
def test_impact_assessment_serialization_roundtrip(short_term_impact, long_term_impact, impact_confidence, reasoning):
    """
    Property 9.6: ImpactAssessment serialization round trip
    For any valid ImpactAssessment, serializing then deserializing should produce an equivalent object
    **Validates: Requirements 9.1, 9.2**
    """
    # Create ImpactAssessment
    impact_assessment = ImpactAssessment(
        short_term_impact=short_term_impact,
        long_term_impact=long_term_impact,
        impact_confidence=impact_confidence,
        reasoning=reasoning
    )
    
    # Serialize to dict and back
    dict_data = impact_assessment.to_dict()
    restored_assessment = ImpactAssessment.from_dict(dict_data)
    
    # Verify equivalence
    assert restored_assessment.short_term_impact == impact_assessment.short_term_impact
    assert restored_assessment.long_term_impact == impact_assessment.long_term_impact
    assert restored_assessment.impact_confidence == impact_assessment.impact_confidence
    assert restored_assessment.reasoning == impact_assessment.reasoning


@given(
    signal_strength=impact_strategy(),
    signal_type=st.sampled_from(SignalType),
    confidence=confidence_strategy(),
    contributing_indicators=st.lists(text_strategy(), min_size=0, max_size=5)
)
def test_technical_signal_serialization_roundtrip(signal_strength, signal_type, confidence, contributing_indicators):
    """
    Property 9.7: TechnicalSignal serialization round trip
    For any valid TechnicalSignal, serializing then deserializing should produce an equivalent object
    **Validates: Requirements 9.1, 9.2**
    """
    # Create TechnicalSignal
    technical_signal = TechnicalSignal(
        signal_strength=signal_strength,
        signal_type=signal_type,
        confidence=confidence,
        contributing_indicators=contributing_indicators
    )
    
    # Serialize to dict and back
    dict_data = technical_signal.to_dict()
    restored_signal = TechnicalSignal.from_dict(dict_data)
    
    # Verify equivalence
    assert restored_signal.signal_strength == technical_signal.signal_strength
    assert restored_signal.signal_type == technical_signal.signal_type
    assert restored_signal.confidence == technical_signal.confidence
    assert restored_signal.contributing_indicators == technical_signal.contributing_indicators


@given(
    min_price=positive_float_strategy(),
    max_price=positive_float_strategy()
)
def test_price_range_serialization_roundtrip(min_price, max_price):
    """
    Property 9.8: PriceRange serialization round trip
    For any valid PriceRange, serializing then deserializing should produce an equivalent object
    **Validates: Requirements 9.1, 9.2**
    """
    # Ensure min_price <= max_price
    assume(min_price <= max_price)
    
    # Create PriceRange
    price_range = PriceRange(
        min_price=min_price,
        max_price=max_price
    )
    
    # Serialize to dict and back
    dict_data = price_range.to_dict()
    restored_range = PriceRange.from_dict(dict_data)
    
    # Verify equivalence
    assert restored_range.min_price == price_range.min_price
    assert restored_range.max_price == price_range.max_price


@given(
    action=st.sampled_from(ActionType),
    confidence=confidence_strategy(),
    suggested_amount=st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False),
    min_price=positive_float_strategy(),
    max_price=positive_float_strategy(),
    reasoning=text_strategy(),
    risk_level=st.sampled_from(RiskLevel)
)
def test_trading_decision_serialization_roundtrip(action, confidence, suggested_amount, min_price, max_price, reasoning, risk_level):
    """
    Property 9.9: TradingDecision serialization round trip
    For any valid TradingDecision, serializing then deserializing should produce an equivalent object
    **Validates: Requirements 9.1, 9.2**
    """
    # Ensure min_price <= max_price
    assume(min_price <= max_price)
    
    # Create TradingDecision
    price_range = PriceRange(min_price=min_price, max_price=max_price)
    trading_decision = TradingDecision(
        action=action,
        confidence=confidence,
        suggested_amount=suggested_amount,
        price_range=price_range,
        reasoning=reasoning,
        risk_level=risk_level
    )
    
    # Serialize to dict and back
    dict_data = trading_decision.to_dict()
    restored_decision = TradingDecision.from_dict(dict_data)
    
    # Verify equivalence
    assert restored_decision.action == trading_decision.action
    assert restored_decision.confidence == trading_decision.confidence
    assert restored_decision.suggested_amount == trading_decision.suggested_amount
    assert restored_decision.price_range.min_price == trading_decision.price_range.min_price
    assert restored_decision.price_range.max_price == trading_decision.price_range.max_price
    assert restored_decision.reasoning == trading_decision.reasoning
    assert restored_decision.risk_level == trading_decision.risk_level


@given(
    order_id=text_strategy(),
    status=st.sampled_from(OrderStatus),
    executed_amount=st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False),
    executed_price=st.floats(min_value=0, max_value=100000, allow_nan=False, allow_infinity=False),
    timestamp=datetime_strategy()
)
def test_order_result_serialization_roundtrip(order_id, status, executed_amount, executed_price, timestamp):
    """
    Property 9.10: OrderResult serialization round trip
    For any valid OrderResult, serializing then deserializing should produce an equivalent object
    **Validates: Requirements 9.1, 9.2**
    """
    # Create OrderResult
    order_result = OrderResult(
        order_id=order_id,
        status=status,
        executed_amount=executed_amount,
        executed_price=executed_price,
        timestamp=timestamp
    )
    
    # Serialize to dict and back
    dict_data = order_result.to_dict()
    restored_result = OrderResult.from_dict(dict_data)
    
    # Verify equivalence
    assert restored_result.order_id == order_result.order_id
    assert restored_result.status == order_result.status
    assert restored_result.executed_amount == order_result.executed_amount
    assert restored_result.executed_price == order_result.executed_price
    assert restored_result.timestamp == order_result.timestamp


@given(
    id=text_strategy(),
    action=st.sampled_from(ActionType),
    amount=positive_float_strategy(),
    price=positive_float_strategy(),
    timestamp=datetime_strategy(),
    decision_reasoning=text_strategy(),
    sentiment_score=percentage_strategy(),
    technical_signals=st.dictionaries(
        text_strategy(max_size=20), 
        st.floats(min_value=-1, max_value=1, allow_nan=False, allow_infinity=False),
        min_size=0,
        max_size=5
    )
)
def test_trading_record_serialization_roundtrip(id, action, amount, price, timestamp, decision_reasoning, sentiment_score, technical_signals):
    """
    Property 9.11: TradingRecord serialization round trip
    For any valid TradingRecord, serializing then deserializing should produce an equivalent object
    **Validates: Requirements 9.1, 9.2**
    """
    # Create TradingRecord
    trading_record = TradingRecord(
        id=id,
        action=action,
        amount=amount,
        price=price,
        timestamp=timestamp,
        decision_reasoning=decision_reasoning,
        sentiment_score=sentiment_score,
        technical_signals=technical_signals
    )
    
    # Serialize to dict and back
    dict_data = trading_record.to_dict()
    restored_record = TradingRecord.from_dict(dict_data)
    
    # Verify equivalence
    assert restored_record.id == trading_record.id
    assert restored_record.action == trading_record.action
    assert restored_record.amount == trading_record.amount
    assert restored_record.price == trading_record.price
    assert restored_record.timestamp == trading_record.timestamp
    assert restored_record.decision_reasoning == trading_record.decision_reasoning
    assert restored_record.sentiment_score == trading_record.sentiment_score
    assert restored_record.technical_signals == trading_record.technical_signals


@given(
    obj=st.one_of(
        st.builds(
            NewsItem,
            id=text_strategy(),
            title=text_strategy(),
            content=text_strategy(),
            source=text_strategy(),
            published_at=datetime_strategy(),
            url=text_strategy(),
            sentiment_score=st.one_of(st.none(), percentage_strategy())
        ),
        st.builds(
            MarketData,
            symbol=text_strategy(),
            price=positive_float_strategy(),
            volume=st.floats(min_value=0, max_value=1000000, allow_nan=False, allow_infinity=False),
            timestamp=datetime_strategy(),
            source=text_strategy()
        )
    )
)
def test_json_serialization_roundtrip(obj):
    """
    Property 9.12: JSON serialization round trip
    For any serializable object, JSON serializing then deserializing should produce an equivalent object
    **Validates: Requirements 9.1, 9.2**
    """
    # Serialize to JSON and back
    json_str = serialize_to_json(obj)
    restored_obj = deserialize_from_json(json_str, type(obj))
    
    # Verify equivalence by comparing dict representations
    assert obj.to_dict() == restored_obj.to_dict()


# Validation property tests
@given(
    symbol=text_strategy(),
    amount=st.floats(min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False).filter(lambda x: x != 0),
    entry_price=positive_float_strategy(),
    current_price=positive_float_strategy(),
    pnl=st.floats(min_value=-10000, max_value=10000, allow_nan=False, allow_infinity=False),
    entry_time=datetime_strategy()
)
def test_position_pnl_calculation_consistency(symbol, amount, entry_price, current_price, pnl, entry_time):
    """
    Property 9.13: Position PnL calculation consistency
    For any Position, the calculated PnL should match the expected formula
    **Validates: Requirements 9.1, 9.2**
    """
    # Create Position
    position = Position(
        symbol=symbol,
        amount=amount,
        entry_price=entry_price,
        current_price=current_price,
        pnl=pnl,
        entry_time=entry_time
    )
    
    # Calculate expected PnL
    if amount > 0:  # Long position
        expected_pnl = (current_price - entry_price) * amount
    else:  # Short position
        expected_pnl = (entry_price - current_price) * abs(amount)
    
    # Verify calculated PnL matches expected
    calculated_pnl = position.calculate_pnl()
    assert abs(calculated_pnl - expected_pnl) < 1e-10  # Account for floating point precision


@given(
    btc_balance=st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False),
    usdt_balance=st.floats(min_value=0, max_value=100000, allow_nan=False, allow_infinity=False),
    total_value_usdt=st.floats(min_value=0, max_value=200000, allow_nan=False, allow_infinity=False),
    unrealized_pnl=st.floats(min_value=-10000, max_value=10000, allow_nan=False, allow_infinity=False),
    positions=st.lists(
        st.builds(
            Position,
            symbol=text_strategy(),
            amount=st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False).filter(lambda x: x != 0),
            entry_price=positive_float_strategy(),
            current_price=positive_float_strategy(),
            pnl=st.floats(min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False),
            entry_time=datetime_strategy()
        ),
        min_size=0,
        max_size=3
    )
)
def test_portfolio_unrealized_pnl_consistency(btc_balance, usdt_balance, total_value_usdt, unrealized_pnl, positions):
    """
    Property 9.14: Portfolio unrealized PnL consistency
    For any Portfolio with positions, the unrealized PnL should equal the sum of position PnLs
    **Validates: Requirements 9.1, 9.2**
    """
    # Create Portfolio
    portfolio = Portfolio(
        btc_balance=btc_balance,
        usdt_balance=usdt_balance,
        total_value_usdt=total_value_usdt,
        unrealized_pnl=unrealized_pnl,
        positions=positions
    )
    
    # Update unrealized PnL
    portfolio.update_unrealized_pnl()
    
    # Calculate expected unrealized PnL
    expected_pnl = sum(pos.pnl for pos in positions)
    
    # Verify unrealized PnL matches expected
    assert abs(portfolio.unrealized_pnl - expected_pnl) < 1e-10  # Account for floating point precision


if __name__ == "__main__":
    # Run the property tests
    pytest.main([__file__, "-v", "--tb=short"])