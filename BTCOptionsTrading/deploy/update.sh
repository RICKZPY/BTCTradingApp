#!/bin/bash

# BTC期权交易系统 - 快速更新脚本
# 用于更新已部署的系统

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROJECT_NAME="btc-options-trading"
DEPLOY_PATH="/opt/${PROJECT_NAME}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}更新 BTC期权交易系统${NC}"
echo -e "${GREEN}========================================${NC}"

# 1. 停止服务
echo -e "\n${GREEN}[1/5] 停止服务...${NC}"
sudo supervisorctl stop ${PROJECT_NAME}-backend

# 2. 备份当前版本
echo -e "\n${GREEN}[2/5] 备份当前版本...${NC}"
BACKUP_DIR="${DEPLOY_PATH}_backup_$(date +%Y%m%d_%H%M%S)"
sudo cp -r ${DEPLOY_PATH} ${BACKUP_DIR}
echo "备份保存在: ${BACKUP_DIR}"

# 3. 更新代码
echo -e "\n${GREEN}[3/5] 更新代码...${NC}"
cd ${DEPLOY_PATH}
# 如果使用git
if [ -d ".git" ]; then
    git pull
else
    echo "请手动上传新代码"
    read -p "代码已更新？按Enter继续..."
fi

# 4. 更新依赖
echo -e "\n${GREEN}[4/5] 更新依赖...${NC}"

# 后端
cd ${DEPLOY_PATH}/backend
source venv/bin/activate
pip install -r requirements.txt

# 前端
cd ${DEPLOY_PATH}/frontend
npm install
npm run build

# 5. 重启服务
echo -e "\n${GREEN}[5/5] 重启服务...${NC}"
sudo supervisorctl start ${PROJECT_NAME}-backend
sudo systemctl reload nginx

# 检查状态
sleep 2
sudo supervisorctl status ${PROJECT_NAME}-backend

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}更新完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "如果遇到问题，可以回滚到备份版本:"
echo -e "  sudo rm -rf ${DEPLOY_PATH}"
echo -e "  sudo mv ${BACKUP_DIR} ${DEPLOY_PATH}"
echo -e "  sudo supervisorctl restart ${PROJECT_NAME}-backend"
