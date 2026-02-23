#!/bin/bash

# Order Book 收集脚本 - 确保虚拟环境激活

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# 进入项目目录
cd "$PROJECT_DIR" || exit 1

# 激活虚拟环境
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "../venv/bin/activate" ]; then
    source ../venv/bin/activate
else
    echo "✗ 找不到虚拟环境"
    exit 1
fi

# 运行收集脚本
python collect_orderbook.py "$@"
