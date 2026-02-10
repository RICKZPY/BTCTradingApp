"""
策略验证器
提供策略配置的验证逻辑
"""

from typing import List, Dict, Tuple
from decimal import Decimal
from datetime import datetime

from src.core.models import StrategyType, OptionType, ActionType
from src.config.logging_config import get_logger

logger = get_logger(__name__)


class ValidationError:
    """验证错误"""
    def __init__(self, field: str, message: str, severity: str = "error"):
        self.field = field
        self.message = message
        self.severity = severity  # "error" or "warning"
    
    def to_dict(self) -> Dict:
        return {
            "field": self.field,
            "message": self.message,
            "severity": self.severity
        }


class StrategyValidator:
    """策略验证器"""
    
    def __init__(self, initial_capital: Decimal = Decimal("100000")):
        """
        初始化验证器
        
        Args:
            initial_capital: 初始资金，用于风险检查
        """
        self.initial_capital = initial_capital
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []
    
    def validate_strategy(
        self,
        strategy_type: str,
        legs: List[Dict],
        name: str = None
    ) -> Tuple[bool, List[Dict], List[Dict]]:
        """
        验证策略配置
        
        Args:
            strategy_type: 策略类型
            legs: 策略腿列表
            name: 策略名称（可选）
            
        Returns:
            (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []
        
        # 验证策略名称
        if name:
            self._validate_name(name)
        
        # 验证策略类型
        if not self._validate_strategy_type(strategy_type):
            return False, [e.to_dict() for e in self.errors], [w.to_dict() for w in self.warnings]
        
        # 验证策略腿
        if not self._validate_legs(legs):
            return False, [e.to_dict() for e in self.errors], [w.to_dict() for w in self.warnings]
        
        # 验证策略类型与腿数量的匹配
        if not self._validate_strategy_structure(strategy_type, legs):
            return False, [e.to_dict() for e in self.errors], [w.to_dict() for w in self.warnings]
        
        # 验证执行价配置的合理性
        self._validate_strike_configuration(strategy_type, legs)
        
        # 验证到期日一致性
        self._validate_expiry_consistency(legs)
        
        # 验证数量的合理性
        self._validate_quantities(legs)
        
        # 风险检查
        self._check_risk_levels(legs)
        
        is_valid = len(self.errors) == 0
        return is_valid, [e.to_dict() for e in self.errors], [w.to_dict() for w in self.warnings]
    
    def _validate_name(self, name: str):
        """验证策略名称"""
        if not name or len(name.strip()) == 0:
            self.errors.append(ValidationError("name", "策略名称不能为空"))
        elif len(name) > 100:
            self.errors.append(ValidationError("name", "策略名称不能超过100个字符"))
    
    def _validate_strategy_type(self, strategy_type: str) -> bool:
        """验证策略类型"""
        valid_types = ["single_leg", "straddle", "strangle", "iron_condor", "butterfly"]
        if strategy_type not in valid_types:
            self.errors.append(ValidationError(
                "strategy_type",
                f"无效的策略类型: {strategy_type}。有效类型: {', '.join(valid_types)}"
            ))
            return False
        return True
    
    def _validate_legs(self, legs: List[Dict]) -> bool:
        """验证策略腿"""
        if not legs or len(legs) == 0:
            self.errors.append(ValidationError("legs", "策略至少需要一个腿"))
            return False
        
        for i, leg in enumerate(legs):
            # 验证必需字段
            if "option_contract" not in leg:
                self.errors.append(ValidationError(f"legs[{i}]", "缺少option_contract字段"))
                continue
            
            if "action" not in leg:
                self.errors.append(ValidationError(f"legs[{i}]", "缺少action字段"))
                continue
            
            if "quantity" not in leg:
                self.errors.append(ValidationError(f"legs[{i}]", "缺少quantity字段"))
                continue
            
            # 验证期权合约
            contract = leg["option_contract"]
            if not self._validate_option_contract(contract, i):
                continue
            
            # 验证买卖方向
            if leg["action"] not in ["buy", "sell"]:
                self.errors.append(ValidationError(
                    f"legs[{i}].action",
                    f"无效的买卖方向: {leg['action']}。必须是'buy'或'sell'"
                ))
            
            # 验证数量
            try:
                quantity = int(leg["quantity"])
                if quantity <= 0:
                    self.errors.append(ValidationError(
                        f"legs[{i}].quantity",
                        "数量必须大于0"
                    ))
            except (ValueError, TypeError):
                self.errors.append(ValidationError(
                    f"legs[{i}].quantity",
                    "数量必须是有效的整数"
                ))
        
        return len(self.errors) == 0
    
    def _validate_option_contract(self, contract: Dict, leg_index: int) -> bool:
        """验证期权合约"""
        required_fields = ["strike_price", "option_type", "expiration_date", "underlying"]
        
        for field in required_fields:
            if field not in contract:
                self.errors.append(ValidationError(
                    f"legs[{leg_index}].option_contract.{field}",
                    f"缺少{field}字段"
                ))
                return False
        
        # 验证期权类型
        if contract["option_type"] not in ["call", "put"]:
            self.errors.append(ValidationError(
                f"legs[{leg_index}].option_contract.option_type",
                f"无效的期权类型: {contract['option_type']}。必须是'call'或'put'"
            ))
        
        # 验证执行价
        try:
            strike = float(contract["strike_price"])
            if strike <= 0:
                self.errors.append(ValidationError(
                    f"legs[{leg_index}].option_contract.strike_price",
                    "执行价必须大于0"
                ))
        except (ValueError, TypeError):
            self.errors.append(ValidationError(
                f"legs[{leg_index}].option_contract.strike_price",
                "执行价必须是有效的数字"
            ))
        
        # 验证到期日
        try:
            expiry = datetime.fromisoformat(contract["expiration_date"].replace('Z', '+00:00'))
            if expiry <= datetime.now():
                self.errors.append(ValidationError(
                    f"legs[{leg_index}].option_contract.expiration_date",
                    "到期日必须是未来的日期"
                ))
        except (ValueError, TypeError):
            self.errors.append(ValidationError(
                f"legs[{leg_index}].option_contract.expiration_date",
                "到期日格式无效"
            ))
        
        return len(self.errors) == 0
    
    def _validate_strategy_structure(self, strategy_type: str, legs: List[Dict]) -> bool:
        """验证策略类型与腿数量的匹配"""
        expected_legs = {
            "single_leg": 1,
            "straddle": 2,
            "strangle": 2,
            "iron_condor": 4,
            "butterfly": 3
        }
        
        expected = expected_legs.get(strategy_type)
        actual = len(legs)
        
        if expected and actual != expected:
            self.errors.append(ValidationError(
                "legs",
                f"{strategy_type}策略需要{expected}个腿，但提供了{actual}个"
            ))
            return False
        
        return True
    
    def _validate_strike_configuration(self, strategy_type: str, legs: List[Dict]):
        """验证执行价配置的合理性"""
        if strategy_type == "strangle":
            # 宽跨式：看涨执行价应该高于看跌执行价
            if len(legs) == 2:
                call_leg = next((l for l in legs if l["option_contract"]["option_type"] == "call"), None)
                put_leg = next((l for l in legs if l["option_contract"]["option_type"] == "put"), None)
                
                if call_leg and put_leg:
                    call_strike = float(call_leg["option_contract"]["strike_price"])
                    put_strike = float(put_leg["option_contract"]["strike_price"])
                    
                    if call_strike <= put_strike:
                        self.errors.append(ValidationError(
                            "legs",
                            f"宽跨式策略中，看涨期权执行价({call_strike})应该高于看跌期权执行价({put_strike})"
                        ))
        
        elif strategy_type == "iron_condor":
            # 铁鹰策略：执行价应该按顺序排列
            if len(legs) == 4:
                strikes = []
                for leg in legs:
                    strike = float(leg["option_contract"]["strike_price"])
                    option_type = leg["option_contract"]["option_type"]
                    strikes.append((strike, option_type))
                
                strikes.sort(key=lambda x: x[0])
                
                # 检查顺序：低put, 高put, 低call, 高call
                if strikes[0][1] != "put" or strikes[1][1] != "put":
                    self.errors.append(ValidationError(
                        "legs",
                        "铁鹰策略的执行价顺序不正确：最低的两个执行价应该是看跌期权"
                    ))
                
                if strikes[2][1] != "call" or strikes[3][1] != "call":
                    self.errors.append(ValidationError(
                        "legs",
                        "铁鹰策略的执行价顺序不正确：最高的两个执行价应该是看涨期权"
                    ))
        
        elif strategy_type == "butterfly":
            # 蝶式策略：中间执行价应该在两侧之间
            if len(legs) == 3:
                strikes = [float(leg["option_contract"]["strike_price"]) for leg in legs]
                strikes.sort()
                
                # 检查是否等距
                wing_width_1 = strikes[1] - strikes[0]
                wing_width_2 = strikes[2] - strikes[1]
                
                if abs(wing_width_1 - wing_width_2) > 0.01:
                    self.warnings.append(ValidationError(
                        "legs",
                        f"蝶式策略的翼宽不相等：{wing_width_1} vs {wing_width_2}。这可能不是标准的蝶式策略",
                        "warning"
                    ))
    
    def _validate_expiry_consistency(self, legs: List[Dict]):
        """验证到期日一致性"""
        expiry_dates = set()
        for leg in legs:
            expiry = leg["option_contract"]["expiration_date"]
            expiry_dates.add(expiry)
        
        if len(expiry_dates) > 1:
            self.warnings.append(ValidationError(
                "legs",
                "策略中的期权合约有不同的到期日。这可能是日历价差策略",
                "warning"
            ))
    
    def _validate_quantities(self, legs: List[Dict]):
        """验证数量的合理性"""
        quantities = [int(leg["quantity"]) for leg in legs]
        
        # 检查是否有异常大的数量
        max_quantity = max(quantities)
        if max_quantity > 100:
            self.warnings.append(ValidationError(
                "legs",
                f"策略中有较大的数量({max_quantity})。请确认这是预期的",
                "warning"
            ))
    
    def _check_risk_levels(self, legs: List[Dict]):
        """检查风险水平"""
        # 简化的风险检查：估算最大损失
        # 这里只是一个粗略的估计，实际应该使用更复杂的风险计算
        
        total_cost = Decimal("0")
        for leg in legs:
            # 假设每个期权的平均价格为执行价的5%
            strike = Decimal(str(leg["option_contract"]["strike_price"]))
            quantity = int(leg["quantity"])
            action = leg["action"]
            
            estimated_price = strike * Decimal("0.05")
            
            if action == "buy":
                total_cost += estimated_price * quantity
            else:  # sell
                total_cost -= estimated_price * quantity
        
        # 如果估算成本超过初始资金的50%，发出警告
        if total_cost > self.initial_capital * Decimal("0.5"):
            self.warnings.append(ValidationError(
                "risk",
                f"策略的估算成本({total_cost})超过初始资金的50%。这是高风险策略",
                "warning"
            ))
