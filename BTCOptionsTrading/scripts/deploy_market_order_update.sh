#!/bin/bash
# 部署 Market Order 更新到服务器
# 日期: 2026-03-12

set -e  # 遇到错误立即退出

# 配置
SERVER_HOST="47.86.62.200"
SERVER_USER="root"
SERVER_PATH="~/BTCOptionsTrading/backend"
LOCAL_BACKEND_PATH="BTCOptionsTrading/backend"

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}部署 Market Order 更新${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 检查是否在正确的目录
if [ ! -d "BTCOptionsTrading/backend" ]; then
    echo -e "${RED}错误: 请在项目根目录运行此脚本${NC}"
    exit 1
fi

# 1. 备份服务器上的文件
echo -e "${YELLOW}步骤 1/5: 备份服务器文件...${NC}"
ssh ${SERVER_USER}@${SERVER_HOST} "cd ${SERVER_PATH} && \
    mkdir -p backups && \
    cp src/trading/deribit_trader.py backups/deribit_trader.py.backup.\$(date +%Y%m%d_%H%M%S) && \
    echo '备份完成'"

# 2. 上传修改的文件
echo -e "${YELLOW}步骤 2/5: 上传修改的文件...${NC}"
scp ${LOCAL_BACKEND_PATH}/src/trading/deribit_trader.py \
    ${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/src/trading/

# 3. 上传文档
echo -e "${YELLOW}步骤 3/5: 上传更新文档...${NC}"
scp ${LOCAL_BACKEND_PATH}/docs/MARKET_ORDER_UPDATE.md \
    ${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/docs/

# 4. 验证文件
echo -e "${YELLOW}步骤 4/5: 验证文件...${NC}"
ssh ${SERVER_USER}@${SERVER_HOST} "cd ${SERVER_PATH} && \
    echo '检查文件是否存在...' && \
    ls -lh src/trading/deribit_trader.py && \
    echo '' && \
    echo '检查 order_type 默认值...' && \
    grep -A 3 'order_type: str = \"market\"' src/trading/deribit_trader.py | head -6"

# 5. 测试运行（可选）
echo -e "${YELLOW}步骤 5/5: 测试配置...${NC}"
echo -e "${YELLOW}是否要在服务器上运行测试? (y/n)${NC}"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo "运行测试..."
    ssh ${SERVER_USER}@${SERVER_HOST} "cd ${SERVER_PATH} && \
        source venv/bin/activate && \
        python3 -c 'from src.trading.deribit_trader import DeribitTrader; print(\"导入成功\")' && \
        echo '测试通过！'"
else
    echo "跳过测试"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}部署完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "修改内容："
echo "  ✓ deribit_trader.py - buy() 方法默认使用 market order"
echo "  ✓ deribit_trader.py - sell() 方法默认使用 market order"
echo "  ✓ 增强日志输出显示订单类型"
echo ""
echo "下次 cron job 执行时将使用新的 market order 配置"
echo ""
echo "监控命令："
echo "  查看日志: ssh ${SERVER_USER}@${SERVER_HOST} 'tail -f ${SERVER_PATH}/logs/sentiment_trading.log'"
echo "  查看cron日志: ssh ${SERVER_USER}@${SERVER_HOST} 'tail -f ${SERVER_PATH}/logs/sentiment_trading_cron.log'"
echo ""
