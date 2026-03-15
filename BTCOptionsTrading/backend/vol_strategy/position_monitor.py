"""
Position Monitor - 持仓监控 + 自动止盈止损

每小时由 cron.py 调用一次，检查所有 open 持仓：
  - 止盈：PnL >= TAKE_PROFIT_PCT
  - 止损：PnL <= STOP_LOSS_PCT
  - 移动止损：从最高点回撤 > TRAILING_STOP_PCT（且曾盈利 > 10%）
  - IV 扩张止盈：当前 IV > 入场 IV * 1.5 且 PnL > 10%
  - 时间止损：持仓超过 MAX_HOLD_DAYS 天
"""

import asyncio
import aiohttp
import sqlite3
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional

from . import config

logger = logging.getLogger("vol_strategy.position_monitor")


class PositionMonitor:
    """持仓监控器"""

    DERIBIT_PUBLIC = "https://test.deribit.com/api/v2" if config.DERIBIT_TESTNET \
                     else "https://www.deribit.com/api/v2"

    def __init__(self, trader):
        self.trader = trader
        # 内存中记录每个持仓的历史最高 PnL（重启后从 0 开始，保守处理）
        self._peak_pnl: Dict[int, float] = {}

    # ── 主入口 ────────────────────────────────────────

    async def check_all(self):
        """检查所有 open 持仓，执行止盈/止损"""
        open_trades = self._load_open_trades()
        if not open_trades:
            logger.info("无持仓，跳过检查")
            return

        logger.info(f"检查 {len(open_trades)} 个持仓...")

        for trade in open_trades:
            try:
                await self._check_one(trade)
            except Exception as e:
                logger.error(f"检查持仓 {trade['id']} 失败: {e}")

    async def _check_one(self, trade: Dict):
        trade_id = trade["id"]

        # 获取当前价格和 IV
        instruments = [i for i in [trade["call_instrument"], trade["put_instrument"]] if i]
        if not instruments:
            return

        current_prices = await asyncio.gather(*[self._get_mark_price(i) for i in instruments])
        current_ivs    = await asyncio.gather(*[self._get_mark_iv(i) for i in instruments])

        # 计算 PnL（以期权价格变化为准）
        entry_premiums = [trade["call_premium"], trade["put_premium"]]
        pnl_pcts = []
        for i, inst in enumerate(instruments):
            entry = entry_premiums[i] if entry_premiums[i] > 0 else 1e-9
            curr  = current_prices[i]
            if curr > 0:
                pnl_pcts.append((curr - entry) / entry)

        if not pnl_pcts:
            return

        # 组合 PnL（简单平均，Straddle 两腿）
        pnl_pct = sum(pnl_pcts) / len(pnl_pcts)
        avg_iv  = sum(current_ivs) / len(current_ivs) if current_ivs else 0.0

        # 更新最高 PnL
        peak = self._peak_pnl.get(trade_id, 0.0)
        if pnl_pct > peak:
            self._peak_pnl[trade_id] = pnl_pct
            peak = pnl_pct

        days_held = (datetime.now(timezone.utc) - datetime.fromisoformat(trade["trade_time"])).days

        logger.info(
            f"持仓 #{trade_id} | {trade['action']} | "
            f"PnL={pnl_pct*100:+.1f}% | peak={peak*100:.1f}% | "
            f"IV={avg_iv*100:.1f}% | days={days_held}"
        )

        # 判断是否平仓
        should_close, reason = self._should_close(
            trade, pnl_pct, peak, avg_iv, days_held
        )

        if should_close:
            await self._close_trade(trade, pnl_pct, reason)

    def _should_close(
        self,
        trade: Dict,
        pnl_pct: float,
        peak_pnl: float,
        current_iv: float,
        days_held: int,
    ) -> tuple:
        entry_iv = trade.get("entry_iv", 0.0)

        # 1. 止盈
        if pnl_pct >= config.TAKE_PROFIT_PCT:
            return True, f"止盈 ({pnl_pct*100:+.1f}%)"

        # 2. 止损
        if pnl_pct <= config.STOP_LOSS_PCT:
            return True, f"止损 ({pnl_pct*100:+.1f}%)"

        # 3. 移动止损（曾盈利 > 10%，从最高点回撤超过阈值）
        if peak_pnl > 0.10:
            drawdown = peak_pnl - pnl_pct
            if drawdown > config.TRAILING_STOP_PCT:
                return True, f"移动止损 (peak={peak_pnl*100:.1f}%, 回撤={drawdown*100:.1f}%)"

        # 4. IV 扩张止盈（IV 上涨 50% 且有盈利）
        if entry_iv > 0 and current_iv > entry_iv * 1.5 and pnl_pct > 0.10:
            return True, f"IV 扩张止盈 (entry={entry_iv*100:.1f}% → {current_iv*100:.1f}%)"

        # 5. 时间止损
        if days_held >= config.MAX_HOLD_DAYS:
            return True, f"时间止损 ({days_held}天, PnL={pnl_pct*100:+.1f}%)"

        # 6. 时间衰减止损（持仓 3 天以上且亏损 > 10%）
        if days_held >= 3 and pnl_pct < -0.10:
            return True, f"时间衰减止损 ({days_held}天, PnL={pnl_pct*100:+.1f}%)"

        return False, ""

    async def _close_trade(self, trade: Dict, pnl_pct: float, reason: str):
        logger.info(f"平仓 #{trade['id']} | 原因: {reason}")

        for inst in [trade["call_instrument"], trade["put_instrument"]]:
            if not inst:
                continue
            try:
                result = await self.trader.close_position(inst)
                if result:
                    logger.info(f"  ✓ 平仓成功: {inst}")
                else:
                    logger.warning(f"  ✗ 平仓失败: {inst}")
            except Exception as e:
                logger.error(f"  ✗ 平仓异常 ({inst}): {e}")

        # 更新数据库
        with sqlite3.connect(config.DB_POSITIONS) as conn:
            conn.execute("""
                UPDATE trades
                SET status='closed', close_time=?, close_reason=?, pnl_pct=?
                WHERE id=?
            """, (datetime.now(timezone.utc).isoformat(), reason, pnl_pct, trade["id"]))
            conn.commit()

        if trade_id := trade.get("id"):
            self._peak_pnl.pop(trade_id, None)

    # ── 数据库 ────────────────────────────────────────

    def _load_open_trades(self) -> List[Dict]:
        with sqlite3.connect(config.DB_POSITIONS) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM trades WHERE status='open' AND success=1"
            ).fetchall()
        return [dict(r) for r in rows]

    def get_stats(self) -> Dict:
        """绩效统计，供 cron.py 打印"""
        with sqlite3.connect(config.DB_POSITIONS) as conn:
            total  = conn.execute("SELECT COUNT(*) FROM trades WHERE success=1").fetchone()[0]
            closed = conn.execute("SELECT COUNT(*) FROM trades WHERE status='closed' AND success=1").fetchone()[0]
            wins   = conn.execute("SELECT COUNT(*) FROM trades WHERE status='closed' AND pnl_pct > 0").fetchone()[0]
            avg_pnl = conn.execute("SELECT AVG(pnl_pct) FROM trades WHERE status='closed'").fetchone()[0] or 0.0
            open_count = conn.execute("SELECT COUNT(*) FROM trades WHERE status='open' AND success=1").fetchone()[0]

        return {
            "total_trades": total,
            "open_positions": open_count,
            "closed_trades": closed,
            "win_rate": wins / closed if closed > 0 else 0.0,
            "avg_pnl_pct": avg_pnl,
        }

    # ── 辅助 ──────────────────────────────────────────

    async def _get_mark_price(self, instrument_name: str) -> float:
        url = f"{self.DERIBIT_PUBLIC}/public/ticker"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params={"instrument_name": instrument_name},
                                       timeout=aiohttp.ClientTimeout(total=8)) as resp:
                    data = await resp.json()
            return float(data["result"].get("mark_price", 0.0))
        except:
            return 0.0

    async def _get_mark_iv(self, instrument_name: str) -> float:
        url = f"{self.DERIBIT_PUBLIC}/public/ticker"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params={"instrument_name": instrument_name},
                                       timeout=aiohttp.ClientTimeout(total=8)) as resp:
                    data = await resp.json()
            return float(data["result"].get("mark_iv", 0.0)) / 100.0
        except:
            return 0.0
