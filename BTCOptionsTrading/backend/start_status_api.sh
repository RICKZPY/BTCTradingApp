#!/bin/bash
# 启动加权情绪交易状态 API

cd "$(dirname "$0")"

# 检查是否已经在运行
if pgrep -f "weighted_sentiment_status_api_v2.py" > /dev/null; then
    echo "状态 API 已经在运行"
    echo "进程信息:"
    ps aux | grep weighted_sentiment_status_api_v2.py | grep -v grep
    exit 0
fi

# 启动 API
echo "启动状态 API..."
nohup python3 weighted_sentiment_status_api_v2.py > logs/status_api.log 2>&1 &

# 等待启动
sleep 2

# 检查是否启动成功
if pgrep -f "weighted_sentiment_status_api_v2.py" > /dev/null; then
    echo "✓ 状态 API 启动成功"
    echo "端口: 5004"
    echo "访问: http://服务器IP:5004/"
    echo "日志: tail -f logs/status_api.log"
else
    echo "✗ 状态 API 启动失败"
    echo "查看日志: cat logs/status_api.log"
    exit 1
fi
