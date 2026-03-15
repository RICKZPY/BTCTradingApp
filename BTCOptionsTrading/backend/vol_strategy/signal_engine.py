"""
Signal Engine - 三重验证信号引擎

三层过滤：
  Layer 1 - 新闻评分（基础门槛，≥7 才进入后续判断）
  Layer 2 - IV Rank（时机过滤，Rank < 40 才适合买入波动率）
  Layer 3 - 市场共振（Fear&Greed + Put/Call Ratio + 成交量异常）

输出：
  action     : BUY_STRADDLE | BUY_CALL | BUY_PUT | WAIT
  confidence : 0-100
  position_size_pct : 0.10 / 0.15 / 0.20（占账户比例）
  reasons    : 决策依据列表
"""

import asyncio
import aiohttp
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from . import config

logger = logging.getLogger("vol_strategy.signal_engine")


@dataclass
class Signal:
    action: str                    # BUY_STRADDLE | BUY_CALL | BUY_PUT | WAIT
    confidence: int                # 0-100
    position_size_pct: float       # 0.0 / 0.10 / 0.15 / 0.20
    news_score: int
    news_sentiment: str
    dvol: float
    iv_rank: float
    fear_greed: int
    put_call_ratio: float
    reasons: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class SignalEngine:
    """三重验证信号引擎"""

    DERIBIT_PUBLIC = "https://test.deribit.com/api/v2" if config.DERIBIT_TESTNET \
                     else "https://www.deribit.com/api/v2"

    # ── 外部数据获取 ──────────────────────────────────

    async def get_fear_greed(self) -> int:
        """
        Alternative.me 恐惧贪婪指数（免费，无需 Key）
        0-24  极度恐惧
        25-44 恐惧
        45-55 中性
        56-75 贪婪
        76-100 极度贪婪
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(config.FEAR_GREED_URL,
                                       timeout=aiohttp.ClientTimeout(total=8)) as resp:
                    data = await resp.json()
            value = int(data["data"][0]["value"])
            label = data["data"][0]["value_classification"]
            logger.info(f"Fear & Greed: {value} ({label})")
            return value
        except Exception as e:
            logger.warning(f"Fear & Greed 获取失败，使用默认值 50: {e}")
            return 50

    async def get_put_call_ratio(self) -> float:
        """
        从 Deribit 计算 BTC 期权的 Put/Call 成交量比率。
        > 1.2 → 市场偏空（恐慌）
        < 0.8 → 市场偏多（贪婪）
        """
        url = f"{self.DERIBIT_PUBLIC}/public/get_book_summary_by_currency"
        params = {"currency": "BTC", "kind": "option"}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params,
                                       timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    data = await resp.json()

            instruments = data.get("result", [])
            put_vol  = sum(i.get("volume", 0) for i in instruments if i.get("instrument_name", "").endswith("-P"))
            call_vol = sum(i.get("volume", 0) for i in instruments if i.get("instrument_name", "").endswith("-C"))

            if call_vol == 0:
                return 1.0

            ratio = put_vol / call_vol
            logger.info(f"Put/Call Ratio: {ratio:.3f}  (put={put_vol:.1f}, call={call_vol:.1f})")
            return ratio

        except Exception as e:
            logger.warning(f"Put/Call Ratio 获取失败，使用默认值 1.0: {e}")
            return 1.0

    async def detect_volume_spike(self) -> bool:
        """
        检测期权成交量是否异常放大（> 过去 7 天均值的 2 倍）。
        用 Deribit 的 24h volume 字段做简单判断。
        """
        url = f"{self.DERIBIT_PUBLIC}/public/get_book_summary_by_currency"
        params = {"currency": "BTC", "kind": "option"}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params,
                                       timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    data = await resp.json()

            instruments = data.get("result", [])
            # 用 volume_usd 的中位数判断是否有异常
            volumes = [i.get("volume_usd", 0) for i in instruments if i.get("volume_usd", 0) > 0]
            if not volumes:
                return False

            avg = sum(volumes) / len(volumes)
            top = max(volumes)
            spike = top > avg * 3  # 最大单合约成交量超过均值 3 倍
            if spike:
                logger.info(f"成交量异常：最大 {top:.0f} USD，均值 {avg:.0f} USD")
            return spike

        except Exception as e:
            logger.warning(f"成交量检测失败: {e}")
            return False

    # ── 核心信号生成 ──────────────────────────────────

    async def generate(
        self,
        news_score: int,
        news_sentiment: str,
        dvol: float,
        iv_rank: float,
    ) -> Signal:
        """
        生成综合交易信号。

        Args:
            news_score    : 新闻重要性评分 1-10
            news_sentiment: positive / negative / neutral
            dvol          : 当前 DVOL 值
            iv_rank       : IV Rank 0-100
        """
        reasons: List[str] = []
        confidence = 0

        # ── Layer 1：新闻评分门槛 ──────────────────────
        if news_score < config.NEWS_SCORE_MIN:
            return Signal(
                action="WAIT", confidence=0, position_size_pct=0.0,
                news_score=news_score, news_sentiment=news_sentiment,
                dvol=dvol, iv_rank=iv_rank, fear_greed=50, put_call_ratio=1.0,
                reasons=[f"新闻评分不足 ({news_score} < {config.NEWS_SCORE_MIN})"]
            )

        confidence += news_score * 3   # 7分=21, 8分=24, 9分=27, 10分=30
        reasons.append(f"新闻评分 {news_score}/10 (+{news_score * 3})")

        # ── Layer 2：IV Rank 时机过滤 ──────────────────
        if iv_rank <= 20:
            confidence += 30
            reasons.append(f"极低 IV 环境，买入成本低 (Rank={iv_rank:.0f}, +30)")
        elif iv_rank <= config.DVOL_RANK_MAX:
            confidence += 20
            reasons.append(f"低 IV 环境 (Rank={iv_rank:.0f}, +20)")
        elif iv_rank <= 60:
            confidence += 5
            reasons.append(f"中等 IV 环境 (Rank={iv_rank:.0f}, +5)")
        else:
            # 高 IV 时买入成本太高，直接拒绝
            return Signal(
                action="WAIT", confidence=confidence, position_size_pct=0.0,
                news_score=news_score, news_sentiment=news_sentiment,
                dvol=dvol, iv_rank=iv_rank, fear_greed=50, put_call_ratio=1.0,
                reasons=reasons + [f"IV 过高，买入成本不划算 (Rank={iv_rank:.0f})"]
            )

        # ── Layer 3：市场共振验证（并发获取）─────────────
        fear_greed, put_call_ratio, volume_spike = await asyncio.gather(
            self.get_fear_greed(),
            self.get_put_call_ratio(),
            self.detect_volume_spike(),
        )

        # Fear & Greed 与新闻情绪一致性
        if news_sentiment == "negative" and fear_greed <= 35:
            confidence += 20
            reasons.append(f"负面新闻 + 市场恐慌共振 (F&G={fear_greed}, +20)")
        elif news_sentiment == "positive" and fear_greed >= 65:
            confidence += 20
            reasons.append(f"正面新闻 + 市场贪婪共振 (F&G={fear_greed}, +20)")
        elif news_sentiment == "neutral":
            confidence += 8
            reasons.append(f"中性新闻，方向不明 (F&G={fear_greed}, +8)")
        else:
            confidence -= 5
            reasons.append(f"新闻情绪与市场情绪背离 (F&G={fear_greed}, -5)")

        # Put/Call Ratio 极端值
        if put_call_ratio >= 1.3:
            confidence += 12
            reasons.append(f"P/C Ratio 偏高，市场恐慌 ({put_call_ratio:.2f}, +12)")
        elif put_call_ratio <= 0.7:
            confidence += 12
            reasons.append(f"P/C Ratio 偏低，市场贪婪 ({put_call_ratio:.2f}, +12)")
        else:
            confidence += 4
            reasons.append(f"P/C Ratio 正常 ({put_call_ratio:.2f}, +4)")

        # 成交量异常
        if volume_spike:
            confidence += 10
            reasons.append("期权成交量异常放大 (+10)")

        # ── 方向判断 ──────────────────────────────────
        action = self._decide_action(news_sentiment, fear_greed, put_call_ratio)

        # ── 仓位大小 ──────────────────────────────────
        position_size_pct = self._decide_position_size(confidence, news_score)

        reasons.append(f"综合置信度: {confidence}")

        return Signal(
            action=action,
            confidence=min(confidence, 100),
            position_size_pct=position_size_pct,
            news_score=news_score,
            news_sentiment=news_sentiment,
            dvol=dvol,
            iv_rank=iv_rank,
            fear_greed=fear_greed,
            put_call_ratio=put_call_ratio,
            reasons=reasons,
        )

    def _decide_action(self, sentiment: str, fear_greed: int, pcr: float) -> str:
        """根据情绪和市场指标决定交易方向"""
        # 方向明确：情绪 + F&G + PCR 三者一致
        bearish_signals = (
            sentiment == "negative"
            and fear_greed < 40
            and pcr > 1.1
        )
        bullish_signals = (
            sentiment == "positive"
            and fear_greed > 60
            and pcr < 0.9
        )

        if bearish_signals:
            return "BUY_PUT"
        elif bullish_signals:
            return "BUY_CALL"
        else:
            return "BUY_STRADDLE"   # 方向不明，买波动率本身

    def _decide_position_size(self, confidence: int, news_score: int) -> float:
        """根据置信度和新闻评分决定仓位比例"""
        if confidence < config.CONFIDENCE_MIN:
            return 0.0
        if confidence >= 80 and news_score >= 9:
            return 0.20
        elif confidence >= 70:
            return 0.15
        else:
            return 0.10
