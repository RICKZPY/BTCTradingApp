#!/usr/bin/env python3
"""
每日 PnL 更新器
Daily PnL Updater - 从主网拉取当前价格，计算每个持仓的盈亏

使用方法：
    python pnl_updater.py

Cron 配置（每天 UTC 00:05 跑一次）：
    5 0 * * * cd /root/BTCOptionsTrading/backend && python pnl_updater.py >> logs/pnl_updater.log 2>&1
"""

import asyncio
import aiohttp
import json
import logging
import re
from datetime import datetime
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

MAINNET_URL = "https://www.deribit.com/api/v2"
BASE_DIR = Path(__file__).parent
TRADE_LOG = BASE_DIR / "logs" / "weighted_sentiment_trades.log"
PNL_FILE = BASE_DIR / "data" / "pnl_history.json"


def parse_trade_log():
    """解析交易日志，提取每个持仓的入场信息"""
    if not TRADE_LOG.exists():
        return []

    positions = []
    try:
        content = TRADE_LOG.read_text(encoding='utf-8')
        entries = content.split('=' * 80)

        for entry in entries:
            entry = entry.strip()
            if not entry or '交易成功: True' not in entry:
                continue

            pos = {}
            lines = entry.split('\n')
            current_side = None  # 'call' or 'put'

            for line in lines:
                line = line.strip()
                if not line or ':' not in line:
                    continue
                key, value = line.split(':', 1)
                key, value = key.strip(), value.strip()

                if key == '交易时间':
                    pos['trade_time'] = value
                elif key == '现货价格':
                    pos['spot_price'] = float(value.replace('$', '').replace(',', ''))
                elif key == '看涨期权':
                    pos['call_instrument'] = value
                    current_side = 'call'
                elif key == '看跌期权':
                    pos['put_instrument'] = value
                    current_side = 'put'
                elif key == '入场价(BTC)':
                    if current_side == 'call':
                        pos['call_entry_btc'] = float(value)
                    elif current_side == 'put':
                        pos['put_entry_btc'] = float(value)
                elif key == '权利金' and '入场价(BTC)' not in pos.get('_seen', ''):
                    # 兼容旧日志（没有入场价字段，用权利金代替）
                    btc_val = float(value.replace(' BTC', ''))
                    if current_side == 'call' and 'call_entry_btc' not in pos:
                        pos['call_entry_btc'] = btc_val
                    elif current_side == 'put' and 'put_entry_btc' not in pos:
                        pos['put_entry_btc'] = btc_val
                elif key == '总成本':
                    pos['total_cost'] = float(value.replace('$', '').replace(',', ''))
                elif key == '虚拟交易':
                    pos['is_virtual'] = value == 'True'

            if 'call_instrument' in pos and 'put_instrument' in pos:
                positions.append(pos)

    except Exception as e:
        logger.error(f"解析交易日志失败: {e}")

    return positions


async def get_current_price(session: aiohttp.ClientSession, instrument_name: str) -> dict:
    """从主网获取合约当前价格"""
    try:
        url = f"{MAINNET_URL}/public/ticker"
        async with session.get(url, params={"instrument_name": instrument_name}) as resp:
            data = await resp.json()
            if 'result' in data:
                r = data['result']
                return {
                    "mark_price": r.get('mark_price', 0.0),
                    "mark_iv": r.get('mark_iv', 0.0),
                    "best_bid": r.get('best_bid_price', 0.0),
                    "best_ask": r.get('best_ask_price', 0.0),
                }
    except Exception as e:
        logger.warning(f"获取 {instrument_name} 价格失败: {e}")
    return {"mark_price": 0.0, "mark_iv": 0.0, "best_bid": 0.0, "best_ask": 0.0}


async def get_spot_price(session: aiohttp.ClientSession) -> float:
    """获取 BTC 现货价格"""
    try:
        url = f"{MAINNET_URL}/public/get_index_price"
        async with session.get(url, params={"index_name": "btc_usd"}) as resp:
            data = await resp.json()
            return data['result']['index_price']
    except Exception as e:
        logger.error(f"获取现货价格失败: {e}")
        return 0.0


async def update_pnl():
    """主函数：更新所有持仓的 PnL"""
    logger.info("开始更新 PnL...")

    positions = parse_trade_log()
    if not positions:
        logger.info("没有持仓记录，退出")
        return

    logger.info(f"找到 {len(positions)} 条持仓记录")

    # 加载已有 PnL 数据
    pnl_data = {}
    if PNL_FILE.exists():
        try:
            pnl_data = json.loads(PNL_FILE.read_text(encoding='utf-8'))
        except Exception:
            pnl_data = {}

    async with aiohttp.ClientSession() as session:
        spot_price = await get_spot_price(session)
        if spot_price <= 0:
            logger.error("无法获取现货价格，退出")
            return

        logger.info(f"当前 BTC 现货价格: ${spot_price:.2f}")

        for pos in positions:
            trade_time = pos.get('trade_time', '')
            call_inst = pos.get('call_instrument', '')
            put_inst = pos.get('put_instrument', '')

            if not call_inst or not put_inst:
                continue

            # 用 trade_time + call_instrument 作为唯一 key
            key = f"{trade_time[:16]}_{call_inst}"

            call_entry = pos.get('call_entry_btc', 0.0)
            put_entry = pos.get('put_entry_btc', 0.0)
            entry_spot = pos.get('spot_price', spot_price)
            quantity = 0.1  # 固定数量

            # 获取当前价格
            call_now = await get_current_price(session, call_inst)
            put_now = await get_current_price(session, put_inst)

            call_current = call_now['mark_price']
            put_current = put_now['mark_price']

            # PnL 计算（BTC单位转USD）
            # PnL = (当前价 - 入场价) × 数量 × 现货价
            call_pnl_usd = (call_current - call_entry) * quantity * spot_price
            put_pnl_usd = (put_current - put_entry) * quantity * spot_price
            total_pnl_usd = call_pnl_usd + put_pnl_usd

            # 入场总成本（USD）
            entry_cost_usd = (call_entry + put_entry) * quantity * entry_spot
            pnl_pct = (total_pnl_usd / entry_cost_usd * 100) if entry_cost_usd > 0 else 0.0

            pnl_data[key] = {
                "trade_time": trade_time,
                "call_instrument": call_inst,
                "put_instrument": put_inst,
                "call_entry_btc": call_entry,
                "put_entry_btc": put_entry,
                "call_current_btc": call_current,
                "put_current_btc": put_current,
                "call_pnl_usd": round(call_pnl_usd, 2),
                "put_pnl_usd": round(put_pnl_usd, 2),
                "total_pnl_usd": round(total_pnl_usd, 2),
                "pnl_pct": round(pnl_pct, 2),
                "entry_cost_usd": round(entry_cost_usd, 2),
                "spot_price": spot_price,
                "is_virtual": pos.get('is_virtual', False),
                "updated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
            }

            logger.info(
                f"{call_inst[:20]}... | "
                f"Call PnL: ${call_pnl_usd:+.2f} | "
                f"Put PnL: ${put_pnl_usd:+.2f} | "
                f"Total: ${total_pnl_usd:+.2f} ({pnl_pct:+.1f}%)"
            )

    # 保存 PnL 数据
    PNL_FILE.parent.mkdir(exist_ok=True)
    PNL_FILE.write_text(
        json.dumps(pnl_data, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    logger.info(f"PnL 数据已保存到 {PNL_FILE}，共 {len(pnl_data)} 条记录")


if __name__ == "__main__":
    asyncio.run(update_pnl())
