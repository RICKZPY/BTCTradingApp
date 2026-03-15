#!/bin/bash
#
# 加权情绪跨式期权交易系统 - 自动部署脚本（非交互式）
# Auto deploy weighted sentiment straddle trading system to remote server
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

print_step "加权情绪跨式期权交易系统 - 自动部署"
echo "目标服务器: $SERVER"
echo "远程目录: $REMOTE_DIR"
echo "本地目录: $LOCAL_DIR"
echo ""

# 测试SSH连接
print_info "测试SSH连接..."
if ssh -o ConnectTimeout=10 -o BatchMode=yes "$SERVER" exit 2>/dev/null; then
    print_success "SSH连接成功"
else
    print_error "无法连接到服务器（需要配置SSH密钥）"
    exit 1
fi

# 步骤1：检查服务器环境
print_step "步骤1: 检查服务器环境"

PYTHON_VERSION=$(ssh "$SERVER" "python3 --version 2>&1" || echo "未安装")
print_info "Python: $PYTHON_VERSION"

# 步骤2：创建远程目录
print_step "步骤2: 创建远程目录"

ssh "$SERVER" "mkdir -p $REMOTE_DIR/backend/{logs,data}"
print_success "远程目录已创建"

# 步骤3：上传文件
print_step "步骤3: 上传文件"

print_info "上传Python脚本..."
scp -q \
    "$LOCAL_DIR/backend/weighted_sentiment_cron.py" \
    "$LOCAL_DIR/backend/weighted_sentiment_api_client.py" \
    "$LOCAL_DIR/backend/weighted_sentiment_news_tracker.py" \
    "$LOCAL_DIR/backend/weighted_sentiment_models.py" \
    "$LOCAL_DIR/backend/weighted_sentiment_status_api.py" \
    "$SERVER:$REMOTE_DIR/backend/"
print_success "Python脚本已上传"

print_info "上传Shell脚本..."
scp -q \
    "$LOCAL_DIR/backend/setup_weighted_sentiment_cron.sh" \
    "$LOCAL_DIR/backend/check_weighted_sentiment_status.sh" \
    "$LOCAL_DIR/backend/verify_weighted_sentiment_credentials.py" \
    "$SERVER:$REMOTE_DIR/backend/"
ssh "$SERVER" "chmod +x $REMOTE_DIR/backend/*.sh"
print_success "Shell脚本已上传"

print_info "上传文档..."
scp -q \
    "$LOCAL_DIR/backend/WEIGHTED_SENTIMENT_IMPLEMENTATION.md" \
    "$LOCAL_DIR/backend/WEIGHTED_SENTIMENT_DEPLOYMENT.md" \
    "$LOCAL_DIR/backend/DEPLOYMENT_SUCCESS.md" \
    "$SERVER:$REMOTE_DIR/backend/" 2>/dev/null || true
print_success "文档已上传"

# 步骤4：检查.env文件
print_step "步骤4: 检查环境变量"

if ssh "$SERVER" "grep -q 'WEIGHTED_SENTIMENT_DERIBIT_API_KEY' $REMOTE_DIR/backend/.env 2>/dev/null"; then
    print_success "加权情绪凭证已配置"
else
    print_warning "加权情绪凭证未配置"
    print_info "请手动添加到.env文件："
    echo "  ssh $SERVER"
    echo "  nano $REMOTE_DIR/backend/.env"
    echo ""
    echo "添加以下内容："
    echo "  WEIGHTED_SENTIMENT_DERIBIT_API_KEY=your_key"
    echo "  WEIGHTED_SENTIMENT_DERIBIT_API_SECRET=your_secret"
fi

# 步骤5：安装依赖
print_step "步骤5: 安装Python依赖"

print_info "检查并安装aiohttp..."
ssh "$SERVER" "pip3 install -q aiohttp python-dotenv 2>/dev/null || pip3 install aiohttp python-dotenv"
print_success "依赖包已安装"

# 步骤6：测试运行
print_step "步骤6: 测试运行"

print_info "执行测试运行..."
ssh "$SERVER" "cd $REMOTE_DIR/backend && timeout 10 python3 weighted_sentiment_cron.py 2>&1 | head -30" || {
    print_info "测试运行完成（超时是正常的）"
}

# 步骤7：安装Cron Job
print_step "步骤7: 安装Cron Job"

print_info "检查现有Cron任务..."
if ssh "$SERVER" "crontab -l 2>/dev/null | grep -q 'weighted_sentiment_cron.py'"; then
    print_warning "Cron任务已存在，跳过安装"
else
    print_info "安装Cron任务..."
    ssh "$SERVER" "cd $REMOTE_DIR/backend && bash setup_weighted_sentiment_cron.sh" <<< $'y\n' 2>/dev/null || {
        # 手动添加cron任务
        ssh "$SERVER" "(crontab -l 2>/dev/null; echo '0 * * * * cd $REMOTE_DIR/backend && python3 weighted_sentiment_cron.py >> logs/weighted_sentiment_cron.log 2>&1') | crontab -"
    }
    print_success "Cron任务已安装"
fi

# 步骤8：显示状态
print_step "步骤8: 系统状态"

ssh "$SERVER" "cd $REMOTE_DIR/backend && bash check_weighted_sentiment_status.sh 2>/dev/null" || {
    print_info "状态检查脚本执行完成"
}

# 完成
print_step "部署完成！"

echo ""
print_success "加权情绪跨式期权交易系统已部署到服务器"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 快速命令："
echo ""
echo "1. SSH登录服务器："
echo "   ssh $SERVER"
echo ""
echo "2. 查看系统状态："
echo "   ssh $SERVER 'cd $REMOTE_DIR/backend && bash check_weighted_sentiment_status.sh'"
echo ""
echo "3. 查看实时日志："
echo "   ssh $SERVER 'tail -f $REMOTE_DIR/backend/logs/weighted_sentiment.log'"
echo ""
echo "4. 手动测试："
echo "   ssh $SERVER 'cd $REMOTE_DIR/backend && python3 weighted_sentiment_cron.py'"
echo ""
echo "5. 查看Cron任务："
echo "   ssh $SERVER 'crontab -l | grep weighted'"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

