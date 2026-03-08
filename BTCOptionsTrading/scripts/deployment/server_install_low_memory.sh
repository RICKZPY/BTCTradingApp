#!/bin/bash
# 低内存服务器安装脚本
# 适用于内存小于1GB的服务器

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "=========================================="
echo "情绪交易系统 - 低内存服务器安装"
echo "=========================================="
echo ""

# 检查内存
TOTAL_MEM=$(free -m | awk '/^Mem:/{print $2}')
echo "系统内存: ${TOTAL_MEM}MB"

if [ "$TOTAL_MEM" -lt 512 ]; then
    echo -e "${YELLOW}⚠ 警告: 内存较低，将使用特殊安装方式${NC}"
    LOW_MEM=true
else
    LOW_MEM=false
fi

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"

echo "安装目录: $SCRIPT_DIR"
echo ""

# 步骤1: 检查Python环境
echo "=========================================="
echo "步骤 1/7: 检查Python环境"
echo "=========================================="

if ! command -v python3 &> /dev/null; then
    echo "Python3未安装，正在安装..."
    if command -v apt-get &> /dev/null; then
        apt-get update
        apt-get install -y python3 python3-pip
    elif command -v yum &> /dev/null; then
        yum install -y python3 python3-pip
    fi
fi

echo -e "${GREEN}✓ Python版本: $(python3 --version)${NC}"

# 步骤2: 配置swap（低内存环境）
if [ "$LOW_MEM" = true ]; then
    echo ""
    echo "=========================================="
    echo "步骤 2/7: 配置临时swap空间"
    echo "=========================================="
    
    if [ ! -f /swapfile_temp ]; then
        echo "创建1GB临时swap..."
        dd if=/dev/zero of=/swapfile_temp bs=1M count=1024 2>/dev/null || true
        chmod 600 /swapfile_temp
        mkswap /swapfile_temp 2>/dev/null || true
        swapon /swapfile_temp 2>/dev/null || true
        echo -e "${GREEN}✓ 临时swap已启用${NC}"
    else
        echo -e "${GREEN}✓ swap已存在${NC}"
    fi
else
    echo ""
    echo "步骤 2/7: 跳过swap配置（内存充足）"
fi

# 步骤3: 升级pip（使用国内镜像）
echo ""
echo "=========================================="
echo "步骤 3/7: 配置pip镜像源"
echo "=========================================="

mkdir -p ~/.pip
cat > ~/.pip/pip.conf << 'EOF'
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
[install]
trusted-host = pypi.tuna.tsinghua.edu.cn
EOF

echo -e "${GREEN}✓ 已配置清华大学镜像源${NC}"

# 升级pip
echo "升级pip..."
python3 -m pip install --upgrade pip --no-cache-dir

# 步骤4: 安装依赖（逐个安装，避免内存溢出）
echo ""
echo "=========================================="
echo "步骤 4/7: 安装Python依赖（逐个安装）"
echo "=========================================="

# 必需的依赖包
REQUIRED_PACKAGES=(
    "aiohttp"
    "fastapi"
    "uvicorn"
    "python-dotenv"
)

for package in "${REQUIRED_PACKAGES[@]}"; do
    echo "安装 $package..."
    pip3 install "$package" --no-cache-dir || {
        echo -e "${YELLOW}⚠ $package 安装失败，尝试使用--no-deps${NC}"
        pip3 install "$package" --no-deps --no-cache-dir
    }
    echo -e "${GREEN}✓ $package 安装完成${NC}"
    sleep 1
done

# 可选依赖（如果内存允许）
if [ "$LOW_MEM" = false ]; then
    echo ""
    echo "安装可选依赖..."
    if [ -f "$BACKEND_DIR/requirements-minimal.txt" ]; then
        pip3 install -r "$BACKEND_DIR/requirements-minimal.txt" --no-cache-dir || echo "部分可选依赖安装失败"
    fi
fi

echo -e "${GREEN}✓ 核心依赖安装完成${NC}"

# 步骤5: 创建必要目录
echo ""
echo "=========================================="
echo "步骤 5/7: 创建目录结构"
echo "=========================================="

cd "$BACKEND_DIR"
mkdir -p data logs backups

echo -e "${GREEN}✓ 目录创建完成${NC}"

# 步骤6: 配置.env文件
echo ""
echo "=========================================="
echo "步骤 6/7: 配置API密钥"
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
else
    echo -e "${GREEN}✓ .env文件已存在${NC}"
fi

# 步骤7: 设置脚本权限
echo ""
echo "=========================================="
echo "步骤 7/7: 设置权限"
echo "=========================================="

chmod +x *.sh 2>/dev/null || true

echo -e "${GREEN}✓ 权限设置完成${NC}"

# 清理临时swap
if [ "$LOW_MEM" = true ] && [ -f /swapfile_temp ]; then
    echo ""
    echo "清理临时swap..."
    swapoff /swapfile_temp 2>/dev/null || true
    rm -f /swapfile_temp
    echo -e "${GREEN}✓ 临时swap已清理${NC}"
fi

# 完成
echo ""
echo "=========================================="
echo -e "${GREEN}安装完成！${NC}"
echo "=========================================="
echo ""
echo "系统信息:"
echo "  内存: ${TOTAL_MEM}MB"
echo "  Python: $(python3 --version)"
echo "  工作目录: $BACKEND_DIR"
echo ""
echo "下一步操作："
echo ""
echo "1. 配置API密钥:"
echo "   nano $BACKEND_DIR/.env"
echo ""
echo "2. 测试系统:"
echo "   cd $BACKEND_DIR"
echo "   python3 test_sentiment_trading.py"
echo ""
echo "3. 启动服务（使用脚本，不使用systemd）:"
echo "   ./start_sentiment_trading.sh"
echo ""
echo "4. 查看状态:"
echo "   curl http://localhost:5002/api/health"
echo ""
echo "注意事项（低内存环境）:"
echo "  - 建议使用脚本启动，不使用systemd"
echo "  - 定期检查内存使用: free -m"
echo "  - 如果服务崩溃，可能需要增加swap空间"
echo ""
echo "增加永久swap的方法:"
echo "  sudo fallocate -l 2G /swapfile"
echo "  sudo chmod 600 /swapfile"
echo "  sudo mkswap /swapfile"
echo "  sudo swapon /swapfile"
echo "  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab"
echo ""
