#!/bin/bash
# 情绪交易系统交互式部署脚本

set -e

echo "=========================================="
echo "🚀 情绪交易系统 - 交互式部署"
echo "=========================================="
echo ""

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 收集服务器信息
echo "请输入服务器信息："
echo ""
read -p "服务器IP地址: " SERVER_HOST
read -p "SSH用户名 (默认: root): " SERVER_USER
SERVER_USER=${SERVER_USER:-root}
read -p "SSH端口 (默认: 22): " SERVER_PORT
SERVER_PORT=${SERVER_PORT:-22}
read -p "部署目录 (默认: /root/BTCOptionsTrading): " REMOTE_DIR
REMOTE_DIR=${REMOTE_DIR:-/root/BTCOptionsTrading}

echo ""
echo "API密钥配置："
read -p "Deribit API Key: " API_KEY
read -s -p "Deribit API Secret: " API_SECRET
echo ""

echo ""
echo "=========================================="
echo "部署配置确认："
echo "=========================================="
echo "服务器: $SERVER_USER@$SERVER_HOST:$SERVER_PORT"
echo "目录: $REMOTE_DIR"
echo "API Key: ${API_KEY:0:10}..."
echo ""
read -p "确认部署? (y/n): " confirm

if [ "$confirm" != "y" ]; then
    echo "部署已取消"
    exit 0
fi

# 导出环境变量供主脚本使用
export SERVER_HOST
export SERVER_USER
export SERVER_PORT
export REMOTE_DIR

echo ""
echo "=========================================="
echo "开始部署..."
echo "=========================================="

# 测试SSH连接
echo ""
echo "测试SSH连接..."
if ! ssh -p $SERVER_PORT -o ConnectTimeout=10 $SERVER_USER@$SERVER_HOST "echo 'SSH连接成功'" 2>/dev/null; then
    echo -e "${RED}✗ SSH连接失败${NC}"
    echo ""
    echo "可能的原因："
    echo "1. 服务器地址或端口错误"
    echo "2. SSH密钥未配置"
    echo "3. 防火墙阻止连接"
    echo ""
    echo "配置SSH密钥的方法："
    echo "  ssh-copy-id -p $SERVER_PORT $SERVER_USER@$SERVER_HOST"
    exit 1
fi
echo -e "${GREEN}✓ SSH连接正常${NC}"

# 创建临时.env文件
echo ""
echo "创建配置文件..."
TEMP_ENV=$(mktemp)
cat > $TEMP_ENV << EOF
# Deribit API配置
DERIBIT_API_KEY=$API_KEY
DERIBIT_API_SECRET=$API_SECRET
EOF

# 备份原有.env（如果存在）
if [ -f "backend/.env" ]; then
    cp backend/.env backend/.env.backup
fi

# 使用新的.env
cp $TEMP_ENV backend/.env
rm $TEMP_ENV

echo -e "${GREEN}✓ 配置文件已创建${NC}"

# 执行主部署脚本
echo ""
echo "执行部署..."
./deploy_sentiment_trading.sh

# 清理
if [ -f "backend/.env.backup" ]; then
    mv backend/.env.backup backend/.env
fi

echo ""
echo "=========================================="
echo -e "${GREEN}✅ 部署完成！${NC}"
echo "=========================================="
echo ""
echo "🌐 访问API："
echo "   http://$SERVER_HOST:5002/api/status"
echo ""
echo "📊 查看监控面板："
echo "   1. 下载: scp -P $SERVER_PORT $SERVER_USER@$SERVER_HOST:$REMOTE_DIR/backend/sentiment_dashboard.html ."
echo "   2. 编辑dashboard中的API_BASE为: http://$SERVER_HOST:5002"
echo "   3. 在浏览器中打开"
echo ""
echo "📝 查看日志："
echo "   ssh -p $SERVER_PORT $SERVER_USER@$SERVER_HOST 'tail -f $REMOTE_DIR/backend/logs/sentiment_trading.log'"
echo ""
echo "🔧 管理服务："
echo "   重启: ssh -p $SERVER_PORT $SERVER_USER@$SERVER_HOST 'systemctl restart sentiment_trading.service'"
echo "   状态: ssh -p $SERVER_PORT $SERVER_USER@$SERVER_HOST 'systemctl status sentiment_trading.service'"
echo ""
