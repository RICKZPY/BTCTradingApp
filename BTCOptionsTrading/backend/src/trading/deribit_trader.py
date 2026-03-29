"""
Deribit交易接口
支持测试环境和生产环境的期权交易
"""
import asyncio
import aiohttp
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DeribitTrader:
    """Deribit交易客户端"""
    
    # API端点
    TEST_API = "https://test.deribit.com/api/v2"
    PROD_API = "https://www.deribit.com/api/v2"
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        """
        初始化交易客户端
        
        Args:
            api_key: API密钥
            api_secret: API密钥
            testnet: 是否使用测试网络
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.base_url = self.TEST_API if testnet else self.PROD_API
        self.access_token = None
        self.refresh_token = None
        
    async def authenticate(self) -> bool:
        """
        认证并获取访问令牌
        
        Returns:
            是否认证成功
        """
        url = f"{self.base_url}/public/auth"
        params = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.api_secret
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    data = await resp.json()
                    if 'result' in data:
                        self.access_token = data['result']['access_token']
                        self.refresh_token = data['result']['refresh_token']
                        logger.info("Deribit认证成功")
                        return True
                    else:
                        logger.error(f"认证失败: {data}")
                        return False
        except Exception as e:
            logger.error(f"认证异常: {e}")
            return False
    async def test_connection(self) -> bool:
        """
        测试API连接

        Returns:
            连接是否成功
        """
        try:
            # 尝试认证来测试连接
            success = await self.authenticate()
            if success:
                logger.info("API连接测试成功")
            else:
                logger.error("API连接测试失败")
            return success
        except Exception as e:
            logger.error(f"API连接测试异常: {e}")
            return False
    
    async def _make_request(self, method: str, params: Dict) -> Optional[Dict]:
        """
        发送API请求
        
        Args:
            method: API方法名
            params: 请求参数
            
        Returns:
            响应数据
        """
        if not self.access_token:
            if not await self.authenticate():
                return None
        
        url = f"{self.base_url}/private/{method}"
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers) as resp:
                    data = await resp.json()
                    if 'result' in data:
                        return data['result']
                    else:
                        # 检查是否是令牌过期错误
                        if 'error' in data and data['error'].get('code') == 13009:
                            logger.warning("访问令牌过期，尝试重新认证...")
                            if await self.authenticate():
                                # 重新认证成功，重试请求
                                headers["Authorization"] = f"Bearer {self.access_token}"
                                async with session.get(url, params=params, headers=headers) as retry_resp:
                                    retry_data = await retry_resp.json()
                                    if 'result' in retry_data:
                                        return retry_data['result']
                                    else:
                                        logger.error(f"重试后仍然失败: {retry_data}")
                                        return None
                            else:
                                logger.error("重新认证失败")
                                return None
                        else:
                            logger.error(f"请求失败: {data}")
                            return None
        except Exception as e:
            logger.error(f"请求异常: {e}")
            return None
    
    async def get_account_summary(self, currency: str = "BTC") -> Optional[Dict]:
        """
        获取账户摘要
        
        Args:
            currency: 币种
            
        Returns:
            账户信息
        """
        return await self._make_request("get_account_summary", {"currency": currency})
    
    async def get_positions(self, currency: str = "BTC") -> Optional[List[Dict]]:
        """
        获取当前持仓
        
        Args:
            currency: 币种
            
        Returns:
            持仓列表
        """
        result = await self._make_request("get_positions", {"currency": currency})
        return result if result else []
    
    async def buy(
        self,
        instrument_name: str,
        amount: float,
        price: Optional[float] = None,
        order_type: str = "market"
    ) -> Optional[Dict]:
        """
        买入期权
        
        Args:
            instrument_name: 合约名称
            amount: 数量
            price: 限价（None为市价）
            order_type: 订单类型 (limit/market)，默认为market以确保快速成交
            
        Returns:
            订单信息
        """
        params = {
            "instrument_name": instrument_name,
            "amount": amount,
            "type": order_type
        }
        
        if price and order_type == "limit":
            params["price"] = price
        
        logger.info(f"买入订单: {instrument_name}, 数量: {amount}, 类型: {order_type}, 价格: {price}")
        return await self._make_request("buy", params)
    
    async def sell(
        self,
        instrument_name: str,
        amount: float,
        price: Optional[float] = None,
        order_type: str = "market"
    ) -> Optional[Dict]:
        """
        卖出期权
        
        Args:
            instrument_name: 合约名称
            amount: 数量
            price: 限价（None为市价）
            order_type: 订单类型 (limit/market)，默认为market以确保快速成交
            
        Returns:
            订单信息
        """
        params = {
            "instrument_name": instrument_name,
            "amount": amount,
            "type": order_type
        }
        
        if price and order_type == "limit":
            params["price"] = price
        
        logger.info(f"卖出订单: {instrument_name}, 数量: {amount}, 类型: {order_type}, 价格: {price}")
        return await self._make_request("sell", params)
    
    async def get_order_state(self, order_id: str) -> Optional[Dict]:
        """
        获取订单状态
        
        Args:
            order_id: 订单ID
            
        Returns:
            订单状态
        """
        return await self._make_request("get_order_state", {"order_id": order_id})
    
    async def cancel_order(self, order_id: str) -> Optional[Dict]:
        """
        取消订单
        
        Args:
            order_id: 订单ID
            
        Returns:
            取消结果
        """
        logger.info(f"取消订单: {order_id}")
        return await self._make_request("cancel", {"order_id": order_id})
    
    async def create_combo(self, call_instrument: str, put_instrument: str, amount: float) -> Optional[str]:
        """
        创建 Straddle Combo instrument
        
        Deribit combo 下单两步：
        1. create_combo → 得到 combo_id（如 BTC-STRD-29OCT21-3000）
        2. buy(combo_id) → 实际下单，Deribit 界面显示为组合持仓
        
        Args:
            call_instrument: 看涨合约名，如 BTC-29MAR26-70000-C
            put_instrument:  看跌合约名，如 BTC-29MAR26-70000-P
            amount: 每条腿的数量（BTC）
            
        Returns:
            combo_id 字符串，失败返回 None
        """
        params = {
            "trades": [
                {"instrument_name": call_instrument, "amount": amount, "direction": "buy"},
                {"instrument_name": put_instrument,  "amount": amount, "direction": "buy"},
            ]
        }
        logger.info(f"创建 Straddle Combo: {call_instrument} + {put_instrument}")
        result = await self._make_request("create_combo", params)
        if result and "instrument_name" in result:
            combo_id = result["instrument_name"]
            logger.info(f"Combo 创建成功: {combo_id}")
            return combo_id
        logger.error(f"Combo 创建失败: {result}")
        return None

    async def buy_combo(self, combo_id: str, amount: float) -> Optional[Dict]:
        """
        买入已创建的 Combo（straddle 组合下单）
        
        Args:
            combo_id: create_combo 返回的 instrument_name
            amount:   数量（BTC，对应每条腿的数量）
            
        Returns:
            订单信息
        """
        logger.info(f"Combo 下单: {combo_id}, 数量: {amount}")
        return await self._make_request("buy", {
            "instrument_name": combo_id,
            "amount": amount,
            "type": "market"
        })
        """
        平仓
        
        Args:
            instrument_name: 合约名称
            
        Returns:
            平仓结果
        """
        logger.info(f"平仓: {instrument_name}")
        return await self._make_request("close_position", {
            "instrument_name": instrument_name,
            "type": "market"
        })
