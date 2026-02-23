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
        order_type: str = "limit"
    ) -> Optional[Dict]:
        """
        买入期权
        
        Args:
            instrument_name: 合约名称
            amount: 数量
            price: 限价（None为市价）
            order_type: 订单类型 (limit/market)
            
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
        
        logger.info(f"买入订单: {instrument_name}, 数量: {amount}, 价格: {price}")
        return await self._make_request("buy", params)
    
    async def sell(
        self,
        instrument_name: str,
        amount: float,
        price: Optional[float] = None,
        order_type: str = "limit"
    ) -> Optional[Dict]:
        """
        卖出期权
        
        Args:
            instrument_name: 合约名称
            amount: 数量
            price: 限价（None为市价）
            order_type: 订单类型 (limit/market)
            
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
        
        logger.info(f"卖出订单: {instrument_name}, 数量: {amount}, 价格: {price}")
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
    
    async def close_position(self, instrument_name: str) -> Optional[Dict]:
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
