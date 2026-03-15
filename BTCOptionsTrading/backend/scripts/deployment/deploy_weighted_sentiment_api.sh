#!/bin/bash
# 部署加权情绪交易状态 API 到服务器
# Deploy weighted sentiment trading status API to server

set -e

SERVER="root@47.86.62.200"
REMOTE_PATH="/root/BTCOptionsTrading/backend"

echo "=========================================="
echo "部署加权情绪交易状态 API"
echo "Deploy Weighted Sentiment Trading API"
echo "=========================================="
echo ""

# 1. 上传文件
echo "1. 上传 API 文件..."
echo "   Uploading API files..."

scp weighted_sentiment_api.py ${SERVER}:${REMOTE_PATH}/
scp start_weighted_sentiment_api.sh ${SERVER}:${REMOTE_PATH}/

if [ $? -ne 0 ]; then
    echo "❌ 上传失败 / Upload failed"
    exit 1
fi

echo "✓ 文件上传成功 / Files uploaded successfully"
echo ""

# 2. 在服务器上安装依赖和测试
echo "2. 在服务器上安装依赖和测试..."
echo "   Installing dependencies and testing on server..."

ssh ${SERVER} << 'EOF'
cd /root/BTCOptionsTrading/backend

# 设置执行权限
chmod +x start_weighted_sentiment_api.sh

# 检查 Python 语法
echo "检查 Python 语法..."
python3 -m py_compile weighted_sentiment_api.py
if [ $? -ne 0 ]; then
    echo "❌ Python 语法检查失败"
    exit 1
fi
echo "✓ Python 语法检查通过"

# 安装依赖
echo "安装依赖..."
pip3 install fastapi uvicorn --break-system-packages 2>/dev/null || true
pip3 install aiohttp --break-system-packages 2>/dev/null || true
echo "✓ 依赖安装完成"

# 测试导入
echo "测试模块导入..."
python3 -c "
import sys
sys.path.insert(0, '/root/BTCOptionsTrading/backend')
from weighted_sentiment_api import app
print('✓ 模块导入成功')
"

if [ $? -ne 0 ]; then
    echo "❌ 模块导入失败"
    exit 1
fi

EOF

if [ $? -ne 0 ]; then
    echo "❌ 服务器测试失败 / Server test failed"
    exit 1
fi

echo "✓ 服务器测试通过 / Server test passed"
echo ""

# 3. 创建 systemd 服务（可选）
echo "3. 是否创建 systemd 服务？(y/n)"
read -r response

if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo "创建 systemd 服务..."
    
    ssh ${SERVER} << 'EOF'
# 创建 systemd 服务文件
cat > /etc/systemd/system/weighted-sentiment-api.service << 'SERVICE'
[Unit]
Description=Weighted Sentiment Trading Status API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/BTCOptionsTrading/backend
ExecStart=/usr/bin/python3 /root/BTCOptionsTrading/backend/weighted_sentiment_api.py
Restart=always
RestartSec=10
StandardOutput=append:/root/BTCOptionsTrading/backend/logs/weighted_sentiment_api.log
StandardError=append:/root/BTCOptionsTrading/backend/logs/weighted_sentiment_api_error.log

[Install]
WantedBy=multi-user.target
SERVICE

# 重新加载 systemd
systemctl daemon-reload

# 启用服务
systemctl enable weighted-sentiment-api.service

echo "✓ systemd 服务已创建"
echo ""
echo "管理命令:"
echo "  启动: systemctl start weighted-sentiment-api"
echo "  停止: systemctl stop weighted-sentiment-api"
echo "  状态: systemctl status weighted-sentiment-api"
echo "  日志: journalctl -u weighted-sentiment-api -f"

EOF
    
    echo ""
    echo "是否立即启动服务？(y/n)"
    read -r start_response
    
    if [[ "$start_response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        ssh ${SERVER} "systemctl start weighted-sentiment-api"
        echo "✓ 服务已启动"
    fi
else
    echo "跳过 systemd 服务创建"
    echo ""
    echo "手动启动命令:"
    echo "  ssh ${SERVER}"
    echo "  cd ${REMOTE_PATH}"
    echo "  ./start_weighted_sentiment_api.sh"
fi

echo ""
echo "=========================================="
echo "部署完成 / Deployment Complete"
echo "=========================================="
echo ""
echo "API 信息:"
echo "  端口: 5004"
echo "  账户: 0366QIa2 (Deribit Test)"
echo "  服务: weighted-sentiment-straddle-trading"
echo ""
echo "访问地址:"
echo "  http://47.86.62.200:5004"
echo ""
echo "API 端点:"
echo "  GET /api/status - 完整状态"
echo "  GET /api/positions - 持仓"
echo "  GET /api/orders - 订单"
echo "  GET /api/trades - 交易历史"
echo "  GET /api/news/history - 新闻统计"
echo "  GET /api/account - 账户信息"
echo "  GET /api/health - 健康检查"
echo ""
echo "与现有服务的区别:"
echo "  sentiment_api.py (端口 5002) - 账户: vXkaBDto"
echo "  weighted_sentiment_api.py (端口 5004) - 账户: 0366QIa2"
echo ""
