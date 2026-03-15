#!/bin/bash
# 停止情绪交易服务

echo "停止情绪交易服务..."

# 停止情绪交易服务
if [ -f data/sentiment_service.pid ]; then
    SERVICE_PID=$(cat data/sentiment_service.pid)
    if ps -p $SERVICE_PID > /dev/null 2>&1; then
        kill $SERVICE_PID
        echo "情绪交易服务已停止 (PID: $SERVICE_PID)"
    else
        echo "情绪交易服务未运行"
    fi
    rm data/sentiment_service.pid
else
    echo "未找到情绪交易服务PID文件"
fi

# 停止API服务
if [ -f data/sentiment_api.pid ]; then
    API_PID=$(cat data/sentiment_api.pid)
    if ps -p $API_PID > /dev/null 2>&1; then
        kill $API_PID
        echo "状态API服务已停止 (PID: $API_PID)"
    else
        echo "状态API服务未运行"
    fi
    rm data/sentiment_api.pid
else
    echo "未找到状态API服务PID文件"
fi

echo "所有服务已停止"
