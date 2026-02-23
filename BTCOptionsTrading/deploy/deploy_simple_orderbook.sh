#!/bin/bash
# 在服务器上部署简单orderbook收集器

set -e

echo "=== 部署简单Orderbook收集器 ==="
echo ""

# 进入backend目录
cd "$(dirname "$0")/../backend"

# 1. 安装依赖
echo "1. 安装Python依赖..."
pip3 install aiohttp pytz

# 2. 测试运行
echo ""
echo "2. 测试运行收集器（会运行2分钟）..."
python3 simple_orderbook_collector.py

# 3. 设置定时任务
echo ""
echo "3. 设置每天北京时间5点的定时任务..."
./setup_daily_orderbook.sh

echo ""
echo "=== 部署完成 ==="
echo ""
echo "数据保存位置: $(pwd)/data/orderbook/"
echo "日志位置: $(pwd)/logs/orderbook_collector.log"
echo ""
echo "查看定时任务: crontab -l"
echo "查看日志: tail -f $(pwd)/logs/orderbook_collector.log"
