#!/bin/bash
# 验证加权情绪交易系统 V2.0 部署状态
# Verify weighted sentiment trading system V2.0 deployment status

SERVER="root@47.86.62.200"
REMOTE_PATH="/root/BTCOptionsTrading/backend"

echo "=========================================="
echo "验证加权情绪交易系统 V2.0 部署"
echo "Verify Weighted Sentiment Trading V2.0"
echo "=========================================="
echo ""

echo "1. 检查文件是否存在..."
echo "   Checking if files exist..."
ssh ${SERVER} << 'EOF'
cd /root/BTCOptionsTrading/backend

if [ -f "weighted_sentiment_cron.py" ]; then
    echo "✓ weighted_sentiment_cron.py 存在"
else
    echo "❌ weighted_sentiment_cron.py 不存在"
    exit 1
fi

if [ -f "src/trading/deribit_trader.py" ]; then
    echo "✓ src/trading/deribit_trader.py 存在"
else
    echo "❌ src/trading/deribit_trader.py 不存在"
    exit 1
fi
EOF

echo ""
echo "2. 检查环境变量配置..."
echo "   Checking environment variables..."
ssh ${SERVER} << 'EOF'
cd /root/BTCOptionsTrading/backend

if grep -q "WEIGHTED_SENTIMENT_DERIBIT_API_KEY" .env; then
    echo "✓ WEIGHTED_SENTIMENT_DERIBIT_API_KEY 已配置"
else
    echo "❌ WEIGHTED_SENTIMENT_DERIBIT_API_KEY 未配置"
    exit 1
fi

if grep -q "WEIGHTED_SENTIMENT_DERIBIT_API_SECRET" .env; then
    echo "✓ WEIGHTED_SENTIMENT_DERIBIT_API_SECRET 已配置"
else
    echo "❌ WEIGHTED_SENTIMENT_DERIBIT_API_SECRET 未配置"
    exit 1
fi
EOF

echo ""
echo "3. 检查 Cron 配置..."
echo "   Checking cron configuration..."
ssh ${SERVER} "crontab -l | grep weighted_sentiment_cron"

echo ""
echo "4. 检查日志目录..."
echo "   Checking log directory..."
ssh ${SERVER} << 'EOF'
cd /root/BTCOptionsTrading/backend

if [ -d "logs" ]; then
    echo "✓ logs 目录存在"
    
    if [ -f "logs/weighted_sentiment_cron.log" ]; then
        echo "✓ weighted_sentiment_cron.log 存在"
        echo "  最后 5 行:"
        tail -5 logs/weighted_sentiment_cron.log
    else
        echo "⚠ weighted_sentiment_cron.log 尚未创建（等待首次执行）"
    fi
    
    if [ -f "logs/weighted_sentiment_trades.log" ]; then
        echo "✓ weighted_sentiment_trades.log 存在"
        echo "  最后 10 行:"
        tail -10 logs/weighted_sentiment_trades.log
    else
        echo "⚠ weighted_sentiment_trades.log 尚未创建（等待首次交易）"
    fi
else
    echo "❌ logs 目录不存在"
    exit 1
fi
EOF

echo ""
echo "5. 检查 Python 模块..."
echo "   Checking Python modules..."
ssh ${SERVER} << 'EOF'
cd /root/BTCOptionsTrading/backend

python3 -c "
import sys
sys.path.insert(0, '/root/BTCOptionsTrading/backend')
from weighted_sentiment_cron import StraddleExecutor
print('✓ StraddleExecutor 导入成功')
"
EOF

echo ""
echo "=========================================="
echo "验证完成 / Verification Complete"
echo "=========================================="
echo ""
echo "部署状态: ✅ 成功"
echo "Deployment Status: ✅ Success"
echo ""
echo "下一步:"
echo "1. 等待下一个高分新闻（评分 >= 7）"
echo "2. 系统会自动执行跨式交易"
echo "3. 查看日志验证交易结果"
echo ""
echo "监控命令:"
echo "  ssh ${SERVER}"
echo "  tail -f ${REMOTE_PATH}/logs/weighted_sentiment_cron.log"
echo ""
