#!/bin/bash
# 部署前检查脚本

echo "=========================================="
echo "部署前环境检查"
echo "=========================================="
echo ""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 检查必要文件
echo "1. 检查必要文件..."
REQUIRED_FILES=(
    "backend/sentiment_trading_service.py"
    "backend/sentiment_api.py"
    "backend/start_sentiment_trading.sh"
    "backend/test_sentiment_trading.py"
    "deploy_sentiment_interactive.sh"
)

all_files_ok=true
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "  ${GREEN}✓${NC} $file"
    else
        echo -e "  ${RED}✗${NC} $file (缺失)"
        all_files_ok=false
    fi
done

if [ "$all_files_ok" = false ]; then
    echo ""
    echo -e "${RED}错误: 缺少必要文件${NC}"
    exit 1
fi

# 检查.env文件
echo ""
echo "2. 检查.env配置..."
if [ -f "backend/.env" ]; then
    if grep -q "DERIBIT_API_KEY" backend/.env && grep -q "DERIBIT_API_SECRET" backend/.env; then
        echo -e "  ${GREEN}✓${NC} .env文件存在且包含API密钥配置"
        
        # 检查是否是默认值
        if grep -q "your_api_key" backend/.env || grep -q "your_api_secret" backend/.env; then
            echo -e "  ${YELLOW}⚠${NC} .env包含默认值，需要修改为真实API密钥"
        fi
    else
        echo -e "  ${YELLOW}⚠${NC} .env文件存在但缺少API密钥配置"
    fi
else
    echo -e "  ${YELLOW}⚠${NC} 未找到.env文件"
    echo ""
    echo "  创建.env文件模板..."
    cat > backend/.env << 'EOF'
# Deribit API配置（测试网）
DERIBIT_API_KEY=your_api_key_here
DERIBIT_API_SECRET=your_api_secret_here
EOF
    echo -e "  ${GREEN}✓${NC} 已创建backend/.env模板"
    echo "  请编辑backend/.env文件，填入真实的Deribit API密钥"
fi

# 检查SSH
echo ""
echo "3. 检查SSH客户端..."
if command -v ssh &> /dev/null; then
    echo -e "  ${GREEN}✓${NC} SSH已安装"
    ssh -V 2>&1 | head -1
else
    echo -e "  ${RED}✗${NC} 未找到SSH客户端"
    exit 1
fi

# 检查SCP
echo ""
echo "4. 检查SCP..."
if command -v scp &> /dev/null; then
    echo -e "  ${GREEN}✓${NC} SCP已安装"
else
    echo -e "  ${RED}✗${NC} 未找到SCP"
    exit 1
fi

# 检查依赖模块
echo ""
echo "5. 检查依赖模块..."
if [ -d "backend/src" ]; then
    echo -e "  ${GREEN}✓${NC} backend/src目录存在"
    echo "  包含的模块:"
    ls -1 backend/src/ | sed 's/^/    - /'
else
    echo -e "  ${RED}✗${NC} backend/src目录不存在"
    exit 1
fi

echo ""
echo "=========================================="
echo "检查完成"
echo "=========================================="
echo ""

if [ "$all_files_ok" = true ]; then
    echo -e "${GREEN}✅ 所有必要文件已就绪${NC}"
    echo ""
    echo "下一步："
    echo "  1. 确保backend/.env文件配置了正确的API密钥"
    echo "  2. 准备服务器信息（IP、用户名、SSH密钥）"
    echo "  3. 运行部署脚本: ./deploy_sentiment_interactive.sh"
    echo ""
else
    echo -e "${RED}❌ 存在问题，请先解决${NC}"
    exit 1
fi
