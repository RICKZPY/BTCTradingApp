#!/bin/bash
# 情绪交易系统管理脚本（服务器端）

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

show_menu() {
    echo ""
    echo "=========================================="
    echo "情绪交易系统管理菜单"
    echo "=========================================="
    echo "1. 查看服务状态"
    echo "2. 启动服务"
    echo "3. 停止服务"
    echo "4. 重启服务"
    echo "5. 查看实时日志"
    echo "6. 查看交易历史"
    echo "7. 查看当前持仓"
    echo "8. 测试系统"
    echo "9. 备份数据"
    echo "10. 清理日志"
    echo "0. 退出"
    echo "=========================================="
    echo -n "请选择操作 [0-10]: "
}

check_status() {
    echo ""
    echo "=========================================="
    echo "服务状态"
    echo "=========================================="
    
    echo ""
    echo "情绪交易服务:"
    if systemctl is-active --quiet sentiment_trading.service; then
        echo -e "${GREEN}✓ 运行中${NC}"
        systemctl status sentiment_trading.service --no-pager | grep -E "Active|Main PID"
    else
        echo -e "${RED}✗ 已停止${NC}"
    fi
    
    echo ""
    echo "API服务:"
    if systemctl is-active --quiet sentiment_api.service; then
        echo -e "${GREEN}✓ 运行中${NC}"
        systemctl status sentiment_api.service --no-pager | grep -E "Active|Main PID"
    else
        echo -e "${RED}✗ 已停止${NC}"
    fi
    
    echo ""
    echo "端口监听:"
    if netstat -tlnp 2>/dev/null | grep -q ":5002"; then
        echo -e "${GREEN}✓ 端口5002已监听${NC}"
    else
        echo -e "${RED}✗ 端口5002未监听${NC}"
    fi
}

start_services() {
    echo ""
    echo "启动服务..."
    systemctl start sentiment_trading.service
    systemctl start sentiment_api.service
    sleep 2
    check_status
}

stop_services() {
    echo ""
    echo "停止服务..."
    systemctl stop sentiment_trading.service
    systemctl stop sentiment_api.service
    echo -e "${GREEN}✓ 服务已停止${NC}"
}

restart_services() {
    echo ""
    echo "重启服务..."
    systemctl restart sentiment_trading.service
    systemctl restart sentiment_api.service
    sleep 2
    check_status
}

view_logs() {
    echo ""
    echo "=========================================="
    echo "实时日志（按Ctrl+C退出）"
    echo "=========================================="
    echo ""
    echo "选择日志类型："
    echo "1. 情绪交易服务日志"
    echo "2. API服务日志"
    echo "3. 应用日志文件"
    echo -n "请选择 [1-3]: "
    read log_choice
    
    case $log_choice in
        1)
            journalctl -u sentiment_trading.service -f
            ;;
        2)
            journalctl -u sentiment_api.service -f
            ;;
        3)
            tail -f logs/sentiment_trading.log
            ;;
        *)
            echo "无效选择"
            ;;
    esac
}

view_history() {
    echo ""
    echo "=========================================="
    echo "交易历史"
    echo "=========================================="
    
    if [ -f data/sentiment_trading_history.json ]; then
        echo ""
        echo "总交易次数: $(cat data/sentiment_trading_history.json | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")"
        echo ""
        echo "最近5笔交易:"
        cat data/sentiment_trading_history.json | python3 -m json.tool | tail -100
    else
        echo "暂无交易历史"
    fi
}

view_positions() {
    echo ""
    echo "=========================================="
    echo "当前持仓和订单"
    echo "=========================================="
    
    if [ -f data/current_positions.json ]; then
        cat data/current_positions.json | python3 -m json.tool
    else
        echo "暂无持仓数据"
    fi
    
    echo ""
    echo "实时查询Deribit..."
    curl -s http://localhost:5002/api/live/positions | python3 -m json.tool 2>/dev/null || echo "API服务未运行"
}

run_test() {
    echo ""
    echo "=========================================="
    echo "运行系统测试"
    echo "=========================================="
    python3 test_sentiment_trading.py
}

backup_data() {
    echo ""
    echo "=========================================="
    echo "备份数据"
    echo "=========================================="
    
    BACKUP_DIR="backups"
    mkdir -p $BACKUP_DIR
    
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="$BACKUP_DIR/sentiment_backup_$TIMESTAMP.tar.gz"
    
    echo "创建备份: $BACKUP_FILE"
    tar -czf $BACKUP_FILE data/ logs/ 2>/dev/null
    
    if [ -f $BACKUP_FILE ]; then
        echo -e "${GREEN}✓ 备份完成${NC}"
        echo "备份文件: $BACKUP_FILE"
        echo "文件大小: $(du -h $BACKUP_FILE | cut -f1)"
    else
        echo -e "${RED}✗ 备份失败${NC}"
    fi
    
    # 清理旧备份（保留最近7天）
    echo ""
    echo "清理旧备份..."
    find $BACKUP_DIR -name "sentiment_backup_*.tar.gz" -mtime +7 -delete
    echo "当前备份文件:"
    ls -lh $BACKUP_DIR/
}

clean_logs() {
    echo ""
    echo "=========================================="
    echo "清理日志"
    echo "=========================================="
    
    echo "当前日志大小:"
    du -sh logs/
    
    echo ""
    echo -n "确认清理日志? (y/n): "
    read confirm
    
    if [ "$confirm" = "y" ]; then
        # 备份当前日志
        TIMESTAMP=$(date +%Y%m%d_%H%M%S)
        tar -czf "backups/logs_backup_$TIMESTAMP.tar.gz" logs/ 2>/dev/null
        
        # 清空日志
        > logs/sentiment_trading.log
        > logs/sentiment_api.log
        
        echo -e "${GREEN}✓ 日志已清理${NC}"
        echo "备份保存在: backups/logs_backup_$TIMESTAMP.tar.gz"
    else
        echo "已取消"
    fi
}

# 主循环
while true; do
    show_menu
    read choice
    
    case $choice in
        1)
            check_status
            ;;
        2)
            start_services
            ;;
        3)
            stop_services
            ;;
        4)
            restart_services
            ;;
        5)
            view_logs
            ;;
        6)
            view_history
            ;;
        7)
            view_positions
            ;;
        8)
            run_test
            ;;
        9)
            backup_data
            ;;
        10)
            clean_logs
            ;;
        0)
            echo ""
            echo "退出管理脚本"
            exit 0
            ;;
        *)
            echo -e "${RED}无效选择，请重试${NC}"
            ;;
    esac
    
    echo ""
    read -p "按Enter继续..."
done
