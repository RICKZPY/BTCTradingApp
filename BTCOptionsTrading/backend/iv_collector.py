#!/usr/bin/env python3
"""
IV 采集器 - 每5分钟采集持仓合约的隐含波动率
IV Collector - Collects mark_iv for held option contracts every 5 minutes

数据存储：SQLite -> data/iv_history.db
表结构：iv_snapshots(instrument, ts, mark_iv, mark_price, spot_price)

Cron 配置（每5分钟）：
    */5 * * * * cd /root/BTCOptionsTrading/backend && python3 iv_collector.py >> logs/iv_collector.log 2>&1
"""

import asyncio
import aiohttp
import sqlite3
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

MAINNET_URL = "https://www.deribit.com/api/v2"
BASE_DIR = Path(__file__).parent
TRADE_LOG = BASE_DIR / "logs" / "weighted_sentiment_trades.log"
DB_PATH = BASE_DIR / "data" / "iv_history.db"


def init_db():
    """初始化数据库"""
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS iv_snapshots (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            instrument TEXT NOT NULL,
            ts        INTEGER NOT NULL,   -- Unix timestamp (seconds)
            mark_iv   REAL,               -- 隐含波动率 (%)
            mark_price REAL,              -- 期权 mark price (BTC)
            spot_price REAL,              -- BTC 现货价格
            UNIQUE(instrument, ts)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_instrument_ts ON iv_snapshots(instrument, ts)")
    conn.commit()
    conn.close()


def is_expired(instrument: str) -> bool:
    """判断合约是否已到期（解析合约名中的到期日）
    
    格式: BTC-23MAR26-70500-C -> 到期日 23 MAR 2026 UTC 08:00
    Deribit 期权到期时间为 UTC 08:00
    """
    try:
        # 提取日期部分，如 "23MAR26"
        m = re.search(r'BTC-(\d{1,2})([A-Z]{3})(\d{2})-', instrument)
        if not m:
            return False
        day, mon_str, yr2 = m.group(1), m.group(2), m.group(3)
        expiry = datetime.strptime(f"{day}{mon_str}20{yr2} 08:00", "%d%b%Y %H:%M")
        expiry = expiry.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) >= expiry
    except Exception:
        return False


def get_active_instruments() -> list[str]:
    """从交易日志中提取所有持仓合约（去重）"""
    if not TRADE_LOG.exists():
        return []

    instruments = set()
    try:
        content = TRADE_LOG.read_text(encoding='utf-8')
        entries = content.split('=' * 80)
        for entry in entries:
            if '交易成功: True' not in entry:
                continue
            for line in entry.split('\n'):
                line = line.strip()
                # 匹配 "看涨期权: BTC-..." 或 "看跌期权: BTC-..."
                if line.startswith('看涨期权:') or line.startswith('看跌期权:'):
                    val = line.split(':', 1)[1].strip()
                    if re.match(r'^BTC-\d+[A-Z]+\d+-\d+-[CP]$', val):
                        instruments.add(val)
    except Exception as e:
        logger.error(f"解析交易日志失败: {e}")

    return sorted(instruments)


async def fetch_ticker(session: aiohttp.ClientSession, instrument: str) -> dict:
    """获取合约 ticker（mark_iv + mark_price）"""
    try:
        url = f"{MAINNET_URL}/public/ticker"
        async with session.get(url, params={"instrument_name": instrument},
                               timeout=aiohttp.ClientTimeout(total=8)) as resp:
            data = await resp.json()
            if 'result' in data:
                r = data['result']
                return {
                    "mark_iv": r.get('mark_iv'),       # 可能为 None（深度虚值合约）
                    "mark_price": r.get('mark_price'),
                }
    except Exception as e:
        logger.warning(f"获取 {instrument} ticker 失败: {e}")
    return {"mark_iv": None, "mark_price": None}


async def fetch_spot(session: aiohttp.ClientSession) -> float:
    """获取 BTC 现货价格"""
    try:
        url = f"{MAINNET_URL}/public/get_index_price"
        async with session.get(url, params={"index_name": "btc_usd"},
                               timeout=aiohttp.ClientTimeout(total=8)) as resp:
            data = await resp.json()
            return data['result']['index_price']
    except Exception as e:
        logger.error(f"获取现货价格失败: {e}")
    return 0.0


async def collect():
    """主采集逻辑"""
    instruments = get_active_instruments()
    if not instruments:
        logger.info("没有持仓合约，退出")
        return

    logger.info(f"采集 {len(instruments)} 个合约的 IV: {instruments}")

    now_ts = int(datetime.utcnow().timestamp())
    # 对齐到5分钟整点，方便后续查询
    now_ts = (now_ts // 300) * 300

    init_db()
    conn = sqlite3.connect(DB_PATH)

    async with aiohttp.ClientSession() as session:
        spot = await fetch_spot(session)

        for inst in instruments:
            if is_expired(inst):
                logger.info(f"  {inst}: 已到期，跳过")
                continue

            ticker = await fetch_ticker(session, inst)
            mark_iv = ticker['mark_iv']
            mark_price = ticker['mark_price']

            if mark_iv is None:
                logger.warning(f"{inst}: mark_iv 为空（可能深度虚值），跳过")
                continue

            try:
                conn.execute(
                    "INSERT OR IGNORE INTO iv_snapshots(instrument, ts, mark_iv, mark_price, spot_price) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (inst, now_ts, mark_iv, mark_price, spot)
                )
                logger.info(f"  {inst}: IV={mark_iv:.2f}%, price={mark_price:.6f} BTC, spot=${spot:.0f}")
            except Exception as e:
                logger.error(f"写入 {inst} 失败: {e}")

    conn.commit()
    conn.close()
    logger.info("采集完成")


if __name__ == "__main__":
    asyncio.run(collect())
