#!/bin/bash
#
# Sentiment Trading Service - Cron Job Setup Script
# 
# 这个脚本自动配置cron job来每天早上5点运行情绪交易服务
# 使用方法：
#   ./setup_cron.sh install   - 安装cron job
#   ./setup_cron.sh uninstall - 卸载cron job
#   ./setup_cron.sh status    - 查看cron job状态
#

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 脚本配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_NAME="sentiment_trading_service.py"
SCRIPT_PATH="${SCRIPT_DIR}/${SCRIPT_NAME}"
LOG_DIR="${SCRIPT_DIR}/logs"
LOG_FILE="${LOG_DIR}/sentiment_trading_cron.log"
CRON_COMMENT="# Sentiment Trading Service - Daily execution at 5:00 AM"

# 检测Python解释器
detect_python() {
    if command -v python3 &> /dev/null; then
        echo "python3"
    elif command -v python &> /dev/null; then
        echo "python"
    else
        echo ""
    fi
}

# 打印带颜色的消息
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${NC}ℹ${NC} $1"
}

# 检查环境
check_environment() {
    print_info "检查环境..."
    
    # 检查Python
    PYTHON_CMD=$(detect_python)
    if [ -z "$PYTHON_CMD" ]; then
        print_error "未找到Python解释器（python3或python）"
        exit 1
    fi
    print_success "找到Python解释器: $PYTHON_CMD"
    
    # 检查脚本文件
    if [ ! -f "$SCRIPT_PATH" ]; then
        print_error "未找到脚本文件: $SCRIPT_PATH"
        exit 1
    fi
    print_success "找到脚本文件: $SCRIPT_PATH"
    
    # 检查.env文件
    if [ ! -f "${SCRIPT_DIR}/.env" ]; then
        print_warning ".env文件不存在，请确保已配置API密钥"
    else
        print_success "找到.env配置文件"
    fi
    
    # 确保日志目录存在
    mkdir -p "$LOG_DIR"
    print_success "日志目录: $LOG_DIR"
}

# 生成cron表达式
generate_cron_entry() {
    # 每天早上5点执行
    # 格式: 分 时 日 月 周 命令
    echo "0 5 * * * cd ${SCRIPT_DIR} && ${PYTHON_CMD} ${SCRIPT_PATH} >> ${LOG_FILE} 2>&1"
}

# 检查cron job是否已存在
cron_exists() {
    crontab -l 2>/dev/null | grep -F "$SCRIPT_NAME" > /dev/null 2>&1
    return $?
}

# 安装cron job
install_cron() {
    print_info "开始安装cron job..."
    
    check_environment
    
    # 检查是否已存在
    if cron_exists; then
        print_warning "Cron job已存在"
        print_info "如需重新安装，请先运行: $0 uninstall"
        exit 0
    fi
    
    # 生成cron条目
    CRON_ENTRY=$(generate_cron_entry)
    
    # 添加到crontab
    (crontab -l 2>/dev/null || true; echo "$CRON_COMMENT"; echo "$CRON_ENTRY") | crontab -
    
    if cron_exists; then
        print_success "Cron job安装成功！"
        echo ""
        print_info "配置详情:"
        echo "  执行时间: 每天早上 5:00 AM"
        echo "  脚本路径: $SCRIPT_PATH"
        echo "  日志文件: $LOG_FILE"
        echo ""
        print_info "查看cron job: crontab -l"
        print_info "查看日志: tail -f $LOG_FILE"
        print_info "手动测试: cd $SCRIPT_DIR && $PYTHON_CMD $SCRIPT_NAME"
    else
        print_error "Cron job安装失败"
        exit 1
    fi
}

# 卸载cron job
uninstall_cron() {
    print_info "开始卸载cron job..."
    
    if ! cron_exists; then
        print_warning "Cron job不存在，无需卸载"
        exit 0
    fi
    
    # 从crontab中移除
    crontab -l 2>/dev/null | grep -v "$SCRIPT_NAME" | grep -v "$CRON_COMMENT" | crontab -
    
    if ! cron_exists; then
        print_success "Cron job卸载成功！"
    else
        print_error "Cron job卸载失败"
        exit 1
    fi
}

# 查看状态
show_status() {
    print_info "Cron Job状态:"
    echo ""
    
    check_environment
    
    if cron_exists; then
        print_success "Cron job已安装"
        echo ""
        echo "当前配置:"
        crontab -l 2>/dev/null | grep -A 1 "$CRON_COMMENT" || crontab -l 2>/dev/null | grep "$SCRIPT_NAME"
        echo ""
        
        # 检查日志文件
        if [ -f "$LOG_FILE" ]; then
            LOG_SIZE=$(du -h "$LOG_FILE" | cut -f1)
            LOG_LINES=$(wc -l < "$LOG_FILE")
            print_info "日志文件: $LOG_FILE ($LOG_SIZE, $LOG_LINES 行)"
            
            if [ "$LOG_LINES" -gt 0 ]; then
                echo ""
                print_info "最近的日志（最后10行）:"
                tail -10 "$LOG_FILE"
            fi
        else
            print_warning "日志文件尚未创建（cron job可能还未执行）"
        fi
        
        echo ""
        print_info "下次执行时间: 明天早上 5:00 AM"
    else
        print_warning "Cron job未安装"
        echo ""
        print_info "安装命令: $0 install"
    fi
}

# 显示帮助
show_help() {
    echo "Sentiment Trading Service - Cron Job Setup"
    echo ""
    echo "使用方法:"
    echo "  $0 install     安装cron job（每天早上5点执行）"
    echo "  $0 uninstall   卸载cron job"
    echo "  $0 status      查看cron job状态和日志"
    echo "  $0 help        显示此帮助信息"
    echo ""
    echo "说明:"
    echo "  此脚本配置cron job来自动运行情绪交易服务"
    echo "  服务将在每天早上5点执行一次，完成后自动退出"
    echo "  相比持续运行的服务，这种方式大幅节省服务器资源"
    echo ""
    echo "文件位置:"
    echo "  脚本: $SCRIPT_PATH"
    echo "  日志: $LOG_FILE"
    echo "  配置: ${SCRIPT_DIR}/.env"
    echo ""
    echo "手动测试:"
    echo "  cd $SCRIPT_DIR"
    echo "  $PYTHON_CMD $SCRIPT_NAME"
}

# 主函数
main() {
    case "${1:-}" in
        install)
            install_cron
            ;;
        uninstall)
            uninstall_cron
            ;;
        status)
            show_status
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "无效的命令: ${1:-}"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

main "$@"
