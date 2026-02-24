#!/bin/bash

# 低内存服务器部署脚本（适用于 1GB RAM）
# 自动添加 swap 并优化部署流程

set -e

echo "=========================================="
echo "低内存服务器部署脚本"
echo "=========================================="

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 检查内存
total_mem=$(free -m | awk 'NR==2{print $2}')
echo -e "\n${YELLOW}检测到系统内存: ${total_mem}MB${NC}"

if [ $total_mem -lt 1500 ]; then
    echo -e "${YELLOW}内存较低，建议添加 swap 空间${NC}"
    
    # 检查是否已有 swap
    if [ $(swapon --show | wc -l) -eq 0 ]; then
        read -p "是否创建 2GB swap 空间? (y/n): " create_swap
        
        if [ "$create_swap" = "y" ]; then
            echo -e "\n${YELLOW}创建 swap 空间...${NC}"
            
            # 创建 swap 文件
            sudo fallocate -l 2G /swapfile || sudo dd if=/dev/zero of=/swapfile bs=1M count=2048
            sudo chmod 600 /swapfile
            sudo mkswap /swapfile
            sudo swapon /swapfile
            
            # 永久启用
            if ! grep -q '/swapfile' /etc/fstab; then
                echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
            fi
            
            # 优化 swap 使用
            sudo sysctl vm.swappiness=10
            if ! grep -q 'vm.swappiness' /etc/sysctl.conf; then
                echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
            fi
            
            echo -e "${GREEN}✓ Swap 空间创建成功${NC}"
            free -h
        fi
    else
        echo -e "${GREEN}✓ 已存在 swap 空间${NC}"
        free -h
    fi
fi

# 1. 拉取最新代码
echo -e "\n${YELLOW}[1/4] 拉取最新代码...${NC}"
git pull origin main
echo -e "${GREEN}✓ 代码更新完成${NC}"

# 2. 更新后端依赖
echo -e "\n${YELLOW}[2/4] 更新后端依赖...${NC}"
cd backend
pip install -r requirements-minimal.txt
echo -e "${GREEN}✓ 后端依赖已更新${NC}"
cd ..

# 3. 处理前端
echo -e "\n${YELLOW}[3/4] 处理前端...${NC}"
cd frontend

# 检查是否已有 build 目录
if [ -d "build" ]; then
    echo -e "${GREEN}✓ 发现已有构建文件，跳过构建${NC}"
else
    echo -e "${YELLOW}未找到构建文件${NC}"
    echo ""
    echo "选择前端部署方式:"
    echo "1) 在服务器上构建（需要足够内存和 swap）"
    echo "2) 跳过构建，稍后手动上传 build 目录"
    echo "3) 使用开发模式（不推荐生产环境）"
    read -p "请选择 (1-3): " frontend_choice
    
    case $frontend_choice in
        1)
            echo -e "\n${YELLOW}开始构建前端（这可能需要几分钟）...${NC}"
            
            # 安装依赖
            if [ ! -d "node_modules" ]; then
                echo "安装依赖..."
                npm install
            fi
            
            # 限制内存构建
            echo "构建中..."
            NODE_OPTIONS="--max-old-space-size=512" npm run build
            
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}✓ 前端构建成功${NC}"
            else
                echo -e "${RED}✗ 构建失败，请尝试其他方式${NC}"
                echo "建议: 在本地构建后上传 build 目录"
                exit 1
            fi
            ;;
        2)
            echo -e "${YELLOW}跳过构建${NC}"
            echo ""
            echo "请在本地电脑执行:"
            echo "  cd frontend"
            echo "  npm run build"
            echo "  tar -czf build.tar.gz build/"
            echo "  scp build.tar.gz root@your_server_ip:/tmp/"
            echo ""
            echo "然后在服务器执行:"
            echo "  cd /root/BTCTradingApp/BTCOptionsTrading/frontend"
            echo "  tar -xzf /tmp/build.tar.gz"
            echo ""
            read -p "按回车继续..."
            
            if [ ! -d "build" ]; then
                echo -e "${RED}错误: 仍未找到 build 目录${NC}"
                exit 1
            fi
            ;;
        3)
            echo -e "${YELLOW}将使用开发模式${NC}"
            ;;
    esac
fi

cd ..

# 4. 停止并启动服务
echo -e "\n${YELLOW}[4/4] 启动服务...${NC}"

# 停止旧进程
if command -v pm2 &> /dev/null; then
    pm2 stop btc-backend 2>/dev/null || true
    pm2 stop btc-frontend 2>/dev/null || true
    pm2 delete btc-backend 2>/dev/null || true
    pm2 delete btc-frontend 2>/dev/null || true
else
    pkill -f "run_api.py" 2>/dev/null || true
    pkill -f "npm" 2>/dev/null || true
fi

# 启动服务
if command -v pm2 &> /dev/null; then
    echo "使用 PM2 启动服务..."
    
    # 启动后端（限制内存）
    cd backend
    pm2 start run_api.py --name btc-backend --interpreter python3 --max-memory-restart 400M
    cd ..
    
    # 启动前端
    cd frontend
    if [ -d "build" ]; then
        pm2 serve build 3000 --name btc-frontend --spa --max-memory-restart 200M
    else
        pm2 start npm --name btc-frontend -- start --max-memory-restart 300M
    fi
    cd ..
    
    pm2 save
    
    echo -e "${GREEN}✓ 服务已启动${NC}"
    pm2 list
else
    echo "使用 nohup 启动服务..."
    
    cd backend
    mkdir -p logs
    nohup python run_api.py > logs/api.log 2>&1 &
    echo "后端 PID: $!"
    cd ..
    
    cd frontend
    mkdir -p logs
    if [ -d "build" ]; then
        nohup npx serve -s build -l 3000 > logs/frontend.log 2>&1 &
    else
        nohup npm start > logs/frontend.log 2>&1 &
    fi
    echo "前端 PID: $!"
    cd ..
    
    echo -e "${GREEN}✓ 服务已启动${NC}"
fi

# 等待服务启动
echo -e "\n${YELLOW}等待服务启动...${NC}"
sleep 5

# 验证服务
echo -e "\n${YELLOW}验证服务状态...${NC}"

if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 后端服务运行正常${NC}"
else
    echo -e "${RED}✗ 后端服务可能未正常启动${NC}"
fi

if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 前端服务运行正常${NC}"
else
    echo -e "${YELLOW}⚠ 前端服务正在启动中${NC}"
fi

# 显示内存使用
echo -e "\n${YELLOW}当前内存使用:${NC}"
free -h

echo ""
echo "=========================================="
echo -e "${GREEN}部署完成！${NC}"
echo "=========================================="
echo ""
echo "访问地址:"
echo "  前端: http://localhost:3000"
echo "  后端: http://localhost:8000"
echo ""
echo "监控命令:"
echo "  pm2 list              - 查看进程"
echo "  pm2 logs              - 查看日志"
echo "  free -h               - 查看内存"
echo "  pm2 monit             - 实时监控"
echo ""
