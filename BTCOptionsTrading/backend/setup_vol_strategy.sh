#!/bin/bash
# ============================================================
# Vol Strategy 服务器初始化脚本
# 在服务器上执行一次即可
# 用法：bash setup_vol_strategy.sh
# ============================================================

set -e
BACKEND_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "=================================================="
echo "  Vol Strategy 初始化"
echo "  目录: $BACKEND_DIR"
echo "=================================================="

# ── 1. 检查 Python ────────────────────────────────────
echo ""
echo "[1/6] 检查 Python 版本..."
python3 --version || { echo "错误：未找到 python3"; exit 1; }

# ── 2. 安装依赖 ───────────────────────────────────────
echo ""
echo "[2/6] 安装 Python 依赖..."
VENV_DIR="$BACKEND_DIR/venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "  创建虚拟环境..."
    python3 -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"
pip install aiohttp python-dotenv --quiet
echo "✓ 依赖安装完成（venv: $VENV_DIR）"

# ── 3. 创建目录 ───────────────────────────────────────
echo ""
echo "[3/6] 创建数据和日志目录..."
mkdir -p "$BACKEND_DIR/vol_strategy/data"
mkdir -p "$BACKEND_DIR/vol_strategy/logs"
chmod 755 "$BACKEND_DIR/vol_strategy/data"
chmod 755 "$BACKEND_DIR/vol_strategy/logs"
echo "✓ 目录创建完成"

# ── 4. 检查 .env 配置 ─────────────────────────────────
echo ""
echo "[4/6] 检查 .env 配置..."
if [ ! -f "$BACKEND_DIR/.env" ]; then
    echo "⚠️  未找到 .env 文件，从 .env.example 复制..."
    cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
    echo "请编辑 .env 文件填入 API Key："
    echo "  nano $BACKEND_DIR/.env"
    echo ""
    echo "需要填写："
    echo "  VOL_STRATEGY_DERIBIT_API_KEY=..."
    echo "  VOL_STRATEGY_DERIBIT_API_SECRET=..."
    exit 1
fi

# 检查 vol_strategy key 是否已填写
VOL_KEY=$(grep "VOL_STRATEGY_DERIBIT_API_KEY" "$BACKEND_DIR/.env" | cut -d'=' -f2 | tr -d '"' | tr -d "'" | tr -d ' ')
if [ -z "$VOL_KEY" ] || [ "$VOL_KEY" = "" ]; then
    echo "⚠️  VOL_STRATEGY_DERIBIT_API_KEY 未配置"
    echo "请编辑 .env 文件："
    echo "  nano $BACKEND_DIR/.env"
    exit 1
fi
echo "✓ .env 配置检查通过"

# ── 5. 冷启动测试（拉取 DVOL 历史数据）──────────────
echo ""
echo "[5/6] 冷启动：拉取 DVOL 历史数据..."
cd "$BACKEND_DIR"
source "$VENV_DIR/bin/activate"
python3 -c "
import asyncio, sys
sys.path.insert(0, '.')
from vol_strategy.iv_tracker import IVTracker
async def run():
    t = IVTracker()
    await t.bootstrap()
    print('✓ DVOL 历史数据初始化完成')
asyncio.run(run())
"

# ── 6. 安装 Cron Job ──────────────────────────────────
echo ""
echo "[6/6] 安装 Cron Job..."

CRON_CMD="0 * * * * cd $BACKEND_DIR && $VENV_DIR/bin/python3 -m vol_strategy.cron >> vol_strategy/logs/cron.log 2>&1"

# 检查是否已存在
if crontab -l 2>/dev/null | grep -q "vol_strategy.cron"; then
    echo "✓ Cron Job 已存在，跳过"
else
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
    echo "✓ Cron Job 安装完成（每小时整点执行）"
fi

echo ""
echo "=================================================="
echo "  ✅ Vol Strategy 初始化完成！"
echo "=================================================="
echo ""
echo "当前 Cron 配置："
crontab -l | grep vol_strategy || echo "  (无)"
echo ""
echo "手动测试运行："
echo "  cd $BACKEND_DIR && source venv/bin/activate && python3 -m vol_strategy.cron"
echo ""
echo "查看日志："
echo "  tail -f $BACKEND_DIR/vol_strategy/logs/cron.log"
