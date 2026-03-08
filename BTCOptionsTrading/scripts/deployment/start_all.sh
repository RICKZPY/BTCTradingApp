#!/bin/bash

# 一键启动前后端服务

set -e

echo "=========================================="
echo "BTC Options Trading 一键启动"
echo "=========================================="

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 检查是否在项目根目录
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo -e "${RED}错误: 请在项目根目录运行此脚本${NC}"
    exit 1
fi

# 询问启动方式
echo "请选择启动方式:"
echo "1) PM2 (推荐，生产环境)"
echo "2) nohup (后台运行)"
echo "3) 前台运行 (调试用)"
read -p "请输入选项 (1-3): " choice

case $choice in
    1)
        # 使用 PM2
        if ! command -v pm2 &> /dev/null; then
            echo -e "${RED}PM2 未安装，正在安装...${NC}"
            npm install -g pm2
        fi
        
        echo -e "\n${YELLOW}使用 PM2 启动服务...${NC}"
        
        # 启动后端
        echo "启动后端..."
        cd backend
        pm2 start run_api.py --name btc-backend --interpreter python3
        cd ..
        
        # 启动前端
        echo "启动前端..."
        cd frontend
        
        # 检查是否需要构建
        if [ ! -d "build" ]; then
            echo "首次运行，正在构建前端..."
            npm run build
        fi
        
        pm2 serve build 3000 --name btc-frontend --spa
        cd ..
        
        # 保存配置
        pm2 save
        
        echo -e "\n${GREEN}✓ 服务已启动${NC}"
        echo ""
        pm2 list
        echo ""
        echo "管理命令:"
        echo "  pm2 list              - 查看所有进程"
        echo "  pm2 logs              - 查看日志"
        echo "  pm2 restart all       - 重启所有服务"
        echo "  pm2 stop all          - 停止所有服务"
        ;;
        
    2)
        # 使用 nohup
        echo -e "\n${YELLOW}使用 nohup 启动服务...${NC}"
        
        # 启动后端
        echo "启动后端..."
        cd backend
        mkdir -p logs
        nohup python run_api.py > logs/api.log 2>&1 &
        backend_pid=$!
        echo "后端 PID: $backend_pid"
        cd ..
        
        # 启动前端
        echo "启动前端..."
        cd frontend
        mkdir -p logs
        nohup npm start > logs/frontend.log 2>&1 &
        frontend_pid=$!
        echo "前端 PID: $frontend_pid"
        cd ..
        
        echo -e "\n${GREEN}✓ 服务已在后台启动${NC}"
        echo ""
        echo "查看日志:"
        echo "  tail -f backend/logs/api.log"
        echo "  tail -f frontend/logs/frontend.log"
        echo ""
        echo "停止服务:"
        echo "  kill $backend_pid $frontend_pid"
        ;;
        
    3)
        # 前台运行
        echo -e "\n${YELLOW}前台运行模式${NC}"
        echo ""
        echo "请打开两个终端窗口："
        echo ""
        echo "终端 1 (后端):"
        echo "  cd backend"
        echo "  python run_api.py"
        echo ""
        echo "终端 2 (前端):"
        echo "  cd frontend"
        echo "  npm start"
        exit 0
        ;;
        
    *)
        echo -e "${RED}无效选项${NC}"
        exit 1
        ;;
esac

# 等待服务启动
echo -e "\n${YELLOW}等待服务启动...${NC}"
sleep 5

# 验证服务
echo -e "\n${YELLOW}验证服务状态...${NC}"

# 检查后端
if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 后端服务运行正常${NC}"
else
    echo -e "${RED}✗ 后端服务可能未正常启动${NC}"
fi

# 检查前端
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 前端服务运行正常${NC}"
else
    echo -e "${YELLOW}⚠ 前端服务正在启动中，请稍候...${NC}"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}启动完成！${NC}"
echo "=========================================="
echo ""
echo "访问地址:"
echo "  前端: http://localhost:3000"
echo "  后端: http://localhost:8000"
echo "  API 文档: http://localhost:8000/docs"
echo ""
echo "如需从本地浏览器访问服务器："
echo "  方法 1: 直接访问 http://your_server_ip:3000"
echo "  方法 2: SSH 端口转发"
echo "    ssh -L 3000:localhost:3000 -L 8000:localhost:8000 root@your_server_ip"
echo "    然后访问 http://localhost:3000"
echo ""
