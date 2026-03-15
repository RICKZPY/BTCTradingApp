#!/bin/bash
# 启动加权情绪跨式期权交易状态 API
# Start weighted sentiment straddle trading status API

set -e

echo "=========================================="
echo "启动加权情绪交易状态 API"
echo "Start Weighted Sentiment Trading API"
echo "=========================================="
echo ""

# 检查端口是否被占用
PORT=5004
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  端口 $PORT 已被占用"
    echo "   Port $PORT is already in use"
    echo ""
    echo "停止现有进程？(y/n)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo "停止现有进程..."
        lsof -ti:$PORT | xargs kill -9
        sleep 2
    else
        echo "取消启动"
        exit 1
    fi
fi

# 检查依赖
echo "检查依赖..."
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "❌ 缺少 fastapi，正在安装..."
    pip3 install fastapi uvicorn --break-system-packages
fi

if ! python3 -c "import aiohttp" 2>/dev/null; then
    echo "❌ 缺少 aiohttp，正在安装..."
    pip3 install aiohttp --break-system-packages
fi

echo "✓ 依赖检查完成"
echo ""

# 启动 API
echo "启动 API 服务..."
echo "端口: $PORT"
echo "账户: 0366QIa2 (Deribit Test)"
echo ""
echo "访问地址:"
echo "  本地: http://localhost:$PORT"
echo "  远程: http://$(hostname -I | awk '{print $1}'):$PORT"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

python3 weighted_sentiment_api.py

