#!/bin/bash

# 依赖修复脚本
# 用于解决 Python 依赖安装问题

set -e

echo "=========================================="
echo "Python 依赖修复脚本"
echo "=========================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 检查 Python 版本
echo -e "\n${YELLOW}检查 Python 版本...${NC}"
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python 版本: $python_version"

# 提取主版本号和次版本号
major_version=$(echo $python_version | cut -d. -f1)
minor_version=$(echo $python_version | cut -d. -f2)

if [ "$major_version" -lt 3 ] || ([ "$major_version" -eq 3 ] && [ "$minor_version" -lt 8 ]); then
    echo -e "${RED}警告: Python 版本过低，建议使用 Python 3.8 或更高版本${NC}"
    echo "当前版本: $python_version"
fi

# 升级 pip
echo -e "\n${YELLOW}升级 pip...${NC}"
python3 -m pip install --upgrade pip

# 询问安装方式
echo -e "\n请选择安装方式:"
echo "1) 完整安装 (requirements.txt)"
echo "2) 最小化安装 (requirements-minimal.txt) - 推荐用于解决依赖冲突"
echo "3) 逐个安装核心依赖 - 用于严重的依赖问题"
read -p "请输入选项 (1-3): " choice

case $choice in
    1)
        echo -e "\n${YELLOW}尝试完整安装...${NC}"
        if pip install -r requirements.txt; then
            echo -e "${GREEN}✓ 依赖安装成功${NC}"
        else
            echo -e "${RED}✗ 完整安装失败，请尝试选项 2 或 3${NC}"
            exit 1
        fi
        ;;
        
    2)
        echo -e "\n${YELLOW}使用最小化依赖安装...${NC}"
        if pip install -r requirements-minimal.txt; then
            echo -e "${GREEN}✓ 最小化依赖安装成功${NC}"
        else
            echo -e "${RED}✗ 最小化安装失败，请尝试选项 3${NC}"
            exit 1
        fi
        ;;
        
    3)
        echo -e "\n${YELLOW}逐个安装核心依赖...${NC}"
        
        # 核心依赖列表
        core_deps=(
            "fastapi"
            "uvicorn"
            "pydantic"
            "websockets"
            "numpy"
            "pandas"
            "aiohttp"
            "requests"
            "python-dotenv"
            "structlog"
            "sqlalchemy<2.0.0"
            "apscheduler"
            "pyyaml"
        )
        
        failed_deps=()
        
        for dep in "${core_deps[@]}"; do
            echo -e "\n安装 $dep..."
            if pip install "$dep"; then
                echo -e "${GREEN}✓ $dep 安装成功${NC}"
            else
                echo -e "${RED}✗ $dep 安装失败${NC}"
                failed_deps+=("$dep")
            fi
        done
        
        if [ ${#failed_deps[@]} -eq 0 ]; then
            echo -e "\n${GREEN}✓ 所有核心依赖安装成功${NC}"
        else
            echo -e "\n${RED}以下依赖安装失败:${NC}"
            for dep in "${failed_deps[@]}"; do
                echo "  - $dep"
            done
            echo -e "\n${YELLOW}建议:${NC}"
            echo "1. 检查 Python 版本是否兼容"
            echo "2. 尝试使用虚拟环境"
            echo "3. 查看具体错误信息并手动安装失败的包"
        fi
        ;;
        
    *)
        echo -e "${RED}无效选项${NC}"
        exit 1
        ;;
esac

# 验证关键包
echo -e "\n${YELLOW}验证关键包...${NC}"

packages_to_check=("fastapi" "uvicorn" "numpy" "pandas" "sqlalchemy" "aiohttp")
all_ok=true

for package in "${packages_to_check[@]}"; do
    if python3 -c "import $package" 2>/dev/null; then
        echo -e "${GREEN}✓ $package${NC}"
    else
        echo -e "${RED}✗ $package 未安装或无法导入${NC}"
        all_ok=false
    fi
done

if [ "$all_ok" = true ]; then
    echo -e "\n${GREEN}=========================================="
    echo "依赖修复完成！"
    echo "==========================================${NC}"
    echo ""
    echo "现在可以启动应用:"
    echo "  python run_api.py"
else
    echo -e "\n${RED}=========================================="
    echo "部分依赖仍有问题"
    echo "==========================================${NC}"
    echo ""
    echo "请检查上面的错误信息"
fi
