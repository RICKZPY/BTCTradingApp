"""
Deribit API连接器实现
提供与Deribit交易所的API交互功能
"""

import asyncio
import time
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Optional
from collections import deque

import httpx

from src.core.interfaces import IDeribitConnector
from src.core.models import (
    OptionContract, MarketData, HistoricalData, VolatilitySurface,
    OptionType
)
from src.core.exceptions import APIConnectionError, DataValidationError
from src.config.settings import settings
from src.config.logging_config import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """API请求限流器"""
    
    def __init__(self, max_requests: int, time_window: int):
        """
        初始化限流器
        
        Args:
            max_requests: 时间窗口内最大请求数
            time_window: 时间窗口（秒）
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
    
    async def acquire(self):
        """获取请求许可，如果超过限制则等待"""
        now = time.time()
        
        # 移除时间窗口外的请求记录
        while self.requests and self.requests[0] < now - self.time_window:
            self.requests.popleft()
        
        # 如果达到限制，等待
        if len(self.requests) >= self.max_requests:
            sleep_time = self.requests[0] + self.time_window - now
            if sleep_time > 0:
                logger.debug(f"Rate limit reached, sleeping for {sleep_time:.2f}s")
                await asyncio.sleep(sleep_time)
                return await self.acquire()
        
        # 记录本次请求
        self.requests.append(now)


class DeribitConnector(IDeribitConnector):
    """Deribit API连接器"""
    
    def __init__(self):
        """初始化连接器"""
        self.base_url = settings.deribit.base_url
        self.api_key = settings.deribit.api_key
        self.api_secret = settings.deribit.api_secret
        self.test_mode = settings.deribit.test_mode
        
        # 初始化HTTP客户端
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=30.0,
            headers={"Content-Type": "application/json"}
        )
        
        # 初始化限流器
        self.rate_limiter = RateLimiter(
            max_requests=settings.deribit.rate_limit_requests,
            time_window=settings.deribit.rate_limit_window
        )
        
        # 认证状态
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expires_at: Optional[float] = None
        
        logger.info(
            "Deribit connector initialized",
            base_url=self.base_url,
            test_mode=self.test_mode
        )
    
    async def _request(
        self, 
        method: str, 
        params: Optional[Dict] = None,
        retry_count: int = 0
    ) -> Dict:
        """
        发送API请求
        
        Args:
            method: API方法名
            params: 请求参数
            retry_count: 当前重试次数
            
        Returns:
            API响应数据
            
        Raises:
            APIConnectionError: API连接错误
        """
        await self.rate_limiter.acquire()
        
        request_data = {
            "jsonrpc": "2.0",
            "id": int(time.time() * 1000),
            "method": method,
            "params": params or {}
        }
        
        try:
            response = await self.client.post("/api/v2/public/", json=request_data)
            response.raise_for_status()
            
            data = response.json()
            
            if "error" in data:
                error_msg = data["error"].get("message", "Unknown error")
                logger.error(f"API error: {error_msg}", method=method, params=params)
                raise APIConnectionError(f"Deribit API error: {error_msg}")
            
            return data.get("result", {})
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error: {str(e)}", method=method)
            
            # 重试逻辑
            if retry_count < settings.deribit.max_retries:
                wait_time = settings.deribit.retry_delay * (2 ** retry_count)
                logger.info(f"Retrying in {wait_time}s (attempt {retry_count + 1})")
                await asyncio.sleep(wait_time)
                return await self._request(method, params, retry_count + 1)
            
            raise APIConnectionError(f"Failed to connect to Deribit API: {str(e)}")
    
    async def authenticate(self, api_key: str, api_secret: str) -> bool:
        """
        认证API连接
        
        Args:
            api_key: API密钥
            api_secret: API密钥
            
        Returns:
            认证是否成功
        """
        try:
            result = await self._request(
                "public/auth",
                {
                    "grant_type": "client_credentials",
                    "client_id": api_key,
                    "client_secret": api_secret
                }
            )
            
            self.access_token = result.get("access_token")
            self.refresh_token = result.get("refresh_token")
            self.token_expires_at = time.time() + result.get("expires_in", 0)
            
            logger.info("Successfully authenticated with Deribit API")
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            return False
    
    async def get_options_chain(self, currency: str = "BTC") -> List[OptionContract]:
        """
        获取期权链数据
        
        Args:
            currency: 货币类型（默认BTC）
            
        Returns:
            期权合约列表
        """
        try:
            # 获取所有期权合约
            result = await self._request(
                "public/get_instruments",
                {
                    "currency": currency,
                    "kind": "option",
                    "expired": False
                }
            )
            
            contracts = []
            for instrument in result:
                try:
                    contract = self._parse_option_contract(instrument)
                    contracts.append(contract)
                except Exception as e:
                    logger.warning(
                        f"Failed to parse instrument: {str(e)}",
                        instrument_name=instrument.get("instrument_name")
                    )
            
            logger.info(f"Retrieved {len(contracts)} option contracts for {currency}")
            return contracts
            
        except Exception as e:
            logger.error(f"Failed to get options chain: {str(e)}")
            raise APIConnectionError(f"Failed to get options chain: {str(e)}")
    
    def _parse_option_contract(self, data: Dict) -> OptionContract:
        """
        解析期权合约数据
        
        Args:
            data: API返回的合约数据
            
        Returns:
            期权合约对象
        """
        # 解析期权类型
        option_type = OptionType.CALL if data.get("option_type") == "call" else OptionType.PUT
        
        # 解析到期日期
        expiration_timestamp = data.get("expiration_timestamp", 0) / 1000
        expiration_date = datetime.fromtimestamp(expiration_timestamp)
        
        return OptionContract(
            instrument_name=data.get("instrument_name", ""),
            underlying=data.get("base_currency", "BTC"),
            option_type=option_type,
            strike_price=Decimal(str(data.get("strike", 0))),
            expiration_date=expiration_date,
            current_price=Decimal(str(data.get("mark_price", 0))),
            bid_price=Decimal(str(data.get("best_bid_price", 0))),
            ask_price=Decimal(str(data.get("best_ask_price", 0))),
            last_price=Decimal(str(data.get("last_price", 0))),
            implied_volatility=float(data.get("mark_iv", 0)) / 100,  # 转换为小数
            delta=float(data.get("greeks", {}).get("delta", 0)),
            gamma=float(data.get("greeks", {}).get("gamma", 0)),
            theta=float(data.get("greeks", {}).get("theta", 0)),
            vega=float(data.get("greeks", {}).get("vega", 0)),
            rho=float(data.get("greeks", {}).get("rho", 0)),
            open_interest=int(data.get("open_interest", 0)),
            volume=int(data.get("stats", {}).get("volume", 0)),
            timestamp=datetime.now()
        )
    
    async def get_historical_data(
        self,
        instrument: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[HistoricalData]:
        """
        获取历史数据
        
        Args:
            instrument: 合约名称
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            历史数据列表
        """
        try:
            # 转换为时间戳（毫秒）
            start_timestamp = int(start_date.timestamp() * 1000)
            end_timestamp = int(end_date.timestamp() * 1000)
            
            result = await self._request(
                "public/get_tradingview_chart_data",
                {
                    "instrument_name": instrument,
                    "start_timestamp": start_timestamp,
                    "end_timestamp": end_timestamp,
                    "resolution": "1D"  # 日线数据
                }
            )
            
            historical_data = []
            if result and "ticks" in result:
                ticks = result["ticks"]
                opens = result.get("open", [])
                highs = result.get("high", [])
                lows = result.get("low", [])
                closes = result.get("close", [])
                volumes = result.get("volume", [])
                
                for i, tick in enumerate(ticks):
                    data = HistoricalData(
                        timestamp=datetime.fromtimestamp(tick / 1000),
                        open_price=Decimal(str(opens[i])) if i < len(opens) else Decimal(0),
                        high_price=Decimal(str(highs[i])) if i < len(highs) else Decimal(0),
                        low_price=Decimal(str(lows[i])) if i < len(lows) else Decimal(0),
                        close_price=Decimal(str(closes[i])) if i < len(closes) else Decimal(0),
                        volume=int(volumes[i]) if i < len(volumes) else 0
                    )
                    historical_data.append(data)
            
            logger.info(
                f"Retrieved {len(historical_data)} historical data points",
                instrument=instrument
            )
            return historical_data
            
        except Exception as e:
            logger.error(f"Failed to get historical data: {str(e)}")
            raise APIConnectionError(f"Failed to get historical data: {str(e)}")
    
    async def get_real_time_data(self, instruments: List[str]) -> Dict[str, MarketData]:
        """
        获取实时数据
        
        Args:
            instruments: 合约名称列表
            
        Returns:
            合约名称到市场数据的映射
        """
        market_data = {}
        
        try:
            for instrument in instruments:
                result = await self._request(
                    "public/ticker",
                    {"instrument_name": instrument}
                )
                
                data = MarketData(
                    symbol=instrument,
                    price=Decimal(str(result.get("last_price", 0))),
                    bid=Decimal(str(result.get("best_bid_price", 0))),
                    ask=Decimal(str(result.get("best_ask_price", 0))),
                    volume=int(result.get("stats", {}).get("volume", 0)),
                    timestamp=datetime.now()
                )
                market_data[instrument] = data
            
            logger.info(f"Retrieved real-time data for {len(market_data)} instruments")
            return market_data
            
        except Exception as e:
            logger.error(f"Failed to get real-time data: {str(e)}")
            raise APIConnectionError(f"Failed to get real-time data: {str(e)}")
    
    async def get_volatility_surface(self, currency: str = "BTC") -> VolatilitySurface:
        """
        获取波动率曲面
        
        Args:
            currency: 货币类型
            
        Returns:
            波动率曲面对象
        """
        try:
            # 获取所有期权合约
            contracts = await self.get_options_chain(currency)
            
            # 提取执行价和到期日
            strikes = sorted(list(set(c.strike_price for c in contracts)))
            expiries = sorted(list(set(c.expiration_date for c in contracts)))
            
            # 构建波动率矩阵
            import numpy as np
            volatilities = np.zeros((len(expiries), len(strikes)))
            
            for contract in contracts:
                try:
                    exp_idx = expiries.index(contract.expiration_date)
                    strike_idx = strikes.index(contract.strike_price)
                    volatilities[exp_idx, strike_idx] = contract.implied_volatility
                except ValueError:
                    continue
            
            surface = VolatilitySurface(
                strikes=strikes,
                expiries=expiries,
                volatilities=volatilities,
                timestamp=datetime.now()
            )
            
            logger.info(
                f"Built volatility surface",
                num_strikes=len(strikes),
                num_expiries=len(expiries)
            )
            return surface
            
        except Exception as e:
            logger.error(f"Failed to get volatility surface: {str(e)}")
            raise APIConnectionError(f"Failed to get volatility surface: {str(e)}")
    
    async def close(self):
        """关闭连接"""
        await self.client.aclose()
        logger.info("Deribit connector closed")
