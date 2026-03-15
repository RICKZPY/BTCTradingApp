#!/bin/bash
# 简化部署脚本 - Market Order 更新
# 使用 rsync 同步修改的文件

set -e

SERVER_HOST="47.86.62.200"
SERVER_USER="root"

echo "========================================="
echo "部署 Market Order 更新到服务器"
echo "========================================="
echo ""
echo "服务器: ${SERVER_USER}@${SERVER_HOST}"
echo ""
echo "将要上传的文件:"
echo "  1. src/trading/deribit_trader.py (修改: market order)"
echo "  2. docs/MARKET_ORDER_UPDATE.md (新增: 更新文档)"
echo ""
echo "请输入服务器上的项目路径 (例如: /root/BTCOptionsTrading/backend 或 ~/BTCOptionsTrading/backend):"
read -r SERVER_PATH

echo ""
echo "开始部署..."
echo ""

# 创建临时目录结构
TEMP_DIR=$(mktemp -d)
mkdir -p ${TEMP_DIR}/src/trading
mkdir -p ${TEMP_DIR}/docs

# 复制要上传的文件
cp BTCOptionsTrading/backend/src/trading/deribit_trader.py ${TEMP_DIR}/src/trading/
cp BTCOptionsTrading/backend/docs/MARKET_ORDER_UPDATE.md ${TEMP_DIR}/docs/

echo "步骤 1: 备份服务器文件..."
ssh ${SERVER_USER}@${SERVER_HOST} "mkdir -p ${SERVER_PATH}/backups && \
    [ -f ${SERVER_PATH}/src/trading/deribit_trader.py ] && \
    cp ${SERVER_PATH}/src/trading/deribit_trader.py ${SERVER_PATH}/backups/deribit_trader.py.backup.\$(date +%Y%m%d_%H%M%S) || \
    echo '原文件不存在，跳过备份'"

echo ""
echo "步骤 2: 上传文件..."
rsync -avz --progress ${TEMP_DIR}/ ${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/

echo ""
echo "步骤 3: 验证..."
ssh ${SERVER_USER}@${SERVER_HOST} "cd ${SERVER_PATH} && \
    echo '检查文件...' && \
    ls -lh src/trading/deribit_trader.py && \
    echo '' && \
    echo '验证 market order 配置:' && \
    grep 'order_type: str = \"market\"' src/trading/deribit_trader.py | head -2"

# 清理临时目录
rm -rf ${TEMP_DIR}

echo ""
echo "========================================="
echo "✓ 部署完成！"
echo "========================================="
echo ""
echo "修改内容："
echo "  • buy() 和 sell() 方法默认使用 market order"
echo "  • 增强日志输出显示订单类型"
echo ""
echo "下次执行时将使用 market order 快速成交"
echo ""
echo "监控命令："
echo "  ssh ${SERVER_USER}@${SERVER_HOST} 'tail -f ${SERVER_PATH}/logs/sentiment_trading.log'"
echo ""
