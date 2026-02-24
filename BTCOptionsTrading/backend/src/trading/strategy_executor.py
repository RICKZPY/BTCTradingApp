"""
策略执行器
负责执行预配置的期权策略
"""
import asyncio
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime
import logging
from ..core.models import Strategy, StrategyLeg, ActionType
from .deribit_trader import DeribitTrader

logger = logging.getLogger(__name__)


class StrategyExecutor:
    """策略执行器"""
    
    def __init__(self, trader: DeribitTrader):
        """
        初始化执行器
        
        Args:
            trader: Deribit交易客户端
        """
        self.trader = trader
        self.execution_log = []
    
    async def execute_strategy(
        self,
        strategy: Strategy,
        use_market_order: bool = False
    ) -> Dict:
        """
        执行策略
        
        Args:
            strategy: 要执行的策略
            use_market_order: 是否使用市价单
            
        Returns:
            执行结果
        """
        logger.info(f"开始执行策略: {strategy.name} (ID: {strategy.id})")
        
        results = {
            "strategy_id": str(strategy.id),
            "strategy_name": strategy.name,
            "execution_time": datetime.now().isoformat(),
            "legs": [],
            "success": True,
            "errors": []
        }
        
        # 逐个执行策略腿
        for i, leg in enumerate(strategy.legs):
            logger.info(f"执行第 {i+1}/{len(strategy.legs)} 腿")
            
            try:
                leg_result = await self._execute_leg(leg, use_market_order)
                results["legs"].append(leg_result)
                
                if not leg_result.get("success"):
                    results["success"] = False
                    results["errors"].append(f"腿 {i+1} 执行失败")
                    
            except Exception as e:
                logger.error(f"执行腿 {i+1} 时出错: {e}")
                results["success"] = False
                results["errors"].append(f"腿 {i+1} 异常: {str(e)}")
                results["legs"].append({
                    "leg_index": i,
                    "success": False,
                    "error": str(e)
                })
        
        # 记录执行日志
        self.execution_log.append(results)
        
        logger.info(f"策略执行完成: {strategy.name}, 成功: {results['success']}")
        return results
    
    async def _execute_leg(
        self,
        leg: StrategyLeg,
        use_market_order: bool
    ) -> Dict:
        """
        执行单个策略腿
        
        Args:
            leg: 策略腿
            use_market_order: 是否使用市价单
            
        Returns:
            执行结果
        """
        instrument_name = leg.option_contract.instrument_name
        amount = abs(leg.quantity)
        
        # 确定价格和订单类型
        # 快速交易默认使用市价单以确保成交
        price = None
        order_type = "market"
        
        # 执行买入或卖出
        if leg.action == ActionType.BUY:
            order = await self.trader.buy(
                instrument_name=instrument_name,
                amount=amount,
                price=price,
                order_type=order_type
            )
        else:
            order = await self.trader.sell(
                instrument_name=instrument_name,
                amount=amount,
                price=price,
                order_type=order_type
            )
        
        if order:
            return {
                "success": True,
                "instrument": instrument_name,
                "action": leg.action.value,
                "quantity": leg.quantity,
                "order_id": order.get("order", {}).get("order_id"),
                "order_state": order.get("order", {}).get("order_state"),
                "filled_amount": order.get("order", {}).get("filled_amount", 0),
                "average_price": order.get("order", {}).get("average_price")
            }
        else:
            return {
                "success": False,
                "instrument": instrument_name,
                "action": leg.action.value,
                "quantity": leg.quantity,
                "error": "订单提交失败"
            }
    
    async def close_strategy_positions(self, strategy: Strategy) -> Dict:
        """
        平掉策略的所有持仓
        
        Args:
            strategy: 策略
            
        Returns:
            平仓结果
        """
        logger.info(f"开始平仓策略: {strategy.name}")
        
        results = {
            "strategy_id": str(strategy.id),
            "strategy_name": strategy.name,
            "close_time": datetime.now().isoformat(),
            "legs": [],
            "success": True
        }
        
        for leg in strategy.legs:
            try:
                close_result = await self.trader.close_position(
                    leg.option_contract.instrument_name
                )
                
                results["legs"].append({
                    "instrument": leg.option_contract.instrument_name,
                    "success": close_result is not None,
                    "result": close_result
                })
                
            except Exception as e:
                logger.error(f"平仓失败: {e}")
                results["success"] = False
                results["legs"].append({
                    "instrument": leg.option_contract.instrument_name,
                    "success": False,
                    "error": str(e)
                })
        
        return results
    
    def get_execution_log(self) -> List[Dict]:
        """获取执行日志"""
        return self.execution_log
