"""
波动率策略配置
独立账户，独立参数，与其他策略完全隔离
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── 目录 ──────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
LOG_DIR  = BASE_DIR / "logs"
DATA_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

# ── Deribit 账户（独立，不与其他策略共用）────────────────
DERIBIT_API_KEY    = os.getenv("VOL_STRATEGY_DERIBIT_API_KEY", "")
DERIBIT_API_SECRET = os.getenv("VOL_STRATEGY_DERIBIT_API_SECRET", "")
DERIBIT_TESTNET    = os.getenv("VOL_STRATEGY_TESTNET", "true").lower() == "true"

# ── 外部数据源（全部免费）────────────────────────────────
NEWS_API_URL       = os.getenv("VOL_STRATEGY_NEWS_API_URL",
                               "http://43.106.51.106:5002/api/weighted-sentiment/news")
FEAR_GREED_URL     = "https://api.alternative.me/fng/?limit=1"

# ── 信号过滤阈值 ──────────────────────────────────────
NEWS_SCORE_MIN     = int(os.getenv("VOL_STRATEGY_NEWS_SCORE_MIN", "7"))
DVOL_RANK_MAX      = float(os.getenv("VOL_STRATEGY_DVOL_RANK_MAX", "40"))   # IV Rank 上限
CONFIDENCE_MIN     = int(os.getenv("VOL_STRATEGY_CONFIDENCE_MIN", "60"))    # 综合置信度下限
DVOL_HISTORY_DAYS  = int(os.getenv("VOL_STRATEGY_DVOL_HISTORY_DAYS", "30")) # IV Rank 计算窗口

# ── 交易参数 ──────────────────────────────────────────
TRADE_AMOUNT       = float(os.getenv("VOL_STRATEGY_TRADE_AMOUNT", "0.1"))   # 每腿数量 (BTC)
EXPIRY_DAYS_MIN    = int(os.getenv("VOL_STRATEGY_EXPIRY_DAYS_MIN", "5"))
EXPIRY_DAYS_MAX    = int(os.getenv("VOL_STRATEGY_EXPIRY_DAYS_MAX", "21"))

# ── 风险管理 ──────────────────────────────────────────
TAKE_PROFIT_PCT    = float(os.getenv("VOL_STRATEGY_TAKE_PROFIT", "0.35"))   # 止盈 35%
STOP_LOSS_PCT      = float(os.getenv("VOL_STRATEGY_STOP_LOSS", "-0.40"))    # 止损 -40%
TRAILING_STOP_PCT  = float(os.getenv("VOL_STRATEGY_TRAILING_STOP", "0.15")) # 移动止损 15%
MAX_HOLD_DAYS      = int(os.getenv("VOL_STRATEGY_MAX_HOLD_DAYS", "7"))
MAX_POSITIONS      = int(os.getenv("VOL_STRATEGY_MAX_POSITIONS", "3"))

# ── 数据库路径 ────────────────────────────────────────
DB_DVOL      = str(DATA_DIR / "dvol_history.db")
DB_NEWS      = str(DATA_DIR / "news_history.db")
DB_POSITIONS = str(DATA_DIR / "positions.db")
