#!/bin/bash
# 启动API服务脚本

cd "$(dirname "$0")"

echo "=========================================="
echo "启动情绪交易API服务"
echo "=========================================="
echo ""

# 检查是否已经在运行
if ps aux | grep -v grep | grep "sentiment_api.py" > /dev/null; then
    echo "⚠ API服务已在运行"
    echo ""
    ps aux | grep -v grep | grep "sentiment_api.py"
    echo ""
    read -p "是否要重启服务？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "停止现有服务..."
        pkill -f "sentiment_api.py"
        sleep 2
    else
        echo "保持现有服务运行"
        exit 0
    fi
fi

# 检查.env文件
if [ ! -f ".env" ]; then
    echo "✗ 错误: .env文件不存在"
    echo "请从.env.example复制并配置API密钥"
    exit 1
fi

# 确保日志目录存在
mkdir -p logs

# 启动API服务
echo "启动API服务..."
nohup python3 sentiment_api.py > logs/api_startup.log 2>&1 &
API_PID=$!

echo "API服务已启动 (PID: $API_PID)"
echo ""

# 等待服务启动
echo "等待服务启动..."
sleep 3

# 检查服务是否正常
if ps -p $API_PID > /dev/null; then
    echo "✓ 服务进程正在运行"
    
    # 测试API连接
    echo "测试API连接..."
    sleep 2
    
    if curl -s http://localhost:5002/api/health > /dev/null 2>&1; then
        echo "✓ API服务正常运行"
        echo ""
        echo "访问地址:"
        echo "  - 本地: http://localhost:5002/api/health"
        echo "  - 外部: http://$(curl -s ifconfig.me 2>/dev/null):5002/api/health"
        echo ""
        echo "查看日志: tail -f logs/sentiment_api.log"
    else
        echo "⚠ API服务启动但无法连接"
        echo "查看日志: tail -f logs/sentiment_api.log"
    fi
else
    echo "✗ 服务启动失败"
    echo "查看启动日志: cat logs/api_startup.log"
    exit 1
fi

echo ""
echo "=========================================="
