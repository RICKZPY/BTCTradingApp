#!/usr/bin/env python3
"""
止盈监控器 - 主账户 ATM Straddle 止盈
Take Profit Monitor for ATM Straddle positions

止盈条件（满足任一即触发）：
  1. BTC 价格相对入场价移动 >= TP_PRICE_PCT（默认 3%）
  2. 当前 straddle 价值相对入场成本盈利 >= TP_PNL_PCT（默认 10%）

Cron 配置（每 5 分钟）：
    */5 * * * * cd /root/BTCTradingApp/BTCOptionsTrading/backend && venv/bin/python3 take_profit_monitor.py >> logs/take_profit.log 2>&1
"""

import asyncio
import aiohttp
import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent
TRADE_LOG = BASE_DIR / "logs" / "weighted_sentiment_trades.log"
TP_LOG = BASE_DIR / "logs" / "take_profit.log"
MAINNET_URL = "https://www.deribit.com/api/v2"
TESTNET_URL = "https://test.deribit.com/api/v2"

# 止盈止损参数
TP_PRICE_PCT = 0.03   # BTC 价格移动 ±3% → 止盈
TP_PNL_PCT = 0.10     # straddle 盈利 10% → 止盈
SL_PNL_PCT = -0.015   # straddle 亏损 1.5% → 止损（新增）

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_KEY = os.getenv('WEIGHTED_SENTIMENT_DERIBIT_API_KEY')
API_SECRET = os.getenv('WEIGHTED_SENTIMENT_DERIBIT_API_SECRET')
TESTNET = True


def parse_active_positions() -> list:
    """从 trades.log 解析活跃持仓（未到期的）"""
    if not TRADE_LOG.exists():
        return []

    from datetime import timedelta
    EXCLUDED = ('27MAR26', '20MAR26')
    positions = []

    try:
        content = TRADE_LOG.read_text(encoding='utf-8')
        for entry in content.split('=' * 80):
            entry = entry.strip()
            if not entry or '交易成功: True' not in entry:
                continue

            pos = {}
            current_side = None
            for line in entry.split('\n'):
                line = line.strip()
                if ':' not in line:
                    continue
                k, v = line.split(':', 1)
                k, v = k.strip(), v.strip()
                if k == '交易时间':
                    pos['trade_time'] = v
                elif k == '现货价格':
                    try:
                        pos['entry_spot'] = float(v.replace('$', '').replace(',', ''))
                    except Exception:
                        pass
                elif k == '看涨期权':
                    pos['call_instrument'] = v
                    current_side = 'call'
                elif k == '看跌期权':
                    pos['put_instrument'] = v
                    current_side = 'put'
                elif k == '入场价(BTC)':
                    if current_side == 'call':
                        pos['call_entry'] = float(v)
                    elif current_side == 'put':
                        pos['put_entry'] = float(v)
                elif k == '权利金' and current_side:
                    btc_val = float(v.replace(' BTC', ''))
                    if current_side == 'call' and 'call_entry' not in pos:
                        pos['call_entry'] = btc_val
                    elif current_side == 'put' and 'put_entry' not in pos:
                        pos['put_entry'] = btc_val
                elif k == '下单数量':
                    try:
                        pos['quantity'] = float(v.replace(' BTC', ''))
                    except Exception:
                        pos['quantity'] = 0.1

            if 'call_instrument' not in pos or 'put_instrument' not in pos:
                continue
            if any(ex in pos.get('call_instrument', '') for ex in EXCLUDED):
                continue

            # 检查是否已到期
            call_inst = pos['call_instrument']
            m = re.search(r'BTC-(\d{1,2})([A-Z]{3})(\d{2})-', call_inst)
            if m:
                try:
                    expiry = datetime.strptime(
                        f"{m.group(1)}{m.group(2)}20{m.group(3)} 08:00", "%d%b%Y %H:%M"
                    ).replace(tzinfo=timezone.utc)
                    if datetime.now(timezone.utc) >= expiry:
                        continue  # 已到期，跳过
                except Exception:
                    pass

            positions.append(pos)

    except Exception as e:
        logger.error(f"解析持仓失败: {e}")

    return positions


async def get_spot_price(session: aiohttp.ClientSession) -> float:
    try:
        async with session.get(f"{MAINNET_URL}/public/get_index_price",
                               params={"index_name": "btc_usd"}) as r:
            d = await r.json()
            return d['result']['index_price']
    except Exception:
        return 0.0


async def get_mark_price(session: aiohttp.ClientSession, instrument: str) -> float:
    try:
        async with session.get(f"{MAINNET_URL}/public/ticker",
                               params={"instrument_name": instrument}) as r:
            d = await r.json()
            return d.get('result', {}).get('mark_price', 0.0)
    except Exception:
        return 0.0


async def close_position(session: aiohttp.ClientSession, token: str,
                         call_inst: str, put_inst: str, quantity: float, reason: str):
    """平仓：卖出 call 和 put"""
    base = TESTNET_URL if TESTNET else MAINNET_URL
    headers = {"Authorization": f"Bearer {token}"}
    try:
        async with session.get(f"{base}/private/sell",
                               params={"instrument_name": call_inst, "amount": quantity, "type": "market"},
                               headers=headers) as r:
            call_result = await r.json()
        async with session.get(f"{base}/private/sell",
                               params={"instrument_name": put_inst, "amount": quantity, "type": "market"},
                               headers=headers) as r:
            put_result = await r.json()

        call_oid = call_result.get('result', {}).get('order', {}).get('order_id', 'FAILED')
        put_oid = put_result.get('result', {}).get('order', {}).get('order_id', 'FAILED')

        log_entry = (
            f"\n{'='*80}\n"
            f"止盈平仓\n"
            f"时间: {datetime.now().isoformat()}\n"
            f"原因: {reason}\n"
            f"卖出 Call: {call_inst} | 订单: {call_oid}\n"
            f"卖出 Put:  {put_inst} | 订单: {put_oid}\n"
            f"{'='*80}\n"
        )
        with open(TP_LOG, 'a', encoding='utf-8') as f:
            f.write(log_entry)

        logger.info(f"✓ 止盈平仓: {call_inst} | {reason}")
        return True
    except Exception as e:
        logger.error(f"止盈平仓失败: {e}")
        return False


async def monitor():
    positions = parse_active_positions()
    if not positions:
        logger.debug("无活跃持仓")
        return

    logger.info(f"检查 {len(positions)} 个活跃持仓的止盈条件")

    # 认证
    base = TESTNET_URL if TESTNET else MAINNET_URL
    async with aiohttp.ClientSession() as session:
        r = await session.get(f"{base}/public/auth", params={
            "grant_type": "client_credentials",
            "client_id": API_KEY, "client_secret": API_SECRET
        })
        d = await r.json()
        if 'result' not in d:
            logger.error("认证失败")
            return
        token = d['result']['access_token']

        spot = await get_spot_price(session)
        if spot <= 0:
            return

        for pos in positions:
            call_inst = pos['call_instrument']
            put_inst = pos['put_instrument']
            entry_spot = pos.get('entry_spot', 0)
            call_entry = pos.get('call_entry', 0)
            put_entry = pos.get('put_entry', 0)
            quantity = pos.get('quantity', 0.1)

            if not entry_spot or not call_entry:
                continue

            # 条件 1：价格移动止盈
            price_move = abs(spot - entry_spot) / entry_spot
            if price_move >= TP_PRICE_PCT:
                reason = f"价格移动 {price_move*100:.1f}%（入场 ${entry_spot:,.0f} → 现在 ${spot:,.0f}）"
                await close_position(session, token, call_inst, put_inst, quantity, reason)
                continue

            # 条件 2：PnL 止盈
            call_now = await get_mark_price(session, call_inst)
            put_now = await get_mark_price(session, put_inst)
            if call_now > 0 and put_now > 0:
                entry_cost = (call_entry + put_entry) * quantity * entry_spot
                current_value = (call_now + put_now) * quantity * spot
                pnl_pct = (current_value - entry_cost) / entry_cost if entry_cost > 0 else 0
                if pnl_pct >= TP_PNL_PCT:
                    reason = f"PnL 止盈 {pnl_pct*100:.1f}%（成本 ${entry_cost:.0f} → 现值 ${current_value:.0f}）"
                    await close_position(session, token, call_inst, put_inst, quantity, reason)
                elif pnl_pct <= SL_PNL_PCT:
                    reason = f"PnL 止损 {pnl_pct*100:.1f}%（成本 ${entry_cost:.0f} → 现值 ${current_value:.0f}）"
                    await close_position(session, token, call_inst, put_inst, quantity, reason)


if __name__ == "__main__":
    asyncio.run(monitor())
