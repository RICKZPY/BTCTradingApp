#!/usr/bin/env python3
"""
Property-based tests for trading execution consistency
验证交易执行一致性 - 属性 6
"""
import pytest
from hypothesis import given, strategies as st, assume, settings
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
from enum import Enum
import uuid

from core.data_models import (
    TradingDecision, ActionType, RiskLevel, PriceRange, 
    OrderResult, OrderStatus, TradingRecord
)


# Mock trading execution classes for testing
class MockTradingExecutor:
    def __init__(self):
        self.orders = []
        self.balance_btc = 1.0
        self.balance_usdt = 50000.0
        self.current_price = 50000.0
        self.execution_delay = 0.1  # seconds
        self.slippage_rate = 0.001  # 0.1%
    
    def execute_order(self, decision: TradingDecision) -> OrderResult:
        """Execute a trading order based on decision"""
        order_id = str(uuid.uuid4())
        
        # Simulate execution with slippage
        if decision.action == ActionType.BUY:
            execution_price = self.current_price * (1 + self.slippage_rate)
            if self.balance_usdt >= decision.suggested_amount * execution_price:
                executed_amount = decision.suggested_amount
                self.balance_usdt -= executed_amount * execution_price
                self.balance_btc += executed_amount
                status = OrderStatus.FILLED
            else:
                executed_amount = 0
                status = OrderStatus.FAILED
        elif decision.action == ActionType.SELL:
            execution_price = self.current_price * (1 - self.slippage_rate)
            if self.balance_btc >= decision.suggested_amount:
                executed_amount = decision.suggested_amount
                self.balance_btc -= executed_amount
                self.balance_usdt += executed_amount * execution_price
                status = OrderStatus.FILLED
            else:
                executed_amount = 0
                status = OrderStatus.FAILED
        else:  # HOLD
            executed_amount = 0
            execution_price = self.current_price
            status = OrderStatus.CANCELLED
        
        result = OrderResult(
            order_id=order_id,
            status=status,
            executed_amount=executed_amount,
            executed_price=execution_price,
            timestamp=datetime.now(timezone.utc)
        )
        
        self.orders.append(result)
        return result


# Hypothesis strategies for generating test data
def trading_decision_strategy():
    """Generate valid trading decisions"""
    return st.builds(
        TradingDecision,
        action=st.sampled_from(ActionType),
        confidence=st.floats(min_value=0.0, max_value=1.0),
        suggested_amount=st.floats(min_value=0.001, max_value=1.0),
        price_range=st.builds(
            PriceRange,
            min_price=st.floats(min_value=30000, max_value=50000),
            max_price=st.floats(min_value=50000, max_value=80000)
        ),
        reasoning=st.text(min_size=10, max_size=100),
        risk_level=st.sampled_from(RiskLevel)
    )


def price_strategy():
    """Generate realistic Bitcoin prices"""
    return st.floats(min_value=20000.0, max_value=100000.0, allow_nan=False, allow_infinity=False)


@given(
    decisions=st.lists(trading_decision_strategy(), min_size=1, max_size=10),
    market_price=price_strategy()
)
def test_order_execution_consistency_property(decisions, market_price):
    """
    Property 6.1: Order execution consistency
    For any trading decision, execution should be consistent and predictable
    **Validates: Requirements 5.2, 5.3**
    """
    executor = MockTradingExecutor()
    executor.current_price = market_price
    
    initial_btc = executor.balance_btc
    initial_usdt = executor.balance_usdt
    
    executed_orders = []
    
    for decision in decisions:
        # Skip invalid decisions
        if decision.suggested_amount <= 0:
            continue
            
        result = executor.execute_order(decision)
        executed_orders.append((decision, result))
    
    # Property: All orders should have valid results
    for decision, result in executed_orders:
        assert isinstance(result, OrderResult)
        assert result.order_id is not None and len(result.order_id) > 0
        assert result.status in [OrderStatus.FILLED, OrderStatus.FAILED, OrderStatus.CANCELLED]
        assert result.executed_amount >= 0
        assert result.executed_price > 0
        assert isinstance(result.timestamp, datetime)
    
    # Property: Balance changes should be consistent with executed orders
    total_btc_change = executor.balance_btc - initial_btc
    total_usdt_change = executor.balance_usdt - initial_usdt
    
    # Calculate expected changes from successful orders
    expected_btc_change = 0
    expected_usdt_change = 0
    
    for decision, result in executed_orders:
        if result.status == OrderStatus.FILLED:
            if decision.action == ActionType.BUY:
                expected_btc_change += result.executed_amount
                expected_usdt_change -= result.executed_amount * result.executed_price
            elif decision.action == ActionType.SELL:
                expected_btc_change -= result.executed_amount
                expected_usdt_change += result.executed_amount * result.executed_price
    
    # Allow small floating point differences
    assert abs(total_btc_change - expected_btc_change) < 1e-10
    assert abs(total_usdt_change - expected_usdt_change) < 1e-6  # Larger tolerance for USDT due to price multiplication


@given(
    buy_amount=st.floats(min_value=0.01, max_value=0.5),
    sell_amount=st.floats(min_value=0.01, max_value=0.5),
    market_price=price_strategy()
)
def test_round_trip_trading_property(buy_amount, sell_amount, market_price):
    """
    Property 6.2: Round-trip trading consistency
    For any buy followed by sell, the execution should be consistent
    **Validates: Requirements 5.2, 5.4**
    """
    executor = MockTradingExecutor()
    executor.current_price = market_price
    
    initial_btc = executor.balance_btc
    initial_usdt = executor.balance_usdt
    
    # Create buy decision
    buy_decision = TradingDecision(
        action=ActionType.BUY,
        confidence=0.8,
        suggested_amount=buy_amount,
        price_range=PriceRange(min_price=market_price * 0.95, max_price=market_price * 1.05),
        reasoning="Test buy order",
        risk_level=RiskLevel.MEDIUM
    )
    
    # Execute buy order
    buy_result = executor.execute_order(buy_decision)
    
    if buy_result.status == OrderStatus.FILLED:
        # Create sell decision for the amount we bought
        actual_sell_amount = min(sell_amount, buy_result.executed_amount)
        
        sell_decision = TradingDecision(
            action=ActionType.SELL,
            confidence=0.8,
            suggested_amount=actual_sell_amount,
            price_range=PriceRange(min_price=market_price * 0.95, max_price=market_price * 1.05),
            reasoning="Test sell order",
            risk_level=RiskLevel.MEDIUM
        )
        
        # Execute sell order
        sell_result = executor.execute_order(sell_decision)
        
        # Property: If buy succeeded, sell should also succeed (assuming sufficient balance)
        if actual_sell_amount <= executor.balance_btc + sell_result.executed_amount:  # Account for the sell that just happened
            assert sell_result.status == OrderStatus.FILLED
        
        # Property: Round-trip should result in predictable balance changes
        if sell_result.status == OrderStatus.FILLED:
            final_btc = executor.balance_btc
            final_usdt = executor.balance_usdt
            
            # Net BTC change should be buy_amount - sell_amount
            net_btc_change = final_btc - initial_btc
            expected_net_btc = buy_result.executed_amount - sell_result.executed_amount
            assert abs(net_btc_change - expected_net_btc) < 1e-10
            
            # USDT change should account for slippage
            net_usdt_change = final_usdt - initial_usdt
            expected_usdt_cost = (buy_result.executed_amount * buy_result.executed_price - 
                                sell_result.executed_amount * sell_result.executed_price)
            assert abs(net_usdt_change + expected_usdt_cost) < 1e-6


@given(
    decisions=st.lists(trading_decision_strategy(), min_size=5, max_size=15),
    market_volatility=st.floats(min_value=0.01, max_value=0.1)
)
def test_execution_order_independence_property(decisions, market_volatility):
    """
    Property 6.3: Execution order independence
    For any set of independent decisions, execution order shouldn't affect individual results
    **Validates: Requirements 5.2, 5.3**
    """
    base_price = 50000.0
    
    # Execute decisions in original order
    executor1 = MockTradingExecutor()
    executor1.current_price = base_price
    executor1.balance_btc = 10.0  # Large balance to avoid insufficient funds
    executor1.balance_usdt = 1000000.0
    
    results1 = []
    for decision in decisions:
        if decision.suggested_amount > 0:
            # Simulate small price changes due to volatility
            price_change = (hash(str(decision)) % 1000 - 500) / 10000 * market_volatility
            executor1.current_price = base_price * (1 + price_change)
            result = executor1.execute_order(decision)
            results1.append(result)
    
    # Execute decisions in reverse order
    executor2 = MockTradingExecutor()
    executor2.current_price = base_price
    executor2.balance_btc = 10.0  # Same large balance
    executor2.balance_usdt = 1000000.0
    
    results2 = []
    for decision in reversed(decisions):
        if decision.suggested_amount > 0:
            # Same price simulation
            price_change = (hash(str(decision)) % 1000 - 500) / 10000 * market_volatility
            executor2.current_price = base_price * (1 + price_change)
            result = executor2.execute_order(decision)
            results2.append(result)
    
    results2.reverse()  # Reverse back to match original order
    
    # Property: Individual order results should be similar regardless of execution order
    # (assuming sufficient balance and no market impact)
    if len(results1) == len(results2):
        for r1, r2 in zip(results1, results2):
            # Status should be the same
            assert r1.status == r2.status
            
            # Executed amounts should be the same
            assert abs(r1.executed_amount - r2.executed_amount) < 1e-10
            
            # Executed prices should be similar (same market conditions)
            if r1.executed_price > 0 and r2.executed_price > 0:
                price_diff_ratio = abs(r1.executed_price - r2.executed_price) / r1.executed_price
                assert price_diff_ratio < market_volatility * 2  # Allow for volatility


@given(
    decision=trading_decision_strategy(),
    execution_attempts=st.integers(min_value=2, max_value=5)
)
def test_execution_idempotency_property(decision, execution_attempts):
    """
    Property 6.4: Execution idempotency for failed orders
    For any failed order, re-execution should produce consistent results
    **Validates: Requirements 5.3, 5.4**
    """
    # Set up executor with insufficient balance to force failures
    executor = MockTradingExecutor()
    executor.balance_btc = 0.001  # Very small balance
    executor.balance_usdt = 10.0   # Very small balance
    executor.current_price = 50000.0
    
    # Ensure the decision will fail due to insufficient balance
    if decision.action == ActionType.BUY:
        decision.suggested_amount = 1.0  # More than we can afford
    elif decision.action == ActionType.SELL:
        decision.suggested_amount = 1.0  # More than we have
    
    results = []
    initial_btc = executor.balance_btc
    initial_usdt = executor.balance_usdt
    
    # Execute the same decision multiple times
    for _ in range(execution_attempts):
        result = executor.execute_order(decision)
        results.append(result)
    
    # Property: All failed executions should produce consistent results
    for result in results:
        if decision.action in [ActionType.BUY, ActionType.SELL]:
            # Should fail due to insufficient balance
            assert result.status == OrderStatus.FAILED
            assert result.executed_amount == 0
        else:  # HOLD
            assert result.status == OrderStatus.CANCELLED
            assert result.executed_amount == 0
    
    # Property: Failed orders should not change balances
    assert executor.balance_btc == initial_btc
    assert executor.balance_usdt == initial_usdt
    
    # Property: All results should have unique order IDs
    order_ids = [result.order_id for result in results]
    assert len(order_ids) == len(set(order_ids))  # All unique


@given(
    decisions=st.lists(trading_decision_strategy(), min_size=3, max_size=8),
    price_changes=st.lists(st.floats(min_value=-0.05, max_value=0.05), min_size=3, max_size=8)
)
def test_market_impact_consistency_property(decisions, price_changes):
    """
    Property 6.5: Market impact consistency
    For any sequence of orders, market impact should be consistent and predictable
    **Validates: Requirements 5.2, 5.4**
    """
    # Ensure we have matching lengths
    min_length = min(len(decisions), len(price_changes))
    decisions = decisions[:min_length]
    price_changes = price_changes[:min_length]
    
    executor = MockTradingExecutor()
    base_price = 50000.0
    executor.current_price = base_price
    executor.balance_btc = 5.0
    executor.balance_usdt = 500000.0
    
    executed_orders = []
    
    for i, (decision, price_change) in enumerate(zip(decisions, price_changes)):
        if decision.suggested_amount <= 0:
            continue
            
        # Apply market price change
        executor.current_price = base_price * (1 + price_change)
        
        result = executor.execute_order(decision)
        executed_orders.append((decision, result, executor.current_price))
    
    # Property: Execution prices should reflect market conditions
    for decision, result, market_price in executed_orders:
        if result.status == OrderStatus.FILLED:
            if decision.action == ActionType.BUY:
                # Buy price should be slightly higher than market (slippage)
                assert result.executed_price >= market_price
                assert result.executed_price <= market_price * 1.01  # Max 1% slippage
            elif decision.action == ActionType.SELL:
                # Sell price should be slightly lower than market (slippage)
                assert result.executed_price <= market_price
                assert result.executed_price >= market_price * 0.99  # Max 1% slippage
    
    # Property: Large orders should have proportional impact
    large_orders = [(d, r, p) for d, r, p in executed_orders 
                   if r.status == OrderStatus.FILLED and d.suggested_amount > 0.1]
    small_orders = [(d, r, p) for d, r, p in executed_orders 
                   if r.status == OrderStatus.FILLED and d.suggested_amount <= 0.1]
    
    if large_orders and small_orders:
        # This is a simplified test - in reality, market impact is complex
        # We just verify that the slippage is consistent
        for decision, result, market_price in large_orders:
            slippage = abs(result.executed_price - market_price) / market_price
            assert slippage <= 0.01  # Max 1% slippage even for large orders


@given(
    trading_session_length=st.integers(min_value=5, max_value=20),
    decision_frequency=st.floats(min_value=0.3, max_value=1.0)
)
def test_trading_session_consistency_property(trading_session_length, decision_frequency):
    """
    Property 6.6: Trading session consistency
    For any trading session, the system should maintain consistency throughout
    **Validates: Requirements 5.2, 5.3, 5.4**
    """
    executor = MockTradingExecutor()
    executor.balance_btc = 2.0
    executor.balance_usdt = 100000.0
    base_price = 50000.0
    
    session_orders = []
    balance_history = [(executor.balance_btc, executor.balance_usdt)]
    
    for step in range(trading_session_length):
        # Randomly decide whether to make a trade this step
        import random
        random.seed(step)  # For reproducibility
        
        if random.random() < decision_frequency:
            # Generate a decision
            action = random.choice([ActionType.BUY, ActionType.SELL, ActionType.HOLD])
            amount = random.uniform(0.01, 0.2)
            
            # Simulate price movement
            price_change = random.uniform(-0.02, 0.02)
            executor.current_price = base_price * (1 + price_change)
            
            decision = TradingDecision(
                action=action,
                confidence=random.uniform(0.5, 1.0),
                suggested_amount=amount,
                price_range=PriceRange(
                    min_price=executor.current_price * 0.98,
                    max_price=executor.current_price * 1.02
                ),
                reasoning=f"Session step {step}",
                risk_level=random.choice(list(RiskLevel))
            )
            
            result = executor.execute_order(decision)
            session_orders.append((step, decision, result))
        
        # Record balance after each step
        balance_history.append((executor.balance_btc, executor.balance_usdt))
    
    # Property: Balance changes should be traceable to executed orders
    total_btc_change = executor.balance_btc - balance_history[0][0]
    total_usdt_change = executor.balance_usdt - balance_history[0][1]
    
    expected_btc_change = 0
    expected_usdt_change = 0
    
    for step, decision, result in session_orders:
        if result.status == OrderStatus.FILLED:
            if decision.action == ActionType.BUY:
                expected_btc_change += result.executed_amount
                expected_usdt_change -= result.executed_amount * result.executed_price
            elif decision.action == ActionType.SELL:
                expected_btc_change -= result.executed_amount
                expected_usdt_change += result.executed_amount * result.executed_price
    
    # Verify balance consistency
    assert abs(total_btc_change - expected_btc_change) < 1e-10
    assert abs(total_usdt_change - expected_usdt_change) < 1e-6
    
    # Property: All balances should be non-negative throughout the session
    for btc_balance, usdt_balance in balance_history:
        assert btc_balance >= 0
        assert usdt_balance >= 0
    
    # Property: All order IDs should be unique
    order_ids = [result.order_id for _, _, result in session_orders]
    assert len(order_ids) == len(set(order_ids))


if __name__ == "__main__":
    # Run the property tests
    pytest.main([__file__, "-v", "--tb=short"])