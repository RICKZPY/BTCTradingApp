#!/bin/bash
# 情绪交易系统部署脚本

set -e  # 遇到错误立即退出

echo "=========================================="
echo "情绪交易系统部署脚本"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置变量（请根据实际情况修改）
SERVER_USER="${SERVER_USER:-root}"
SERVER_HOST="${SERVER_HOST}"
SERVER_PORT="${SERVER_PORT:-22}"
REMOTE_DIR="${REMOTE_DIR:-/root/BTCOptionsTrading}"
LOCAL_DIR="$(cd "$(dirname "$0")" && pwd)"

# 检查是否提供了服务器地址
if [ -z "$SERVER_HOST" ]; then
    echo -e "${YELLOW}请提供服务器信息：${NC}"
    read -p "服务器地址 (例如: 43.106.51.106): " SERVER_HOST
    read -p "服务器用户 (默认: root): " input_user
    SERVER_USER=${input_user:-root}
    read -p "SSH端口 (默认: 22): " input_port
    SERVER_PORT=${input_port:-22}
    read -p "远程目录 (默认: /root/BTCOptionsTrading): " input_dir
    REMOTE_DIR=${input_dir:-/root/BTCOptionsTrading}
fi

echo ""
echo "部署配置："
echo "  服务器: $SERVER_USER@$SERVER_HOST:$SERVER_PORT"
echo "  远程目录: $REMOTE_DIR"
echo ""

# 确认部署
read -p "确认部署? (y/n): " confirm
if [ "$confirm" != "y" ]; then
    echo "部署已取消"
    exit 0
fi

echo ""
echo "=========================================="
echo "步骤 1/6: 检查本地文件"
echo "=========================================="

# 检查必要文件
REQUIRED_FILES=(
    "backend/sentiment_trading_service.py"
    "backend/sentiment_api.py"
    "backend/start_sentiment_trading.sh"
    "backend/stop_sentiment_trading.sh"
    "backend/test_sentiment_trading.py"
    "backend/sentiment_trading.service"
    "backend/sentiment_api.service"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$LOCAL_DIR/$file" ]; then
        echo -e "${RED}✗ 缺少文件: $file${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓${NC} $file"
done

echo ""
echo "=========================================="
echo "步骤 2/6: 测试SSH连接"
echo "=========================================="

if ssh -p $SERVER_PORT -o ConnectTimeout=10 $SERVER_USER@$SERVER_HOST "echo '连接成功'" 2>/dev/null; then
    echo -e "${GREEN}✓ SSH连接正常${NC}"
else
    echo -e "${RED}✗ SSH连接失败${NC}"
    echo "请检查："
    echo "  1. 服务器地址是否正确"
    echo "  2. SSH密钥是否配置"
    echo "  3. 防火墙是否开放SSH端口"
    exit 1
fi

echo ""
echo "=========================================="
echo "步骤 3/6: 创建远程目录并上传文件"
echo "=========================================="

# 创建远程目录结构
ssh -p $SERVER_PORT $SERVER_USER@$SERVER_HOST "mkdir -p $REMOTE_DIR/backend/{data,logs,src,examples,docs,scripts}"

# 上传后端文件
echo "上传情绪交易服务文件..."
scp -P $SERVER_PORT \
    "$LOCAL_DIR/backend/sentiment_trading_service.py" \
    "$LOCAL_DIR/backend/sentiment_api.py" \
    "$LOCAL_DIR/backend/start_sentiment_trading.sh" \
    "$LOCAL_DIR/backend/stop_sentiment_trading.sh" \
    "$LOCAL_DIR/backend/test_sentiment_trading.py" \
    "$LOCAL_DIR/backend/quick_test_sentiment.sh" \
    "$LOCAL_DIR/backend/sentiment_dashboard.html" \
    $SERVER_USER@$SERVER_HOST:$REMOTE_DIR/backend/

# 上传服务配置文件
echo "上传systemd服务配置..."
scp -P $SERVER_PORT \
    "$LOCAL_DIR/backend/sentiment_trading.service" \
    "$LOCAL_DIR/backend/sentiment_api.service" \
    $SERVER_USER@$SERVER_HOST:$REMOTE_DIR/backend/

# 上传文档
echo "上传文档..."
scp -P $SERVER_PORT \
    "$LOCAL_DIR/SENTIMENT_TRADING_README.md" \
    "$LOCAL_DIR/SENTIMENT_TRADING_QUICKSTART.md" \
    $SERVER_USER@$SERVER_HOST:$REMOTE_DIR/

# 上传.env文件（如果存在）
if [ -f "$LOCAL_DIR/backend/.env" ]; then
    echo "上传.env配置文件..."
    scp -P $SERVER_PORT "$LOCAL_DIR/backend/.env" $SERVER_USER@$SERVER_HOST:$REMOTE_DIR/backend/
else
    echo -e "${YELLOW}⚠ 未找到.env文件，需要手动配置${NC}"
fi

# 上传依赖的源代码
echo "上传依赖模块..."
if [ -d "$LOCAL_DIR/backend/src" ]; then
    scp -r -P $SERVER_PORT "$LOCAL_DIR/backend/src" $SERVER_USER@$SERVER_HOST:$REMOTE_DIR/backend/
fi

# 上传requirements.txt
if [ -f "$LOCAL_DIR/backend/requirements.txt" ]; then
    scp -P $SERVER_PORT "$LOCAL_DIR/backend/requirements.txt" $SERVER_USER@$SERVER_HOST:$REMOTE_DIR/backend/
fi

echo -e "${GREEN}✓ 文件上传完成${NC}"

echo ""
echo "=========================================="
echo "步骤 4/6: 安装依赖"
echo "=========================================="

ssh -p $SERVER_PORT $SERVER_USER@$SERVER_HOST "bash -s" << 'ENDSSH'
set -e

cd $REMOTE_DIR/backend || exit 1

echo "检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "安装Python3..."
    apt-get update
    apt-get install -y python3 python3-pip
fi

echo "Python版本: $(python3 --version)"

echo "安装Python依赖..."
pip3 install --upgrade pip
pip3 install aiohttp fastapi uvicorn python-dotenv

# 如果有requirements.txt，也安装
if [ -f requirements.txt ]; then
    echo "安装requirements.txt中的依赖..."
    pip3 install -r requirements.txt || echo "部分依赖安装失败，继续..."
fi

echo "依赖安装完成"
ENDSSH

echo -e "${GREEN}✓ 依赖安装完成${NC}"

echo ""
echo "=========================================="
echo "步骤 5/6: 配置systemd服务"
echo "=========================================="

ssh -p $SERVER_PORT $SERVER_USER@$SERVER_HOST "bash -s" << ENDSSH
set -e

cd $REMOTE_DIR/backend || exit 1

# 获取当前用户和工作目录
CURRENT_USER=\$(whoami)
WORK_DIR=\$(pwd)

echo "配置服务文件..."
echo "  用户: \$CURRENT_USER"
echo "  工作目录: \$WORK_DIR"

# 修改服务文件中的路径和用户
sed -i "s|YOUR_USERNAME|\$CURRENT_USER|g" sentiment_trading.service
sed -i "s|/path/to/BTCOptionsTrading/backend|\$WORK_DIR|g" sentiment_trading.service

sed -i "s|YOUR_USERNAME|\$CURRENT_USER|g" sentiment_api.service
sed -i "s|/path/to/BTCOptionsTrading/backend|\$WORK_DIR|g" sentiment_api.service

# 复制服务文件到systemd目录
echo "安装systemd服务..."
cp sentiment_trading.service /etc/systemd/system/
cp sentiment_api.service /etc/systemd/system/

# 重载systemd
systemctl daemon-reload

# 启用服务（开机自启）
systemctl enable sentiment_trading.service
systemctl enable sentiment_api.service

echo "systemd服务配置完成"
ENDSSH

echo -e "${GREEN}✓ systemd服务配置完成${NC}"

echo ""
echo "=========================================="
echo "步骤 6/6: 检查配置并启动服务"
echo "=========================================="

ssh -p $SERVER_PORT $SERVER_USER@$SERVER_HOST "bash -s" << 'ENDSSH'
set -e

cd $REMOTE_DIR/backend || exit 1

# 设置脚本执行权限
chmod +x *.sh

# 检查.env文件
if [ ! -f .env ]; then
    echo "⚠ 警告: 未找到.env文件"
    echo "请创建.env文件并配置以下内容："
    echo ""
    echo "DERIBIT_API_KEY=your_api_key"
    echo "DERIBIT_API_SECRET=your_api_secret"
    echo ""
    echo "创建示例.env文件..."
    cat > .env << 'EOF'
# Deribit API配置
DERIBIT_API_KEY=your_api_key_here
DERIBIT_API_SECRET=your_api_secret_here
EOF
    echo "✓ 已创建.env模板，请编辑并填入真实的API密钥"
    exit 1
fi

echo "检查.env配置..."
if grep -q "your_api_key" .env || grep -q "your_api_secret" .env; then
    echo "⚠ 警告: .env文件包含默认值，请修改为真实的API密钥"
    exit 1
fi

echo "✓ .env配置正常"

# 运行测试
echo ""
echo "运行系统测试..."
python3 test_sentiment_trading.py || echo "⚠ 测试未完全通过，请检查日志"

echo ""
echo "启动服务..."
systemctl start sentiment_trading.service
systemctl start sentiment_api.service

# 等待服务启动
sleep 3

# 检查服务状态
echo ""
echo "检查服务状态..."
if systemctl is-active --quiet sentiment_trading.service; then
    echo "✓ 情绪交易服务运行中"
else
    echo "✗ 情绪交易服务启动失败"
    systemctl status sentiment_trading.service --no-pager
fi

if systemctl is-active --quiet sentiment_api.service; then
    echo "✓ API服务运行中"
else
    echo "✗ API服务启动失败"
    systemctl status sentiment_api.service --no-pager
fi

ENDSSH

echo ""
echo "=========================================="
echo -e "${GREEN}部署完成！${NC}"
echo "=========================================="
echo ""
echo "服务信息："
echo "  情绪交易服务: systemctl status sentiment_trading.service"
echo "  API服务: systemctl status sentiment_api.service"
echo ""
echo "API访问地址："
echo "  http://$SERVER_HOST:5002/api/status"
echo "  http://$SERVER_HOST:5002/api/positions"
echo "  http://$SERVER_HOST:5002/api/orders"
echo "  http://$SERVER_HOST:5002/api/history"
echo ""
echo "管理命令："
echo "  查看日志: ssh $SERVER_USER@$SERVER_HOST 'journalctl -u sentiment_trading.service -f'"
echo "  重启服务: ssh $SERVER_USER@$SERVER_HOST 'systemctl restart sentiment_trading.service'"
echo "  停止服务: ssh $SERVER_USER@$SERVER_HOST 'systemctl stop sentiment_trading.service sentiment_api.service'"
echo ""
echo "下一步："
echo "  1. 确保.env文件配置了正确的API密钥"
echo "  2. 检查防火墙是否开放5002端口"
echo "  3. 访问API确认服务正常运行"
echo ""
echo "=========================================="
