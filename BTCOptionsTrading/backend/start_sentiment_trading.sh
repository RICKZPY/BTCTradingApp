#!/bin/bash
# 启动情绪交易服务

echo "启动情绪驱动交易服务..."

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到python3"
    exit 1
fi

# 检查.env文件
if [ ! -f .env ]; then
    echo "警告: 未找到.env文件，请确保配置了DERIBIT_API_KEY和DERIBIT_API_SECRET"
fi

# 创建必要的目录
mkdir -p data logs

# 激活虚拟环境（如果存在）
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# 安装依赖
echo "检查依赖..."
pip install -q aiohttp fastapi uvicorn python-dotenv

# 启动服务
echo "启动情绪交易服务..."
nohup python3 sentiment_trading_service.py > logs/sentiment_service.log 2>&1 &
SERVICE_PID=$!
echo "情绪交易服务已启动 (PID: $SERVICE_PID)"
echo $SERVICE_PID > data/sentiment_service.pid

# 等待2秒
sleep 2

# 启动API服务
echo "启动状态API服务..."
nohup python3 sentiment_api.py > logs/sentiment_api.log 2>&1 &
API_PID=$!
echo "状态API服务已启动 (PID: $API_PID)"
echo $API_PID > data/sentiment_api.pid

echo ""
echo "=========================================="
echo "服务启动完成！"
echo "=========================================="
echo "情绪交易服务 PID: $SERVICE_PID"
echo "状态API服务 PID: $API_PID (端口: 5002)"
echo ""
echo "查看日志:"
echo "  情绪交易: tail -f logs/sentiment_trading.log"
echo "  状态API: tail -f logs/sentiment_api.log"
echo ""
echo "API访问地址:"
echo "  http://localhost:5002/api/status - 完整状态"
echo "  http://localhost:5002/api/positions - 持仓信息"
echo "  http://localhost:5002/api/orders - 订单信息"
echo "  http://localhost:5002/api/history - 交易历史"
echo ""
echo "停止服务: ./stop_sentiment_trading.sh"
echo "=========================================="
