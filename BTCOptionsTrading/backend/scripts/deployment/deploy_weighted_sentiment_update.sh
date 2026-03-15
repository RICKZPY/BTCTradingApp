#!/bin/bash
# 部署加权情绪交易系统更新（启用实际 Deribit 交易）
# Deploy weighted sentiment trading system update (enable actual Deribit trading)

set -e

SERVER="root@47.86.62.200"
REMOTE_PATH="/root/BTCOptionsTrading/backend"

echo "=========================================="
echo "部署加权情绪交易系统更新"
echo "Deploy Weighted Sentiment Trading Update"
echo "=========================================="
echo ""

# 1. 上传更新的文件
echo "1. 上传更新的文件..."
echo "   Uploading updated files..."

scp weighted_sentiment_cron.py ${SERVER}:${REMOTE_PATH}/
if [ $? -ne 0 ]; then
    echo "❌ 上传失败 / Upload failed"
    exit 1
fi

echo "✓ 文件上传成功 / Files uploaded successfully"
echo ""

# 2. 在服务器上测试脚本
echo "2. 在服务器上测试脚本..."
echo "   Testing script on server..."

ssh ${SERVER} << 'EOF'
cd /root/BTCOptionsTrading/backend

# 测试 Python 语法
echo "检查 Python 语法..."
python3 -m py_compile weighted_sentiment_cron.py
if [ $? -ne 0 ]; then
    echo "❌ Python 语法检查失败"
    exit 1
fi

echo "✓ Python 语法检查通过"

# 测试导入
echo "测试模块导入..."
python3 -c "
import sys
sys.path.insert(0, '/root/BTCOptionsTrading/backend')
from weighted_sentiment_cron import StraddleExecutor
print('✓ 模块导入成功')
"

if [ $? -ne 0 ]; then
    echo "❌ 模块导入失败"
    exit 1
fi

EOF

if [ $? -ne 0 ]; then
    echo "❌ 服务器测试失败 / Server test failed"
    exit 1
fi

echo "✓ 服务器测试通过 / Server test passed"
echo ""

# 3. 显示部署信息
echo "=========================================="
echo "部署完成 / Deployment Complete"
echo "=========================================="
echo ""
echo "更新内容 / Updates:"
echo "  ✓ 替换 SimplifiedStraddleExecutor 为 StraddleExecutor"
echo "  ✓ 集成 DeribitTrader 实际交易功能"
echo "  ✓ 支持 ATM 期权查找和下单"
echo "  ✓ 使用市价单执行跨式交易"
echo ""
echo "下次 cron 执行时间 / Next cron execution:"
ssh ${SERVER} "crontab -l | grep weighted_sentiment_cron"
echo ""
echo "手动测试命令 / Manual test command:"
echo "  ssh ${SERVER}"
echo "  cd ${REMOTE_PATH}"
echo "  python3 weighted_sentiment_cron.py"
echo ""
echo "查看日志 / View logs:"
echo "  ssh ${SERVER}"
echo "  tail -f ${REMOTE_PATH}/logs/weighted_sentiment_cron.log"
echo "  tail -f ${REMOTE_PATH}/logs/weighted_sentiment_trades.log"
echo ""
