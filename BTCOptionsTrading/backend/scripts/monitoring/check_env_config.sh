#!/bin/bash
# 检查.env配置

echo "=========================================="
echo "检查.env配置"
echo "=========================================="
echo ""

if [ ! -f ".env" ]; then
    echo "✗ .env文件不存在"
    echo ""
    echo "请创建.env文件："
    echo "  cp .env.example .env"
    echo "  nano .env"
    exit 1
fi

echo "✓ .env文件存在"
echo ""

# 检查测试网配置
echo "检查测试网配置..."
if grep -q "^DERIBIT_TESTNET_API_KEY=" .env && grep -q "^DERIBIT_TESTNET_API_SECRET=" .env; then
    testnet_key=$(grep "^DERIBIT_TESTNET_API_KEY=" .env | cut -d'=' -f2 | tr -d '"' | tr -d "'")
    if [ -n "$testnet_key" ] && [ "$testnet_key" != "your_testnet_api_key_here" ]; then
        echo "✓ 测试网API密钥已配置"
    else
        echo "✗ 测试网API密钥未配置或使用默认值"
        echo "  请在.env中设置 DERIBIT_TESTNET_API_KEY"
    fi
else
    echo "⚠ 未找到测试网配置项"
fi
echo ""

# 检查主网配置
echo "检查主网配置（可选）..."
if grep -q "^DERIBIT_MAINNET_API_KEY=" .env && grep -q "^DERIBIT_MAINNET_API_SECRET=" .env; then
    mainnet_key=$(grep "^DERIBIT_MAINNET_API_KEY=" .env | cut -d'=' -f2 | tr -d '"' | tr -d "'")
    if [ -n "$mainnet_key" ] && [ "$mainnet_key" != "your_mainnet_api_key_here" ]; then
        echo "✓ 主网API密钥已配置"
    else
        echo "⚠ 主网API密钥未配置（将使用测试网数据）"
    fi
else
    echo "⚠ 未找到主网配置项（将使用测试网数据）"
fi
echo ""

# 检查旧配置
echo "检查旧配置格式..."
if grep -q "^DERIBIT_API_KEY=" .env && grep -q "^DERIBIT_API_SECRET=" .env; then
    old_key=$(grep "^DERIBIT_API_KEY=" .env | cut -d'=' -f2 | tr -d '"' | tr -d "'")
    if [ -n "$old_key" ] && [ "$old_key" != "your_api_key_here" ]; then
        echo "✓ 旧格式API密钥已配置（将作为测试网密钥使用）"
    else
        echo "⚠ 旧格式API密钥未配置"
    fi
else
    echo "⚠ 未找到旧格式配置项"
fi
echo ""

echo "=========================================="
echo "配置建议"
echo "=========================================="
echo ""
echo "推荐配置格式（在.env文件中）："
echo ""
echo "# 测试网配置（用于交易下单）- 必需"
echo "DERIBIT_TESTNET_API_KEY=your_testnet_key"
echo "DERIBIT_TESTNET_API_SECRET=your_testnet_secret"
echo ""
echo "# 主网配置（用于数据收集）- 可选"
echo "DERIBIT_MAINNET_API_KEY=your_mainnet_key"
echo "DERIBIT_MAINNET_API_SECRET=your_mainnet_secret"
echo ""
echo "如果只有一套密钥，也可以使用旧格式："
echo "DERIBIT_API_KEY=your_key"
echo "DERIBIT_API_SECRET=your_secret"
echo ""
