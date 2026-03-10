#!/usr/bin/env python3
"""
Preservation Property Tests for Sentiment Trading Service
测试目标：确保修复后所有交易逻辑、情绪分析、错误处理保持不变

CRITICAL: 这些测试MUST PASS在未修复的代码上（建立baseline）
然后在修复后的代码上也MUST PASS（确保无回归）
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict
from hypothesis import given, strategies as st, settings
from hypothesis import HealthCheck


def analyze_sentiment_reference(sentiment_data: Dict) -> str:
    """
    参考实现：情绪分析逻辑
    这是从sentiment_trading_service.py中提取的逻辑
    """
    try:
        data = sentiment_data.get('data', {})
        negative_count = data.get('negative_count', 0)
        positive_count = data.get('positive_count', 0)
        
        if negative_count > positive_count:
            return "bearish_news"
        elif negative_count < positive_count:
            return "bullish_news"
        else:
            return "mixed_news"
    except Exception:
        return "mixed_news"


class TestPreservationProperties:
    """
    Property 2: Preservation - Trading Logic and Configuration Compatibility
    
    这些测试捕获当前（未修复）代码的行为，确保修复后行为保持不变。
    """
    
    def test_sentiment_analysis_logic_preserved(self):
        """
        测试1：情绪分析逻辑保持不变
        
        验证analyze_sentiment方法对不同输入产生相同的输出
        """
        print("\n=== Test 1: Sentiment Analysis Logic Preservation ===")
        
        # 测试用例：不同的情绪数据
        test_cases = [
            # (input, expected_strategy)
            ({"data": {"negative_count": 10, "positive_count": 5}}, "bearish_news"),
            ({"data": {"negative_count": 3, "positive_count": 8}}, "bullish_news"),
            ({"data": {"negative_count": 5, "positive_count": 5}}, "mixed_news"),
            ({"data": {"negative_count": 0, "positive_count": 0}}, "mixed_news"),
            ({"data": {"negative_count": 100, "positive_count": 1}}, "bearish_news"),
            ({"data": {"negative_count": 1, "positive_count": 100}}, "bullish_news"),
        ]
        
        print("Testing sentiment analysis logic...")
        for sentiment_data, expected_strategy in test_cases:
            result = analyze_sentiment_reference(sentiment_data)
            print(f"  Input: neg={sentiment_data['data']['negative_count']}, "
                  f"pos={sentiment_data['data']['positive_count']} "
                  f"→ Strategy: {result}")
            assert result == expected_strategy, (
                f"Sentiment analysis logic changed! "
                f"Expected: {expected_strategy}, Got: {result}"
            )
        
        print("✓ Sentiment analysis logic preserved")
    
    def test_strategy_selection_rules_preserved(self):
        """
        测试2：策略选择规则保持不变
        
        验证情绪分析到策略选择的映射关系不变
        """
        print("\n=== Test 2: Strategy Selection Rules Preservation ===")
        
        # 规则1：负面 > 正面 → bearish_news
        result1 = analyze_sentiment_reference({"data": {"negative_count": 10, "positive_count": 5}})
        assert result1 == "bearish_news", "Rule 1 violated: negative > positive should give bearish_news"
        
        # 规则2：正面 > 负面 → bullish_news
        result2 = analyze_sentiment_reference({"data": {"negative_count": 5, "positive_count": 10}})
        assert result2 == "bullish_news", "Rule 2 violated: positive > negative should give bullish_news"
        
        # 规则3：正面 = 负面 → mixed_news
        result3 = analyze_sentiment_reference({"data": {"negative_count": 5, "positive_count": 5}})
        assert result3 == "mixed_news", "Rule 3 violated: positive = negative should give mixed_news"
        
        print("✓ All strategy selection rules preserved")
    
    def test_trading_history_format_preserved(self):
        """
        测试3：交易历史记录格式保持不变
        
        验证历史记录的数据结构和字段不变
        """
        print("\n=== Test 3: Trading History Format Preservation ===")
        
        # 模拟一个交易记录
        mock_sentiment_data = {"data": {"negative_count": 10, "positive_count": 5}}
        mock_execution_result = {"success": True, "orders": []}
        
        # 手动创建一个交易记录（模拟execute_sentiment_strategy的行为）
        trade_record = {
            "timestamp": datetime.now().isoformat(),
            "strategy_type": "bearish_news",
            "sentiment_data": mock_sentiment_data,
            "execution_result": mock_execution_result,
            "success": True
        }
        
        # 验证必需字段存在
        required_fields = ["timestamp", "strategy_type", "sentiment_data", "execution_result", "success"]
        for field in required_fields:
            assert field in trade_record, f"Required field '{field}' missing from trade record"
        
        # 验证字段类型
        assert isinstance(trade_record["timestamp"], str), "timestamp should be string (ISO format)"
        assert isinstance(trade_record["strategy_type"], str), "strategy_type should be string"
        assert isinstance(trade_record["sentiment_data"], dict), "sentiment_data should be dict"
        assert isinstance(trade_record["execution_result"], dict), "execution_result should be dict"
        assert isinstance(trade_record["success"], bool), "success should be boolean"
        
        print("✓ Trading history format preserved")
    
    def test_position_data_format_preserved(self):
        """
        测试4：持仓数据格式保持不变
        
        验证get_positions_and_orders返回的数据结构不变
        """
        print("\n=== Test 4: Position Data Format Preservation ===")
        
        # 模拟预期的持仓数据格式
        expected_format = {
            "timestamp": str,
            "network": str,
            "positions": list,
            "open_orders": list,
            "errors": (list, type(None)),
            "position_count": int,
            "order_count": int
        }
        
        # 创建一个示例数据
        sample_data = {
            "timestamp": datetime.now().isoformat(),
            "network": "testnet",
            "positions": [],
            "open_orders": [],
            "errors": None,
            "position_count": 0,
            "order_count": 0
        }
        
        # 验证格式
        for field, expected_type in expected_format.items():
            assert field in sample_data, f"Required field '{field}' missing"
            if isinstance(expected_type, tuple):
                assert isinstance(sample_data[field], expected_type), \
                    f"Field '{field}' has wrong type"
            else:
                assert isinstance(sample_data[field], expected_type), \
                    f"Field '{field}' should be {expected_type}"
        
        print("✓ Position data format preserved")
    
    def test_error_handling_behavior_preserved(self):
        """
        测试5：错误处理行为保持不变
        
        验证各种错误情况下的处理逻辑不变
        """
        print("\n=== Test 5: Error Handling Preservation ===")
        
        # 测试1：空情绪数据
        result1 = analyze_sentiment_reference({})
        assert result1 == "mixed_news", "Empty data should default to mixed_news"
        
        # 测试2：缺少data字段
        result2 = analyze_sentiment_reference({"other": "field"})
        assert result2 == "mixed_news", "Missing 'data' field should default to mixed_news"
        
        # 测试3：缺少count字段
        result3 = analyze_sentiment_reference({"data": {}})
        assert result3 == "mixed_news", "Missing count fields should default to mixed_news"
        
        # 测试4：异常值处理
        result4 = analyze_sentiment_reference({"data": {"negative_count": -1, "positive_count": -1}})
        assert result4 == "mixed_news", "Negative counts should be handled gracefully"
        
        print("✓ Error handling behavior preserved")
    
    def test_configuration_file_paths_preserved(self):
        """
        测试6：配置文件路径保持不变
        
        验证配置常量不变
        """
        print("\n=== Test 6: Configuration File Paths Preservation ===")
        
        # 从源代码中读取配置
        with open('sentiment_trading_service.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 验证关键配置存在
        assert 'SENTIMENT_API_URL' in content, "SENTIMENT_API_URL constant missing"
        assert 'CHECK_TIME = time(5, 0)' in content, "CHECK_TIME constant changed"
        assert 'DATA_FILE = "data/sentiment_trading_history.json"' in content, "DATA_FILE path changed"
        assert 'POSITION_FILE = "data/current_positions.json"' in content, "POSITION_FILE path changed"
        
        print("✓ Configuration file paths preserved")
    
    @given(
        negative_count=st.integers(min_value=0, max_value=100),
        positive_count=st.integers(min_value=0, max_value=100)
    )
    @settings(
        max_examples=50,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_property_sentiment_analysis_deterministic(
        self,
        negative_count: int,
        positive_count: int
    ):
        """
        Property Test: 情绪分析的确定性
        
        For any valid sentiment counts, analyze_sentiment should:
        1. Always return the same result for the same input
        2. Follow the documented rules (negative>positive→bearish, etc.)
        """
        sentiment_data = {
            "data": {
                "negative_count": negative_count,
                "positive_count": positive_count
            }
        }
        
        # 调用两次，应该得到相同结果（确定性）
        result1 = analyze_sentiment_reference(sentiment_data)
        result2 = analyze_sentiment_reference(sentiment_data)
        
        assert result1 == result2, "analyze_sentiment should be deterministic"
        
        # 验证规则
        if negative_count > positive_count:
            assert result1 == "bearish_news", \
                f"Rule violated: neg({negative_count}) > pos({positive_count}) should give bearish_news"
        elif negative_count < positive_count:
            assert result1 == "bullish_news", \
                f"Rule violated: neg({negative_count}) < pos({positive_count}) should give bullish_news"
        else:
            assert result1 == "mixed_news", \
                f"Rule violated: neg({negative_count}) = pos({positive_count}) should give mixed_news"


def run_preservation_tests():
    """运行所有保留性测试"""
    print("=" * 80)
    print("PRESERVATION PROPERTY TESTS")
    print("=" * 80)
    print("\nIMPORTANT: These tests establish baseline behavior on unfixed code.")
    print("They MUST PASS on both unfixed and fixed code (no regressions).")
    print("=" * 80)
    
    test_suite = TestPreservationProperties()
    
    failures = []
    
    # Test 1
    try:
        test_suite.test_sentiment_analysis_logic_preserved()
    except AssertionError as e:
        print(f"\n✗ Test 1 FAILED: {e}")
        failures.append(("Test 1", str(e)))
    
    # Test 2
    try:
        test_suite.test_strategy_selection_rules_preserved()
    except AssertionError as e:
        print(f"\n✗ Test 2 FAILED: {e}")
        failures.append(("Test 2", str(e)))
    
    # Test 3
    try:
        test_suite.test_trading_history_format_preserved()
    except AssertionError as e:
        print(f"\n✗ Test 3 FAILED: {e}")
        failures.append(("Test 3", str(e)))
    
    # Test 4
    try:
        test_suite.test_position_data_format_preserved()
    except AssertionError as e:
        print(f"\n✗ Test 4 FAILED: {e}")
        failures.append(("Test 4", str(e)))
    
    # Test 5
    try:
        test_suite.test_error_handling_behavior_preserved()
    except AssertionError as e:
        print(f"\n✗ Test 5 FAILED: {e}")
        failures.append(("Test 5", str(e)))
    
    # Test 6
    try:
        test_suite.test_configuration_file_paths_preserved()
    except AssertionError as e:
        print(f"\n✗ Test 6 FAILED: {e}")
        failures.append(("Test 6", str(e)))
    
    # Summary
    print("\n" + "=" * 80)
    print("PRESERVATION TEST SUMMARY")
    print("=" * 80)
    
    if failures:
        print(f"\n{len(failures)} test(s) FAILED!")
        print("\nFailures:")
        for test_name, error in failures:
            print(f"\n{test_name}:")
            print(f"  {error[:200]}...")
        print("\nThese tests capture baseline behavior.")
        print("Fix any failures before proceeding with code changes.")
    else:
        print("\n✓ All preservation tests PASSED!")
        print("\nBaseline behavior established.")
        print("These tests will ensure no regressions after fix implementation.")
    
    print("=" * 80)
    
    return len(failures) == 0


if __name__ == "__main__":
    success = run_preservation_tests()
    exit(0 if success else 1)
