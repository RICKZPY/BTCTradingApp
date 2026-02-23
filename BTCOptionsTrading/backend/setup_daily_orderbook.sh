#!/bin/bash
# 设置每天北京时间早上5点运行orderbook收集脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/simple_orderbook_collector.py"

# 北京时间5点 = UTC时间21点（前一天）
# Cron格式: 分 时 日 月 周
CRON_TIME="0 21 * * *"

# 创建cron任务
CRON_JOB="$CRON_TIME cd $SCRIPT_DIR && /usr/bin/python3 $PYTHON_SCRIPT >> $SCRIPT_DIR/logs/orderbook_collector.log 2>&1"

# 检查是否已存在
if crontab -l 2>/dev/null | grep -q "simple_orderbook_collector.py"; then
    echo "Cron任务已存在"
    crontab -l | grep "simple_orderbook_collector.py"
else
    # 添加到crontab
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "Cron任务已添加："
    echo "$CRON_JOB"
fi

echo ""
echo "当前所有cron任务："
crontab -l

echo ""
echo "日志文件位置: $SCRIPT_DIR/logs/orderbook_collector.log"
