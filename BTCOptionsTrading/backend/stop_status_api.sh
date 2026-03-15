#!/bin/bash
# 停止加权情绪交易状态 API

echo "停止状态 API..."

# 查找并停止进程
pkill -f "weighted_sentiment_status_api_v2.py"

# 等待进程结束
sleep 1

# 检查是否已停止
if pgrep -f "weighted_sentiment_status_api_v2.py" > /dev/null; then
    echo "✗ 进程仍在运行，尝试强制停止..."
    pkill -9 -f "weighted_sentiment_status_api_v2.py"
    sleep 1
fi

if ! pgrep -f "weighted_sentiment_status_api_v2.py" > /dev/null; then
    echo "✓ 状态 API 已停止"
else
    echo "✗ 无法停止进程"
    exit 1
fi
