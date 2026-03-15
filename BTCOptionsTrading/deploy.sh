#!/bin/bash
# ============================================================
# 部署脚本 - 上传代码到 47.86.62.200
# 用法：./deploy.sh
# ============================================================

SERVER="47.86.62.200"
SERVER_USER="root"                          # 如果不是 root，改这里
REMOTE_DIR="/root/BTCTradingApp"            # 服务器上的目标目录
LOCAL_DIR="$(cd "$(dirname "$0")" && pwd)"  # 本脚本所在目录（项目根目录）

echo "=================================================="
echo "  部署到 $SERVER_USER@$SERVER:$REMOTE_DIR"
echo "=================================================="

# 用 rsync 同步，排除不需要上传的文件
rsync -avz --progress \
  --exclude='.git/' \
  --exclude='__pycache__/' \
  --exclude='*.pyc' \
  --exclude='.pytest_cache/' \
  --exclude='.hypothesis/' \
  --exclude='BTCOptionsTrading/backend/data/' \
  --exclude='BTCOptionsTrading/backend/logs/' \
  --exclude='BTCOptionsTrading/backend/venv/' \
  --exclude='BTCOptionsTrading/backend/.env' \
  --exclude='BTCOptionsTrading/backend/vol_strategy/data/' \
  --exclude='BTCOptionsTrading/backend/vol_strategy/logs/' \
  "$LOCAL_DIR/" \
  "$SERVER_USER@$SERVER:$REMOTE_DIR/"

echo ""
echo "✓ 代码同步完成"
echo ""
echo "下一步在服务器上执行："
echo "  ssh $SERVER_USER@$SERVER"
echo "  cd $REMOTE_DIR/BTCOptionsTrading/backend"
echo "  bash setup_vol_strategy.sh"
