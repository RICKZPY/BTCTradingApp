#!/bin/bash
# 服务器端快速检查 orderbook collector

echo "=========================================="
echo "服务器端 Orderbook Collector 检查"
echo "=========================================="
echo ""

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "工作目录: $BACKEND_DIR"
echo "当前时间: $(date)"
echo "UTC 时间: $(date -u)"
echo ""

# 1. 检查 crontab
echo "1. Crontab 配置："
echo "---"
if crontab -l 2>/dev/null | grep -q "orderbook"; then
    echo "✓ 找到 cron 任务："
    crontab -l | grep orderbook
else
    echo "✗ 未找到 cron 任务"
fi
echo ""

# 2. 检查日志
echo "2. 日志文件："
echo "---"
LOG_FILE="$BACKEND_DIR/logs/orderbook_collector.log"
if [ -f "$LOG_FILE" ]; then
    echo "✓ 日志文件存在"
    echo "  大小: $(du -h "$LOG_FILE" | cut -f1)"
    echo "  最后修改: $(stat -c %y "$LOG_FILE" 2>/dev/null || stat -f "%Sm" "$LOG_FILE")"
    echo ""
    echo "  最近20行："
    tail -20 "$LOG_FILE"
else
    echo "✗ 日志文件不存在: $LOG_FILE"
fi
echo ""

# 3. 检查数据文件
echo "3. 数据文件："
echo "---"
DATA_DIR="$BACKEND_DIR/data/orderbook"
if [ -d "$DATA_DIR" ]; then
    FILE_COUNT=$(ls -1 "$DATA_DIR" 2>/dev/null | wc -l)
    echo "✓ 数据目录存在，文件数: $FILE_COUNT"
    echo ""
    echo "  最近5个文件："
    ls -lth "$DATA_DIR" | head -6
    echo ""
    echo "  今天的文件 ($(date +%Y%m%d)):"
    ls -lh "$DATA_DIR" | grep "$(date +%Y%m%d)" || echo "  (无)"
else
    echo "✗ 数据目录不存在: $DATA_DIR"
fi
echo ""

# 4. 检查系统 cron 日志
echo "4. 系统 Cron 日志 (最近10条):"
echo "---"
if [ -f /var/log/syslog ]; then
    grep CRON /var/log/syslog | grep orderbook | tail -10 || echo "(无相关日志)"
elif [ -f /var/log/cron ]; then
    grep orderbook /var/log/cron | tail -10 || echo "(无相关日志)"
else
    echo "(无法访问系统日志)"
fi
echo ""

echo "=========================================="
echo "检查完成"
echo "=========================================="
