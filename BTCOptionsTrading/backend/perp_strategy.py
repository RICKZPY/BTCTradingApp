#!/usr/bin/env python3
"""
新闻驱动永续合约策略
Sentiment-Driven BTC-PERPETUAL Strategy

逻辑：
  正面新闻（≥7分）→ 买入多头 $1000
  负面新闻（≥7分）→ 卖出空头 $1000
  3 天后自动平仓（cron 每小时检查）

日志：logs/perp_trades.log
状态：data/perp_positions.json
"""

import asyncio
import aiohttp
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent
LOG_FILE = BASE_DIR / "logs" / "perp_trades.log"
STATE_FILE = BASE_DIR / "data" / "perp_positions.json"
TESTNET_URL = "https://test.deribit.com/api/v2"
MAINNET_URL = "https://www.deribit.com/api/v2"

TRADE_AMOUNT_USD = 1000   # 每笔 $1000
HOLD_DAYS = 3             # 持仓 3 天后平仓
MIN_SCORE = 7             # 最低触发分数

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


ACCOUNTS = {
    "qCoXRSu6": os.getenv('VOL_STRATEGY_DERIBIT_API_SECRET',
                           'GhL6l32FUgm7tKgtRJVsngdF5Cp5j-JhVIr5Js4kvTQ'),
    "vXkaBDto": os.getenv('DERIBIT_API_SECRET',
                           'J54Ccsff9g5PlYK-ELRVunkvnST-cZ6puVBXbhwYrnY'),
}


def load_positions() -> list:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding='utf-8'))
        except Exception:
            pass
    return []


def save_positions(positions: list):
    STATE_FILE.parent.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps(positions, ensure_ascii=False, indent=2), encoding='utf-8')


def log_trade(entry: str):
    LOG_FILE.parent.mkdir(exist_ok=True)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(entry)


async def authenticate(session: aiohttp.ClientSession, api_key: str, api_secret: str) -> Optional[str]:
    try:
        r = await session.get(f"{TESTNET_URL}/public/auth", params={
            "grant_type": "client_credentials",
            "client_id": api_key, "client_secret": api_secret
        })
        d = await r.json()
        return d['result']['access_token']
    except Exception as e:
        logger.error(f"认证失败 {api_key}: {e}")
        return None


async def get_spot_price(session: aiohttp.ClientSession) -> float:
    try:
        r = await session.get(f"{MAINNET_URL}/public/get_index_price",
                              params={"index_name": "btc_usd"})
        return (await r.json())['result']['index_price']
    except Exception:
        return 0.0


async def open_position(api_key: str, api_secret: str,
                        direction: str, news_title: str, score: float,
                        sentiment: str) -> Optional[dict]:
    """开仓：direction = 'buy'（多）或 'sell'（空）"""
    async with aiohttp.ClientSession() as session:
        token = await authenticate(session, api_key, api_secret)
        if not token:
            return None

        spot = await get_spot_price(session)
        headers = {"Authorization": f"Bearer {token}"}

        method = "buy" if direction == "buy" else "sell"
        r = await session.get(f"{TESTNET_URL}/private/{method}", params={
            "instrument_name": "BTC-PERPETUAL",
            "amount": TRADE_AMOUNT_USD,
            "type": "market",
            "label": f"sentiment_{score}"
        }, headers=headers)
        result = await r.json()

        if 'result' not in result:
            logger.error(f"下单失败 {api_key}: {result}")
            return None

        order = result['result'].get('order', {})
        order_id = order.get('order_id', '')
        avg_price = order.get('average_price', spot)

        close_time = (datetime.now(timezone.utc) + timedelta(days=HOLD_DAYS)).isoformat()

        pos = {
            "account": api_key,
            "order_id": order_id,
            "direction": direction,
            "amount_usd": TRADE_AMOUNT_USD,
            "entry_price": avg_price,
            "entry_spot": spot,
            "open_time": datetime.now(timezone.utc).isoformat(),
            "close_time": close_time,
            "news_title": news_title[:80],
            "score": score,
            "sentiment": sentiment,
            "closed": False,
        }

        log_entry = (
            f"\n{'='*80}\n"
            f"开仓: BTC-PERPETUAL {'多头' if direction=='buy' else '空头'}\n"
            f"账户: {api_key}\n"
            f"时间: {pos['open_time']}\n"
            f"新闻: [{score}/10] {news_title[:70]}\n"
            f"情绪: {sentiment}\n"
            f"方向: {'买入多头' if direction=='buy' else '卖出空头'} ${TRADE_AMOUNT_USD}\n"
            f"入场价: ${avg_price:,.2f}\n"
            f"订单ID: {order_id}\n"
            f"计划平仓: {close_time[:16]}\n"
            f"{'='*80}\n"
        )
        log_trade(log_entry)
        logger.info(f"✓ 开仓 {api_key}: {'多' if direction=='buy' else '空'} ${TRADE_AMOUNT_USD} @ ${avg_price:,.0f}")
        return pos


async def close_position_by_order(api_key: str, api_secret: str, pos: dict) -> bool:
    """平仓"""
    async with aiohttp.ClientSession() as session:
        token = await authenticate(session, api_key, api_secret)
        if not token:
            return False

        spot = await get_spot_price(session)
        headers = {"Authorization": f"Bearer {token}"}

        # 反向平仓
        close_method = "sell" if pos['direction'] == "buy" else "buy"
        r = await session.get(f"{TESTNET_URL}/private/{close_method}", params={
            "instrument_name": "BTC-PERPETUAL",
            "amount": pos['amount_usd'],
            "type": "market",
            "label": f"close_{pos['order_id'][:8]}"
        }, headers=headers)
        result = await r.json()

        if 'result' not in result:
            logger.error(f"平仓失败 {api_key}: {result}")
            return False

        order = result['result'].get('order', {})
        close_price = order.get('average_price', spot)

        # 计算 PnL
        entry = pos.get('entry_price', pos.get('entry_spot', spot))
        if pos['direction'] == 'buy':
            pnl_pct = (close_price - entry) / entry * 100
        else:
            pnl_pct = (entry - close_price) / entry * 100
        pnl_usd = pnl_pct / 100 * pos['amount_usd']

        sign = '+' if pnl_usd >= 0 else ''
        log_entry = (
            f"\n{'='*80}\n"
            f"平仓: BTC-PERPETUAL {'多头' if pos['direction']=='buy' else '空头'}\n"
            f"账户: {api_key}\n"
            f"时间: {datetime.now(timezone.utc).isoformat()}\n"
            f"入场价: ${entry:,.2f} → 平仓价: ${close_price:,.2f}\n"
            f"PnL: {sign}{pnl_usd:.2f} USD ({sign}{pnl_pct:.2f}%)\n"
            f"{'='*80}\n"
        )
        log_trade(log_entry)
        logger.info(f"✓ 平仓 {api_key}: PnL={sign}${pnl_usd:.2f}")
        return True


async def execute_news_trade(news_title: str, score: float, sentiment: str):
    """根据新闻执行两个账户的交易"""
    if score < MIN_SCORE:
        return

    # 判断方向
    sentiment_lower = sentiment.lower()
    is_positive = any(w in sentiment_lower for w in ['positive', '积极', '正面', 'bullish'])
    is_negative = any(w in sentiment_lower for w in ['negative', '负面', '消极', 'bearish'])

    if not is_positive and not is_negative:
        logger.info(f"情绪不明确（{sentiment}），跳过")
        return

    direction = "buy" if is_positive else "sell"
    positions = load_positions()

    for api_key, api_secret in ACCOUNTS.items():
        # 检查该账户是否已有未平仓的同方向持仓（48h 内）
        recent = [p for p in positions
                  if p['account'] == api_key and not p['closed']
                  and p['direction'] == direction]
        if recent:
            logger.info(f"{api_key}: 已有{direction}方向持仓，跳过")
            continue

        pos = await open_position(api_key, api_secret, direction, news_title, score, sentiment)
        if pos:
            positions.append(pos)

    save_positions(positions)


async def check_and_close_expired():
    """检查并平仓到期持仓"""
    positions = load_positions()
    now = datetime.now(timezone.utc)
    updated = False

    for pos in positions:
        if pos.get('closed'):
            continue
        close_time = datetime.fromisoformat(pos['close_time'])
        if now >= close_time:
            api_key = pos['account']
            api_secret = ACCOUNTS.get(api_key, '')
            if api_secret:
                success = await close_position_by_order(api_key, api_secret, pos)
                if success:
                    pos['closed'] = True
                    updated = True

    if updated:
        save_positions(positions)


if __name__ == "__main__":
    asyncio.run(check_and_close_expired())
