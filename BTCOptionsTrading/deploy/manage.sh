#!/bin/bash

# 服务器管理脚本 - 统一管理接口

PROJECT_NAME="btc-options-trading"
DEPLOY_PATH="/opt/${PROJECT_NAME}"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

show_menu() {
    clear
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  BTC期权交易系统 - 服务器管理${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo "1. 查看服务状态"
    echo "2. 启动所有服务"
    echo "3. 停止所有服务"
    echo "4. 重启所有服务"
    echo "5. 查看后端日志"
    echo "6. 查看Nginx日志"
    echo "7. 系统监控"
    echo "8. 更新系统"
    echo "9. 备份数据"
    echo "10. 清理日志"
    echo "0. 退出"
    echo ""
    echo -e "${BLUE}========================================${NC}"
}

check_status() {
    echo -e "\n${GREEN}=== 服务状态 ===${NC}"
    echo -e "\n后端服务:"
    sudo supervisorctl status ${PROJECT_NAME}-backend
    
    echo -e "\nNginx服务:"
    sudo systemctl status nginx --no-pager | head -5
    
    echo -e "\n端口监听:"
    sudo netstat -tlnp | grep -E ':(80|8000)' || echo "无监听端口"
    
    echo -e "\n系统资源:"
    echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}')%"
    echo "内存: $(free -m | awk 'NR==2{printf "%.1f%%", $3*100/$2}')"
    echo "磁盘: $(df -h / | awk 'NR==2{print $5}')"
}

start_services() {
    echo -e "\n${GREEN}启动所有服务...${NC}"
    sudo supervisorctl start ${PROJECT_NAME}-backend
    sudo systemctl start nginx
    echo -e "${GREEN}完成！${NC}"
    sleep 2
    check_status
}

stop_services() {
    echo -e "\n${YELLOW}停止所有服务...${NC}"
    sudo supervisorctl stop ${PROJECT_NAME}-backend
    sudo systemctl stop nginx
    echo -e "${GREEN}完成！${NC}"
}

restart_services() {
    echo -e "\n${GREEN}重启所有服务...${NC}"
    sudo supervisorctl restart ${PROJECT_NAME}-backend
    sudo systemctl restart nginx
    echo -e "${GREEN}完成！${NC}"
    sleep 2
    check_status
}

view_backend_logs() {
    echo -e "\n${GREEN}后端日志 (Ctrl+C退出)${NC}"
    sudo tail -f /var/log/${PROJECT_NAME}-backend.log
}

view_nginx_logs() {
    echo -e "\n${GREEN}选择日志类型:${NC}"
    echo "1. 访问日志"
    echo "2. 错误日志"
    read -p "请选择 (1-2): " log_choice
    
    case $log_choice in
        1)
            echo -e "\n${GREEN}Nginx访问日志 (Ctrl+C退出)${NC}"
            sudo tail -f /var/log/nginx/${PROJECT_NAME}_access.log
            ;;
        2)
            echo -e "\n${GREEN}Nginx错误日志 (Ctrl+C退出)${NC}"
            sudo tail -f /var/log/nginx/${PROJECT_NAME}_error.log
            ;;
        *)
            echo -e "${RED}无效选择${NC}"
            ;;
    esac
}

run_monitor() {
    echo -e "\n${GREEN}运行系统监控...${NC}"
    cd ${DEPLOY_PATH}/deploy
    sudo ./monitor.sh
}

update_system() {
    echo -e "\n${YELLOW}确定要更新系统吗？${NC}"
    read -p "输入 'yes' 确认: " confirm
    
    if [ "$confirm" = "yes" ]; then
        cd ${DEPLOY_PATH}/deploy
        sudo ./update.sh
    else
        echo "已取消"
    fi
}

backup_data() {
    echo -e "\n${GREEN}备份数据...${NC}"
    
    BACKUP_DIR="/opt/backups"
    sudo mkdir -p ${BACKUP_DIR}
    
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    
    # 备份数据库
    if [ -f "${DEPLOY_PATH}/backend/data/btc_options.db" ]; then
        sudo cp ${DEPLOY_PATH}/backend/data/btc_options.db \
               ${BACKUP_DIR}/btc_options_${TIMESTAMP}.db
        echo -e "${GREEN}✓ 数据库已备份${NC}"
    fi
    
    # 备份配置
    sudo tar czf ${BACKUP_DIR}/config_${TIMESTAMP}.tar.gz \
           ${DEPLOY_PATH}/backend/.env \
           ${DEPLOY_PATH}/frontend/.env \
           2>/dev/null
    echo -e "${GREEN}✓ 配置文件已备份${NC}"
    
    echo -e "\n备份位置: ${BACKUP_DIR}"
    ls -lh ${BACKUP_DIR}
}

clean_logs() {
    echo -e "\n${YELLOW}清理日志文件...${NC}"
    
    # 显示当前日志大小
    echo "当前日志大小:"
    sudo du -sh /var/log/${PROJECT_NAME}-backend.log 2>/dev/null || echo "后端日志: 0"
    sudo du -sh /var/log/nginx/${PROJECT_NAME}_*.log 2>/dev/null || echo "Nginx日志: 0"
    
    read -p "确定要清理吗？(yes/no): " confirm
    
    if [ "$confirm" = "yes" ]; then
        # 备份后清理
        sudo cp /var/log/${PROJECT_NAME}-backend.log \
               /var/log/${PROJECT_NAME}-backend.log.backup 2>/dev/null
        sudo truncate -s 0 /var/log/${PROJECT_NAME}-backend.log
        
        sudo cp /var/log/nginx/${PROJECT_NAME}_access.log \
               /var/log/nginx/${PROJECT_NAME}_access.log.backup 2>/dev/null
        sudo truncate -s 0 /var/log/nginx/${PROJECT_NAME}_access.log
        
        echo -e "${GREEN}✓ 日志已清理（备份已保存）${NC}"
    else
        echo "已取消"
    fi
}

# 主循环
while true; do
    show_menu
    read -p "请选择操作 (0-10): " choice
    
    case $choice in
        1) check_status ;;
        2) start_services ;;
        3) stop_services ;;
        4) restart_services ;;
        5) view_backend_logs ;;
        6) view_nginx_logs ;;
        7) run_monitor ;;
        8) update_system ;;
        9) backup_data ;;
        10) clean_logs ;;
        0) 
            echo -e "\n${GREEN}再见！${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}无效选择，请重试${NC}"
            ;;
    esac
    
    echo ""
    read -p "按Enter继续..."
done
