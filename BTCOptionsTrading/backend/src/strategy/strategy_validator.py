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
        """
        验证执行价配置的合理性（任务11.3：配置合理性检查）
        """
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
                            f"❌ 宽跨式策略配置错误：看涨期权执行价(${call_strike:.2f})必须高于看跌期权执行价(${put_strike:.2f})"
                        ))
                    elif call_strike - put_strike < 1000:
                        self.warnings.append(ValidationError(
                            "legs",
                            f"⚠️ 宽跨式策略的执行价差距较小(${call_strike - put_strike:.2f})，可能更适合使用跨式策略。",
                            "warning"
                        ))
        
        elif strategy_type == "iron_condor":
            # 铁鹰策略：执行价应该按顺序排列
            if len(legs) == 4:
                strikes = []
                for i, leg in enumerate(legs):
                    strike = float(leg["option_contract"]["strike_price"])
                    option_type = leg["option_contract"]["option_type"]
                    action = leg["action"]
                    strikes.append((strike, option_type, action, i))
                
                strikes.sort(key=lambda x: x[0])
                
                # 检查顺序：低put, 高put, 低call, 高call
                if strikes[0][1] != "put" or strikes[1][1] != "put":
                    self.errors.append(ValidationError(
                        "legs",
                        "❌ 铁鹰策略配置错误：最低的两个执行价必须是看跌期权"
                    ))
                
                if strikes[2][1] != "call" or strikes[3][1] != "call":
                    self.errors.append(ValidationError(
                        "legs",
                        "❌ 铁鹰策略配置错误：最高的两个执行价必须是看涨期权"
                    ))
                
                # 检查买卖方向：应该是 买put, 卖put, 卖call, 买call
                expected_actions = ["buy", "sell", "sell", "buy"]
                actual_actions = [s[2] for s in strikes]
                
                if actual_actions != expected_actions:
                    self.errors.append(ValidationError(
                        "legs",
                        f"❌ 铁鹰策略配置错误：买卖方向不正确。应该是：买入低执行价看跌、卖出高执行价看跌、卖出低执行价看涨、买入高执行价看涨"
                    ))
                
                # 检查价差宽度是否合理
                put_spread = strikes[1][0] - strikes[0][0]
                call_spread = strikes[3][0] - strikes[2][0]
                
                if abs(put_spread - call_spread) > 500:
                    self.warnings.append(ValidationError(
                        "legs",
                        f"⚠️ 铁鹰策略的看跌价差(${put_spread:.2f})和看涨价差(${call_spread:.2f})不相等。标准铁鹰策略通常使用相等的价差。",
                        "warning"
                    ))
                
                # 检查中间区间是否合理
                middle_gap = strikes[2][0] - strikes[1][0]
                if middle_gap < 1000:
                    self.warnings.append(ValidationError(
                        "legs",
                        f"⚠️ 铁鹰策略的中间区间较窄(${middle_gap:.2f})，盈利区间较小，风险较高。",
                        "warning"
                    ))
        
        elif strategy_type == "butterfly":
            # 蝶式策略：中间执行价应该在两侧之间
            if len(legs) == 3:
                strikes_with_action = [(float(leg["option_contract"]["strike_price"]), leg["action"]) for leg in legs]
                strikes_with_action.sort(key=lambda x: x[0])
                
                strikes = [s[0] for s in strikes_with_action]
                actions = [s[1] for s in strikes_with_action]
                
                # 检查买卖方向：应该是 买, 卖, 买
                if actions != ["buy", "sell", "buy"]:
                    self.errors.append(ValidationError(
                        "legs",
                        "❌ 蝶式策略配置错误：买卖方向应该是：买入低执行价、卖出中间执行价、买入高执行价"
                    ))
                
                # 检查是否等距
                wing_width_1 = strikes[1] - strikes[0]
                wing_width_2 = strikes[2] - strikes[1]
                
                if abs(wing_width_1 - wing_width_2) > 100:
                    self.warnings.append(ValidationError(
                        "legs",
                        f"⚠️ 蝶式策略的翼宽不相等：左翼${wing_width_1:.2f} vs 右翼${wing_width_2:.2f}。标准蝶式策略应该使用相等的翼宽。",
                        "warning"
                    ))
                
                # 检查翼宽是否合理
                if wing_width_1 < 500:
                    self.warnings.append(ValidationError(
                        "legs",
                        f"⚠️ 蝶式策略的翼宽较小(${wing_width_1:.2f})，盈利区间较窄。",
                        "warning"
                    ))
        
        elif strategy_type == "straddle":
            # 跨式策略：看涨和看跌应该使用相同的执行价
            if len(legs) == 2:
                strikes = [float(leg["option_contract"]["strike_price"]) for leg in legs]
                if abs(strikes[0] - strikes[1]) > 0.01:
                    self.errors.append(ValidationError(
                        "legs",
                        f"❌ 跨式策略配置错误：看涨和看跌期权必须使用相同的执行价。当前：${strikes[0]:.2f} vs ${strikes[1]:.2f}"
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
        """
        验证数量的合理性（任务11.3：配置合理性检查）
        """
        quantities = [int(leg["quantity"]) for leg in legs]
        
        # 检查是否有负数数量
        if any(q < 0 for q in quantities):
            self.errors.append(ValidationError(
                "legs",
                "❌ 数量不能为负数"
            ))
        
        # 检查是否有零数量
        if any(q == 0 for q in quantities):
            self.errors.append(ValidationError(
                "legs",
                "❌ 数量不能为零"
            ))
        
        # 检查是否有异常大的数量
        max_quantity = max(quantities) if quantities else 0
        if max_quantity > 100:
            self.warnings.append(ValidationError(
                "legs",
                f"⚠️ 策略中有较大的数量({max_quantity})。请确认这是预期的，大数量会增加交易成本和滑点风险。",
                "warning"
            ))
        
        # 检查数量比例是否合理（对于多腿策略）
        if len(quantities) > 1:
            # 对于蝶式策略，中间腿的数量应该是两侧的2倍
            if len(quantities) == 3:
                sorted_quantities = sorted(quantities)
                if sorted_quantities[2] != sorted_quantities[0] * 2 and sorted_quantities[2] != sorted_quantities[1] * 2:
                    self.warnings.append(ValidationError(
                        "legs",
                        f"⚠️ 蝶式策略的数量比例不标准。标准蝶式策略中间腿的数量应该是两侧的2倍。当前数量：{quantities}",
                        "warning"
                    ))
            
            # 检查数量是否相等（对于跨式、宽跨式）
            if len(quantities) == 2:
                if quantities[0] != quantities[1]:
                    self.warnings.append(ValidationError(
                        "legs",
                        f"⚠️ 两腿策略的数量不相等({quantities[0]} vs {quantities[1]})。这可能导致不对称的风险暴露。",
                        "warning"
                    ))
    
    def _check_risk_levels(self, legs: List[Dict]):
        """检查风险水平（任务11.2：风险阈值检查）"""
        # 简化的风险检查：估算最大损失
        # 这里只是一个粗略的估计，实际应该使用更复杂的风险计算
        
        total_cost = Decimal("0")
        max_potential_loss = Decimal("0")
        
        for leg in legs:
            # 假设每个期权的平均价格为执行价的5%
            strike = Decimal(str(leg["option_contract"]["strike_price"]))
            quantity = int(leg["quantity"])
            action = leg["action"]
            
            estimated_price = strike * Decimal("0.05")
            
            if action == "buy":
                # 买入期权：最大损失是权利金
                leg_cost = estimated_price * quantity
                total_cost += leg_cost
                max_potential_loss += leg_cost
            else:  # sell
                # 卖出期权：收入权利金，但有潜在的无限损失风险
                total_cost -= estimated_price * quantity
                # 对于卖出期权，估算最大损失为执行价的50%
                max_potential_loss += strike * Decimal("0.5") * quantity
        
        # 风险阈值检查
        risk_threshold = self.initial_capital * Decimal("0.5")
        
        # 检查1：估算成本是否超过初始资金的50%
        if total_cost > risk_threshold:
            self.warnings.append(ValidationError(
                "risk",
                f"⚠️ 高风险警告：策略的估算成本(${float(total_cost):.2f})超过初始资金的50%(${float(risk_threshold):.2f})。",
                "warning"
            ))
        
        # 检查2：最大潜在损失是否超过初始资金的50%
        if max_potential_loss > risk_threshold:
            self.warnings.append(ValidationError(
                "risk",
                f"⚠️ 高风险警告：策略的最大潜在损失(${float(max_potential_loss):.2f})超过初始资金的50%(${float(risk_threshold):.2f})。建议降低数量或选择风险较低的策略。",
                "warning"
            ))
        
        # 检查3：是否包含卖出期权（裸卖）
        has_naked_sell = any(leg["action"] == "sell" for leg in legs)
        if has_naked_sell:
            self.warnings.append(ValidationError(
                "risk",
                "⚠️ 策略包含卖出期权，存在潜在的无限损失风险。请确保您了解相关风险。",
                "warning"
            ))
    
    def validate_real_time(
        self,
        strategy_type: str,
        legs: List[Dict],
        name: str = None,
        spot_price: float = None
    ) -> Tuple[bool, List[Dict], List[Dict]]:
        """
        实时参数验证（任务11.1）
        提供更详细的实时验证反馈
        
        Args:
            strategy_type: 策略类型
            legs: 策略腿列表
            name: 策略名称（可选）
            spot_price: 当前标的价格（可选，用于更精确的风险评估）
            
        Returns:
            (is_valid, errors, warnings)
        """
        # 先执行基本验证
        is_valid, errors, warnings = self.validate_strategy(strategy_type, legs, name)
        
        # 如果提供了标的价格，进行更详细的检查
        if spot_price and is_valid:
            self._validate_strike_reasonableness(legs, spot_price)
            self._check_moneyness_warnings(legs, spot_price)
        
        return len(self.errors) == 0, [e.to_dict() for e in self.errors], [w.to_dict() for w in self.warnings]
    
    def _validate_strike_reasonableness(self, legs: List[Dict], spot_price: float):
        """
        验证执行价的合理性（任务11.3：配置合理性检查）
        
        Args:
            legs: 策略腿列表
            spot_price: 当前标的价格
        """
        for i, leg in enumerate(legs):
            strike = float(leg["option_contract"]["strike_price"])
            
            # 检查执行价是否偏离标的价格太远
            deviation = abs(strike - spot_price) / spot_price
            
            if deviation > 0.5:  # 偏离超过50%
                self.warnings.append(ValidationError(
                    f"legs[{i}].strike_price",
                    f"执行价${strike:.2f}偏离当前标的价格${spot_price:.2f}超过50%。这可能是深度虚值期权，流动性可能较差。",
                    "warning"
                ))
            
            # 检查执行价是否为合理的整数倍（BTC通常是1000的倍数）
            if strike % 1000 != 0 and strike > 10000:
                self.warnings.append(ValidationError(
                    f"legs[{i}].strike_price",
                    f"执行价${strike:.2f}不是1000的整数倍。标准BTC期权执行价通常是1000的倍数。",
                    "warning"
                ))
    
    def _check_moneyness_warnings(self, legs: List[Dict], spot_price: float):
        """
        检查期权的价值状态并提供警告
        
        Args:
            legs: 策略腿列表
            spot_price: 当前标的价格
        """
        for i, leg in enumerate(legs):
            strike = float(leg["option_contract"]["strike_price"])
            option_type = leg["option_contract"]["option_type"]
            action = leg["action"]
            
            # 判断期权的价值状态
            if option_type == "call":
                if strike < spot_price * 0.9:  # 深度实值
                    moneyness = "深度实值"
                elif strike < spot_price:  # 实值
                    moneyness = "实值"
                elif strike <= spot_price * 1.1:  # 平值
                    moneyness = "平值"
                elif strike <= spot_price * 1.3:  # 虚值
                    moneyness = "虚值"
                else:  # 深度虚值
                    moneyness = "深度虚值"
            else:  # put
                if strike > spot_price * 1.1:  # 深度实值
                    moneyness = "深度实值"
                elif strike > spot_price:  # 实值
                    moneyness = "实值"
                elif strike >= spot_price * 0.9:  # 平值
                    moneyness = "平值"
                elif strike >= spot_price * 0.7:  # 虚值
                    moneyness = "虚值"
                else:  # 深度虚值
                    moneyness = "深度虚值"
            
            # 对深度虚值期权提供警告
            if moneyness == "深度虚值":
                self.warnings.append(ValidationError(
                    f"legs[{i}]",
                    f"腿{i+1}是{moneyness}{option_type}期权（执行价${strike:.2f}，标的${spot_price:.2f}）。深度虚值期权到期归零的概率较高。",
                    "warning"
                ))
