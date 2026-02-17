#!/bin/bash

# BTC期权交易系统 - 服务器部署脚本
# 使用方法: ./deploy.sh [环境]
# 环境选项: dev (开发), prod (生产)

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置
ENVIRONMENT=${1:-prod}
PROJECT_NAME="btc-options-trading"
DEPLOY_USER="deploy"
DEPLOY_PATH="/opt/${PROJECT_NAME}"
BACKEND_PORT=8000
FRONTEND_PORT=3000

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}BTC期权交易系统 - 服务器部署${NC}"
echo -e "${GREEN}环境: ${ENVIRONMENT}${NC}"
echo -e "${GREEN}========================================${NC}"

# 检查是否为root用户
if [ "$EUID" -eq 0 ]; then 
    echo -e "${YELLOW}警告: 建议使用非root用户运行此脚本${NC}"
fi

# 1. 更新系统
echo -e "\n${GREEN}[1/10] 更新系统包...${NC}"
sudo apt-get update
sudo apt-get upgrade -y

# 2. 安装基础依赖
echo -e "\n${GREEN}[2/10] 安装基础依赖...${NC}"
sudo apt-get install -y \
    git \
    curl \
    wget \
    build-essential \
    python3 \
    python3-pip \
    python3-venv \
    nginx \
    supervisor \
    ufw

# 3. 安装Node.js (使用NodeSource)
echo -e "\n${GREEN}[3/10] 安装Node.js...${NC}"
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi
node --version
npm --version

# 4. 创建部署目录
echo -e "\n${GREEN}[4/10] 创建部署目录...${NC}"
sudo mkdir -p ${DEPLOY_PATH}
sudo chown -R $USER:$USER ${DEPLOY_PATH}

# 5. 克隆或更新代码
echo -e "\n${GREEN}[5/10] 部署代码...${NC}"
if [ -d "${DEPLOY_PATH}/.git" ]; then
    echo "更新现有代码..."
    cd ${DEPLOY_PATH}
    git pull
else
    echo "首次部署，请手动上传代码到 ${DEPLOY_PATH}"
    echo "或使用: rsync -avz --exclude 'node_modules' --exclude 'venv' ./ user@server:${DEPLOY_PATH}/"
fi

# 6. 配置后端
echo -e "\n${GREEN}[6/10] 配置后端...${NC}"
cd ${DEPLOY_PATH}/backend

# 创建Python虚拟环境
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# 激活虚拟环境并安装依赖
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 复制环境配置
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${YELLOW}请编辑 ${DEPLOY_PATH}/backend/.env 配置文件${NC}"
fi

# 7. 配置前端
echo -e "\n${GREEN}[7/10] 配置前端...${NC}"
cd ${DEPLOY_PATH}/frontend

# 安装依赖
npm install

# 复制环境配置
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${YELLOW}请编辑 ${DEPLOY_PATH}/frontend/.env 配置文件${NC}"
fi

# 构建生产版本
if [ "$ENVIRONMENT" = "prod" ]; then
    echo "构建生产版本..."
    npm run build
fi

# 8. 配置Nginx
echo -e "\n${GREEN}[8/10] 配置Nginx...${NC}"
sudo tee /etc/nginx/sites-available/${PROJECT_NAME} > /dev/null <<EOF
# BTC期权交易系统 Nginx配置

# 后端API
upstream backend {
    server 127.0.0.1:${BACKEND_PORT};
}

server {
    listen 80;
    server_name _;  # 替换为你的域名

    # 前端静态文件
    location / {
        root ${DEPLOY_PATH}/frontend/dist;
        try_files \$uri \$uri/ /index.html;
        
        # 缓存静态资源
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # 后端API代理
    location /api {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        
        # WebSocket支持
        proxy_read_timeout 86400;
    }

    # WebSocket端点
    location /ws {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_read_timeout 86400;
    }

    # 日志
    access_log /var/log/nginx/${PROJECT_NAME}_access.log;
    error_log /var/log/nginx/${PROJECT_NAME}_error.log;
}
EOF

# 启用站点
sudo ln -sf /etc/nginx/sites-available/${PROJECT_NAME} /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# 测试Nginx配置
sudo nginx -t

# 9. 配置Supervisor (进程管理)
echo -e "\n${GREEN}[9/10] 配置Supervisor...${NC}"
sudo tee /etc/supervisor/conf.d/${PROJECT_NAME}-backend.conf > /dev/null <<EOF
[program:${PROJECT_NAME}-backend]
command=${DEPLOY_PATH}/backend/venv/bin/python ${DEPLOY_PATH}/backend/run_api.py
directory=${DEPLOY_PATH}/backend
user=$USER
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/${PROJECT_NAME}-backend.log
environment=PATH="${DEPLOY_PATH}/backend/venv/bin"
EOF

# 10. 配置防火墙
echo -e "\n${GREEN}[10/10] 配置防火墙...${NC}"
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw --force enable

# 重启服务
echo -e "\n${GREEN}重启服务...${NC}"
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart ${PROJECT_NAME}-backend
sudo systemctl restart nginx

# 显示状态
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}部署完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "后端API: http://your-server-ip/api"
echo -e "前端界面: http://your-server-ip"
echo -e "\n查看后端日志: sudo tail -f /var/log/${PROJECT_NAME}-backend.log"
echo -e "查看Nginx日志: sudo tail -f /var/log/nginx/${PROJECT_NAME}_access.log"
echo -e "\n管理命令:"
echo -e "  启动后端: sudo supervisorctl start ${PROJECT_NAME}-backend"
echo -e "  停止后端: sudo supervisorctl stop ${PROJECT_NAME}-backend"
echo -e "  重启后端: sudo supervisorctl restart ${PROJECT_NAME}-backend"
echo -e "  查看状态: sudo supervisorctl status"
echo -e "${GREEN}========================================${NC}"
