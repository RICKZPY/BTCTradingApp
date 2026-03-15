#!/bin/bash
#
# 加权情绪跨式期权交易系统 - 服务器部署脚本
# Deploy weighted sentiment straddle trading system to remote server
#
# 使用方法：
#   ./deploy_weighted_sentiment.sh
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

# 服务器配置
SERVER="root@47.86.62.200"
REMOTE_DIR="/root/BTCOptionsTrading"
LOCAL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

print_step "加权情绪跨式期权交易系统 - 服务器部署"
echo "目标服务器: $SERVER"
echo "远程目录: $REMOTE_DIR"
echo "本地目录: $LOCAL_DIR"
echo ""

# 测试SSH连接
print_info "测试SSH连接..."
if ssh -o ConnectTimeout=10 "$SERVER" exit 2>/dev/null; then
    print_success "SSH连接成功"
else
    print_error "无法连接到服务器"
    print_info "请确保："
    echo "  1. 服务器地址正确: 47.86.62.200"
    echo "  2. SSH密钥已配置或可以使用密码登录"
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
    exit 1
fi

print_info "检查pip..."
if ssh "$SERVER" "command -v pip3 &> /dev/null"; then
    print_success "找到pip3"
else
    print_warning "未找到pip3"
fi

print_info "检查SQLite..."
if ssh "$SERVER" "command -v sqlite3 &> /dev/null"; then
    SQLITE_VERSION=$(ssh "$SERVER" "sqlite3 --version | awk '{print \$1}'")
    print_success "找到SQLite: $SQLITE_VERSION"
else
    print_warning "未找到sqlite3"
fi

# 步骤2：创建远程目录
print_step "步骤2: 创建远程目录"

ssh "$SERVER" "mkdir -p $REMOTE_DIR/backend/{logs,data}"
print_success "远程目录已创建"

# 步骤3：上传加权情绪系统文件
print_step "步骤3: 上传加权情绪系统文件"

print_info "上传核心文件..."

# 上传Python脚本
rsync -avz --progress \
    "$LOCAL_DIR/backend/weighted_sentiment_cron.py" \
    "$LOCAL_DIR/backend/weighted_sentiment_api_client.py" \
    "$LOCAL_DIR/backend/weighted_sentiment_news_tracker.py" \
    "$LOCAL_DIR/backend/weighted_sentiment_models.py" \
    "$LOCAL_DIR/backend/weighted_sentiment_status_api.py" \
    "$SERVER:$REMOTE_DIR/backend/"

print_success "Python脚本已上传"

# 上传Shell脚本
print_info "上传Shell脚本..."
rsync -avz --progress \
    "$LOCAL_DIR/backend/setup_weighted_sentiment_cron.sh" \
    "$LOCAL_DIR/backend/check_weighted_sentiment_status.sh" \
    "$LOCAL_DIR/backend/verify_weighted_sentiment_credentials.py" \
    "$SERVER:$REMOTE_DIR/backend/"

ssh "$SERVER" "chmod +x $REMOTE_DIR/backend/*.sh"
print_success "Shell脚本已上传并添加执行权限"

# 上传文档
print_info "上传文档..."
rsync -avz --progress \
    "$LOCAL_DIR/backend/WEIGHTED_SENTIMENT_IMPLEMENTATION.md" \
    "$LOCAL_DIR/backend/WEIGHTED_SENTIMENT_DEPLOYMENT.md" \
    "$LOCAL_DIR/backend/DEPLOYMENT_SUCCESS.md" \
    "$SERVER:$REMOTE_DIR/backend/" 2>/dev/null || true

print_success "文档已上传"

# 步骤4：配置.env文件
print_step "步骤4: 配置环境变量"

print_info "检查.env文件..."
if ssh "$SERVER" "[ -f $REMOTE_DIR/backend/.env ]"; then
    print_warning ".env文件已存在"
    
    # 检查是否包含加权情绪凭证
    if ssh "$SERVER" "grep -q 'WEIGHTED_SENTIMENT_DERIBIT_API_KEY' $REMOTE_DIR/backend/.env"; then
        print_success "加权情绪凭证已配置"
    else
        print_warning "需要添加加权情绪凭证"
        echo ""
        read -p "是否现在添加？(y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo ""
            read -p "WEIGHTED_SENTIMENT_DERIBIT_API_KEY: " WS_KEY
            read -p "WEIGHTED_SENTIMENT_DERIBIT_API_SECRET: " WS_SECRET
            
            ssh "$SERVER" "cat >> $REMOTE_DIR/backend/.env << EOF

# ========================================
# 加权情绪跨式期权交易 - 独立账户
# ========================================
WEIGHTED_SENTIMENT_DERIBIT_API_KEY=$WS_KEY
WEIGHTED_SENTIMENT_DERIBIT_API_SECRET=$WS_SECRET
EOF"
            print_success "加权情绪凭证已添加"
        fi
    fi
else
    print_error ".env文件不存在"
    print_info "请先部署主系统或手动创建.env文件"
    exit 1
fi

# 步骤5：安装Python依赖
print_step "步骤5: 安装Python依赖"

print_info "检查aiohttp..."
if ssh "$SERVER" "cd $REMOTE_DIR/backend && python3 -c 'import aiohttp' 2>/dev/null"; then
    print_success "aiohttp已安装"
else
    print_info "安装aiohttp..."
    ssh "$SERVER" "pip3 install aiohttp python-dotenv"
    print_success "依赖包安装完成"
fi

# 步骤6：验证凭证配置
print_step "步骤6: 验证凭证配置"

print_info "运行凭证验证脚本..."
ssh "$SERVER" "cd $REMOTE_DIR/backend && python3 verify_weighted_sentiment_credentials.py" || {
    print_warning "凭证验证失败"
    print_info "请检查.env文件中的配置"
}

# 步骤7：测试运行
print_step "步骤7: 测试运行"

print_info "执行测试运行..."
if ssh "$SERVER" "cd $REMOTE_DIR/backend && timeout 30 python3 weighted_sentiment_cron.py 2>&1 | head -50"; then
    print_success "测试运行成功"
else
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 124 ]; then
        print_success "测试运行正常（超时是预期的）"
    else
        print_warning "测试运行失败，退出码: $EXIT_CODE"
    fi
fi

# 步骤8：安装Cron Job
print_step "步骤8: 安装Cron Job"

echo ""
read -p "是否立即安装Cron Job（每小时执行一次）？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "安装Cron Job..."
    ssh "$SERVER" "cd $REMOTE_DIR/backend && bash setup_weighted_sentiment_cron.sh" <<< "y"
    print_success "Cron Job已安装"
    
    # 显示Cron任务
    echo ""
    print_info "当前Cron任务："
    ssh "$SERVER" "crontab -l | grep weighted_sentiment"
else
    print_warning "跳过Cron Job安装"
    print_info "稍后可以手动安装："
    echo "  ssh $SERVER"
    echo "  cd $REMOTE_DIR/backend"
    echo "  bash setup_weighted_sentiment_cron.sh"
fi

# 步骤9：检查系统状态
print_step "步骤9: 检查系统状态"

print_info "运行状态检查..."
ssh "$SERVER" "cd $REMOTE_DIR/backend && bash check_weighted_sentiment_status.sh"

# 步骤10：配置日志轮转（可选）
print_step "步骤10: 配置日志轮转（可选）"

echo ""
read -p "是否配置日志轮转？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "创建logrotate配置..."
    ssh "$SERVER" "sudo tee /etc/logrotate.d/weighted-sentiment > /dev/null << 'EOF'
$REMOTE_DIR/backend/logs/weighted_sentiment*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
}
EOF"
    print_success "日志轮转已配置"
else
    print_warning "跳过日志轮转配置"
fi

# 完成
print_step "部署完成！"

echo ""
print_success "加权情绪跨式期权交易系统已成功部署到服务器"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 系统信息："
echo "   服务器: 47.86.62.200"
echo "   路径: $REMOTE_DIR/backend"
echo "   执行频率: 每小时整点"
echo ""
echo "🔍 监控命令："
echo ""
echo "1. 查看系统状态："
echo "   ssh $SERVER 'cd $REMOTE_DIR/backend && bash check_weighted_sentiment_status.sh'"
echo ""
echo "2. 查看实时日志："
echo "   ssh $SERVER 'tail -f $REMOTE_DIR/backend/logs/weighted_sentiment.log'"
echo ""
echo "3. 查看Cron执行日志："
echo "   ssh $SERVER 'tail -f $REMOTE_DIR/backend/logs/weighted_sentiment_cron.log'"
echo ""
echo "4. 查看交易记录："
echo "   ssh $SERVER 'tail -f $REMOTE_DIR/backend/logs/weighted_sentiment_trades.log'"
echo ""
echo "5. 手动测试运行："
echo "   ssh $SERVER 'cd $REMOTE_DIR/backend && python3 weighted_sentiment_cron.py'"
echo ""
echo "6. 查看数据库："
echo "   ssh $SERVER 'sqlite3 $REMOTE_DIR/backend/data/weighted_news_history.db \"SELECT COUNT(*) FROM news_history;\"'"
echo ""
echo "7. 查看Cron任务："
echo "   ssh $SERVER 'crontab -l | grep weighted_sentiment'"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
print_info "系统将在每小时整点自动执行"
print_info "首次执行时间：下一个整点（例如：10:00, 11:00, 12:00...）"
echo ""

