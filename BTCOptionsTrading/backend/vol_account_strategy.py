#!/usr/bin/env python3
"""
Vol Account Strategy - qCoXRSu6 账户
策略：Theta Harvesting（卖出 ATM Straddle + 新闻止损）

逻辑：
  横盘期：卖出 ATM Straddle，收取权利金（theta 每天自然衰减）
  出现重大新闻：立即平仓，锁定已赚的 theta，避免大波动亏损

开仓条件（每天 UTC 08:00 自动检查）：
  - 当前无持仓
  - ATM IV 在合理范围（25%-60%）
  - 仓位：每腿 0.1 BTC

平仓触发：
  1. 新闻触发：v3 打分 A≥3 + B≥2（重大增量新闻）
  2. 价格止损：BTC 移动超过 ±3%（相对于开仓时现货价）
  3. 到期自然结算

日志：logs/vol_account_trades.log
"""

import asyncio
import aiohttp
import json
import logging
import os
import re
from datetime import datetime, timedelta, timezone
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
STATE_FILE = BASE_DIR / "data" / "vol_account_state.json"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class VolAccountStrategy:
    """Theta Harvesting 策略 - 卖出 ATM Straddle，新闻止损"""

    TRADE_AMOUNT = 0.1       # 每条腿 0.1 BTC
    MIN_IV = 25.0            # IV 低于此值不开仓（权利金太少）
    MAX_IV = 60.0            # IV 高于此值不开仓（风险太大）
    PRICE_STOP_PCT = 0.03    # 价格止损：BTC 移动超过 ±3%

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

    async def find_atm_instruments(self, spot: float) -> tuple:
        """查找 +3 天到期的 ATM Call 和 Put"""
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

            calls, puts = [], []
            for inst in instruments:
                ts = inst.get('expiration_timestamp')
                if not ts or datetime.fromtimestamp(ts / 1000).date() != chosen.date():
                    continue
                strike = inst.get('strike', 0)
                name = inst.get('instrument_name', '')
                opt_type = inst.get('option_type', '')
                diff = abs(strike - spot)
                if opt_type == 'call':
                    calls.append((name, strike, diff))
                elif opt_type == 'put':
                    puts.append((name, strike, diff))

            if not calls or not puts:
                return None, None

            calls.sort(key=lambda x: x[2])
            best_call = calls[0]
            same_strike_puts = [p for p in puts if p[1] == best_call[1]]
            best_put = same_strike_puts[0] if same_strike_puts else puts[0]

            logger.info(f"ATM: {best_call[0]} / {best_put[0]} (到期: {chosen.strftime('%Y-%m-%d')})")
            return best_call[0], best_put[0]
        except Exception as e:
            logger.error(f"查找 ATM 合约失败: {e}")
            return None, None

    def _load_state(self) -> dict:
        """加载当前持仓状态"""
        if STATE_FILE.exists():
            try:
                return json.loads(STATE_FILE.read_text(encoding='utf-8'))
            except Exception:
                pass
        return {}

    def _save_state(self, state: dict):
        STATE_FILE.parent.mkdir(exist_ok=True)
        STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')

    def _log_trade(self, action: str, result: dict):
        entry = (
            f"\n{'='*80}\n"
            f"操作: {action}\n"
            f"账户: {self.api_key} (Theta Harvesting)\n"
            f"时间: {result.get('time', datetime.now().isoformat())}\n"
            f"现货: ${result.get('spot', 0):,.2f}\n"
            f"ATM IV: {result.get('atm_iv', 0):.1f}%\n"
        )
        if 'call_instrument' in result:
            entry += (
                f"Call: {result['call_instrument']} | 订单: {result.get('call_order_id', '')}\n"
                f"Put:  {result['put_instrument']} | 订单: {result.get('put_order_id', '')}\n"
                f"权利金收入: ${result.get('premium_usd', 0):.2f}\n"
            )
        if 'reason' in result:
            entry += f"平仓原因: {result['reason']}\n"
        if 'pnl_usd' in result:
            sign = '+' if result['pnl_usd'] >= 0 else ''
            entry += f"平仓盈亏: {sign}${result['pnl_usd']:.2f}\n"
        entry += f"{'='*80}\n"
        with open(TRADE_LOG, 'a', encoding='utf-8') as f:
            f.write(entry)

    async def open_position(self) -> Optional[dict]:
        """开仓：卖出 ATM Straddle"""
        state = self._load_state()
        if state.get('has_position'):
            logger.info("Vol 策略: 已有持仓，跳过开仓")
            return None

        if not await self.authenticate():
            return None

        spot = await self.get_spot_price()
        if spot <= 0:
            return None

        atm_iv = await self.get_atm_iv(spot)
        logger.info(f"Vol 策略开仓检查: IV={atm_iv:.1f}% (范围 {self.MIN_IV}%-{self.MAX_IV}%)")

        if not (self.MIN_IV <= atm_iv <= self.MAX_IV):
            logger.info(f"Vol 策略: IV={atm_iv:.1f}% 不在范围内，不开仓")
            return None

        call_inst, put_inst = await self.find_atm_instruments(spot)
        if not call_inst or not put_inst:
            return None

        # 获取权利金
        async with aiohttp.ClientSession() as s:
            rc = await s.get(f"{MAINNET_URL}/public/ticker", params={"instrument_name": call_inst})
            call_price = (await rc.json()).get('result', {}).get('mark_price', 0)
            rp = await s.get(f"{MAINNET_URL}/public/ticker", params={"instrument_name": put_inst})
            put_price = (await rp.json()).get('result', {}).get('mark_price', 0)

        premium_usd = (call_price + put_price) * self.TRADE_AMOUNT * spot

        # 卖出
        call_order = await self._request("sell", {
            "instrument_name": call_inst, "amount": self.TRADE_AMOUNT, "type": "market"
        })
        put_order = await self._request("sell", {
            "instrument_name": put_inst, "amount": self.TRADE_AMOUNT, "type": "market"
        })

        if not call_order or not put_order:
            logger.error("Vol 策略: 开仓下单失败")
            return None

        call_oid = call_order.get('order', {}).get('order_id', '')
        put_oid = put_order.get('order', {}).get('order_id', '')

        result = {
            "time": datetime.now().isoformat(),
            "spot": spot,
            "atm_iv": atm_iv,
            "call_instrument": call_inst,
            "put_instrument": put_inst,
            "call_entry_price": call_price,
            "put_entry_price": put_price,
            "call_order_id": call_oid,
            "put_order_id": put_oid,
            "premium_usd": premium_usd,
            "amount": self.TRADE_AMOUNT,
        }

        # 保存状态
        self._save_state({
            "has_position": True,
            "open_time": result["time"],
            "open_spot": spot,
            "call_instrument": call_inst,
            "put_instrument": put_inst,
            "call_entry_price": call_price,
            "put_entry_price": put_price,
            "premium_usd": premium_usd,
            "amount": self.TRADE_AMOUNT,
        })

        self._log_trade("开仓（卖出 ATM Straddle）", result)
        logger.info(f"✓ Vol 策略开仓成功: 收入 ${premium_usd:.2f} | IV={atm_iv:.1f}%")
        return result

    async def close_position(self, reason: str) -> Optional[dict]:
        """平仓：买回 Straddle"""
        state = self._load_state()
        if not state.get('has_position'):
            logger.info("Vol 策略: 无持仓，无需平仓")
            return None

        if not await self.authenticate():
            return None

        spot = await self.get_spot_price()
        call_inst = state['call_instrument']
        put_inst = state['put_instrument']

        # 获取当前价格
        async with aiohttp.ClientSession() as s:
            rc = await s.get(f"{MAINNET_URL}/public/ticker", params={"instrument_name": call_inst})
            call_now = (await rc.json()).get('result', {}).get('mark_price', 0)
            rp = await s.get(f"{MAINNET_URL}/public/ticker", params={"instrument_name": put_inst})
            put_now = (await rp.json()).get('result', {}).get('mark_price', 0)

        close_cost_usd = (call_now + put_now) * state['amount'] * spot
        pnl_usd = state['premium_usd'] - close_cost_usd  # 收入 - 平仓成本

        # 买回平仓
        call_order = await self._request("buy", {
            "instrument_name": call_inst, "amount": state['amount'], "type": "market"
        })
        put_order = await self._request("buy", {
            "instrument_name": put_inst, "amount": state['amount'], "type": "market"
        })

        result = {
            "time": datetime.now().isoformat(),
            "spot": spot,
            "atm_iv": 0,
            "call_instrument": call_inst,
            "put_instrument": put_inst,
            "reason": reason,
            "premium_usd": state['premium_usd'],
            "close_cost_usd": close_cost_usd,
            "pnl_usd": pnl_usd,
        }

        # 清除状态
        self._save_state({"has_position": False})
        self._log_trade("平仓", result)

        sign = '+' if pnl_usd >= 0 else ''
        logger.info(f"✓ Vol 策略平仓: {reason} | PnL={sign}${pnl_usd:.2f}")
        return result

    async def check_price_stop(self) -> bool:
        """检查价格止损：BTC 移动超过 ±3%"""
        state = self._load_state()
        if not state.get('has_position'):
            return False
        open_spot = state.get('open_spot', 0)
        if open_spot <= 0:
            return False
        current_spot = await self.get_spot_price()
        move_pct = abs(current_spot - open_spot) / open_spot
        if move_pct >= self.PRICE_STOP_PCT:
            logger.info(f"Vol 策略价格止损触发: BTC 移动 {move_pct*100:.1f}%")
            await self.close_position(f"价格止损（BTC 移动 {move_pct*100:.1f}%）")
            return True
        return False

    async def news_triggered_close(self, news_title: str, score: float, a_score: int, b_score: int):
        """新闻触发平仓"""
        state = self._load_state()
        if not state.get('has_position'):
            return
        reason = f"新闻止损 [{score}/10 A={a_score} B={b_score}]: {news_title[:60]}"
        await self.close_position(reason)

    async def get_positions(self) -> list:
        if not await self.authenticate():
            return []
        result = await self._request("get_positions", {"currency": "BTC", "kind": "option"})
        return result if isinstance(result, list) else []

    async def get_account_summary(self) -> dict:
        if not await self.authenticate():
            return {}
        return await self._request("get_account_summary", {"currency": "BTC"})

    def get_state(self) -> dict:
        return self._load_state()


if __name__ == "__main__":
    async def test():
        strategy = VolAccountStrategy()
        summary = await strategy.get_account_summary()
        print(f"账户余额: {summary.get('balance')} BTC")
        state = strategy.get_state()
        print(f"当前状态: {'有持仓' if state.get('has_position') else '无持仓'}")

    asyncio.run(test())
