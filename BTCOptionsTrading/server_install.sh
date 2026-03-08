#!/bin/bash
# 服务器端一键安装脚本
# 在服务器上运行此脚本来安装情绪交易系统

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "=========================================="
echo "情绪交易系统 - 服务器端安装"
echo "=========================================="
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"

echo "安装目录: $SCRIPT_DIR"
echo ""

# 步骤1: 检查Python环境
echo "=========================================="
echo "步骤 1/6: 检查Python环境"
echo "=========================================="

if ! command -v python3 &> /dev/null; then
    echo "Python3未安装，正在安装..."
    if command -v apt-get &> /dev/null; then
        apt-get update
        apt-get install -y python3 python3-pip
    elif command -v yum &> /dev/null; then
        yum install -y python3 python3-pip
    else
        echo -e "${RED}无法自动安装Python3，请手动安装${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✓ Python版本: $(python3 --version)${NC}"

# 步骤2: 安装依赖
echo ""
echo "=========================================="
echo "步骤 2/6: 安装Python依赖"
echo "=========================================="

pip3 install --upgrade pip
pip3 install aiohttp fastapi uvicorn python-dotenv

# 如果有requirements.txt也安装
if [ -f "$BACKEND_DIR/requirements.txt" ]; then
    echo "安装requirements.txt中的依赖..."
    pip3 install -r "$BACKEND_DIR/requirements.txt" || echo "部分依赖安装失败，继续..."
fi

echo -e "${GREEN}✓ 依赖安装完成${NC}"

# 步骤3: 创建必要目录
echo ""
echo "=========================================="
echo "步骤 3/6: 创建目录结构"
echo "=========================================="

cd "$BACKEND_DIR"
mkdir -p data logs backups

echo -e "${GREEN}✓ 目录创建完成${NC}"

# 步骤4: 配置.env文件
echo ""
echo "=========================================="
echo "步骤 4/6: 配置API密钥"
echo "=========================================="

if [ ! -f .env ]; then
    echo "创建.env配置文件..."
    cat > .env << 'EOF'
# Deribit API配置（测试网）
DERIBIT_API_KEY=your_api_key_here
DERIBIT_API_SECRET=your_api_secret_here
EOF
    echo -e "${YELLOW}⚠ 已创建.env模板${NC}"
    echo "请编辑 $BACKEND_DIR/.env 文件，填入真实的API密钥"
    echo ""
    read -p "现在编辑.env文件? (y/n): " edit_env
    if [ "$edit_env" = "y" ]; then
        ${EDITOR:-nano} .env
    fi
else
    echo -e "${GREEN}✓ .env文件已存在${NC}"
fi

# 检查.env是否配置
if grep -q "your_api_key" .env || grep -q "your_api_secret" .env; then
    echo -e "${YELLOW}⚠ 警告: .env文件包含默认值${NC}"
    echo "请确保修改为真实的API密钥后再启动服务"
fi

# 步骤5: 设置脚本权限
echo ""
echo "=========================================="
echo "步骤 5/6: 设置权限"
echo "=========================================="

chmod +x *.sh 2>/dev/null || true
chmod +x ../deploy*.sh 2>/dev/null || true

echo -e "${GREEN}✓ 权限设置完成${NC}"

# 步骤6: 配置systemd服务
echo ""
echo "=========================================="
echo "步骤 6/6: 配置systemd服务"
echo "=========================================="

CURRENT_USER=$(whoami)
WORK_DIR=$(pwd)

echo "配置信息:"
echo "  用户: $CURRENT_USER"
echo "  工作目录: $WORK_DIR"
echo ""

# 修改服务文件
if [ -f sentiment_trading.service ]; then
    sed -i.bak "s|YOUR_USERNAME|$CURRENT_USER|g" sentiment_trading.service
    sed -i.bak "s|/path/to/BTCOptionsTrading/backend|$WORK_DIR|g" sentiment_trading.service
    echo -e "${GREEN}✓ sentiment_trading.service 已配置${NC}"
fi

if [ -f sentiment_api.service ]; then
    sed -i.bak "s|YOUR_USERNAME|$CURRENT_USER|g" sentiment_api.service
    sed -i.bak "s|/path/to/BTCOptionsTrading/backend|$WORK_DIR|g" sentiment_api.service
    echo -e "${GREEN}✓ sentiment_api.service 已配置${NC}"
fi

# 询问是否安装systemd服务
echo ""
read -p "是否安装systemd服务（需要root权限）? (y/n): " install_systemd

if [ "$install_systemd" = "y" ]; then
    if [ "$EUID" -ne 0 ]; then
        echo "需要root权限，使用sudo..."
        sudo cp sentiment_trading.service /etc/systemd/system/
        sudo cp sentiment_api.service /etc/systemd/system/
        sudo systemctl daemon-reload
        sudo systemctl enable sentiment_trading.service
        sudo systemctl enable sentiment_api.service
    else
        cp sentiment_trading.service /etc/systemd/system/
        cp sentiment_api.service /etc/systemd/system/
        systemctl daemon-reload
        systemctl enable sentiment_trading.service
        systemctl enable sentiment_api.service
    fi
    echo -e "${GREEN}✓ systemd服务已安装${NC}"
fi

# 完成
echo ""
echo "=========================================="
echo -e "${GREEN}安装完成！${NC}"
echo "=========================================="
echo ""
echo "下一步操作："
echo ""
echo "1. 配置API密钥:"
echo "   编辑文件: $BACKEND_DIR/.env"
echo "   填入真实的 DERIBIT_API_KEY 和 DERIBIT_API_SECRET"
echo ""
echo "2. 测试系统:"
echo "   cd $BACKEND_DIR"
echo "   python3 test_sentiment_trading.py"
echo ""
echo "3. 启动服务:"
echo "   方式A - 使用脚本:"
echo "     ./start_sentiment_trading.sh"
echo ""
echo "   方式B - 使用systemd:"
echo "     sudo systemctl start sentiment_trading.service"
echo "     sudo systemctl start sentiment_api.service"
echo ""
echo "4. 查看状态:"
echo "   ./manage_sentiment.sh"
echo ""
echo "5. 访问API:"
echo "   curl http://localhost:5002/api/health"
echo ""
echo "=========================================="
echo ""
echo "文档位置:"
echo "  快速开始: $SCRIPT_DIR/SENTIMENT_TRADING_QUICKSTART.md"
echo "  完整文档: $SCRIPT_DIR/SENTIMENT_TRADING_README.md"
echo "  部署指南: $SCRIPT_DIR/DEPLOYMENT_SENTIMENT.md"
echo ""
