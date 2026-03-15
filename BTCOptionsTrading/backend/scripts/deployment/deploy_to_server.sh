#!/bin/bash
#
# 服务器部署脚本
# 用于快速部署情绪交易系统到远程服务器
#
# 使用方法：
#   ./deploy_to_server.sh user@server_ip
#

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_error() { echo -e "${RED}✗${NC} $1"; }
print_warning() { echo -e "${YELLOW}⚠${NC} $1"; }
print_info() { echo -e "${BLUE}ℹ${NC} $1"; }
print_step() { echo -e "\n${BLUE}===${NC} $1 ${BLUE}===${NC}"; }

# 检查参数
if [ -z "$1" ]; then
    print_error "请提供服务器地址"
    echo ""
    echo "使用方法："
    echo "  $0 user@server_ip"
    echo ""
    echo "示例："
    echo "  $0 ubuntu@192.168.1.100"
    echo "  $0 root@example.com"
    exit 1
fi

SERVER=$1
REMOTE_DIR="BTCOptionsTrading"
LOCAL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

print_step "服务器部署向导"
echo "目标服务器: $SERVER"
echo "本地目录: $LOCAL_DIR"
echo ""

# 测试SSH连接
print_info "测试SSH连接..."
if ssh -o ConnectTimeout=5 -o BatchMode=yes "$SERVER" exit 2>/dev/null; then
    print_success "SSH连接成功"
else
    print_error "无法连接到服务器"
    print_info "请确保："
    echo "  1. 服务器地址正确"
    echo "  2. SSH密钥已配置"
    echo "  3. 服务器可访问"
    exit 1
fi

# 询问是否继续
echo ""
read -p "是否继续部署？(y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "部署已取消"
    exit 0
fi

# 步骤1：检查服务器环境
print_step "步骤1: 检查服务器环境"

print_info "检查Python..."
if ssh "$SERVER" "command -v python3 &> /dev/null"; then
    PYTHON_VERSION=$(ssh "$SERVER" "python3 --version")
    print_success "找到Python: $PYTHON_VERSION"
else
    print_error "服务器上未安装Python3"
    print_info "请先在服务器上安装Python3："
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
    echo "  CentOS/RHEL: sudo yum install python3 python3-pip"
    exit 1
fi

print_info "检查pip..."
if ssh "$SERVER" "command -v pip3 &> /dev/null"; then
    print_success "找到pip3"
else
    print_warning "未找到pip3，将尝试安装"
fi

# 步骤2：创建远程目录
print_step "步骤2: 创建远程目录"

ssh "$SERVER" "mkdir -p ~/$REMOTE_DIR/backend/{logs,data}"
print_success "远程目录已创建"

# 步骤3：上传文件
print_step "步骤3: 上传文件到服务器"

print_info "使用rsync上传文件..."
rsync -avz --progress \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='venv' \
    --exclude='logs/*' \
    --exclude='data/*.json' \
    --exclude='data/*.db' \
    --exclude='.hypothesis' \
    --exclude='.pytest_cache' \
    --exclude='test_*.py' \
    "$LOCAL_DIR/" "$SERVER:~/$REMOTE_DIR/"

print_success "文件上传完成"

# 步骤4：配置.env文件
print_step "步骤4: 配置环境变量"

if ssh "$SERVER" "[ -f ~/$REMOTE_DIR/backend/.env ]"; then
    print_warning ".env文件已存在，跳过配置"
    print_info "如需重新配置，请手动编辑: ssh $SERVER 'nano ~/$REMOTE_DIR/backend/.env'"
else
    print_info "需要配置API密钥"
    echo ""
    read -p "Deribit测试网API Key: " TESTNET_KEY
    read -p "Deribit测试网API Secret: " TESTNET_SECRET
    
    ssh "$SERVER" "cat > ~/$REMOTE_DIR/backend/.env << EOF
# Deribit API配置
DERIBIT_TESTNET_API_KEY=$TESTNET_KEY
DERIBIT_TESTNET_API_SECRET=$TESTNET_SECRET

# 可选：主网配置（用于获取真实市场数据）
# DERIBIT_MAINNET_API_KEY=
# DERIBIT_MAINNET_API_SECRET=
EOF"
    
    ssh "$SERVER" "chmod 600 ~/$REMOTE_DIR/backend/.env"
    print_success ".env文件已创建"
fi

# 步骤5：安装Python依赖
print_step "步骤5: 安装Python依赖"

print_info "创建虚拟环境..."
ssh "$SERVER" "cd ~/$REMOTE_DIR/backend && python3 -m venv venv"
print_success "虚拟环境已创建"

print_info "安装依赖包（这可能需要几分钟）..."
ssh "$SERVER" "cd ~/$REMOTE_DIR/backend && source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"
print_success "依赖包安装完成"

# 步骤6：测试运行
print_step "步骤6: 测试运行"

print_info "执行测试运行..."
if ssh "$SERVER" "cd ~/$REMOTE_DIR/backend && source venv/bin/activate && timeout 60 python3 sentiment_trading_service.py" 2>&1 | tee /tmp/test_run.log; then
    print_success "测试运行成功"
else
    print_warning "测试运行超时或失败（这可能是正常的）"
    print_info "请查看日志确认是否正常"
fi

# 步骤7：修改setup_cron.sh使用虚拟环境
print_step "步骤7: 配置Cron脚本"

print_info "更新setup_cron.sh以使用虚拟环境..."
ssh "$SERVER" "cd ~/$REMOTE_DIR/backend && sed -i.bak 's|cd \${SCRIPT_DIR} && \${PYTHON_CMD} \${SCRIPT_PATH}|cd \${SCRIPT_DIR} \&\& source venv/bin/activate \&\& python3 \${SCRIPT_PATH}|g' setup_cron.sh"
ssh "$SERVER" "chmod +x ~/$REMOTE_DIR/backend/setup_cron.sh"
print_success "Cron脚本已配置"

# 步骤8：安装Cron Job
print_step "步骤8: 安装Cron Job"

echo ""
read -p "是否立即安装Cron Job？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    ssh "$SERVER" "cd ~/$REMOTE_DIR/backend && ./setup_cron.sh install"
    print_success "Cron Job已安装"
    
    # 显示状态
    echo ""
    ssh "$SERVER" "cd ~/$REMOTE_DIR/backend && ./setup_cron.sh status"
else
    print_warning "跳过Cron Job安装"
    print_info "稍后可以手动安装："
    echo "  ssh $SERVER"
    echo "  cd ~/$REMOTE_DIR/backend"
    echo "  ./setup_cron.sh install"
fi

# 步骤9：配置时区
print_step "步骤9: 检查服务器时区"

TIMEZONE=$(ssh "$SERVER" "timedatectl | grep 'Time zone' | awk '{print \$3}'")
print_info "当前时区: $TIMEZONE"

echo ""
read -p "是否需要修改时区？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "常用时区："
    echo "  1. Asia/Shanghai (中国)"
    echo "  2. America/New_York (美国东部)"
    echo "  3. Europe/London (英国)"
    echo "  4. Asia/Tokyo (日本)"
    echo ""
    read -p "请输入时区（或按Enter跳过）: " NEW_TIMEZONE
    
    if [ ! -z "$NEW_TIMEZONE" ]; then
        ssh "$SERVER" "sudo timedatectl set-timezone $NEW_TIMEZONE"
        print_success "时区已更新为: $NEW_TIMEZONE"
    fi
fi

# 完成
print_step "部署完成！"

echo ""
print_success "情绪交易系统已成功部署到服务器"
echo ""
echo "下一步："
echo ""
echo "1. 查看Cron Job状态："
echo "   ssh $SERVER 'cd ~/$REMOTE_DIR/backend && ./setup_cron.sh status'"
echo ""
echo "2. 查看日志："
echo "   ssh $SERVER 'tail -f ~/$REMOTE_DIR/backend/logs/sentiment_trading_cron.log'"
echo ""
echo "3. 手动测试："
echo "   ssh $SERVER 'cd ~/$REMOTE_DIR/backend && source venv/bin/activate && python3 sentiment_trading_service.py'"
echo ""
echo "4. 查看交易历史："
echo "   ssh $SERVER 'cat ~/$REMOTE_DIR/backend/data/sentiment_trading_history.json | python3 -m json.tool'"
echo ""
print_info "系统将在每天早上5点（服务器时间）自动执行"
echo ""
