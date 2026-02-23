#!/bin/bash

# Order Book 收集器最终部署脚本 - 支持虚拟环境

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 配置
SERVER_IP="47.86.62.200"
USERNAME="root"
REMOTE_DIR="/opt/orderbook-collector"

echo -e "${GREEN}================================${NC}"
echo "Order Book 收集器部署 (最终版)"
echo -e "${GREEN}================================${NC}"
echo "服务器: $SERVER_IP"
echo "用户: $USERNAME"
echo "远程目录: $REMOTE_DIR"
echo ""

# 步骤 1: 检查连接
echo -e "${YELLOW}[1/6] 检查服务器连接...${NC}"
if ! ssh -o ConnectTimeout=5 "$USERNAME@$SERVER_IP" "echo 'OK'" > /dev/null 2>&1; then
    echo -e "${RED}✗ 无法连接到服务器${NC}"
    exit 1
fi
echo -e "${GREEN}✓ 连接成功${NC}\n"

# 步骤 2: 创建远程目录和虚拟环境
echo -e "${YELLOW}[2/6] 创建远程目录和虚拟环境...${NC}"
ssh "$USERNAME@$SERVER_IP" << 'EOF'
mkdir -p /opt/orderbook-collector/data/orderbook
cd /opt/orderbook-collector
python3 -m venv venv
echo "✓ 虚拟环境创建成功"
EOF
echo -e "${GREEN}✓ 目录和虚拟环境创建成功${NC}\n"

# 步骤 3: 上传文件
echo -e "${YELLOW}[3/6] 上传文件...${NC}"
scp -r "BTCOptionsTrading/backend/src" "$USERNAME@$SERVER_IP:$REMOTE_DIR/"
scp "BTCOptionsTrading/backend/requirements.txt" "$USERNAME@$SERVER_IP:$REMOTE_DIR/"
scp "BTCOptionsTrading/backend/collect_orderbook.py" "$USERNAME@$SERVER_IP:$REMOTE_DIR/"
scp "BTCOptionsTrading/backend/schedule_orderbook_collection.py" "$USERNAME@$SERVER_IP:$REMOTE_DIR/"
echo -e "${GREEN}✓ 文件上传成功${NC}\n"

# 步骤 4: 安装依赖
echo -e "${YELLOW}[4/6] 安装依赖...${NC}"
ssh "$USERNAME@$SERVER_IP" << 'EOF'
cd /opt/orderbook-collector
source venv/bin/activate
pip install -q -r requirements.txt
echo "✓ 依赖安装成功"
EOF
echo -e "${GREEN}✓ 依赖安装成功${NC}\n"

# 步骤 5: 测试运行
echo -e "${YELLOW}[5/6] 测试运行...${NC}"
ssh "$USERNAME@$SERVER_IP" << 'EOF'
cd /opt/orderbook-collector
source venv/bin/activate
python collect_orderbook.py --help > /dev/null
echo "✓ 测试成功"
EOF
echo -e "${GREEN}✓ 测试成功${NC}\n"

# 步骤 6: 创建启动脚本
echo -e "${YELLOW}[6/6] 创建启动脚本...${NC}"
ssh "$USERNAME@$SERVER_IP" << 'EOF'
cat > /opt/orderbook-collector/start_collection.sh << 'SCRIPT'
#!/bin/bash
cd /opt/orderbook-collector
source venv/bin/activate
python schedule_orderbook_collection.py "$@"
SCRIPT
chmod +x /opt/orderbook-collector/start_collection.sh
echo "✓ 启动脚本创建成功"
EOF
echo -e "${GREEN}✓ 启动脚本创建成功${NC}\n"

echo -e "${GREEN}================================${NC}"
echo "✓ 部署完成"
echo -e "${GREEN}================================${NC}"
echo ""
echo "下一步:"
echo "1. 登录服务器: ssh root@47.86.62.200"
echo "2. 进入目录: cd /opt/orderbook-collector"
echo "3. 运行收集: ./start_collection.sh"
echo ""
echo "或者直接运行:"
echo "  ssh root@47.86.62.200 'cd /opt/orderbook-collector && ./start_collection.sh'"
echo ""
echo "更多选项:"
echo "  ./start_collection.sh --help"
echo ""
