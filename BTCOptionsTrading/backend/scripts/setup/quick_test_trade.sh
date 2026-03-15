#!/bin/bash
# 快速测试交易脚本

cd "$(dirname "$0")"

echo "=========================================="
echo "快速测试交易"
echo "=========================================="
echo ""

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "✗ Python3未安装"
    exit 1
fi

# 检查.env配置
if [ ! -f ".env" ]; then
    echo "✗ .env文件不存在"
    echo "请先配置.env文件"
    exit 1
fi

echo "准备执行测试交易..."
echo ""
echo "此脚本将："
echo "  1. 读取情绪API数据"
echo "  2. 根据情绪选择策略"
echo "  3. 在Deribit测试网执行交易"
echo "  4. 显示交易结果"
echo ""
echo "⚠ 注意: 这将在测试网执行真实交易"
echo ""

read -p "按Enter继续，或Ctrl+C取消..."

echo ""
echo "启动测试..."
echo ""

python3 test_manual_trade.py

echo ""
echo "=========================================="
