#!/usr/bin/env python3
"""
Vol Account Strategy - qCoXRSu6 账户
策略：IV Reversion（波动率均值回归）

逻辑：
  当近期 IV > 55% 时，市场对波动的预期已经过高。
  卖出 OTM Strangle（宽跨式）：
    - 卖出 +5% OTM Call（BTC 需要涨 5% 才亏损）
    - 卖出 -5% OTM Put（BTC 需要跌 5% 才亏损）
  收取权利金，只要 BTC 在 ±5% 内就全部盈利。

触发条件：
  - 新闻评分 >= 8（有新闻驱动 IV 上升）
  - 当前 ATM IV >= 55%（IV 足够高，值得卖）
  - 48h 内未触发过同类下单

日志：logs/vol_account_trades.log
"""

import asyncio
import aiohttp
import json
import logging
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

MAINNET_URL = "https://www.deribit.com/api/v2"
TESTNET_URL = "https://test.deribit.com/api/v2"

TRADE_LOG = LOG_DIR / "vol_account_trades.log"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class VolAccountStrategy:
    """IV Reversion 策略 - 卖出 OTM Strangle"""

    MIN_IV_TO_SELL = 55.0    # IV 高于此值才卖
    OTM_PCT = 0.05           # 5% OTM
    TRADE_AMOUNT = 0.1       # 每条腿 0.1 BTC
    COOLDOWN_HOURS = 48      # 48h 内不重复下单

    def __init__(self):
        self.api_key = os.getenv('VOL_STRATEGY_DERIBIT_API_KEY', 'qCoXRSu6')
        self.api_secret = os.getenv('VOL_STRATEGY_DERIBIT_API_SECRET',
                                    'GhL6l32FUgm7tKgtRJVsngdF5Cp5j-JhVIr5Js4kvTQ')
        self.testnet = os.getenv('VOL_STRATEGY_TESTNET', 'true').lower() == 'true'
        self.base_url = TESTNET_URL if self.testnet else MAINNET_URL
        self.access_token = None

    async def authenticate(self) -> bool:
        try:
            async with aiohttp.ClientSession() as s:
                r = await s.get(f"{self.base_url}/public/auth", params={
                    "grant_type": "client_credentials",
                    "client_id": self.api_key,
                    "client_secret": self.api_secret
                })
                d = await r.json()
                if 'result' in d:
                    self.access_token = d['result']['access_token']
                    return True
        except Exception as e:
            logger.error(f"Vol 账户认证失败: {e}")
        return False

    async def _request(self, method: str, params: dict) -> dict:
        if not self.access_token:
            await self.authenticate()
        url = f"{self.base_url}/private/{method}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        async with aiohttp.ClientSession() as s:
            r = await s.get(url, params=params, headers=headers)
            d = await r.json()
            return d.get('result', {})

    async def get_spot_price(self) -> float:
        try:
            async with aiohttp.ClientSession() as s:
                r = await s.get(f"{MAINNET_URL}/public/get_index_price",
                                params={"index_name": "btc_usd"})
                d = await r.json()
                return d['result']['index_price']
        except Exception:
            return 0.0

    async def get_atm_iv(self, spot: float) -> float:
        """获取当前 ATM 期权的 IV"""
        try:
            now = datetime.now()
            target = now + timedelta(days=3)
            async with aiohttp.ClientSession() as s:
                r = await s.get(f"{MAINNET_URL}/public/get_instruments",
                                params={"currency": "BTC", "kind": "option", "expired": "false"})
                instruments = (await r.json()).get('result', [])

            expiries = set()
            for inst in instruments:
                ts = inst.get('expiration_timestamp')
                if ts:
                    expiries.add(datetime.fromtimestamp(ts / 1000))
            future = sorted(e for e in expiries if e > now)
            if not future:
                return 0.0
            chosen = min(future, key=lambda e: abs((e - target).total_seconds()))

            # 找最近 ATM call
            calls = []
            for inst in instruments:
                ts = inst.get('expiration_timestamp')
                if not ts or datetime.fromtimestamp(ts / 1000).date() != chosen.date():
                    continue
                if inst.get('option_type') != 'call':
                    continue
                strike = inst.get('strike', 0)
                calls.append((inst['instrument_name'], abs(strike - spot)))

            if not calls:
                return 0.0
            atm_name = min(calls, key=lambda x: x[1])[0]

            async with aiohttp.ClientSession() as s:
                r = await s.get(f"{MAINNET_URL}/public/ticker",
                                params={"instrument_name": atm_name})
                d = await r.json()
                return d.get('result', {}).get('mark_iv', 0.0)
        except Exception as e:
            logger.error(f"获取 ATM IV 失败: {e}")
            return 0.0

    async def find_otm_instruments(self, spot: float) -> tuple:
        """查找 OTM Call 和 Put（±5%）"""
        try:
            now = datetime.now()
            target = now + timedelta(days=3)
            async with aiohttp.ClientSession() as s:
                r = await s.get(f"{MAINNET_URL}/public/get_instruments",
                                params={"currency": "BTC", "kind": "option", "expired": "false"})
                instruments = (await r.json()).get('result', [])

            expiries = set()
            for inst in instruments:
                ts = inst.get('expiration_timestamp')
                if ts:
                    expiries.add(datetime.fromtimestamp(ts / 1000))
            future = sorted(e for e in expiries if e > now)
            if not future:
                return None, None
            chosen = min(future, key=lambda e: abs((e - target).total_seconds()))

            call_target = spot * (1 + self.OTM_PCT)  # +5%
            put_target = spot * (1 - self.OTM_PCT)   # -5%

            calls, puts = [], []
            for inst in instruments:
                ts = inst.get('expiration_timestamp')
                if not ts or datetime.fromtimestamp(ts / 1000).date() != chosen.date():
                    continue
                strike = inst.get('strike', 0)
                name = inst.get('instrument_name', '')
                opt_type = inst.get('option_type', '')
                if opt_type == 'call':
                    calls.append((name, strike, abs(strike - call_target)))
                elif opt_type == 'put':
                    puts.append((name, strike, abs(strike - put_target)))

            if not calls or not puts:
                return None, None

            best_call = min(calls, key=lambda x: x[2])
            best_put = min(puts, key=lambda x: x[2])
            logger.info(f"OTM Call: {best_call[0]} (执行价 ${best_call[1]:,.0f}, 目标 ${call_target:,.0f})")
            logger.info(f"OTM Put:  {best_put[0]} (执行价 ${best_put[1]:,.0f}, 目标 ${put_target:,.0f})")
            return best_call[0], best_put[0]
        except Exception as e:
            logger.error(f"查找 OTM 合约失败: {e}")
            return None, None

    def _check_cooldown(self) -> bool:
        """检查 48h 内是否已下单"""
        if not TRADE_LOG.exists():
            return True
        try:
            content = TRADE_LOG.read_text(encoding='utf-8')
            cutoff = datetime.now() - timedelta(hours=self.COOLDOWN_HOURS)
            for entry in content.split('=' * 80):
                for line in entry.split('\n'):
                    if line.strip().startswith('交易时间:'):
                        try:
                            dt = datetime.fromisoformat(line.split(':', 1)[1].strip())
                            if dt > cutoff:
                                return False  # 48h 内已有下单
                        except Exception:
                            pass
            return True
        except Exception:
            return True

    def _log_trade(self, result: dict):
        """记录交易到日志"""
        entry = (
            f"\n{'='*80}\n"
            f"策略: IV Reversion (OTM Strangle)\n"
            f"账户: {self.api_key}\n"
            f"交易时间: {result['trade_time']}\n"
            f"触发新闻: {result.get('news_content', '')[:80]}\n"
            f"现货价格: ${result['spot_price']:,.2f}\n"
            f"ATM IV: {result['atm_iv']:.1f}%\n"
            f"卖出 OTM Call: {result['call_instrument']}\n"
            f"  执行价: ${result['call_strike']:,.0f} (+{self.OTM_PCT*100:.0f}% OTM)\n"
            f"  权利金: {result['call_premium']:.4f} BTC\n"
            f"  订单 ID: {result['call_order_id']}\n"
            f"卖出 OTM Put: {result['put_instrument']}\n"
            f"  执行价: ${result['put_strike']:,.0f} (-{self.OTM_PCT*100:.0f}% OTM)\n"
            f"  权利金: {result['put_premium']:.4f} BTC\n"
            f"  订单 ID: {result['put_order_id']}\n"
            f"总收入: ${result['total_premium_usd']:.2f}\n"
            f"盈利区间: ${result['put_strike']:,.0f} ~ ${result['call_strike']:,.0f}\n"
            f"{'='*80}\n"
        )
        with open(TRADE_LOG, 'a', encoding='utf-8') as f:
            f.write(entry)
        logger.info(f"Vol 账户交易记录已保存")

    async def execute(self, news_content: str = "", news_score: float = 0) -> Optional[dict]:
        """执行 IV Reversion 策略"""
        # 冷却检查
        if not self._check_cooldown():
            logger.info("Vol 策略: 48h 内已下单，跳过")
            return None

        if not await self.authenticate():
            return None

        spot = await self.get_spot_price()
        if spot <= 0:
            return None

        atm_iv = await self.get_atm_iv(spot)
        logger.info(f"Vol 策略: 当前 ATM IV={atm_iv:.1f}%，阈值={self.MIN_IV_TO_SELL}%")

        if atm_iv < self.MIN_IV_TO_SELL:
            logger.info(f"Vol 策略: IV 不够高，不下单")
            return None

        call_inst, put_inst = await self.find_otm_instruments(spot)
        if not call_inst or not put_inst:
            return None

        # 获取价格
        async with aiohttp.ClientSession() as s:
            r1 = await s.get(f"{MAINNET_URL}/public/ticker", params={"instrument_name": call_inst})
            call_data = (await r1.json()).get('result', {})
            r2 = await s.get(f"{MAINNET_URL}/public/ticker", params={"instrument_name": put_inst})
            put_data = (await r2.json()).get('result', {})

        call_premium = call_data.get('mark_price', 0)
        put_premium = put_data.get('mark_price', 0)
        call_strike = call_data.get('strike', 0)
        put_strike = put_data.get('strike', 0)

        # 解析执行价
        m = re.search(r'-(\d+)-C$', call_inst)
        if m:
            call_strike = float(m.group(1))
        m = re.search(r'-(\d+)-P$', put_inst)
        if m:
            put_strike = float(m.group(1))

        total_premium_usd = (call_premium + put_premium) * self.TRADE_AMOUNT * spot

        # 下单（卖出）
        logger.info(f"Vol 策略: 卖出 {call_inst} + {put_inst}")
        call_order = await self._request("sell", {
            "instrument_name": call_inst,
            "amount": self.TRADE_AMOUNT,
            "type": "market"
        })
        put_order = await self._request("sell", {
            "instrument_name": put_inst,
            "amount": self.TRADE_AMOUNT,
            "type": "market"
        })

        if not call_order or not put_order:
            logger.error("Vol 策略: 下单失败")
            return None

        result = {
            "trade_time": datetime.now().isoformat(),
            "news_content": news_content,
            "news_score": news_score,
            "spot_price": spot,
            "atm_iv": atm_iv,
            "call_instrument": call_inst,
            "call_strike": call_strike,
            "call_premium": call_premium,
            "call_order_id": call_order.get('order', {}).get('order_id', ''),
            "put_instrument": put_inst,
            "put_strike": put_strike,
            "put_premium": put_premium,
            "put_order_id": put_order.get('order', {}).get('order_id', ''),
            "total_premium_usd": total_premium_usd,
            "amount": self.TRADE_AMOUNT,
        }

        logger.info(f"✓ Vol 策略下单成功: 收入 ${total_premium_usd:.2f}")
        self._log_trade(result)
        return result

    async def get_positions(self) -> list:
        """获取当前持仓"""
        if not await self.authenticate():
            return []
        result = await self._request("get_positions", {"currency": "BTC", "kind": "option"})
        return result if isinstance(result, list) else []

    async def get_account_summary(self) -> dict:
        """获取账户摘要"""
        if not await self.authenticate():
            return {}
        return await self._request("get_account_summary", {"currency": "BTC"})


if __name__ == "__main__":
    async def test():
        strategy = VolAccountStrategy()
        summary = await strategy.get_account_summary()
        print(f"账户余额: {summary.get('balance')} BTC")
        positions = await strategy.get_positions()
        print(f"当前持仓: {len(positions)} 个")
        for p in positions:
            print(f"  {p['instrument_name']}: size={p['size']}")

    asyncio.run(test())
