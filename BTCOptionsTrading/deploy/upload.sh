#!/bin/bash

# 本地上传脚本 - 将代码上传到服务器
# 使用方法: ./upload.sh user@server-ip

set -e

if [ -z "$1" ]; then
    echo "使用方法: ./upload.sh user@server-ip"
    echo "例如: ./upload.sh root@123.45.67.89"
    exit 1
fi

SERVER=$1
REMOTE_PATH="/opt/btc-options-trading"

echo "========================================="
echo "上传代码到服务器: $SERVER"
echo "========================================="

# 确保远程目录存在
ssh $SERVER "sudo mkdir -p $REMOTE_PATH && sudo chown -R \$USER:\$USER $REMOTE_PATH"

# 上传代码（排除不需要的文件）
rsync -avz --progress \
    --exclude 'node_modules' \
    --exclude 'venv' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '.git' \
    --exclude 'dist' \
    --exclude 'build' \
    --exclude '.hypothesis' \
    --exclude '.pytest_cache' \
    --exclude 'data/*.db' \
    --exclude 'logs/*.log' \
    ../ $SERVER:$REMOTE_PATH/

echo ""
echo "========================================="
echo "上传完成！"
echo "========================================="
echo "下一步:"
echo "1. SSH登录服务器: ssh $SERVER"
echo "2. 运行部署脚本: cd $REMOTE_PATH/deploy && chmod +x deploy.sh && sudo ./deploy.sh"
