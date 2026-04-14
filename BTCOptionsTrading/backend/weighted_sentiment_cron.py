#!/usr/bin/env python3
"""
加权情绪跨式期权交易 - Cron Job 脚本
Lightweight cron job for weighted sentiment straddle trading

这是一个轻量级脚本，设计用于通过 cron 定期执行（每小时一次）。
适合资源受限的测试环境。

使用方法：
    python weighted_sentiment_cron.py

Cron 配置示例：
    0 * * * * cd /path/to/BTCOptionsTrading/backend && python weighted_sentiment_cron.py >> logs/weighted_sentiment_cron.log 2>&1
"""

import asyncio
import aiohttp
import importlib.util
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# 添加当前目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

# 加载环境变量
load_dotenv()

from weighted_sentiment_api_client import NewsAPIClient
from weighted_sentiment_news_tracker import NewsTracker
from weighted_sentiment_models import WeightedNews, StraddleTradeResult, OptionTrade

# 直接导入 DeribitTrader，避免触发包的 __init__.py
import importlib.util
spec = importlib.util.spec_from_file_location(
    "deribit_trader",
    Path(__file__).parent / "src" / "trading" / "deribit_trader.py"
)
deribit_trader_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deribit_trader_module)
DeribitTrader = deribit_trader_module.DeribitTrader


# 配置日志
def setup_logging():
    """配置日志系统"""
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / "weighted_sentiment.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)


logger = setup_logging()


class StraddleExecutor:
    """跨式期权执行器 - 集成 Deribit 实际交易
    
    使用 DeribitTrader 在 Deribit Test 环境下单
    """
    
    def __init__(self):
        """初始化执行器"""
        self.api_key = os.getenv('WEIGHTED_SENTIMENT_DERIBIT_API_KEY')
        self.api_secret = os.getenv('WEIGHTED_SENTIMENT_DERIBIT_API_SECRET')
        
        if not self.api_key or not self.api_secret:
            logger.error(
                "未配置 Deribit 凭证。请设置环境变量：\n"
                "  WEIGHTED_SENTIMENT_DERIBIT_API_KEY\n"
                "  WEIGHTED_SENTIMENT_DERIBIT_API_SECRET"
            )
            raise ValueError("缺少 Deribit API 凭证")
        
        # 初始化 DeribitTrader（测试网，仅用于下单）
        self.trader = DeribitTrader(self.api_key, self.api_secret, testnet=True)
        self.authenticated = False
        
        # 主网公开API（无需认证，用于获取真实行情和IV）
        self.mainnet_url = "https://www.deribit.com/api/v2"
    
    async def authenticate(self) -> bool:
        """认证 Deribit API
        
        Returns:
            是否认证成功
        """
        if self.authenticated:
            return True
        
        try:
            success = await self.trader.authenticate()
            if success:
                self.authenticated = True
                logger.info("Deribit 认证成功")
            else:
                logger.error("Deribit 认证失败")
            return success
        except Exception as e:
            logger.error(f"Deribit 认证异常: {e}")
            return False
    
    async def get_spot_price(self) -> float:
        """获取 BTC 现货价格（主网真实数据）"""
        try:
            url = f"{self.mainnet_url}/public/get_index_price"
            params = {"index_name": "btc_usd"}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    data = await resp.json()
                    if 'result' in data and 'index_price' in data['result']:
                        price = data['result']['index_price']
                        logger.info(f"获取 BTC 现货价格: ${price:.2f}")
                        return price
                    else:
                        logger.error(f"获取现货价格失败: {data}")
                        return 0.0
        except Exception as e:
            logger.error(f"获取现货价格异常: {e}")
            return 0.0
    
    async def find_atm_options(self, spot_price: float) -> tuple[Optional[str], Optional[str]]:
        """查找 ATM（平值）期权合约（主网真实数据）"""
        try:
            url = f"{self.mainnet_url}/public/get_instruments"
            params = {"currency": "BTC", "kind": "option", "expired": "false"}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    data = await resp.json()
                    if 'result' not in data:
                        logger.error(f"获取合约列表失败: {data}")
                        return None, None
                    
                    instruments = data['result']
                    logger.info(f"获取到 {len(instruments)} 个期权合约")
                    
                    # 找到最接近现货价格的执行价格
                    # 筛选出最近到期的合约（通常流动性更好）
                    from datetime import datetime, timedelta
                    
                    # 目标：找距今最接近 3 天后到期的合约（保证每笔信号期权长度一致）
                    # 由于 Deribit 不是每天都有合约，取所有到期日中最接近 +3 天的那个
                    now = datetime.now()
                    target_expiry = now + timedelta(days=3)

                    # 先收集所有未来合约的到期日（去重）
                    all_expiries = set()
                    for inst in instruments:
                        exp_ts = inst.get('expiration_timestamp')
                        if exp_ts:
                            all_expiries.add(datetime.fromtimestamp(exp_ts / 1000))

                    # 只保留未来的到期日，找最接近 target_expiry 的
                    future_expiries = sorted(e for e in all_expiries if e > now)
                    if not future_expiries:
                        logger.error("未找到任何未来到期合约")
                        return None, None

                    chosen_expiry = min(future_expiries, key=lambda e: abs((e - target_expiry).total_seconds()))
                    logger.info(f"目标到期日: {target_expiry.strftime('%Y-%m-%d')}，"
                                f"实际选用: {chosen_expiry.strftime('%Y-%m-%d')} "
                                f"(距今 {(chosen_expiry - now).days} 天)")

                    call_options = []
                    put_options = []

                    for inst in instruments:
                        try:
                            exp_ts = inst.get('expiration_timestamp')
                            if not exp_ts:
                                continue

                            expiry_dt = datetime.fromtimestamp(exp_ts / 1000)

                            # 只取 chosen_expiry 当天的合约
                            if expiry_dt.date() != chosen_expiry.date():
                                continue

                            strike = inst.get('strike')
                            option_type = inst.get('option_type')
                            instrument_name = inst.get('instrument_name')

                            if not all([strike, option_type, instrument_name]):
                                continue

                            price_diff = abs(strike - spot_price)

                            if option_type == 'call':
                                call_options.append((instrument_name, strike, price_diff, expiry_dt))
                            elif option_type == 'put':
                                put_options.append((instrument_name, strike, price_diff, expiry_dt))

                        except Exception as e:
                            logger.debug(f"解析合约失败: {e}")
                            continue

                    if not call_options or not put_options:
                        logger.error(f"在 {chosen_expiry.strftime('%Y-%m-%d')} 未找到合适的期权合约")
                        return None, None

                    # 按与现货价差排序，选 ATM
                    call_options.sort(key=lambda x: x[2])
                    put_options.sort(key=lambda x: x[2])

                    # 优先选同一执行价的 call/put（真正的 ATM straddle）
                    best_call = call_options[0]
                    same_strike_puts = [p for p in put_options if p[1] == best_call[1]]
                    best_put = same_strike_puts[0] if same_strike_puts else put_options[0]

                    call_instrument = best_call[0]
                    put_instrument = best_put[0]

                    logger.info(f"选择 ATM 期权:")
                    logger.info(f"  看涨: {call_instrument} (执行价: {best_call[1]}, 价差: {best_call[2]:.0f})")
                    logger.info(f"  看跌: {put_instrument} (执行价: {best_put[1]}, 价差: {best_put[2]:.0f})")
                    
                    return call_instrument, put_instrument
        
        except Exception as e:
            logger.error(f"查找 ATM 期权异常: {e}")
            return None, None
    
    async def get_option_price(self, instrument_name: str) -> float:
        """获取期权价格（主网真实数据）"""
        try:
            url = f"{self.mainnet_url}/public/ticker"
            params = {"instrument_name": instrument_name}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    data = await resp.json()
                    if 'result' in data and 'mark_price' in data['result']:
                        price = data['result']['mark_price']
                        logger.info(f"{instrument_name} 价格: {price}")
                        return price
                    else:
                        logger.error(f"获取期权价格失败: {data}")
                        return 0.0
        except Exception as e:
            logger.error(f"获取期权价格异常: {e}")
            return 0.0
    
    async def get_option_iv(self, instrument_name: str) -> float:
        """获取期权隐含波动率（主网真实数据）"""
        try:
            url = f"{self.mainnet_url}/public/ticker"
            params = {"instrument_name": instrument_name}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    data = await resp.json()
                    if 'result' in data and 'mark_iv' in data['result']:
                        iv = data['result']['mark_iv']
                        logger.info(f"{instrument_name} IV: {iv:.2f}%")
                        return iv
                    else:
                        logger.warning(f"获取 IV 失败: {data}")
                        return 0.0
        except Exception as e:
            logger.error(f"获取 IV 异常: {e}")
            return 0.0
    
    async def execute_straddle(self, news: WeightedNews) -> StraddleTradeResult:
        """执行跨式期权交易
        
        Args:
            news: 触发交易的新闻
        
        Returns:
            交易结果
        """
        logger.info(f"执行跨式交易，触发新闻: {news.news_id}")
        logger.info(f"  内容: {news.content[:80]}...")
        logger.info(f"  情绪: {news.sentiment}")
        logger.info(f"  评分: {news.importance_score}/10")
        
        try:
            # 1. 认证
            if not await self.authenticate():
                return StraddleTradeResult(
                    success=False,
                    news_id=news.news_id,
                    trade_time=datetime.now(),
                    spot_price=0.0,
                    call_option=None,
                    put_option=None,
                    total_cost=0.0,
                    error_message="Deribit 认证失败"
                )
            
            # 2. 获取现货价格
            spot_price = await self.get_spot_price()
            if spot_price <= 0:
                return StraddleTradeResult(
                    success=False,
                    news_id=news.news_id,
                    trade_time=datetime.now(),
                    spot_price=0.0,
                    call_option=None,
                    put_option=None,
                    total_cost=0.0,
                    error_message="无法获取现货价格"
                )
            
            # 3. 查找 ATM 期权
            call_instrument, put_instrument = await self.find_atm_options(spot_price)
            if not call_instrument or not put_instrument:
                return StraddleTradeResult(
                    success=False,
                    news_id=news.news_id,
                    trade_time=datetime.now(),
                    spot_price=spot_price,
                    call_option=None,
                    put_option=None,
                    total_cost=0.0,
                    error_message="未找到合适的 ATM 期权"
                )
            
            # 4. 获取期权价格和IV（主网真实数据，无论下单是否成功都会记录）
            call_price = await self.get_option_price(call_instrument)
            put_price = await self.get_option_price(put_instrument)
            call_iv = await self.get_option_iv(call_instrument)
            put_iv = await self.get_option_iv(put_instrument)
            
            if call_price <= 0 or put_price <= 0:
                return StraddleTradeResult(
                    success=False,
                    news_id=news.news_id,
                    trade_time=datetime.now(),
                    spot_price=spot_price,
                    call_option=None,
                    put_option=None,
                    total_cost=0.0,
                    error_message="无法获取期权价格"
                )
            
            # 5. 解析合约信息 + 下单（优先 combo 组合下单，失败回退分腿）
            # 目标总成本 $10,000，每条腿各 $5,000
            TARGET_LEG_USD = 5000.0
            MIN_AMOUNT = 0.1  # Deribit 最小单位
            # 每条腿数量 = $5000 / (mark_price_btc × spot_price)，向上取整到 0.1
            import math
            if call_price > 0 and spot_price > 0:
                raw_amount = TARGET_LEG_USD / (call_price * spot_price)
                trade_amount = max(MIN_AMOUNT, round(math.ceil(raw_amount / MIN_AMOUNT) * MIN_AMOUNT, 1))
            else:
                trade_amount = MIN_AMOUNT
            logger.info(f"目标每腿 ${TARGET_LEG_USD:.0f} → 数量: {trade_amount} BTC")
            import re
            call_match = re.search(r'BTC-(\d+[A-Z]{3}\d+)-(\d+)-C', call_instrument)
            call_strike = float(call_match.group(2)) if call_match else spot_price
            put_match = re.search(r'BTC-(\d+[A-Z]{3}\d+)-(\d+)-P', put_instrument)
            put_strike = float(put_match.group(2)) if put_match else spot_price
            expiry_date = datetime.now() + timedelta(days=14)
            total_cost = (call_price + put_price) * trade_amount * spot_price
            avg_iv = (call_iv + put_iv) / 2

            # 尝试 combo 组合下单
            combo_order = None
            combo_id = await self.trader.create_combo(call_instrument, put_instrument, trade_amount)
            if combo_id:
                combo_order = await self.trader.buy_combo(combo_id, trade_amount)

            if combo_order:
                # combo 下单成功，两条腿共用同一个 combo order_id
                combo_order_id = combo_order.get('order', {}).get('order_id', combo_id)
                logger.info(f"✓ Combo 下单成功: {combo_id}, 订单ID: {combo_order_id}")
                call_option = OptionTrade(
                    instrument_name=call_instrument,
                    option_type="call",
                    strike_price=call_strike,
                    expiry_date=expiry_date,
                    premium=call_price,
                    quantity=trade_amount,
                    order_id=f"COMBO:{combo_order_id}"
                )
                put_option = OptionTrade(
                    instrument_name=put_instrument,
                    option_type="put",
                    strike_price=put_strike,
                    expiry_date=expiry_date,
                    premium=put_price,
                    quantity=trade_amount,
                    order_id=f"COMBO:{combo_order_id}"
                )
            else:
                # combo 失败，回退到分腿下单
                logger.warning("Combo 下单失败，回退到分腿下单")
                logger.info(f"下单买入看涨期权: {call_instrument}, 数量: {trade_amount}")
                call_order = await self.trader.buy(
                    instrument_name=call_instrument,
                    amount=trade_amount,
                    order_type="market"
                )

                if not call_order:
                    logger.warning(f"看涨期权下单失败，记录为虚拟交易")
                    return self._build_virtual_result(
                        news, spot_price, call_instrument, put_instrument,
                        call_price, put_price, call_strike, put_strike,
                        expiry_date, trade_amount, total_cost, call_iv, put_iv,
                        "看涨期权下单失败（测试网不可用）"
                    )

                logger.info(f"下单买入看跌期权: {put_instrument}, 数量: {trade_amount}")
                put_order = await self.trader.buy(
                    instrument_name=put_instrument,
                    amount=trade_amount,
                    order_type="market"
                )

                if not put_order:
                    logger.warning(f"看跌期权下单失败，记录为虚拟交易")
                    return self._build_virtual_result(
                        news, spot_price, call_instrument, put_instrument,
                        call_price, put_price, call_strike, put_strike,
                        expiry_date, trade_amount, total_cost, call_iv, put_iv,
                        "看跌期权下单失败（测试网不可用）"
                    )

                call_option = OptionTrade(
                    instrument_name=call_instrument,
                    option_type="call",
                    strike_price=call_strike,
                    expiry_date=expiry_date,
                    premium=call_price,
                    quantity=trade_amount,
                    order_id=call_order.get('order', {}).get('order_id')
                )
                put_option = OptionTrade(
                    instrument_name=put_instrument,
                    option_type="put",
                    strike_price=put_strike,
                    expiry_date=expiry_date,
                    premium=put_price,
                    quantity=trade_amount,
                    order_id=put_order.get('order', {}).get('order_id')
                )
            
            logger.info(f"✓ 跨式交易执行成功")
            logger.info(f"  看涨订单 ID: {call_option.order_id}")
            logger.info(f"  看跌订单 ID: {put_option.order_id}")
            logger.info(f"  平均 IV: {avg_iv:.2f}%")
            logger.info(f"  总成本: ${total_cost:.2f}")
            
            return StraddleTradeResult(
                success=True,
                news_id=news.news_id,
                trade_time=datetime.now(),
                spot_price=spot_price,
                call_option=call_option,
                put_option=put_option,
                total_cost=total_cost,
                error_message=None
            )
        
        except Exception as e:
            logger.error(f"执行跨式交易异常: {e}", exc_info=True)
            return StraddleTradeResult(
                success=False,
                news_id=news.news_id,
                trade_time=datetime.now(),
                spot_price=0.0,
                call_option=None,
                put_option=None,
                total_cost=0.0,
                error_message=f"交易异常: {str(e)}"
            )
    def _build_virtual_result(
        self, news, spot_price, call_instrument, put_instrument,
        call_price, put_price, call_strike, put_strike,
        expiry_date, trade_amount, total_cost, call_iv, put_iv, reason
    ) -> StraddleTradeResult:
        """构建虚拟交易结果（测试网不可用时，用主网行情数据模拟）"""
        call_option = OptionTrade(
            instrument_name=call_instrument,
            option_type="call",
            strike_price=call_strike,
            expiry_date=expiry_date,
            premium=call_price,
            quantity=trade_amount,
            order_id="VIRTUAL"
        )
        put_option = OptionTrade(
            instrument_name=put_instrument,
            option_type="put",
            strike_price=put_strike,
            expiry_date=expiry_date,
            premium=put_price,
            quantity=trade_amount,
            order_id="VIRTUAL"
        )
        avg_iv = (call_iv + put_iv) / 2
        logger.info(f"✓ 虚拟交易记录（主网行情）: IV={avg_iv:.2f}%, 成本=${total_cost:.2f}, 原因: {reason}")
        return StraddleTradeResult(
            success=True,
            news_id=news.news_id,
            trade_time=datetime.now(),
            spot_price=spot_price,
            call_option=call_option,
            put_option=put_option,
            total_cost=total_cost,
            error_message=None
        )


class CalendarSpreadExecutor:
    """日历价差执行器
    
    策略：卖近期（+3天）ATM Straddle + 买远期（+7天）ATM Straddle
    触发条件：近期 IV ≥ 50% 且 近期IV - 远期IV ≥ 3%
    逻辑：近期 IV 被新闻推高，卖出收取溢价；远期 IV 相对便宜，买入保护
    """

    # IV 触发阈值
    MIN_NEAR_IV = 50.0    # 近期 IV 至少 50%
    MIN_IV_SPREAD = 3.0   # 近远期 IV 差至少 3%
    TRADE_AMOUNT = 0.1    # 每条腿数量（calendar spread 用小仓位测试）

    def __init__(self, straddle_executor: 'StraddleExecutor'):
        self.ex = straddle_executor  # 复用认证和行情接口

    async def check_and_execute(self, news: 'WeightedNews') -> Optional[dict]:
        """检查条件并执行 Calendar Spread
        
        Returns:
            成功时返回结果 dict，不满足条件或失败返回 None
        """
        if not await self.ex.authenticate():
            return None

        spot = await self.ex.get_spot_price()
        if spot <= 0:
            return None

        # 查找近期（+3天）和远期（+7天）ATM 合约
        near_call, near_put = await self._find_atm_by_days(spot, target_days=3)
        far_call, far_put = await self._find_atm_by_days(spot, target_days=7)

        if not all([near_call, near_put, far_call, far_put]):
            logger.info("Calendar: 未找到合适的近期或远期合约")
            return None

        # 获取 IV
        near_iv = await self.ex.get_option_iv(near_call)
        far_iv = await self.ex.get_option_iv(far_call)
        iv_spread = near_iv - far_iv

        logger.info(f"Calendar IV 检查: 近期={near_iv:.1f}% 远期={far_iv:.1f}% 差={iv_spread:.1f}%")

        if near_iv < self.MIN_NEAR_IV:
            logger.info(f"Calendar: 近期 IV={near_iv:.1f}% < {self.MIN_NEAR_IV}%，不满足条件")
            return None
        if iv_spread < self.MIN_IV_SPREAD:
            logger.info(f"Calendar: IV 期限差={iv_spread:.1f}% < {self.MIN_IV_SPREAD}%，不满足条件")
            return None

        logger.info(f"Calendar: 条件满足，执行下单")
        logger.info(f"  卖出近期: {near_call} + {near_put}")
        logger.info(f"  买入远期: {far_call} + {far_put}")

        # 获取价格
        near_call_price = await self.ex.get_option_price(near_call)
        near_put_price = await self.ex.get_option_price(near_put)
        far_call_price = await self.ex.get_option_price(far_call)
        far_put_price = await self.ex.get_option_price(far_put)

        # 净成本（买远期 - 卖近期），正数表示净支出
        net_cost_btc = (far_call_price + far_put_price - near_call_price - near_put_price)
        net_cost_usd = net_cost_btc * self.TRADE_AMOUNT * spot

        # 下单：卖近期（sell），买远期（buy）
        results = {}
        try:
            results['sell_near_call'] = await self.ex.trader.sell(near_call, self.TRADE_AMOUNT, order_type="market")
            results['sell_near_put']  = await self.ex.trader.sell(near_put,  self.TRADE_AMOUNT, order_type="market")
            results['buy_far_call']   = await self.ex.trader.buy(far_call,   self.TRADE_AMOUNT, order_type="market")
            results['buy_far_put']    = await self.ex.trader.buy(far_put,    self.TRADE_AMOUNT, order_type="market")
        except Exception as e:
            logger.error(f"Calendar 下单异常: {e}")
            return None

        if not all(results.values()):
            logger.warning("Calendar: 部分腿下单失败")
            return None

        result = {
            "strategy": "calendar_spread",
            "news_id": news.news_id,
            "news_content": news.content[:100],
            "trade_time": datetime.now().isoformat(),
            "spot_price": spot,
            "near_iv": near_iv,
            "far_iv": far_iv,
            "iv_spread": iv_spread,
            "sell_near_call": near_call,
            "sell_near_put": near_put,
            "buy_far_call": far_call,
            "buy_far_put": far_put,
            "net_cost_usd": round(net_cost_usd, 2),
            "amount": self.TRADE_AMOUNT,
            "order_ids": {
                "sell_near_call": results['sell_near_call'].get('order', {}).get('order_id'),
                "sell_near_put":  results['sell_near_put'].get('order', {}).get('order_id'),
                "buy_far_call":   results['buy_far_call'].get('order', {}).get('order_id'),
                "buy_far_put":    results['buy_far_put'].get('order', {}).get('order_id'),
            }
        }

        logger.info(f"✓ Calendar Spread 执行成功")
        logger.info(f"  净成本: ${net_cost_usd:.2f} | IV差: {iv_spread:.1f}%")
        return result

    async def _find_atm_by_days(self, spot: float, target_days: int) -> tuple[Optional[str], Optional[str]]:
        """查找距今 target_days 天最近的 ATM 合约"""
        try:
            url = f"{self.ex.mainnet_url}/public/get_instruments"
            params = {"currency": "BTC", "kind": "option", "expired": "false"}
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    data = await resp.json()
                    if 'result' not in data:
                        return None, None

                    now = datetime.now()
                    target_expiry = now + timedelta(days=target_days)

                    # 找最接近 target_days 的到期日
                    expiries = set()
                    for inst in data['result']:
                        exp_ts = inst.get('expiration_timestamp')
                        if exp_ts:
                            expiries.add(datetime.fromtimestamp(exp_ts / 1000))

                    future_expiries = sorted(e for e in expiries if e > now)
                    if not future_expiries:
                        return None, None

                    chosen = min(future_expiries, key=lambda e: abs((e - target_expiry).total_seconds()))

                    # 找 ATM
                    calls, puts = [], []
                    for inst in data['result']:
                        exp_ts = inst.get('expiration_timestamp')
                        if not exp_ts:
                            continue
                        if datetime.fromtimestamp(exp_ts / 1000).date() != chosen.date():
                            continue
                        strike = inst.get('strike')
                        opt_type = inst.get('option_type')
                        name = inst.get('instrument_name')
                        if not all([strike, opt_type, name]):
                            continue
                        diff = abs(strike - spot)
                        if opt_type == 'call':
                            calls.append((name, strike, diff))
                        elif opt_type == 'put':
                            puts.append((name, strike, diff))

                    if not calls or not puts:
                        return None, None

                    calls.sort(key=lambda x: x[2])
                    puts.sort(key=lambda x: x[2])
                    best_call = calls[0]
                    same_strike_puts = [p for p in puts if p[1] == best_call[1]]
                    best_put = same_strike_puts[0] if same_strike_puts else puts[0]

                    logger.info(f"Calendar +{target_days}天: {best_call[0]} / {best_put[0]}")
                    return best_call[0], best_put[0]
        except Exception as e:
            logger.error(f"查找 +{target_days}天合约失败: {e}")
            return None, None


class TradeFilter:
    """下单前置过滤器
    
    四个条件全部满足才允许下单：
    1. 新闻评分 >= 8
    2. 当前 ATM 期权 IV < 55%
    3. 过去 4 小时 IV 趋势向上（至少上涨 0.5%）
    4. 同类新闻 48 小时内未触发过下单
    """

    IV_DB = Path(__file__).parent / "data" / "iv_history.db"
    TRADE_LOG = Path(__file__).parent / "logs" / "weighted_sentiment_trades.log"

    def __init__(self, executor: 'StraddleExecutor'):
        self.executor = executor

    async def check(self, news: 'WeightedNews', call_instrument: str, put_instrument: str) -> tuple[bool, str]:
        """
        Returns:
            (allowed, reason) — allowed=True 表示可以下单
        """
        # ── 条件 1：评分 >= 8 ──────────────────────────────
        if news.importance_score < 8:
            return False, f"评分 {news.importance_score} < 8，跳过"

        # ── 条件 1b：API 已标记同类高频新闻 ──────────────────
        if news.has_similar_high_scores:
            return False, f"API 标记 has_similar_high_scores=True（同类事件已高频出现），跳过"

        # ── 条件 2：当前 IV < 55% ──────────────────────────
        call_iv = await self.executor.get_option_iv(call_instrument)
        put_iv = await self.executor.get_option_iv(put_instrument)
        avg_iv = (call_iv + put_iv) / 2 if call_iv and put_iv else call_iv or put_iv
        if avg_iv >= 55:
            return False, f"当前 IV={avg_iv:.1f}% >= 55%，IV 已在高位，跳过"

        # ── 条件 3：过去 4 小时 IV 趋势向上 ──────────────────
        iv_trend_ok, trend_msg = self._check_iv_trend(call_instrument)
        if not iv_trend_ok:
            return False, trend_msg

        # ── 条件 4：同类新闻 48 小时内未触发 ─────────────────
        dup_ok, dup_msg = self._check_duplicate(news)
        if not dup_ok:
            return False, dup_msg

        return True, f"通过所有过滤条件（评分={news.importance_score}, IV={avg_iv:.1f}%）"

    def _check_iv_trend(self, instrument: str) -> tuple[bool, str]:
        """检查过去 4 小时 IV 是否趋势向上（至少 +0.5%）"""
        if not self.IV_DB.exists():
            # 没有 IV 数据库，放行（不阻止下单）
            return True, "无 IV 历史数据，跳过趋势检查"
        try:
            import sqlite3
            from datetime import timezone
            now_ts = int(datetime.now(timezone.utc).timestamp())
            four_h_ago = now_ts - 4 * 3600

            conn = sqlite3.connect(self.IV_DB)
            rows = conn.execute(
                "SELECT ts, mark_iv FROM iv_snapshots "
                "WHERE instrument=? AND ts >= ? ORDER BY ts",
                (instrument, four_h_ago)
            ).fetchall()
            conn.close()

            if len(rows) < 2:
                return True, "IV 历史数据不足，跳过趋势检查"

            iv_start = rows[0][1]
            iv_end = rows[-1][1]
            change = iv_end - iv_start

            if change < 0.5:
                return False, f"IV 趋势未向上（4h变化={change:+.2f}%），市场已定价，跳过"
            return True, f"IV 趋势向上 {change:+.2f}%"
        except Exception as e:
            logger.warning(f"IV 趋势检查失败: {e}，放行")
            return True, "IV 趋势检查异常，放行"

    def _check_duplicate(self, news: 'WeightedNews') -> tuple[bool, str]:
        """检查 48 小时内是否有同类新闻已触发下单"""
        if not self.TRADE_LOG.exists():
            return True, "无交易日志"
        try:
            content = self.TRADE_LOG.read_text(encoding='utf-8')
            cutoff = datetime.now() - timedelta(hours=48)

            # 提取关键词（取新闻内容前 20 字）
            keywords = news.content[:20].strip()

            for entry in content.split('=' * 80):
                if '交易成功: True' not in entry:
                    continue
                # 解析交易时间
                for line in entry.split('\n'):
                    line = line.strip()
                    if line.startswith('交易时间:'):
                        try:
                            trade_dt = datetime.fromisoformat(line.split(':', 1)[1].strip())
                            if trade_dt < cutoff:
                                break  # 超出 48h 窗口
                            # 检查新闻内容是否相似
                            if keywords and keywords in entry:
                                return False, f"48h 内已有同类新闻触发下单，跳过"
                        except Exception:
                            pass
                        break

            return True, "无重复触发"
        except Exception as e:
            logger.warning(f"重复检查失败: {e}，放行")
            return True, "重复检查异常，放行"


class SimplifiedTradeLogger:
    """简化版交易日志记录器
    
    将交易记录写入日志文件，而不是数据库。
    适合资源受限环境。
    """
    
    def __init__(self):
        """初始化日志记录器"""
        self.log_dir = Path(__file__).parent / "logs"
        self.log_dir.mkdir(exist_ok=True)
        self.trade_log_file = self.log_dir / "weighted_sentiment_trades.log"
    
    async def log_trade(self, news: WeightedNews, result: StraddleTradeResult, call_iv: float = 0.0, put_iv: float = 0.0):
        """记录交易
        
        Args:
            news: 触发交易的新闻
            result: 交易结果
            call_iv: 看涨期权IV
            put_iv: 看跌期权IV
        """
        log_entry = (
            f"\n{'='*80}\n"
            f"交易时间: {result.trade_time.isoformat()}\n"
            f"新闻 ID: {news.news_id}\n"
            f"新闻内容: {news.content}\n"
            f"情绪: {news.sentiment}\n"
            f"重要性评分: {news.importance_score}/10\n"
            f"交易成功: {result.success}\n"
        )
        
        if result.success:
            avg_iv = (call_iv + put_iv) / 2 if call_iv > 0 and put_iv > 0 else 0.0
            is_virtual = (
                result.call_option and result.call_option.order_id == "VIRTUAL"
            )
            # 主网入场价格（BTC单位，用于PnL计算）
            call_entry_btc = result.call_option.premium
            put_entry_btc = result.put_option.premium
            # 提取 combo_id（格式 COMBO:xxx）
            call_oid = result.call_option.order_id or ''
            combo_id = call_oid[6:] if call_oid.startswith('COMBO:') else ''
            # 盈亏平衡点：执行价 ± 总权利金(USD)
            strike = result.call_option.strike_price
            total_premium_usd = (call_entry_btc + put_entry_btc) * result.spot_price
            be_upper = strike + total_premium_usd
            be_lower = strike - total_premium_usd
            log_entry += (
                f"虚拟交易: {'True' if is_virtual else 'False'}\n"
                f"现货价格: ${result.spot_price:.2f}\n"
                + (f"Combo ID: {combo_id}\n" if combo_id else "")
                + f"盈亏平衡: ${be_lower:.2f} ~ ${be_upper:.2f}\n"
                + f"下单数量: {result.call_option.quantity} BTC\n"
                + f"看涨期权: {result.call_option.instrument_name}\n"
                f"  执行价: ${result.call_option.strike_price:.2f}\n"
                f"  入场价(BTC): {call_entry_btc:.6f}\n"
                f"  权利金: {result.call_option.premium:.4f} BTC\n"
                f"  IV: {call_iv:.2f}%\n"
                f"  订单 ID: {result.call_option.order_id}\n"
                f"看跌期权: {result.put_option.instrument_name}\n"
                f"  执行价: ${result.put_option.strike_price:.2f}\n"
                f"  入场价(BTC): {put_entry_btc:.6f}\n"
                f"  权利金: {result.put_option.premium:.4f} BTC\n"
                f"  IV: {put_iv:.2f}%\n"
                f"  订单 ID: {result.put_option.order_id}\n"
                f"平均 IV: {avg_iv:.2f}%\n"
                f"总成本: ${result.total_cost:.2f}\n"
            )
        else:
            log_entry += f"错误信息: {result.error_message}\n"
        
        log_entry += f"{'='*80}\n"
        
        # 写入文件
        with open(self.trade_log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        logger.info(f"交易记录已保存: {news.news_id}")

    async def log_calendar_trade(self, result: dict):
        """记录 Calendar Spread 交易"""
        cal_log_file = self.log_dir / "calendar_spread_trades.log"
        import json
        entry = (
            f"\n{'='*80}\n"
            f"策略: Calendar Spread\n"
            f"交易时间: {result['trade_time']}\n"
            f"新闻: {result['news_content']}\n"
            f"现货价格: ${result['spot_price']:.2f}\n"
            f"近期 IV: {result['near_iv']:.1f}%  远期 IV: {result['far_iv']:.1f}%  IV差: {result['iv_spread']:.1f}%\n"
            f"卖出近期 Call: {result['sell_near_call']}  订单ID: {result['order_ids']['sell_near_call']}\n"
            f"卖出近期 Put:  {result['sell_near_put']}  订单ID: {result['order_ids']['sell_near_put']}\n"
            f"买入远期 Call: {result['buy_far_call']}  订单ID: {result['order_ids']['buy_far_call']}\n"
            f"买入远期 Put:  {result['buy_far_put']}  订单ID: {result['order_ids']['buy_far_put']}\n"
            f"净成本: ${result['net_cost_usd']:.2f}\n"
            f"数量: {result['amount']} BTC\n"
            f"{'='*80}\n"
        )
        with open(cal_log_file, 'a', encoding='utf-8') as f:
            f.write(entry)
        logger.info(f"Calendar Spread 记录已保存，净成本: ${result['net_cost_usd']:.2f}")


async def main():
    """主函数：执行新闻监听和交易流程（每分钟触发）"""
    # ── 防重入锁：避免上一次还没跑完下一次就启动 ──────────
    lock_file = Path(__file__).parent / "logs" / ".cron_running.lock"
    if lock_file.exists():
        # 检查锁文件是否超过 5 分钟（防止异常退出后锁文件残留）
        import time
        if time.time() - lock_file.stat().st_mtime < 300:
            logger.debug("上一次执行尚未完成，跳过本次")
            return
    lock_file.touch()
    try:
        await _main()
    finally:
        lock_file.unlink(missing_ok=True)



async def _main():
    """内部主函数：每分钟轮询，发现新高分新闻即评估下单"""
    logger.debug(f"轮询: {datetime.now().strftime('%H:%M:%S')}")
    try:
        api_client = NewsAPIClient()
        news_tracker = NewsTracker()
        executor = StraddleExecutor()
        calendar_executor = CalendarSpreadExecutor(executor)
        trade_filter = TradeFilter(executor)
        trade_logger = SimplifiedTradeLogger()

        news_list = await api_client.fetch_weighted_news()
        if not news_list:
            return

        new_high_score_news = await news_tracker.identify_new_news(news_list)

        if not new_high_score_news:
            await news_tracker.update_history(news_list)
            return

        logger.info(f"发现 {len(new_high_score_news)} 条新的高分新闻，开始评估...")

        # 永续合约策略：所有 ≥7 分新闻都触发（不受 IV 过滤限制）
        try:
            from perp_strategy import execute_news_trade
            for news in new_high_score_news:
                asyncio.create_task(execute_news_trade(news.content, news.importance_score, news.sentiment))
        except Exception as pe:
            logger.warning(f"永续合约策略触发失败: {pe}")

        for news in new_high_score_news:
            logger.info(f"处理: [{news.importance_score}/10] {news.content[:60]}...")
            try:
                spot_price = await executor.get_spot_price()
                call_inst, put_inst = await executor.find_atm_options(spot_price)

                if not call_inst or not put_inst:
                    logger.warning("  ✗ 未找到 ATM 合约，跳过")
                    continue

                allowed, reason = await trade_filter.check(news, call_inst, put_inst)
                if not allowed:
                    logger.info(f"  ⏭ {reason}")
                    continue

                logger.info(f"  ✓ 过滤通过: {reason}")
                result = await executor.execute_straddle(news)

                call_iv, put_iv = 0.0, 0.0
                if result.success and result.call_option and result.put_option:
                    call_iv = await executor.get_option_iv(result.call_option.instrument_name)
                    put_iv = await executor.get_option_iv(result.put_option.instrument_name)

                await trade_logger.log_trade(news, result, call_iv, put_iv)

                if result.success:
                    logger.info(f"  ✓ 下单成功: {result.call_option.instrument_name} | ${result.total_cost:.2f}")
                    # Calendar Spread（独立策略）
                    try:
                        cal_result = await calendar_executor.check_and_execute(news)
                        if cal_result:
                            await trade_logger.log_calendar_trade(cal_result)
                    except Exception as ce:
                        logger.warning(f"  Calendar Spread 评估失败（不影响主流程）: {ce}")
                    # Vol Account Strategy（qCoXRSu6 账户）
                    try:
                        from vol_account_strategy import VolAccountStrategy
                        vol = VolAccountStrategy()
                        vol_result = await vol.execute(news.content, news.importance_score)
                        if vol_result:
                            logger.info(f"  ✓ Vol 账户下单成功: 收入 ${vol_result['total_premium_usd']:.2f}")
                    except Exception as ve:
                        logger.warning(f"  Vol 账户策略失败（不影响主流程）: {ve}")
                else:
                    logger.warning(f"  ✗ 下单失败: {result.error_message}")

            except Exception as e:
                logger.error(f"  ✗ 处理新闻时发生错误: {e}", exc_info=True)

        await news_tracker.update_history(news_list)

    except Exception as e:
        logger.error(f"执行过程中发生错误: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
