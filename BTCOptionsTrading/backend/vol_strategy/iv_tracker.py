"""
IV Tracker - DVOL 历史数据采集 + IV Rank 计算

数据来源：Deribit 公开接口（无需 API Key）
  GET /public/get_volatility_index_data  → DVOL 时间序列
  GET /public/ticker                     → 单合约 mark_iv

IV Rank 公式：
  rank = (current_dvol - min_30d) / (max_30d - min_30d) * 100
  rank < 30  → 低波动，买入机会
  rank > 70  → 高波动，不适合买入
"""

import asyncio
import aiohttp
import sqlite3
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from . import config

logger = logging.getLogger("vol_strategy.iv_tracker")


class IVTracker:
    """DVOL 历史数据管理 + IV Rank 计算"""

    DERIBIT_PUBLIC = "https://test.deribit.com/api/v2" if config.DERIBIT_TESTNET \
                     else "https://www.deribit.com/api/v2"

    def __init__(self):
        self._init_db()

    # ── 数据库初始化 ──────────────────────────────────

    def _init_db(self):
        with sqlite3.connect(config.DB_DVOL) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS dvol_history (
                    ts    INTEGER PRIMARY KEY,  -- unix timestamp (秒)
                    dvol  REAL NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_dvol_ts ON dvol_history(ts)")
            conn.commit()

    # ── 数据采集 ──────────────────────────────────────

    async def bootstrap(self):
        """
        冷启动：一次性拉取过去 30 天的 DVOL 历史数据。
        只在数据库为空时调用一次。
        """
        with sqlite3.connect(config.DB_DVOL) as conn:
            count = conn.execute("SELECT COUNT(*) FROM dvol_history").fetchone()[0]

        if count >= 100:
            logger.info(f"DVOL 历史数据已有 {count} 条，跳过冷启动")
            return

        logger.info("冷启动：拉取过去 30 天 DVOL 数据...")
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        start_ms = now_ms - config.DVOL_HISTORY_DAYS * 86400 * 1000

        url = f"{self.DERIBIT_PUBLIC}/public/get_volatility_index_data"
        params = {
            "currency": "BTC",
            "resolution": "3600",   # 1 小时粒度
            "start_timestamp": start_ms,
            "end_timestamp": now_ms,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    data = await resp.json()

            rows = data.get("result", {}).get("data", [])
            if not rows:
                logger.warning("冷启动：未获取到 DVOL 数据")
                return

            # rows 格式：[[ts_ms, open, high, low, close], ...]
            with sqlite3.connect(config.DB_DVOL) as conn:
                conn.executemany(
                    "INSERT OR IGNORE INTO dvol_history(ts, dvol) VALUES(?,?)",
                    [(int(r[0] / 1000), float(r[4])) for r in rows]  # 用 close 价
                )
                conn.commit()

            logger.info(f"冷启动完成，写入 {len(rows)} 条 DVOL 数据")

        except Exception as e:
            logger.error(f"冷启动失败: {e}")

    async def fetch_latest_dvol(self) -> Optional[float]:
        """
        拉取最新 DVOL 值并写入数据库。
        每小时调用一次即可。
        """
        url = f"{self.DERIBIT_PUBLIC}/public/get_volatility_index_data"
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        params = {
            "currency": "BTC",
            "resolution": "3600",
            "start_timestamp": now_ms - 2 * 3600 * 1000,  # 最近 2 小时
            "end_timestamp": now_ms,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    data = await resp.json()

            rows = data.get("result", {}).get("data", [])
            if not rows:
                return None

            latest = rows[-1]
            ts   = int(latest[0] / 1000)
            dvol = float(latest[4])

            with sqlite3.connect(config.DB_DVOL) as conn:
                conn.execute("INSERT OR IGNORE INTO dvol_history(ts, dvol) VALUES(?,?)", (ts, dvol))
                conn.commit()

            logger.info(f"DVOL 更新: {dvol:.2f}")
            return dvol

        except Exception as e:
            logger.error(f"获取 DVOL 失败: {e}")
            return None

    # ── IV Rank 计算 ──────────────────────────────────

    def calculate_iv_rank(self, current_dvol: float) -> float:
        """
        计算 IV Rank（0-100）。
        使用过去 DVOL_HISTORY_DAYS 天的数据。
        """
        cutoff = int((datetime.now(timezone.utc) - timedelta(days=config.DVOL_HISTORY_DAYS)).timestamp())

        with sqlite3.connect(config.DB_DVOL) as conn:
            rows = conn.execute(
                "SELECT dvol FROM dvol_history WHERE ts >= ? ORDER BY ts",
                (cutoff,)
            ).fetchall()

        if len(rows) < 10:
            logger.warning(f"历史数据不足（{len(rows)} 条），返回默认 IV Rank 50")
            return 50.0

        values = [r[0] for r in rows]
        lo, hi = min(values), max(values)

        if hi == lo:
            return 50.0

        rank = (current_dvol - lo) / (hi - lo) * 100
        rank = max(0.0, min(100.0, rank))
        logger.info(f"IV Rank: {rank:.1f}  (DVOL={current_dvol:.2f}, 30d range [{lo:.2f}, {hi:.2f}])")
        return rank

    async def get_atm_iv(self, instrument_name: str) -> float:
        """
        获取单个合约的 mark_iv（用于记录入场 IV，方便后续计算 IV 扩张）
        """
        url = f"{self.DERIBIT_PUBLIC}/public/ticker"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params={"instrument_name": instrument_name},
                                       timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    data = await resp.json()
            return float(data["result"].get("mark_iv", 0.0)) / 100.0
        except Exception as e:
            logger.error(f"获取 mark_iv 失败 ({instrument_name}): {e}")
            return 0.0
