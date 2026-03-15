#!/bin/bash
#
# 启动情绪交易API服务（后台运行）
# 使用nohup确保SSH断开后服务继续运行
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
API_SCRIPT="sentiment_api.py"
PID_FILE="$SCRIPT_DIR/sentiment_api.pid"
LOG_FILE="$SCRIPT_DIR/logs/sentiment_api.log"
PORT=5002

# 确保日志目录存在
mkdir -p "$SCRIPT_DIR/logs"

# 检查是否已经在运行
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        print_warning "API服务已经在运行 (PID: $PID)"
        print_info "如需重启，请先运行: ./stop_sentiment_api.sh"
        exit 0
    else
        print_warning "发现过期的PID文件，清理中..."
        rm -f "$PID_FILE"
    fi
fi

print_info "启动情绪交易API服务..."

# 检查虚拟环境
if [ -d "$SCRIPT_DIR/venv" ]; then
    print_info "使用虚拟环境"
    PYTHON_CMD="$SCRIPT_DIR/venv/bin/python3"
else
    print_warning "未找到虚拟环境，使用系统Python"
    PYTHON_CMD="python3"
fi

# 检查Python和依赖
if ! command -v $PYTHON_CMD &> /dev/null; then
    print_error "未找到Python3"
    exit 1
fi

# 使用nohup在后台启动
cd "$SCRIPT_DIR"
nohup $PYTHON_CMD "$API_SCRIPT" >> "$LOG_FILE" 2>&1 &
API_PID=$!

# 保存PID
echo $API_PID > "$PID_FILE"

# 等待服务启动
sleep 2

# 验证服务是否运行
if ps -p $API_PID > /dev/null 2>&1; then
    print_success "API服务已启动 (PID: $API_PID)"
    echo ""
    print_info "服务信息:"
    echo "  PID: $API_PID"
    echo "  端口: $PORT"
    echo "  日志: $LOG_FILE"
    echo "  PID文件: $PID_FILE"
    echo ""
    print_info "测试访问:"
    echo "  curl http://localhost:$PORT/api/health"
    echo ""
    print_info "查看日志:"
    echo "  tail -f $LOG_FILE"
    echo ""
    print_info "停止服务:"
    echo "  ./stop_sentiment_api.sh"
else
    print_error "API服务启动失败"
    print_info "查看日志: tail -50 $LOG_FILE"
    rm -f "$PID_FILE"
    exit 1
fi
