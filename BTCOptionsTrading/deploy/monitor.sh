#!/bin/bash

# 系统监控脚本
# 用于监控服务状态和系统资源

PROJECT_NAME="btc-options-trading"
BACKEND_URL="http://localhost:8000/api/health"
LOG_FILE="/var/log/${PROJECT_NAME}-monitor.log"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 记录日志
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a $LOG_FILE
}

# 检查后端健康
check_backend() {
    if curl -f $BACKEND_URL > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 后端服务正常${NC}"
        return 0
    else
        echo -e "${RED}✗ 后端服务异常${NC}"
        log "ERROR: Backend service is down"
        return 1
    fi
}

# 检查Nginx
check_nginx() {
    if systemctl is-active --quiet nginx; then
        echo -e "${GREEN}✓ Nginx正常${NC}"
        return 0
    else
        echo -e "${RED}✗ Nginx异常${NC}"
        log "ERROR: Nginx is down"
        return 1
    fi
}

# 检查磁盘空间
check_disk() {
    USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ $USAGE -lt 80 ]; then
        echo -e "${GREEN}✓ 磁盘空间充足 (${USAGE}%)${NC}"
        return 0
    elif [ $USAGE -lt 90 ]; then
        echo -e "${YELLOW}⚠ 磁盘空间不足 (${USAGE}%)${NC}"
        log "WARNING: Disk usage is ${USAGE}%"
        return 1
    else
        echo -e "${RED}✗ 磁盘空间严重不足 (${USAGE}%)${NC}"
        log "ERROR: Disk usage is ${USAGE}%"
        return 1
    fi
}

# 检查内存
check_memory() {
    USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100}')
    if [ $USAGE -lt 80 ]; then
        echo -e "${GREEN}✓ 内存充足 (${USAGE}%)${NC}"
        return 0
    elif [ $USAGE -lt 90 ]; then
        echo -e "${YELLOW}⚠ 内存使用较高 (${USAGE}%)${NC}"
        log "WARNING: Memory usage is ${USAGE}%"
        return 1
    else
        echo -e "${RED}✗ 内存不足 (${USAGE}%)${NC}"
        log "ERROR: Memory usage is ${USAGE}%"
        return 1
    fi
}

# 检查CPU
check_cpu() {
    USAGE=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
    USAGE_INT=${USAGE%.*}
    if [ $USAGE_INT -lt 80 ]; then
        echo -e "${GREEN}✓ CPU正常 (${USAGE}%)${NC}"
        return 0
    elif [ $USAGE_INT -lt 90 ]; then
        echo -e "${YELLOW}⚠ CPU使用较高 (${USAGE}%)${NC}"
        log "WARNING: CPU usage is ${USAGE}%"
        return 1
    else
        echo -e "${RED}✗ CPU过载 (${USAGE}%)${NC}"
        log "ERROR: CPU usage is ${USAGE}%"
        return 1
    fi
}

# 自动修复
auto_fix() {
    echo -e "\n${YELLOW}尝试自动修复...${NC}"
    
    # 重启后端
    if ! check_backend; then
        log "INFO: Attempting to restart backend"
        sudo supervisorctl restart ${PROJECT_NAME}-backend
        sleep 5
        if check_backend; then
            log "INFO: Backend restarted successfully"
        else
            log "ERROR: Failed to restart backend"
        fi
    fi
    
    # 重启Nginx
    if ! check_nginx; then
        log "INFO: Attempting to restart nginx"
        sudo systemctl restart nginx
        sleep 2
        if check_nginx; then
            log "INFO: Nginx restarted successfully"
        else
            log "ERROR: Failed to restart nginx"
        fi
    fi
}

# 主函数
main() {
    echo "========================================="
    echo "系统监控 - $(date '+%Y-%m-%d %H:%M:%S')"
    echo "========================================="
    
    # 运行所有检查
    check_backend
    BACKEND_STATUS=$?
    
    check_nginx
    NGINX_STATUS=$?
    
    check_disk
    check_memory
    check_cpu
    
    echo "========================================="
    
    # 如果有服务异常，尝试修复
    if [ $BACKEND_STATUS -ne 0 ] || [ $NGINX_STATUS -ne 0 ]; then
        auto_fix
    fi
}

# 运行
main
