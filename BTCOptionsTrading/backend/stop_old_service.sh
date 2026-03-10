#!/bin/bash
#
# 停止旧的情绪交易服务脚本
# 用于停止服务器上正在运行的持续模式Python进程
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

print_step "停止旧的情绪交易服务"

# 查找sentiment_trading_service.py进程
print_info "查找正在运行的sentiment_trading_service.py进程..."

PIDS=$(ps aux | grep '[s]entiment_trading_service.py' | awk '{print $2}')

if [ -z "$PIDS" ]; then
    print_success "没有找到正在运行的sentiment_trading_service.py进程"
    echo ""
    print_info "系统已经是干净状态，可以直接部署新版本"
    exit 0
fi

# 显示找到的进程
echo ""
print_warning "找到以下进程："
echo ""
ps aux | grep '[s]entiment_trading_service.py' | while read line; do
    echo "  $line"
done
echo ""

# 询问是否停止
read -p "是否停止这些进程？(y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "操作已取消"
    exit 0
fi

# 停止进程
print_info "正在停止进程..."

for PID in $PIDS; do
    print_info "停止进程 PID: $PID"
    
    # 先尝试优雅停止 (SIGTERM)
    if kill -15 $PID 2>/dev/null; then
        print_info "发送SIGTERM信号到进程 $PID"
        
        # 等待最多10秒
        for i in {1..10}; do
            if ! ps -p $PID > /dev/null 2>&1; then
                print_success "进程 $PID 已优雅停止"
                break
            fi
            sleep 1
        done
        
        # 如果还在运行，强制停止
        if ps -p $PID > /dev/null 2>&1; then
            print_warning "进程 $PID 未响应SIGTERM，使用SIGKILL强制停止"
            kill -9 $PID 2>/dev/null || true
            sleep 1
            
            if ! ps -p $PID > /dev/null 2>&1; then
                print_success "进程 $PID 已强制停止"
            else
                print_error "无法停止进程 $PID"
            fi
        fi
    else
        print_error "无法发送信号到进程 $PID（可能需要sudo权限）"
    fi
done

# 再次检查
echo ""
print_info "验证所有进程已停止..."
sleep 2

REMAINING=$(ps aux | grep '[s]entiment_trading_service.py' | wc -l)

if [ "$REMAINING" -eq 0 ]; then
    print_success "所有sentiment_trading_service.py进程已停止"
    echo ""
    print_info "现在可以安全地部署新版本了"
else
    print_warning "仍有 $REMAINING 个进程在运行"
    echo ""
    print_info "剩余进程："
    ps aux | grep '[s]entiment_trading_service.py'
    echo ""
    print_warning "你可能需要使用sudo权限："
    echo "  sudo kill -9 \$(ps aux | grep '[s]entiment_trading_service.py' | awk '{print \$2}')"
fi

echo ""
print_info "提示：如果有systemd服务，也需要停止："
echo "  sudo systemctl stop sentiment_trading"
echo "  sudo systemctl disable sentiment_trading"
