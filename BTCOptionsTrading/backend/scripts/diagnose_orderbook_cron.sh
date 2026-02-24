#!/bin/bash
# 诊断 orderbook collector cron 任务

echo "=========================================="
echo "Orderbook Collector 诊断工具"
echo "=========================================="
echo ""

# 1. 检查 crontab
echo "1. 检查 crontab 配置："
echo "---"
if crontab -l 2>/dev/null | grep -q "orderbook"; then
    echo "✓ 找到 orderbook 相关的 cron 任务："
    crontab -l | grep orderbook
else
    echo "✗ 未找到 orderbook 相关的 cron 任务"
    echo "  请运行: cd BTCOptionsTrading/backend/scripts && ./setup_daily_orderbook.sh"
fi
echo ""

# 2. 检查脚本文件
echo "2. 检查脚本文件："
echo "---"
SCRIPT_PATH="BTCOptionsTrading/backend/simple_orderbook_collector.py"
if [ -f "$SCRIPT_PATH" ]; then
    echo "✓ 脚本文件存在: $SCRIPT_PATH"
    if [ -x "$SCRIPT_PATH" ]; then
        echo "✓ 脚本有执行权限"
    else
        echo "⚠ 脚本没有执行权限，添加权限..."
        chmod +x "$SCRIPT_PATH"
    fi
else
    echo "✗ 脚本文件不存在: $SCRIPT_PATH"
fi
echo ""

# 3. 检查日志目录和文件
echo "3. 检查日志："
echo "---"
LOG_DIR="BTCOptionsTrading/backend/logs"
LOG_FILE="$LOG_DIR/orderbook_collector.log"

if [ -d "$LOG_DIR" ]; then
    echo "✓ 日志目录存在: $LOG_DIR"
else
    echo "⚠ 日志目录不存在，创建中..."
    mkdir -p "$LOG_DIR"
fi

if [ -f "$LOG_FILE" ]; then
    echo "✓ 日志文件存在: $LOG_FILE"
    echo "  最后修改时间: $(ls -l $LOG_FILE | awk '{print $6, $7, $8}')"
    echo "  文件大小: $(ls -lh $LOG_FILE | awk '{print $5}')"
    echo ""
    echo "  最近10行日志："
    tail -10 "$LOG_FILE" 2>/dev/null || echo "  (日志为空)"
else
    echo "⚠ 日志文件不存在: $LOG_FILE"
    echo "  这可能意味着 cron 任务从未运行过"
fi
echo ""

# 4. 检查数据目录
echo "4. 检查数据目录："
echo "---"
DATA_DIR="BTCOptionsTrading/backend/data/orderbook"

if [ -d "$DATA_DIR" ]; then
    echo "✓ 数据目录存在: $DATA_DIR"
    FILE_COUNT=$(ls -1 "$DATA_DIR" 2>/dev/null | wc -l)
    echo "  文件数量: $FILE_COUNT"
    
    if [ $FILE_COUNT -gt 0 ]; then
        echo ""
        echo "  最近5个文件："
        ls -lt "$DATA_DIR" | head -6 | tail -5
        
        echo ""
        echo "  今天的文件："
        TODAY=$(date +%Y%m%d)
        ls -l "$DATA_DIR" | grep "$TODAY" || echo "  (今天没有文件)"
    else
        echo "  ⚠ 目录为空"
    fi
else
    echo "✗ 数据目录不存在: $DATA_DIR"
fi
echo ""

# 5. 检查 Python 环境
echo "5. 检查 Python 环境："
echo "---"
echo "Python 路径: $(which python3)"
echo "Python 版本: $(python3 --version 2>&1)"
echo ""
echo "检查必需的包："
for pkg in aiohttp pytz; do
    if python3 -c "import $pkg" 2>/dev/null; then
        echo "  ✓ $pkg 已安装"
    else
        echo "  ✗ $pkg 未安装"
    fi
done
echo ""

# 6. 检查时区和时间
echo "6. 检查时区和时间："
echo "---"
echo "当前系统时间: $(date)"
echo "UTC 时间: $(date -u)"
echo "北京时间 5:00 对应 UTC: 21:00 (前一天)"
echo ""

# 7. 测试手动运行
echo "7. 建议的测试命令："
echo "---"
echo "手动测试运行："
echo "  cd BTCOptionsTrading/backend && python3 simple_orderbook_collector.py"
echo ""
echo "查看实时日志："
echo "  tail -f BTCOptionsTrading/backend/logs/orderbook_collector.log"
echo ""
echo "重新设置 cron 任务："
echo "  cd BTCOptionsTrading/backend/scripts && ./setup_daily_orderbook.sh"
echo ""

echo "=========================================="
echo "诊断完成"
echo "=========================================="
