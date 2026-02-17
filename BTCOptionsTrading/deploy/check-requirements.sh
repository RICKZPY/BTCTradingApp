#!/bin/bash

# 服务器环境检查脚本
# 在部署前运行，检查服务器是否满足要求

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
FAIL=0
WARN=0

check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ $1${NC}"
        ((PASS++))
        return 0
    else
        echo -e "${RED}✗ $1${NC}"
        ((FAIL++))
        return 1
    fi
}

warn() {
    echo -e "${YELLOW}⚠ $1${NC}"
    ((WARN++))
}

echo "========================================="
echo "服务器环境检查"
echo "========================================="

# 检查操作系统
echo -e "\n【操作系统】"
if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo "系统: $NAME $VERSION"
    if [[ "$ID" == "ubuntu" ]]; then
        check "Ubuntu系统"
    else
        warn "推荐使用Ubuntu系统"
    fi
else
    warn "无法识别操作系统"
fi

# 检查CPU
echo -e "\n【CPU】"
CPU_CORES=$(nproc)
echo "CPU核心数: $CPU_CORES"
if [ $CPU_CORES -ge 2 ]; then
    check "CPU核心数充足 (>= 2核)"
else
    warn "CPU核心数不足，推荐至少2核"
fi

# 检查内存
echo -e "\n【内存】"
TOTAL_MEM=$(free -m | awk 'NR==2{print $2}')
echo "总内存: ${TOTAL_MEM}MB"
if [ $TOTAL_MEM -ge 4096 ]; then
    check "内存充足 (>= 4GB)"
elif [ $TOTAL_MEM -ge 2048 ]; then
    warn "内存较少 (${TOTAL_MEM}MB)，推荐至少4GB"
else
    echo -e "${RED}✗ 内存不足 (${TOTAL_MEM}MB)，最低需要2GB${NC}"
    ((FAIL++))
fi

# 检查磁盘空间
echo -e "\n【磁盘空间】"
DISK_AVAIL=$(df -BG / | awk 'NR==2{print $4}' | sed 's/G//')
echo "可用空间: ${DISK_AVAIL}GB"
if [ $DISK_AVAIL -ge 20 ]; then
    check "磁盘空间充足 (>= 20GB)"
else
    warn "磁盘空间不足 (${DISK_AVAIL}GB)，推荐至少20GB"
fi

# 检查Python
echo -e "\n【Python】"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    echo "Python版本: $PYTHON_VERSION"
    check "Python3已安装"
else
    echo -e "${RED}✗ Python3未安装${NC}"
    ((FAIL++))
fi

# 检查pip
if command -v pip3 &> /dev/null; then
    check "pip3已安装"
else
    warn "pip3未安装"
fi

# 检查Node.js
echo -e "\n【Node.js】"
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "Node.js版本: $NODE_VERSION"
    check "Node.js已安装"
else
    warn "Node.js未安装"
fi

# 检查npm
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    echo "npm版本: $NPM_VERSION"
    check "npm已安装"
else
    warn "npm未安装"
fi

# 检查Git
echo -e "\n【Git】"
if command -v git &> /dev/null; then
    GIT_VERSION=$(git --version | awk '{print $3}')
    echo "Git版本: $GIT_VERSION"
    check "Git已安装"
else
    warn "Git未安装"
fi

# 检查Nginx
echo -e "\n【Nginx】"
if command -v nginx &> /dev/null; then
    NGINX_VERSION=$(nginx -v 2>&1 | awk -F'/' '{print $2}')
    echo "Nginx版本: $NGINX_VERSION"
    check "Nginx已安装"
else
    warn "Nginx未安装"
fi

# 检查Supervisor
echo -e "\n【Supervisor】"
if command -v supervisorctl &> /dev/null; then
    check "Supervisor已安装"
else
    warn "Supervisor未安装"
fi

# 检查端口
echo -e "\n【端口检查】"
if ! sudo netstat -tlnp | grep -q ':80 '; then
    check "端口80可用"
else
    warn "端口80已被占用"
fi

if ! sudo netstat -tlnp | grep -q ':8000 '; then
    check "端口8000可用"
else
    warn "端口8000已被占用"
fi

# 检查防火墙
echo -e "\n【防火墙】"
if command -v ufw &> /dev/null; then
    UFW_STATUS=$(sudo ufw status | head -1)
    echo "UFW状态: $UFW_STATUS"
    check "UFW已安装"
else
    warn "UFW未安装"
fi

# 总结
echo -e "\n========================================="
echo "检查完成"
echo "========================================="
echo -e "${GREEN}通过: $PASS${NC}"
echo -e "${YELLOW}警告: $WARN${NC}"
echo -e "${RED}失败: $FAIL${NC}"

if [ $FAIL -eq 0 ]; then
    echo -e "\n${GREEN}✓ 服务器满足部署要求！${NC}"
    echo "可以运行: sudo ./deploy.sh prod"
    exit 0
else
    echo -e "\n${RED}✗ 服务器不满足部署要求${NC}"
    echo "请先安装缺失的软件包"
    exit 1
fi
