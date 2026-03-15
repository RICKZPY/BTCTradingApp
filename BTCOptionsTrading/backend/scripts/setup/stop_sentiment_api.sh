#!/bin/bash
#
# 停止情绪交易API服务
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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/sentiment_api.pid"

print_info "停止情绪交易API服务..."

# 检查PID文件
if [ ! -f "$PID_FILE" ]; then
    print_warning "未找到PID文件"
    
    # 尝试查找进程
    PIDS=$(ps aux | grep '[s]entiment_api.py' | awk '{print $2}')
    if [ -z "$PIDS" ]; then
        print_info "API服务未运行"
        exit 0
    else
        print_warning "找到运行中的进程，尝试停止..."
        for PID in $PIDS; do
            kill $PID 2>/dev/null || true
            print_success "已停止进程 $PID"
        done
        exit 0
    fi
fi

# 读取PID
PID=$(cat "$PID_FILE")

# 检查进程是否存在
if ! ps -p $PID > /dev/null 2>&1; then
    print_warning "进程不存在 (PID: $PID)"
    rm -f "$PID_FILE"
    exit 0
fi

# 停止进程
print_info "停止进程 (PID: $PID)..."
kill $PID 2>/dev/null || true

# 等待进程结束
for i in {1..10}; do
    if ! ps -p $PID > /dev/null 2>&1; then
        print_success "API服务已停止"
        rm -f "$PID_FILE"
        exit 0
    fi
    sleep 1
done

# 如果还在运行，强制停止
if ps -p $PID > /dev/null 2>&1; then
    print_warning "进程未响应，强制停止..."
    kill -9 $PID 2>/dev/null || true
    sleep 1
    
    if ! ps -p $PID > /dev/null 2>&1; then
        print_success "API服务已强制停止"
        rm -f "$PID_FILE"
    else
        print_error "无法停止进程"
        exit 1
    fi
fi
