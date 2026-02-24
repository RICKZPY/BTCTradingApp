#!/bin/bash

# 快速部署脚本 - 跳过依赖安装，只更新代码和重启服务
# 适用于代码更新但依赖没有变化的情况

set -e

echo "=========================================="
echo "BTC Options Trading 快速部署"
echo "=========================================="

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 检查是否在项目根目录
if [ ! -f "DEPLOYMENT_GUIDE.md" ]; then
    echo -e "${RED}错误: 请在项目根目录运行此脚本${NC}"
    exit 1
fi

# 1. 拉取最新代码
echo -e "\n${YELLOW}[1/3] 拉取最新代码...${NC}"
git pull origin main
echo -e "${GREEN}✓ 代码更新完成${NC}"

# 2. 停止旧进程
echo -e "\n${YELLOW}[2/3] 停止旧进程...${NC}"

# 检查是否使用 PM2
if command -v pm2 &> /dev/null; then
    echo "使用 PM2 管理进程..."
    pm2 stop btc-backend 2>/dev/null || echo "后端进程未运行"
    pm2 stop btc-frontend 2>/dev/null || echo "前端进程未运行"
    echo -e "${GREEN}✓ PM2 进程已停止${NC}"
else
    echo "手动停止进程..."
    pkill -f "run_api.py" 2>/dev/null || echo "后端进程未运行"
    pkill -f "npm.*start" 2>/dev/null || echo "前端进程未运行"
    echo -e "${GREEN}✓ 进程已停止${NC}"
fi

# 3. 启动服务
echo -e "\n${YELLOW}[3/3] 启动服务...${NC}"

# 检查是否使用 PM2
if command -v pm2 &> /dev/null; then
    echo "使用 PM2 重启服务..."
    
    # 重启后端
    cd backend
    pm2 restart btc-backend 2>/dev/null || pm2 start run_api.py --name btc-backend --interpreter python3
    cd ..
    
    # 重启前端
    cd frontend
    pm2 restart btc-frontend 2>/dev/null || pm2 serve build 3000 --name btc-frontend --spa
    cd ..
    
    echo -e "${GREEN}✓ 服务已通过 PM2 重启${NC}"
    echo ""
    pm2 list
else
    echo "使用 nohup 启动服务..."
    
    # 启动后端
    cd backend
    mkdir -p logs
    nohup python run_api.py > logs/api.log 2>&1 &
    echo "后端 PID: $!"
    cd ..
    
    # 启动前端
    cd frontend
    mkdir -p logs
    nohup npm start > logs/frontend.log 2>&1 &
    echo "前端 PID: $!"
    cd ..
    
    echo -e "${GREEN}✓ 服务已在后台启动${NC}"
fi

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
    echo -e "${YELLOW}⚠ 前端服务正在启动中${NC}"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}快速部署完成！${NC}"
echo "=========================================="
echo ""
echo "如果遇到问题，请使用完整部署: ./deploy.sh"
