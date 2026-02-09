"""
自定义异常类定义
定义系统中使用的所有异常类型
"""

from typing import Optional, Dict, Any


class BTCOptionsError(Exception):
    """基础异常类"""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}


class OptionsCalculationError(BTCOptionsError):
    """期权计算相关错误"""
    pass


class DataValidationError(BTCOptionsError):
    """数据验证错误"""
    pass


class APIConnectionError(BTCOptionsError):
    """API连接错误"""
    pass


class DeribitAPIError(APIConnectionError):
    """Deribit API特定错误"""
    
    def __init__(
        self, 
        message: str, 
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, "DERIBIT_API_ERROR")
        self.status_code = status_code
        self.response_data = response_data or {}


class ConfigurationError(BTCOptionsError):
    """配置错误"""
    pass


class DatabaseError(BTCOptionsError):
    """数据库错误"""
    pass


class StrategyValidationError(BTCOptionsError):
    """策略验证错误"""
    pass


class RiskLimitExceededError(BTCOptionsError):
    """风险限额超出错误"""
    pass


class InsufficientDataError(BTCOptionsError):
    """数据不足错误"""
    pass


class BacktestError(BTCOptionsError):
    """回测错误"""
    pass


class VolatilityCalculationError(OptionsCalculationError):
    """波动率计算错误"""
    pass


class GreeksCalculationError(OptionsCalculationError):
    """希腊字母计算错误"""
    pass


class PricingModelError(OptionsCalculationError):
    """定价模型错误"""
    pass


class ConvergenceError(OptionsCalculationError):
    """数值收敛错误"""
    pass


# 错误处理装饰器
def handle_calculation_errors(func):
    """处理计算错误的装饰器"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (ValueError, ZeroDivisionError, ArithmeticError) as e:
            raise OptionsCalculationError(
                f"计算错误在 {func.__name__}: {str(e)}",
                error_code="CALCULATION_ERROR",
                context={"function": func.__name__, "args": str(args)[:100]}
            )
        except Exception as e:
            raise BTCOptionsError(
                f"未预期的错误在 {func.__name__}: {str(e)}",
                error_code="UNEXPECTED_ERROR",
                context={"function": func.__name__}
            )
    return wrapper


def handle_api_errors(func):
    """处理API错误的装饰器"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except APIConnectionError:
            # 重新抛出API连接错误
            raise
        except Exception as e:
            raise APIConnectionError(
                f"API调用失败在 {func.__name__}: {str(e)}",
                error_code="API_CALL_FAILED",
                context={"function": func.__name__}
            )
    return wrapper


def handle_validation_errors(func):
    """处理验证错误的装饰器"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (TypeError, ValueError) as e:
            raise DataValidationError(
                f"数据验证失败在 {func.__name__}: {str(e)}",
                error_code="VALIDATION_FAILED",
                context={"function": func.__name__}
            )
        except Exception as e:
            raise BTCOptionsError(
                f"验证过程中发生错误在 {func.__name__}: {str(e)}",
                error_code="VALIDATION_ERROR",
                context={"function": func.__name__}
            )
    return wrapper