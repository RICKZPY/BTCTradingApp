#!/bin/bash
#
# 设置情绪交易API为systemd服务
# 这样可以开机自启动，并且自动重启
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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_FILE="sentiment_api.service"
SYSTEMD_DIR="/etc/systemd/system"

# 检查是否为root
if [ "$EUID" -ne 0 ]; then 
    print_error "请使用root权限运行此脚本"
    echo "使用: sudo $0"
    exit 1
fi

print_step "设置情绪交易API服务"

# 检查服务文件
if [ ! -f "$SCRIPT_DIR/$SERVICE_FILE" ]; then
    print_error "未找到服务文件: $SERVICE_FILE"
    exit 1
fi

# 更新服务文件中的路径
print_info "配置服务文件..."
TEMP_SERVICE="/tmp/sentiment_api.service"
sed "s|/root/BTCOptionsTrading|$SCRIPT_DIR/..|g" "$SCRIPT_DIR/$SERVICE_FILE" > "$TEMP_SERVICE"

# 复制服务文件
print_info "安装服务文件..."
cp "$TEMP_SERVICE" "$SYSTEMD_DIR/$SERVICE_FILE"
rm "$TEMP_SERVICE"

# 重新加载systemd
print_info "重新加载systemd..."
systemctl daemon-reload

# 启用服务
print_info "启用服务（开机自启）..."
systemctl enable sentiment_api.service

# 启动服务
print_info "启动服务..."
systemctl start sentiment_api.service

# 等待服务启动
sleep 2

# 检查状态
if systemctl is-active --quiet sentiment_api.service; then
    print_success "API服务已成功启动"
    echo ""
    print_info "服务信息:"
    systemctl status sentiment_api.service --no-pager -l
    echo ""
    print_info "常用命令:"
    echo "  查看状态: sudo systemctl status sentiment_api"
    echo "  查看日志: sudo journalctl -u sentiment_api -f"
    echo "  重启服务: sudo systemctl restart sentiment_api"
    echo "  停止服务: sudo systemctl stop sentiment_api"
    echo "  禁用服务: sudo systemctl disable sentiment_api"
else
    print_error "服务启动失败"
    print_info "查看日志:"
    journalctl -u sentiment_api.service -n 50 --no-pager
    exit 1
fi
