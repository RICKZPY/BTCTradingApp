#!/bin/bash
# 检查加权情绪跨式期权交易系统状态
# Check weighted sentiment straddle trading system status

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DB_FILE="$SCRIPT_DIR/data/weighted_news_history.db"
LOG_FILE="$SCRIPT_DIR/logs/weighted_sentiment.log"
TRADE_LOG="$SCRIPT_DIR/logs/weighted_sentiment_trades.log"

echo "=========================================="
echo "加权情绪跨式期权交易系统 - 状态检查"
echo "=========================================="
echo ""

# 1. 检查 Cron 任务
echo "1. Cron 任务状态："
if crontab -l 2>/dev/null | grep -q "weighted_sentiment_cron.py"; then
    echo "   ✓ Cron 任务已配置"
    crontab -l | grep "weighted_sentiment_cron.py"
else
    echo "   ✗ Cron 任务未配置"
fi
echo ""

# 2. 检查数据库
echo "2. 数据库状态："
if [ -f "$DB_FILE" ]; then
    echo "   ✓ 数据库文件存在"
    NEWS_COUNT=$(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM news_history;" 2>/dev/null || echo "0")
    echo "   历史新闻数量: $NEWS_COUNT"
    
    if [ "$NEWS_COUNT" -gt 0 ]; then
        LATEST=$(sqlite3 "$DB_FILE" "SELECT timestamp FROM news_history ORDER BY processed_at DESC LIMIT 1;" 2>/dev/null || echo "未知")
        echo "   最新新闻时间: $LATEST"
    fi
else
    echo "   ✗ 数据库文件不存在"
fi
echo ""

# 3. 检查日志
echo "3. 日志状态："
if [ -f "$LOG_FILE" ]; then
    echo "   ✓ 系统日志存在"
    EXEC_COUNT=$(grep -c "Cron Job 开始执行" "$LOG_FILE" 2>/dev/null || echo "0")
    echo "   执行次数: $EXEC_COUNT"
    
    if [ "$EXEC_COUNT" -gt 0 ]; then
        LAST_EXEC=$(grep "Cron Job 开始执行" "$LOG_FILE" | tail -1 | awk '{print $1, $2}')
        echo "   最后执行: $LAST_EXEC"
        
        # 检查最后一次执行的结果
        LAST_NEWS=$(grep "成功解析.*条有效新闻" "$LOG_FILE" | tail -1 | grep -oP '\d+(?= 条有效新闻)' || echo "0")
        LAST_HIGH=$(grep "识别到.*条新的高分新闻" "$LOG_FILE" | tail -1 | grep -oP '\d+(?= 条新的高分新闻)' || echo "0")
        echo "   最后一次: 解析 $LAST_NEWS 条新闻, 识别 $LAST_HIGH 条高分新闻"
    fi
else
    echo "   ✗ 系统日志不存在"
fi
echo ""

# 4. 检查交易日志
echo "4. 交易记录："
if [ -f "$TRADE_LOG" ]; then
    echo "   ✓ 交易日志存在"
    TRADE_COUNT=$(grep -c "交易时间:" "$TRADE_LOG" 2>/dev/null || echo "0")
    echo "   交易记录数: $TRADE_COUNT"
    
    if [ "$TRADE_COUNT" -gt 0 ]; then
        echo "   最近 3 条交易:"
        grep -A 5 "交易时间:" "$TRADE_LOG" | tail -18 | head -18
    fi
else
    echo "   ✗ 交易日志不存在"
fi
echo ""

# 5. 检查环境变量
echo "5. 环境配置："
if [ -f "$SCRIPT_DIR/.env" ]; then
    echo "   ✓ .env 文件存在"
    if grep -q "WEIGHTED_SENTIMENT_DERIBIT_API_KEY" "$SCRIPT_DIR/.env"; then
        echo "   ✓ 加权情绪凭证已配置"
    else
        echo "   ✗ 加权情绪凭证未配置"
    fi
else
    echo "   ✗ .env 文件不存在"
fi
echo ""

# 6. 系统资源
echo "6. 系统资源："
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1)
    echo "   Python: $PYTHON_VERSION"
else
    echo "   ✗ Python3 未安装"
fi

if command -v sqlite3 &> /dev/null; then
    SQLITE_VERSION=$(sqlite3 --version 2>&1 | awk '{print $1}')
    echo "   SQLite: $SQLITE_VERSION"
else
    echo "   ✗ SQLite3 未安装"
fi
echo ""

echo "=========================================="
echo "状态检查完成"
echo "=========================================="
echo ""
echo "查看实时日志："
echo "  tail -f $LOG_FILE"
echo ""
echo "手动测试运行："
echo "  cd $SCRIPT_DIR && python3 weighted_sentiment_cron.py"
echo ""
