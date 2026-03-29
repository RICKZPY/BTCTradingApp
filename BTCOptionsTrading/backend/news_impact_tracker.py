#!/usr/bin/env python3
"""
新闻事后影响追踪器
News Impact Tracker - 追踪每条触发交易的新闻对 BTC 价格 + IV 的实际影响

逻辑：
  - 以交易时间作为 T0（新闻触发下单时刻）
  - 查询 T+1h / T+4h / T+24h 的 BTC 价格（Deribit OHLC 1小时K线）
  - 从 iv_history.db 查询同一合约在 T0 / T+1h / T+4h 的 IV 变化
  - 综合价格变化 + IV 变化生成 straddle 有效性结论

Cron 配置（每小时跑一次，补全未完成的数据点）：
    0 * * * * cd /root/BTCTradingApp/BTCOptionsTrading/backend && venv/bin/python3 news_impact_tracker.py >> logs/news_impact.log 2>&1
"""

import asyncio
import aiohttp
import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

MAINNET_URL = "https://www.deribit.com/api/v2"
BASE_DIR = Path(__file__).parent
TRADE_LOG = BASE_DIR / "logs" / "weighted_sentiment_trades.log"
IMPACT_FILE = BASE_DIR / "data" / "news_impact.json"
IV_DB = BASE_DIR / "data" / "iv_history.db"

CHECKPOINTS = [1, 4, 24]  # 小时


def parse_trades() -> list[dict]:
    """从 trades.log 提取成功交易的新闻信息（只取 23MAR26 及以后）"""
    if not TRADE_LOG.exists():
        return []

    trades = []
    EXCLUDED = ('27MAR26', '20MAR26')

    try:
        content = TRADE_LOG.read_text(encoding='utf-8')
        for entry in content.split('=' * 80):
            entry = entry.strip()
            if not entry or '交易成功: True' not in entry:
                continue

            t = {}
            for line in entry.split('\n'):
                line = line.strip()
                if ':' not in line:
                    continue
                k, v = line.split(':', 1)
                k, v = k.strip(), v.strip()
                if k == '交易时间':
                    t['trade_time'] = v
                elif k == '新闻 ID':
                    t['news_id'] = v
                elif k == '新闻内容':
                    t['news_content'] = v
                elif k == '情绪':
                    t['sentiment'] = v
                elif k == '重要性评分':
                    t['score'] = v
                elif k == '现货价格':
                    try:
                        t['spot_at_trade'] = float(v.replace('$', '').replace(',', ''))
                    except Exception:
                        pass
                elif k == '看涨期权':
                    t['call_instrument'] = v

            if 'trade_time' not in t or 'call_instrument' not in t:
                continue
            if any(ex in t.get('call_instrument', '') for ex in EXCLUDED):
                continue

            trades.append(t)

    except Exception as e:
        logger.error(f"解析 trades.log 失败: {e}")

    return trades


async def fetch_btc_price_at(session: aiohttp.ClientSession, ts: int) -> float:
    """获取指定时间点附近的 BTC 价格（用1小时K线的收盘价）"""
    try:
        # 取该时间点所在小时的K线
        start_ts = (ts // 3600) * 3600 * 1000  # 对齐到小时，毫秒
        end_ts = start_ts + 3600 * 1000

        url = f"{MAINNET_URL}/public/get_tradingview_chart_data"
        params = {
            "instrument_name": "BTC-PERPETUAL",
            "start_timestamp": start_ts,
            "end_timestamp": end_ts,
            "resolution": "60"  # 1小时
        }
        async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            data = await resp.json()
            if 'result' in data and data['result'].get('status') == 'ok':
                closes = data['result'].get('close', [])
                if closes:
                    return float(closes[-1])
    except Exception as e:
        logger.warning(f"获取 ts={ts} 价格失败: {e}")
    return 0.0


def get_iv_changes(instrument: str, t0_ts: int) -> dict:
    """从 iv_history.db 查询合约在 T0 / T+1h / T+4h 的 IV 值及变化"""
    if not IV_DB.exists():
        return {}
    try:
        conn = sqlite3.connect(IV_DB)
        # 查询 T0 前后 10 分钟 + T+1h + T+4h 的数据
        rows = conn.execute(
            "SELECT ts, mark_iv FROM iv_snapshots "
            "WHERE instrument=? AND ts BETWEEN ? AND ? ORDER BY ts",
            (instrument, t0_ts - 600, t0_ts + 4 * 3600 + 600)
        ).fetchall()
        conn.close()

        if not rows:
            return {}

        # T0 最近点
        t0_row = min(rows, key=lambda r: abs(r[0] - t0_ts))
        iv0 = t0_row[1]

        result = {"iv_at_t0": round(iv0, 2)}

        for hours in [1, 4]:
            target_ts = t0_ts + hours * 3600
            nearby = [r for r in rows if abs(r[0] - target_ts) < 600]
            if nearby:
                iv_n = min(nearby, key=lambda r: abs(r[0] - target_ts))[1]
                result[f"iv_chg_t{hours}h"] = round(iv_n - iv0, 2)
                result[f"iv_t{hours}h"] = round(iv_n, 2)

        return result
    except Exception as e:
        logger.warning(f"查询 IV 数据失败 {instrument}: {e}")
        return {}


def get_conclusion(price_changes: dict, iv_changes: dict) -> str:
    """综合价格变化 + IV 变化，生成 straddle 有效性结论"""
    price_vals = [v for v in price_changes.values() if v is not None]
    if not price_vals:
        return "数据不足"

    max_price_abs = max(abs(v) for v in price_vals)
    iv0 = iv_changes.get("iv_at_t0")
    iv_chg_t1 = iv_changes.get("iv_chg_t1h")
    iv_chg_t4 = iv_changes.get("iv_chg_t4h")

    # 判断 IV 趋势
    iv_rose = (iv_chg_t1 is not None and iv_chg_t1 > 1.0) or \
              (iv_chg_t4 is not None and iv_chg_t4 > 1.5)
    iv_fell = (iv_chg_t1 is not None and iv_chg_t1 < -1.0) or \
              (iv_chg_t4 is not None and iv_chg_t4 < -1.5)
    price_moved = max_price_abs >= 2.0
    iv_was_high = iv0 is not None and iv0 >= 55

    # 四象限结论
    if iv_rose and price_moved:
        return f"✅ 新闻有效：价格波动 {max_price_abs:.1f}% + IV 上升，straddle 双赢"
    elif iv_rose and not price_moved:
        return f"⚠️ IV 虚高陷阱：IV 上升但价格仅波动 {max_price_abs:.1f}%，vega 收益被 theta 抵消"
    elif not iv_rose and price_moved:
        if iv_fell:
            return f"📉 靴子落地：价格波动 {max_price_abs:.1f}% 但 IV 下跌，delta 盈利被 vega 损失部分对冲"
        return f"🔶 价格有效但 IV 未响应：波动 {max_price_abs:.1f}%，straddle 轻微盈利"
    else:
        if iv_was_high:
            return f"❌ 无效下单：IV 已在高位（{iv0:.0f}%）且价格仅波动 {max_price_abs:.1f}%，theta + vega 双亏"
        return f"😐 新闻无效：价格仅波动 {max_price_abs:.1f}%，未引发明显波动"


async def update_impact():
    """主逻辑：补全所有交易的价格影响 + IV 变化数据"""
    trades = parse_trades()
    if not trades:
        logger.info("没有交易记录，退出")
        return

    impact_data = {}
    if IMPACT_FILE.exists():
        try:
            impact_data = json.loads(IMPACT_FILE.read_text(encoding='utf-8'))
        except Exception:
            impact_data = {}

    now = datetime.now(timezone.utc)
    updated = 0

    async with aiohttp.ClientSession() as session:
        for trade in trades:
            trade_time_str = trade['trade_time']
            call_inst = trade.get('call_instrument', '')
            key = f"{trade_time_str[:16]}_{call_inst}"

            try:
                t0 = datetime.fromisoformat(trade_time_str)
                if t0.tzinfo is None:
                    t0 = t0.replace(tzinfo=timezone.utc)
            except Exception:
                continue

            t0_ts = int(t0.timestamp())
            spot_t0 = trade.get('spot_at_trade', 0.0)

            # 初始化记录
            if key not in impact_data:
                impact_data[key] = {
                    "trade_time": trade_time_str,
                    "news_id": trade.get('news_id', ''),
                    "news_content": trade.get('news_content', '')[:150],
                    "sentiment": trade.get('sentiment', ''),
                    "score": trade.get('score', ''),
                    "call_instrument": call_inst,
                    "spot_at_trade": spot_t0,
                    "price_changes": {},
                    "iv_changes": {},
                    "conclusion": "待计算"
                }

            record = impact_data[key]
            changes = record.get('price_changes', {})
            needs_update = False

            # ── 价格变化 ──────────────────────────────────────
            for hours in CHECKPOINTS:
                label = f"T+{hours}h"
                target_ts = t0_ts + hours * 3600
                if now < datetime.fromtimestamp(target_ts, tz=timezone.utc):
                    continue
                if label in changes and changes[label] is not None:
                    continue

                price = await fetch_btc_price_at(session, target_ts)
                if price > 0 and spot_t0 > 0:
                    pct = (price - spot_t0) / spot_t0 * 100
                    changes[label] = round(pct, 2)
                    logger.info(f"  {key[:30]}... {label}: {price:.0f} ({pct:+.2f}%)")
                    needs_update = True
                elif price > 0:
                    changes[label] = None
                    needs_update = True

            # ── IV 变化（从本地 SQLite 查，无需网络）────────────
            iv_changes = record.get('iv_changes', {})
            if call_inst and not iv_changes.get('iv_at_t0'):
                iv_data = get_iv_changes(call_inst, t0_ts)
                if iv_data:
                    iv_changes.update(iv_data)
                    needs_update = True
                    logger.info(
                        f"  {key[:30]}... IV@T0={iv_data.get('iv_at_t0')}% "
                        f"T+1h={iv_data.get('iv_chg_t1h'):+.2f}% "
                        f"T+4h={iv_data.get('iv_chg_t4h', 'N/A')}"
                        if iv_data.get('iv_chg_t1h') is not None else
                        f"  {key[:30]}... IV@T0={iv_data.get('iv_at_t0')}%"
                    )

            if needs_update:
                record['price_changes'] = changes
                record['iv_changes'] = iv_changes
                record['conclusion'] = get_conclusion(changes, iv_changes)
                record['updated_at'] = now.strftime("%Y-%m-%d %H:%M UTC")
                updated += 1

    IMPACT_FILE.parent.mkdir(exist_ok=True)
    IMPACT_FILE.write_text(json.dumps(impact_data, ensure_ascii=False, indent=2), encoding='utf-8')
    logger.info(f"完成，更新 {updated} 条，共 {len(impact_data)} 条记录")


if __name__ == "__main__":
    asyncio.run(update_impact())
