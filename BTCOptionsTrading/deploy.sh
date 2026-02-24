#!/bin/bash

# BTC Options Trading 部署脚本
# 用于在服务器上快速部署和启动应用

set -e  # 遇到错误立即退出

echo "=========================================="
echo "BTC Options Trading 部署脚本"
echo "=========================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查是否在项目根目录
if [ ! -f "DEPLOYMENT_GUIDE.md" ]; then
    echo -e "${RED}错误: 请在项目根目录运行此脚本${NC}"
    exit 1
fi

# 1. 拉取最新代码
echo -e "\n${YELLOW}[1/5] 拉取最新代码...${NC}"
git pull origin main
echo -e "${GREEN}✓ 代码更新完成${NC}"

# 2. 更新后端依赖
echo -e "\n${YELLOW}[2/5] 检查后端依赖...${NC}"
cd backend
if [ -f "requirements.txt" ]; then
    echo "尝试安装依赖（这可能需要几分钟）..."
    if pip install -r requirements.txt 2>/dev/null; then
        echo -e "${GREEN}✓ 后端依赖已更新${NC}"
    else
        echo -e "${YELLOW}完整依赖安装失败，尝试最小化安装...${NC}"
        if [ -f "requirements-minimal.txt" ]; then
            if pip install -r requirements-minimal.txt; then
                echo -e "${GREEN}✓ 最小化依赖安装成功${NC}"
            else
                echo -e "${RED}依赖安装失败，请运行: cd backend && ./fix_dependencies.sh${NC}"
                exit 1
            fi
        else
            echo -e "${RED}依赖安装失败，请手动安装${NC}"
            exit 1
        fi
    fi
else
    echo -e "${RED}警告: 未找到 requirements.txt${NC}"
fi
cd ..

# 3. 更新前端依赖
echo -e "\n${YELLOW}[3/5] 检查前端依赖...${NC}"
cd frontend
if [ -f "package.json" ]; then
    echo "安装前端依赖（这可能需要几分钟）..."
    npm install
    echo -e "${GREEN}✓ 前端依赖已更新${NC}"
else
    echo -e "${RED}警告: 未找到 package.json${NC}"
fi
cd ..

# 4. 停止旧进程
echo -e "\n${YELLOW}[4/5] 停止旧进程...${NC}"

# 检查是否使用 PM2
if command -v pm2 &> /dev/null; then
    echo "使用 PM2 管理进程..."
    pm2 stop btc-backend 2>/dev/null || echo "后端进程未运行"
    pm2 stop btc-frontend 2>/dev/null || echo "前端进程未运行"
    pm2 delete btc-backend 2>/dev/null || true
    pm2 delete btc-frontend 2>/dev/null || true
    echo -e "${GREEN}✓ PM2 进程已停止${NC}"
else
    echo "手动停止进程..."
    pkill -f "run_api.py" 2>/dev/null || echo "后端进程未运行"
    pkill -f "npm.*start" 2>/dev/null || echo "前端进程未运行"
    echo -e "${GREEN}✓ 进程已停止${NC}"
fi

# 5. 启动服务
echo -e "\n${YELLOW}[5/5] 启动服务...${NC}"

# 询问启动方式
echo "请选择启动方式:"
echo "1) PM2 (推荐用于生产环境)"
echo "2) nohup (后台运行)"
echo "3) 前台运行 (用于调试)"
read -p "请输入选项 (1-3): " choice

case $choice in
    1)
        # 使用 PM2
        if ! command -v pm2 &> /dev/null; then
            echo -e "${RED}错误: PM2 未安装${NC}"
            echo "请运行: npm install -g pm2"
            exit 1
        fi
        
        echo "使用 PM2 启动服务..."
        
        # 启动后端
        cd backend
        pm2 start run_api.py --name btc-backend --interpreter python3
        cd ..
        
        # 构建并启动前端
        cd frontend
        npm run build
        pm2 serve build 3000 --name btc-frontend --spa
        cd ..
        
        # 保存 PM2 配置
        pm2 save
        
        echo -e "${GREEN}✓ 服务已通过 PM2 启动${NC}"
        echo ""
        echo "查看状态: pm2 list"
        echo "查看日志: pm2 logs"
        ;;
        
    2)
        # 使用 nohup
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
        echo ""
        echo "查看后端日志: tail -f backend/logs/api.log"
        echo "查看前端日志: tail -f frontend/logs/frontend.log"
        ;;
        
    3)
        # 前台运行
        echo "前台运行模式..."
        echo "请在两个终端窗口中分别运行:"
        echo ""
        echo "终端 1 (后端):"
        echo "  cd backend && python run_api.py"
        echo ""
        echo "终端 2 (前端):"
        echo "  cd frontend && npm start"
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
    echo -e "${GREEN}✓ 后端服务运行正常 (http://localhost:8000)${NC}"
else
    echo -e "${RED}✗ 后端服务可能未正常启动${NC}"
    echo "请检查日志: tail -f backend/logs/api.log"
fi

# 检查前端
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 前端服务运行正常 (http://localhost:3000)${NC}"
else
    echo -e "${RED}✗ 前端服务可能未正常启动${NC}"
    echo "请检查日志或稍后再试"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}部署完成！${NC}"
echo "=========================================="
echo ""
echo "访问应用: http://localhost:3000"
echo "API 文档: http://localhost:8000/docs"
echo ""

if [ "$choice" = "1" ]; then
    echo "管理命令:"
    echo "  pm2 list              - 查看所有进程"
    echo "  pm2 logs              - 查看日志"
    echo "  pm2 restart all       - 重启所有服务"
    echo "  pm2 stop all          - 停止所有服务"
fi
