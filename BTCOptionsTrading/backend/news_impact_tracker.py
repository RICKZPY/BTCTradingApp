#!/usr/bin/env python3
"""
新闻事后影响追踪器
News Impact Tracker - 追踪每条触发交易的新闻对 BTC 价格的实际影响

逻辑：
  - 以交易时间作为 T0（新闻触发下单时刻）
  - 查询 T+1h / T+4h / T+24h 的 BTC 价格（Deribit OHLC 1小时K线）
  - 计算价格变化百分比，存入 data/news_impact.json

Cron 配置（每小时跑一次，补全未完成的数据点）：
    0 * * * * cd /root/BTCTradingApp/BTCOptionsTrading/backend && venv/bin/python3 news_impact_tracker.py >> logs/news_impact.log 2>&1
"""

import asyncio
import aiohttp
import json
import logging
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

MAINNET_URL = "https://www.deribit.com/api/v2"
BASE_DIR = Path(__file__).parent
TRADE_LOG = BASE_DIR / "logs" / "weighted_sentiment_trades.log"
IMPACT_FILE = BASE_DIR / "data" / "news_impact.json"

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


def get_conclusion(changes: dict) -> str:
    """根据价格变化生成结论"""
    vals = [v for v in changes.values() if v is not None]
    if not vals:
        return "数据不足"

    max_abs = max(abs(v) for v in vals)
    last = vals[-1]

    if max_abs < 1.0:
        return f"该新闻未引发明显波动（最大变化 {max_abs:.1f}%）"
    elif max_abs < 3.0:
        direction = "上涨" if last > 0 else "下跌"
        return f"轻微影响，价格{direction} {abs(last):.1f}%"
    else:
        direction = "大幅上涨" if last > 0 else "大幅下跌"
        return f"显著影响，价格{direction} {abs(last):.1f}%"


async def update_impact():
    """主逻辑：补全所有交易的价格影响数据"""
    trades = parse_trades()
    if not trades:
        logger.info("没有交易记录，退出")
        return

    # 加载已有数据
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
            key = f"{trade_time_str[:16]}_{trade.get('call_instrument', '')}"

            # 解析 T0 时间
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
                    "call_instrument": trade.get('call_instrument', ''),
                    "spot_at_trade": spot_t0,
                    "price_changes": {},
                    "conclusion": "待计算"
                }

            record = impact_data[key]
            changes = record.get('price_changes', {})
            needs_update = False

            for hours in CHECKPOINTS:
                label = f"T+{hours}h"
                target_ts = t0_ts + hours * 3600
                target_dt = datetime.fromtimestamp(target_ts, tz=timezone.utc)

                # 时间点还没到，跳过
                if now < target_dt:
                    continue

                # 已有数据且不为 None，跳过
                if label in changes and changes[label] is not None:
                    continue

                # 获取目标时间点价格
                price = await fetch_btc_price_at(session, target_ts)
                if price > 0 and spot_t0 > 0:
                    pct = (price - spot_t0) / spot_t0 * 100
                    changes[label] = round(pct, 2)
                    logger.info(f"  {key[:30]}... {label}: {price:.0f} ({pct:+.2f}%)")
                    needs_update = True
                elif price > 0:
                    changes[label] = None  # 没有 T0 价格，无法计算
                    needs_update = True

            if needs_update:
                record['price_changes'] = changes
                record['conclusion'] = get_conclusion(changes)
                record['updated_at'] = now.strftime("%Y-%m-%d %H:%M UTC")
                updated += 1

    # 保存
    IMPACT_FILE.parent.mkdir(exist_ok=True)
    IMPACT_FILE.write_text(json.dumps(impact_data, ensure_ascii=False, indent=2), encoding='utf-8')
    logger.info(f"完成，更新 {updated} 条，共 {len(impact_data)} 条记录")


if __name__ == "__main__":
    asyncio.run(update_impact())
