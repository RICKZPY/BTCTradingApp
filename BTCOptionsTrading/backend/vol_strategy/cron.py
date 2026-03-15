#!/usr/bin/env python3
"""
Vol Strategy - 每小时 Cron 入口

完全独立于 sentiment_trading_service 和 weighted_sentiment 系统。
使用独立账户（VOL_STRATEGY_DERIBIT_API_KEY）。

Cron 配置：
  0 * * * * cd /path/to/BTCOptionsTrading/backend && python3 -m vol_strategy.cron >> vol_strategy/logs/cron.log 2>&1

手动运行：
  cd BTCOptionsTrading/backend
  python3 -m vol_strategy.cron
"""

import asyncio
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# 确保 backend 目录在 path 中
sys.path.insert(0, str(Path(__file__).parent.parent))

from vol_strategy import config
from vol_strategy.iv_tracker import IVTracker
from vol_strategy.signal_engine import SignalEngine
from vol_strategy.executor import Executor
from vol_strategy.position_monitor import PositionMonitor

# 复用已有的 DeribitTrader
from src.trading.deribit_trader import DeribitTrader

# 复用已有的 NewsTracker（新闻去重）
from weighted_sentiment_news_tracker import NewsTracker
from weighted_sentiment_api_client import NewsAPIClient


# ── 日志配置 ──────────────────────────────────────────

def _setup_logging():
    log_file = config.LOG_DIR / "cron.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ],
    )

_setup_logging()
logger = logging.getLogger("vol_strategy.cron")


# ── 主流程 ────────────────────────────────────────────

async def main():
    logger.info("=" * 70)
    logger.info(f"Vol Strategy Cron 开始  {datetime.now(timezone.utc).isoformat()}")
    logger.info("=" * 70)

    # ── 1. 检查配置 ───────────────────────────────────
    if not config.DERIBIT_API_KEY or not config.DERIBIT_API_SECRET:
        logger.error(
            "未配置 Deribit 凭证，请在 .env 中设置：\n"
            "  VOL_STRATEGY_DERIBIT_API_KEY=...\n"
            "  VOL_STRATEGY_DERIBIT_API_SECRET=..."
        )
        sys.exit(1)

    # ── 2. 初始化组件 ─────────────────────────────────
    trader = DeribitTrader(
        config.DERIBIT_API_KEY,
        config.DERIBIT_API_SECRET,
        testnet=config.DERIBIT_TESTNET,
    )
    if not await trader.authenticate():
        logger.error("Deribit 认证失败，退出")
        sys.exit(1)
    logger.info(f"Deribit 认证成功 ({'testnet' if config.DERIBIT_TESTNET else 'mainnet'})")

    iv_tracker      = IVTracker()
    signal_engine   = SignalEngine()
    executor        = Executor(trader)
    position_monitor = PositionMonitor(trader)
    news_api        = NewsAPIClient()
    news_tracker    = NewsTracker()

    # ── 3. DVOL 冷启动（首次运行时拉取历史数据）────────
    await iv_tracker.bootstrap()

    # ── 4. 先检查并处理现有持仓（止盈/止损）────────────
    logger.info("── 持仓检查 ──")
    await position_monitor.check_all()

    stats = position_monitor.get_stats()
    logger.info(
        f"绩效统计 | 总交易={stats['total_trades']} | "
        f"持仓={stats['open_positions']} | "
        f"胜率={stats['win_rate']*100:.1f}% | "
        f"平均PnL={stats['avg_pnl_pct']*100:+.1f}%"
    )

    # ── 5. 检查持仓上限 ───────────────────────────────
    if stats["open_positions"] >= config.MAX_POSITIONS:
        logger.info(f"持仓已达上限 ({config.MAX_POSITIONS})，跳过开仓")
        _log_end()
        return

    # ── 6. 获取并更新 DVOL ────────────────────────────
    logger.info("── IV 数据更新 ──")
    dvol = await iv_tracker.fetch_latest_dvol()
    if dvol is None:
        logger.warning("DVOL 获取失败，跳过本次开仓检查")
        _log_end()
        return

    iv_rank = iv_tracker.calculate_iv_rank(dvol)
    logger.info(f"DVOL={dvol:.2f}  IV Rank={iv_rank:.1f}")

    # ── 7. 获取新闻，筛选新的高分新闻 ────────────────
    logger.info("── 新闻检查 ──")
    news_list = await news_api.fetch_weighted_news()
    logger.info(f"获取到 {len(news_list)} 条新闻")

    if not news_list:
        logger.info("无新闻数据，结束")
        await news_tracker.update_history([])
        _log_end()
        return

    new_news = await news_tracker.identify_new_news(news_list)
    logger.info(f"新的高分新闻（评分≥{config.NEWS_SCORE_MIN}）: {len(new_news)} 条")

    # ── 8. 对每条新闻生成信号并执行 ──────────────────
    for news in new_news:
        # 再次检查持仓上限（每笔交易后重新检查）
        current_stats = position_monitor.get_stats()
        if current_stats["open_positions"] >= config.MAX_POSITIONS:
            logger.info("持仓已达上限，停止开仓")
            break

        logger.info(f"\n── 处理新闻 {news.news_id} ──")
        logger.info(f"  内容: {news.content[:80]}...")
        logger.info(f"  评分: {news.importance_score}/10  情绪: {news.sentiment}")

        # 生成信号
        signal = await signal_engine.generate(
            news_score=news.importance_score,
            news_sentiment=news.sentiment,
            dvol=dvol,
            iv_rank=iv_rank,
        )

        logger.info(f"  信号: {signal.action} | 置信度: {signal.confidence} | 仓位: {signal.position_size_pct*100:.0f}%")
        for r in signal.reasons:
            logger.info(f"    · {r}")

        if signal.action == "WAIT" or signal.position_size_pct == 0.0:
            logger.info("  → 信号不足，跳过")
            continue

        # 执行开仓
        record = await executor.execute(signal, news.news_id)

        if record.success:
            logger.info(
                f"  ✓ 开仓成功 | {record.action} | "
                f"成本=${record.total_cost_usd:.2f} | "
                f"entry_iv={record.entry_iv*100:.1f}%"
            )
        else:
            logger.warning(f"  ✗ 开仓失败: {record.error}")

    # ── 9. 更新新闻历史（防止重复处理）──────────────
    await news_tracker.update_history(news_list)

    _log_end()


def _log_end():
    logger.info("=" * 70)
    logger.info(f"Vol Strategy Cron 完成  {datetime.now(timezone.utc).isoformat()}")
    logger.info("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
