#!/bin/bash
# 快速测试情绪交易系统

echo "=========================================="
echo "情绪交易系统快速测试"
echo "=========================================="
echo ""

# 1. 检查Python
echo "1. 检查Python环境..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "   ✓ $PYTHON_VERSION"
else
    echo "   ✗ 未找到Python3"
    exit 1
fi

# 2. 检查依赖
echo ""
echo "2. 检查依赖包..."
MISSING_DEPS=()

for pkg in aiohttp fastapi uvicorn python-dotenv; do
    if python3 -c "import ${pkg//-/_}" 2>/dev/null; then
        echo "   ✓ $pkg"
    else
        echo "   ✗ $pkg (缺失)"
        MISSING_DEPS+=($pkg)
    fi
done

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    echo ""
    echo "安装缺失的依赖..."
    pip install ${MISSING_DEPS[@]}
fi

# 3. 检查.env文件
echo ""
echo "3. 检查配置文件..."
if [ -f .env ]; then
    if grep -q "DERIBIT_API_KEY" .env && grep -q "DERIBIT_API_SECRET" .env; then
        echo "   ✓ .env文件配置正确"
    else
        echo "   ✗ .env文件缺少API密钥配置"
        echo "   请在.env中添加:"
        echo "   DERIBIT_API_KEY=your_key"
        echo "   DERIBIT_API_SECRET=your_secret"
        exit 1
    fi
else
    echo "   ✗ 未找到.env文件"
    exit 1
fi

# 4. 创建必要目录
echo ""
echo "4. 创建数据目录..."
mkdir -p data logs
echo "   ✓ 目录已创建"

# 5. 测试情绪API连接
echo ""
echo "5. 测试情绪API连接..."
if curl -s --connect-timeout 5 http://43.106.51.106:5001/api/sentiment > /dev/null; then
    echo "   ✓ 情绪API可访问"
else
    echo "   ⚠ 情绪API暂时无法访问（可能是时间未到或网络问题）"
fi

# 6. 运行测试脚本
echo ""
echo "6. 运行功能测试..."
echo "=========================================="
python3 test_sentiment_trading.py
echo "=========================================="

echo ""
echo "测试完成！"
echo ""
echo "如果测试通过，可以使用以下命令启动服务:"
echo "  ./start_sentiment_trading.sh"
echo ""
