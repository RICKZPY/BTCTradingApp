"""
Executor - 开仓执行器

根据 Signal 执行实际交易：
  BUY_STRADDLE → 买入 ATM Call + ATM Put
  BUY_CALL     → 只买入 ATM Call
  BUY_PUT      → 只买入 ATM Put

使用 DeribitTrader（已有，复用）
"""

import asyncio
import aiohttp
import logging
import re
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from . import config
from .signal_engine import Signal

logger = logging.getLogger("vol_strategy.executor")


@dataclass
class TradeRecord:
    news_id: str
    news_score: int
    news_sentiment: str
    action: str
    confidence: int
    spot_price: float
    call_instrument: Optional[str]
    put_instrument: Optional[str]
    call_order_id: Optional[str]
    put_order_id: Optional[str]
    call_premium: float
    put_premium: float
    total_cost_usd: float
    entry_iv: float
    iv_rank: float
    dvol: float
    fear_greed: int
    success: bool
    error: Optional[str]
    trade_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class Executor:
    """开仓执行器"""

    DERIBIT_PUBLIC = "https://test.deribit.com/api/v2" if config.DERIBIT_TESTNET \
                     else "https://www.deribit.com/api/v2"

    def __init__(self, trader):
        """
        Args:
            trader: DeribitTrader 实例（已认证）
        """
        self.trader = trader
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(config.DB_POSITIONS) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id               INTEGER PRIMARY KEY AUTOINCREMENT,
                    news_id          TEXT,
                    news_score       INTEGER,
                    news_sentiment   TEXT,
                    action           TEXT,
                    confidence       INTEGER,
                    spot_price       REAL,
                    call_instrument  TEXT,
                    put_instrument   TEXT,
                    call_order_id    TEXT,
                    put_order_id     TEXT,
                    call_premium     REAL,
                    put_premium      REAL,
                    total_cost_usd   REAL,
                    entry_iv         REAL,
                    iv_rank          REAL,
                    dvol             REAL,
                    fear_greed       INTEGER,
                    success          INTEGER,
                    error            TEXT,
                    trade_time       TEXT,
                    -- 平仓字段（后续由 position_monitor 填写）
                    close_time       TEXT,
                    close_reason     TEXT,
                    pnl_pct          REAL,
                    status           TEXT DEFAULT 'open'
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_trades_news ON trades(news_id)")
            conn.commit()

    # ── 主入口 ────────────────────────────────────────

    async def execute(self, signal: Signal, news_id: str) -> TradeRecord:
        """
        根据信号执行开仓。

        Args:
            signal : SignalEngine 生成的信号
            news_id: 触发本次交易的新闻 ID
        """
        logger.info(f"执行开仓 | action={signal.action} | confidence={signal.confidence} | news={news_id}")

        # 1. 获取现货价格
        spot_price = await self._get_spot_price()
        if spot_price <= 0:
            return self._fail_record(signal, news_id, "无法获取现货价格")

        # 2. 查找 ATM 期权
        call_inst, put_inst = await self._find_atm_options(spot_price)
        if not call_inst or not put_inst:
            return self._fail_record(signal, news_id, "未找到合适的 ATM 期权")

        # 3. 获取期权价格
        call_price = await self._get_mark_price(call_inst)
        put_price  = await self._get_mark_price(put_inst)

        # 4. 下单
        call_order_id, put_order_id = None, None
        error = None

        # 获取最小下单量并对齐
        trade_amount = await self._get_safe_amount(call_inst)

        if signal.action in ("BUY_STRADDLE", "BUY_CALL"):
            result = await self.trader.buy(call_inst, trade_amount, order_type="market")
            if result:
                call_order_id = result.get("order", {}).get("order_id")
                logger.info(f"Call 买入成功: {call_inst} | order_id={call_order_id}")
            else:
                return self._fail_record(signal, news_id, f"Call 下单失败: {call_inst}")

        if signal.action in ("BUY_STRADDLE", "BUY_PUT"):
            result = await self.trader.buy(put_inst, trade_amount, order_type="market")
            if result:
                put_order_id = result.get("order", {}).get("order_id")
                logger.info(f"Put 买入成功: {put_inst} | order_id={put_order_id}")
            else:
                # 回滚 Call
                if call_order_id:
                    await self.trader.close_position(call_inst)
                    logger.warning(f"Put 下单失败，已回滚 Call: {call_inst}")
                return self._fail_record(signal, news_id, f"Put 下单失败: {put_inst}")

        # 5. 计算总成本
        total_cost = 0.0
        if call_order_id:
            total_cost += call_price * trade_amount * spot_price
        if put_order_id:
            total_cost += put_price * trade_amount * spot_price

        # 6. 获取入场 IV（用 Call 的 mark_iv 代表）
        entry_iv = await self._get_mark_iv(call_inst)

        record = TradeRecord(
            news_id=news_id,
            news_score=signal.news_score,
            news_sentiment=signal.news_sentiment,
            action=signal.action,
            confidence=signal.confidence,
            spot_price=spot_price,
            call_instrument=call_inst if call_order_id else None,
            put_instrument=put_inst if put_order_id else None,
            call_order_id=call_order_id,
            put_order_id=put_order_id,
            call_premium=call_price,
            put_premium=put_price,
            total_cost_usd=total_cost,
            entry_iv=entry_iv,
            iv_rank=signal.iv_rank,
            dvol=signal.dvol,
            fear_greed=signal.fear_greed,
            success=True,
            error=None,
        )

        self._save_trade(record)
        logger.info(f"开仓完成 | 总成本 ${total_cost:.2f} | entry_iv={entry_iv*100:.1f}%")
        return record

    # ── ATM 期权查找 ──────────────────────────────────

    async def _find_atm_options(self, spot_price: float) -> Tuple[Optional[str], Optional[str]]:
        """查找到期日在 EXPIRY_DAYS_MIN ~ EXPIRY_DAYS_MAX 之间、执行价最接近现货的 Call 和 Put"""
        url = f"{self.DERIBIT_PUBLIC}/public/get_instruments"
        params = {"currency": "BTC", "kind": "option", "expired": "false"}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params,
                                       timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    data = await resp.json()

            now = datetime.now(timezone.utc)
            min_exp = now + timedelta(days=config.EXPIRY_DAYS_MIN)
            max_exp = now + timedelta(days=config.EXPIRY_DAYS_MAX)

            calls, puts = [], []
            for inst in data.get("result", []):
                exp_ts = inst.get("expiration_timestamp", 0)
                exp_dt = datetime.fromtimestamp(exp_ts / 1000, tz=timezone.utc)
                if not (min_exp <= exp_dt <= max_exp):
                    continue

                strike = inst.get("strike", 0)
                opt_type = inst.get("option_type", "")
                name = inst.get("instrument_name", "")
                diff = abs(strike - spot_price)

                if opt_type == "call":
                    calls.append((name, strike, diff, exp_dt))
                elif opt_type == "put":
                    puts.append((name, strike, diff, exp_dt))

            if not calls or not puts:
                logger.warning(f"未找到 {config.EXPIRY_DAYS_MIN}-{config.EXPIRY_DAYS_MAX} 天到期的期权")
                return None, None

            # 优先选同一执行价的 Call/Put（真正的 ATM Straddle）
            calls.sort(key=lambda x: x[2])
            puts.sort(key=lambda x: x[2])

            best_call = calls[0]
            # 找与 Call 执行价相同的 Put
            same_strike_puts = [p for p in puts if p[1] == best_call[1]]
            best_put = same_strike_puts[0] if same_strike_puts else puts[0]

            logger.info(f"ATM Call: {best_call[0]} (strike={best_call[1]}, diff={best_call[2]:.0f})")
            logger.info(f"ATM Put:  {best_put[0]}  (strike={best_put[1]}, diff={best_put[2]:.0f})")
            return best_call[0], best_put[0]

        except Exception as e:
            logger.error(f"查找 ATM 期权失败: {e}")
            return None, None

    # ── 辅助方法 ──────────────────────────────────────

    async def _get_spot_price(self) -> float:
        url = f"{self.DERIBIT_PUBLIC}/public/get_index_price"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params={"index_name": "btc_usd"},
                                       timeout=aiohttp.ClientTimeout(total=8)) as resp:
                    data = await resp.json()
            return float(data["result"]["index_price"])
        except Exception as e:
            logger.error(f"获取现货价格失败: {e}")
            return 0.0

    async def _get_mark_price(self, instrument_name: str) -> float:
        url = f"{self.DERIBIT_PUBLIC}/public/ticker"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params={"instrument_name": instrument_name},
                                       timeout=aiohttp.ClientTimeout(total=8)) as resp:
                    data = await resp.json()
            return float(data["result"].get("mark_price", 0.0))
        except Exception as e:
            logger.error(f"获取 mark_price 失败 ({instrument_name}): {e}")
            return 0.0

    async def _get_mark_iv(self, instrument_name: str) -> float:
        url = f"{self.DERIBIT_PUBLIC}/public/ticker"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params={"instrument_name": instrument_name},
                                       timeout=aiohttp.ClientTimeout(total=8)) as resp:
                    data = await resp.json()
            return float(data["result"].get("mark_iv", 0.0)) / 100.0
        except Exception as e:
            logger.error(f"获取 mark_iv 失败 ({instrument_name}): {e}")
            return 0.0

    async def _get_safe_amount(self, instrument_name: str) -> float:
        """获取对齐最小下单量的交易数量"""
        url = f"{self.DERIBIT_PUBLIC}/public/get_instrument"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params={"instrument_name": instrument_name},
                                       timeout=aiohttp.ClientTimeout(total=8)) as resp:
                    data = await resp.json()
            min_amount = float(data["result"].get("min_trade_amount", 0.1))
        except Exception:
            min_amount = 0.1  # Deribit BTC 期权默认最小量

        desired = config.TRADE_AMOUNT
        if desired < min_amount:
            logger.warning(f"TRADE_AMOUNT={desired} 小于最小下单量 {min_amount}，自动调整为 {min_amount}")
            return min_amount
        # 对齐到 min_amount 的整数倍
        import math
        aligned = math.floor(desired / min_amount) * min_amount
        return round(aligned, 8)

    def _fail_record(self, signal: Signal, news_id: str, error: str) -> TradeRecord:
        logger.error(f"开仓失败: {error}")
        record = TradeRecord(
            news_id=news_id, news_score=signal.news_score,
            news_sentiment=signal.news_sentiment, action=signal.action,
            confidence=signal.confidence, spot_price=0.0,
            call_instrument=None, put_instrument=None,
            call_order_id=None, put_order_id=None,
            call_premium=0.0, put_premium=0.0, total_cost_usd=0.0,
            entry_iv=0.0, iv_rank=signal.iv_rank, dvol=signal.dvol,
            fear_greed=signal.fear_greed, success=False, error=error,
        )
        self._save_trade(record)
        return record

    def _save_trade(self, record: TradeRecord):
        with sqlite3.connect(config.DB_POSITIONS) as conn:
            conn.execute("""
                INSERT INTO trades (
                    news_id, news_score, news_sentiment, action, confidence,
                    spot_price, call_instrument, put_instrument,
                    call_order_id, put_order_id, call_premium, put_premium,
                    total_cost_usd, entry_iv, iv_rank, dvol, fear_greed,
                    success, error, trade_time
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                record.news_id, record.news_score, record.news_sentiment,
                record.action, record.confidence, record.spot_price,
                record.call_instrument, record.put_instrument,
                record.call_order_id, record.put_order_id,
                record.call_premium, record.put_premium, record.total_cost_usd,
                record.entry_iv, record.iv_rank, record.dvol, record.fear_greed,
                int(record.success), record.error,
                record.trade_time.isoformat(),
            ))
            conn.commit()
