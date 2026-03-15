#!/bin/bash
# 设置加权情绪跨式期权交易 Cron Job
# Setup cron job for weighted sentiment straddle trading

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CRON_SCRIPT="$SCRIPT_DIR/weighted_sentiment_cron.py"
LOG_DIR="$SCRIPT_DIR/logs"

echo "=========================================="
echo "设置加权情绪跨式期权交易 Cron Job"
echo "=========================================="

# 检查 Python 脚本是否存在
if [ ! -f "$CRON_SCRIPT" ]; then
    echo "错误: 找不到脚本文件 $CRON_SCRIPT"
    exit 1
fi

# 创建日志目录
mkdir -p "$LOG_DIR"
echo "✓ 日志目录已创建: $LOG_DIR"

# 添加执行权限
chmod +x "$CRON_SCRIPT"
echo "✓ 脚本已添加执行权限"

# 生成 cron 任务
CRON_JOB="0 * * * * cd $SCRIPT_DIR && python3 $CRON_SCRIPT >> $LOG_DIR/weighted_sentiment_cron.log 2>&1"

echo ""
echo "建议的 Cron 任务配置："
echo "----------------------------------------"
echo "$CRON_JOB"
echo "----------------------------------------"
echo ""
echo "此配置将每小时整点执行一次脚本"
echo ""

# 检查是否已存在相同的 cron 任务
if crontab -l 2>/dev/null | grep -q "weighted_sentiment_cron.py"; then
    echo "⚠ 警告: Cron 任务可能已存在"
    echo ""
    echo "当前的 cron 任务："
    crontab -l | grep "weighted_sentiment_cron.py" || true
    echo ""
    read -p "是否要替换现有任务？(y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "取消操作"
        exit 0
    fi
    # 删除旧任务
    crontab -l | grep -v "weighted_sentiment_cron.py" | crontab -
    echo "✓ 已删除旧任务"
fi

# 添加新的 cron 任务
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
echo "✓ Cron 任务已添加"

echo ""
echo "=========================================="
echo "设置完成！"
echo "=========================================="
echo ""
echo "查看 cron 任务："
echo "  crontab -l"
echo ""
echo "查看日志："
echo "  tail -f $LOG_DIR/weighted_sentiment_cron.log"
echo "  tail -f $LOG_DIR/weighted_sentiment.log"
echo ""
echo "手动测试运行："
echo "  cd $SCRIPT_DIR && python3 $CRON_SCRIPT"
echo ""
echo "删除 cron 任务："
echo "  crontab -l | grep -v 'weighted_sentiment_cron.py' | crontab -"
echo ""
