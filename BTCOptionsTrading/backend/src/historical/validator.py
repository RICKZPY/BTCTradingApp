"""
历史数据验证器
验证历史期权数据的完整性、合理性和质量
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Tuple, Optional
from collections import defaultdict

from src.historical.models import (
    HistoricalOptionData, ValidationResult, DataQualityReport,
    DataIssue, ValidationSeverity, CoverageStats
)
from src.core.models import OptionType
from src.config.logging_config import get_logger

logger = get_logger(__name__)


class HistoricalDataValidator:
    """历史数据验证器"""
    
    # 验证阈值
    MAX_PRICE_CHANGE_RATIO = Decimal('0.5')  # 最大价格变化比例 50%
    MIN_VOLUME = Decimal('0')  # 最小成交量
    MAX_PRICE = Decimal('10.0')  # 最大期权价格（BTC）
    MIN_PRICE = Decimal('0')  # 最小期权价格
    
    def __init__(self):
        """初始化验证器"""
        logger.info("HistoricalDataValidator initialized")
    
    def validate_data_completeness(
        self,
        data: List[HistoricalOptionData],
        expected_interval: timedelta = timedelta(hours=1)
    ) -> ValidationResult:
        """
        验证数据完整性
        
        Args:
            data: 历史数据列表
            expected_interval: 预期的时间间隔
            
        Returns:
            验证结果
        """
        logger.info(f"Validating data completeness for {len(data)} records")
        
        errors = []
        warnings = []
        issues = []
        
        if not data:
            errors.append("No data to validate")
            return ValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                issues=issues
            )
        
        # 按时间戳排序
        sorted_data = sorted(data, key=lambda x: x.timestamp)
        
        # 检查时间序列单调性
        timestamps = [d.timestamp for d in sorted_data]
        if timestamps != sorted(timestamps):
            errors.append("Timestamps are not monotonically increasing")
            issues.append(DataIssue(
                severity=ValidationSeverity.ERROR,
                message="Timestamps are not in chronological order"
            ))
        
        # 检查重复时间戳
        unique_timestamps = set(timestamps)
        if len(timestamps) != len(unique_timestamps):
            duplicate_count = len(timestamps) - len(unique_timestamps)
            warnings.append(f"Found {duplicate_count} duplicate timestamps")
            issues.append(DataIssue(
                severity=ValidationSeverity.WARNING,
                message=f"Duplicate timestamps detected: {duplicate_count} duplicates"
            ))
        
        # 检查时间间隔
        missing_intervals = []
        for i in range(len(sorted_data) - 1):
            current = sorted_data[i].timestamp
            next_ts = sorted_data[i + 1].timestamp
            actual_interval = next_ts - current
            
            if actual_interval > expected_interval * 1.5:  # 允许 50% 误差
                missing_intervals.append((current, next_ts, actual_interval))
        
        if missing_intervals:
            warnings.append(f"Found {len(missing_intervals)} gaps in time series")
            for start, end, interval in missing_intervals[:5]:  # 只报告前5个
                issues.append(DataIssue(
                    severity=ValidationSeverity.WARNING,
                    message=f"Time gap detected: {start} to {end} ({interval})",
                    timestamp=start
                ))
        
        # 检查缺失值
        missing_count = 0
        for i, d in enumerate(sorted_data):
            if d.close_price == 0 or d.volume == 0:
                missing_count += 1
                if missing_count <= 5:  # 只记录前5个
                    issues.append(DataIssue(
                        severity=ValidationSeverity.WARNING,
                        message=f"Zero price or volume at {d.timestamp}",
                        timestamp=d.timestamp,
                        record_index=i
                    ))
        
        if missing_count > 0:
            warnings.append(f"Found {missing_count} records with zero price or volume")
        
        # 统计信息
        stats = {
            'total_records': len(data),
            'unique_timestamps': len(unique_timestamps),
            'time_range': (min(timestamps), max(timestamps)) if timestamps else None,
            'missing_intervals': len(missing_intervals),
            'zero_values': missing_count
        }
        
        is_valid = len(errors) == 0
        
        logger.info(f"Completeness validation: {len(errors)} errors, {len(warnings)} warnings")
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            issues=issues,
            stats=stats
        )

    
    def validate_price_sanity(
        self,
        data: List[HistoricalOptionData]
    ) -> ValidationResult:
        """
        验证价格合理性
        
        Args:
            data: 历史数据列表
            
        Returns:
            验证结果
        """
        logger.info(f"Validating price sanity for {len(data)} records")
        
        errors = []
        warnings = []
        issues = []
        
        if not data:
            errors.append("No data to validate")
            return ValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                issues=issues
            )
        
        # 按时间戳排序
        sorted_data = sorted(data, key=lambda x: x.timestamp)
        
        # 检查每条记录
        for i, d in enumerate(sorted_data):
            # 检查负价格
            if d.open_price < self.MIN_PRICE or d.high_price < self.MIN_PRICE or \
               d.low_price < self.MIN_PRICE or d.close_price < self.MIN_PRICE:
                errors.append(f"Record {i}: Negative price detected at {d.timestamp}")
                issues.append(DataIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Negative price: O={d.open_price}, H={d.high_price}, L={d.low_price}, C={d.close_price}",
                    timestamp=d.timestamp,
                    record_index=i
                ))
            
            # 检查 OHLC 关系
            if not (d.low_price <= d.open_price <= d.high_price):
                errors.append(f"Record {i}: Invalid OHLC relationship - Open outside Low-High range")
                issues.append(DataIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Open price {d.open_price} not in range [{d.low_price}, {d.high_price}]",
                    timestamp=d.timestamp,
                    record_index=i,
                    field_name='open_price'
                ))
            
            if not (d.low_price <= d.close_price <= d.high_price):
                errors.append(f"Record {i}: Invalid OHLC relationship - Close outside Low-High range")
                issues.append(DataIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Close price {d.close_price} not in range [{d.low_price}, {d.high_price}]",
                    timestamp=d.timestamp,
                    record_index=i,
                    field_name='close_price'
                ))
            
            # 检查异常高价
            if d.high_price > self.MAX_PRICE:
                warnings.append(f"Record {i}: Unusually high price {d.high_price} at {d.timestamp}")
                issues.append(DataIssue(
                    severity=ValidationSeverity.WARNING,
                    message=f"High price {d.high_price} exceeds threshold {self.MAX_PRICE}",
                    timestamp=d.timestamp,
                    record_index=i,
                    field_name='high_price'
                ))
            
            # 检查负成交量
            if d.volume < self.MIN_VOLUME:
                errors.append(f"Record {i}: Negative volume {d.volume} at {d.timestamp}")
                issues.append(DataIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Negative volume: {d.volume}",
                    timestamp=d.timestamp,
                    record_index=i,
                    field_name='volume'
                ))
        
        # 检查价格跳变
        anomaly_count = 0
        for i in range(len(sorted_data) - 1):
            current = sorted_data[i]
            next_data = sorted_data[i + 1]
            
            if current.close_price > 0:
                price_change = abs(next_data.open_price - current.close_price) / current.close_price
                
                if price_change > self.MAX_PRICE_CHANGE_RATIO:
                    anomaly_count += 1
                    if anomaly_count <= 5:  # 只记录前5个
                        warnings.append(
                            f"Large price jump: {current.close_price} -> {next_data.open_price} "
                            f"({price_change:.1%}) at {next_data.timestamp}"
                        )
                        issues.append(DataIssue(
                            severity=ValidationSeverity.WARNING,
                            message=f"Price jump of {price_change:.1%} detected",
                            timestamp=next_data.timestamp,
                            record_index=i + 1
                        ))
        
        if anomaly_count > 5:
            warnings.append(f"Total {anomaly_count} large price jumps detected")
        
        # 统计信息
        prices = [d.close_price for d in sorted_data]
        stats = {
            'total_records': len(data),
            'min_price': min(prices) if prices else None,
            'max_price': max(prices) if prices else None,
            'avg_price': sum(prices) / len(prices) if prices else None,
            'anomaly_count': anomaly_count
        }
        
        is_valid = len(errors) == 0
        
        logger.info(f"Price sanity validation: {len(errors)} errors, {len(warnings)} warnings")
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            issues=issues,
            stats=stats
        )
    
    def validate_option_parity(
        self,
        call_data: List[HistoricalOptionData],
        put_data: List[HistoricalOptionData],
        underlying_price: Optional[Decimal] = None,
        tolerance: Decimal = Decimal('0.1')
    ) -> ValidationResult:
        """
        验证期权平价关系
        
        Put-Call Parity: C - P = S - K * e^(-r*T)
        简化版本（忽略利率和时间价值）: C - P ≈ S - K
        
        Args:
            call_data: 看涨期权数据
            put_data: 看跌期权数据
            underlying_price: 标的资产价格（如果提供）
            tolerance: 容忍度（相对误差）
            
        Returns:
            验证结果
        """
        logger.info(f"Validating option parity: {len(call_data)} calls, {len(put_data)} puts")
        
        errors = []
        warnings = []
        issues = []
        
        if not call_data or not put_data:
            warnings.append("Insufficient data for parity check")
            return ValidationResult(
                is_valid=True,
                errors=errors,
                warnings=warnings,
                issues=issues
            )
        
        # 按执行价和时间戳分组
        call_dict: Dict[Tuple[Decimal, datetime], HistoricalOptionData] = {}
        for call in call_data:
            key = (call.strike_price, call.timestamp)
            call_dict[key] = call
        
        put_dict: Dict[Tuple[Decimal, datetime], HistoricalOptionData] = {}
        for put in put_data:
            key = (put.strike_price, put.timestamp)
            put_dict[key] = put
        
        # 找到匹配的看涨看跌对
        matched_pairs = []
        for key in call_dict:
            if key in put_dict:
                matched_pairs.append((call_dict[key], put_dict[key]))
        
        if not matched_pairs:
            warnings.append("No matching call-put pairs found for parity check")
            return ValidationResult(
                is_valid=True,
                errors=errors,
                warnings=warnings,
                issues=issues
            )
        
        logger.info(f"Found {len(matched_pairs)} matching call-put pairs")
        
        # 检查平价关系
        parity_violations = 0
        for call, put in matched_pairs:
            # 简化的平价检查：看涨期权价格应该 >= 看跌期权价格（当 S > K 时）
            # 这是一个粗略的检查，实际平价关系更复杂
            
            price_diff = call.close_price - put.close_price
            
            # 如果提供了标的价格，进行更精确的检查
            if underlying_price:
                expected_diff = underlying_price - call.strike_price
                actual_diff = price_diff
                
                if expected_diff != 0:
                    relative_error = abs(actual_diff - expected_diff) / abs(expected_diff)
                    
                    if relative_error > tolerance:
                        parity_violations += 1
                        if parity_violations <= 5:
                            warnings.append(
                                f"Parity violation at {call.timestamp}: "
                                f"C-P={price_diff:.4f}, S-K={expected_diff:.4f}, "
                                f"error={relative_error:.1%}"
                            )
                            issues.append(DataIssue(
                                severity=ValidationSeverity.WARNING,
                                message=f"Put-call parity violation: relative error {relative_error:.1%}",
                                timestamp=call.timestamp
                            ))
            else:
                # 基本合理性检查：价格不应该相差太大
                if abs(price_diff) > call.strike_price * tolerance:
                    parity_violations += 1
                    if parity_violations <= 5:
                        warnings.append(
                            f"Large call-put price difference at {call.timestamp}: "
                            f"C={call.close_price}, P={put.close_price}, diff={price_diff}"
                        )
                        issues.append(DataIssue(
                            severity=ValidationSeverity.WARNING,
                            message=f"Large call-put price difference: {price_diff}",
                            timestamp=call.timestamp
                        ))
        
        if parity_violations > 5:
            warnings.append(f"Total {parity_violations} parity violations detected")
        
        # 统计信息
        stats = {
            'total_pairs': len(matched_pairs),
            'parity_violations': parity_violations,
            'violation_rate': parity_violations / len(matched_pairs) if matched_pairs else 0
        }
        
        is_valid = len(errors) == 0
        
        logger.info(f"Parity validation: {parity_violations} violations out of {len(matched_pairs)} pairs")
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            issues=issues,
            stats=stats
        )
    
    def generate_quality_report(
        self,
        data: List[HistoricalOptionData],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> DataQualityReport:
        """
        生成数据质量报告
        
        Args:
            data: 历史数据列表
            start_date: 开始日期（用于计算覆盖率）
            end_date: 结束日期（用于计算覆盖率）
            
        Returns:
            数据质量报告
        """
        logger.info(f"Generating quality report for {len(data)} records")
        
        if not data:
            return DataQualityReport(
                total_records=0,
                missing_records=0,
                anomaly_records=0,
                coverage_percentage=0.0,
                time_range=(datetime.now(), datetime.now()),
                issues=[]
            )
        
        # 运行所有验证
        completeness_result = self.validate_data_completeness(data)
        sanity_result = self.validate_price_sanity(data)
        
        # 收集所有问题
        all_issues = completeness_result.issues + sanity_result.issues
        
        # 计算统计信息
        sorted_data = sorted(data, key=lambda x: x.timestamp)
        actual_start = sorted_data[0].timestamp
        actual_end = sorted_data[-1].timestamp
        
        # 使用提供的日期范围或实际数据范围
        range_start = start_date or actual_start
        range_end = end_date or actual_end
        
        # 计算覆盖率
        total_hours = int((range_end - range_start).total_seconds() / 3600)
        actual_records = len(data)
        expected_records = total_hours  # 假设每小时一条记录
        
        coverage_percentage = min(1.0, actual_records / expected_records) if expected_records > 0 else 0.0
        
        # 计算缺失和异常记录数
        missing_records = max(0, expected_records - actual_records)
        anomaly_records = len([
            issue for issue in all_issues 
            if issue.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]
        ])
        
        report = DataQualityReport(
            total_records=len(data),
            missing_records=missing_records,
            anomaly_records=anomaly_records,
            coverage_percentage=coverage_percentage,
            time_range=(actual_start, actual_end),
            issues=all_issues,
            generated_at=datetime.now()
        )
        
        logger.info(
            f"Quality report generated: "
            f"score={report.quality_score:.1f}, "
            f"coverage={coverage_percentage:.1%}, "
            f"issues={len(all_issues)}"
        )
        
        return report
    
    def get_coverage_stats(
        self,
        data: List[HistoricalOptionData],
        start_date: datetime,
        end_date: datetime
    ) -> CoverageStats:
        """
        获取数据覆盖率统计
        
        Args:
            data: 历史数据列表
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            覆盖率统计
        """
        logger.info(f"Calculating coverage stats from {start_date} to {end_date}")
        
        if not data:
            return CoverageStats(
                start_date=start_date,
                end_date=end_date,
                total_days=0,
                days_with_data=0,
                coverage_percentage=0.0,
                missing_dates=[],
                strikes_covered=[],
                expiries_covered=[]
            )
        
        # 按日期分组
        dates_with_data = set()
        strikes = set()
        expiries = set()
        
        for d in data:
            dates_with_data.add(d.timestamp.date())
            strikes.add(d.strike_price)
            expiries.add(d.expiry_date.date())
        
        # 计算总天数
        total_days = (end_date - start_date).days + 1
        days_with_data = len(dates_with_data)
        
        # 找出缺失的日期
        all_dates = {start_date.date() + timedelta(days=i) for i in range(total_days)}
        missing_dates = sorted([
            datetime.combine(d, datetime.min.time()) 
            for d in (all_dates - dates_with_data)
        ])
        
        coverage_percentage = days_with_data / total_days if total_days > 0 else 0.0
        
        stats = CoverageStats(
            start_date=start_date,
            end_date=end_date,
            total_days=total_days,
            days_with_data=days_with_data,
            coverage_percentage=coverage_percentage,
            missing_dates=missing_dates[:100],  # 限制返回数量
            strikes_covered=sorted(strikes),
            expiries_covered=sorted([datetime.combine(d, datetime.min.time()) for d in expiries])
        )
        
        logger.info(
            f"Coverage stats: {days_with_data}/{total_days} days "
            f"({coverage_percentage:.1%}), "
            f"{len(strikes)} strikes, {len(expiries)} expiries"
        )
        
        return stats
