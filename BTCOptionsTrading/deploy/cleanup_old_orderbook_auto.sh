#!/bin/bash
# 自动清理服务器上 /opt 目录下的旧orderbook collector文件（无需确认）

set -e

echo "=== 自动清理旧的Orderbook Collector文件 ==="
echo ""

# 检查是否有sudo权限
if [ "$EUID" -ne 0 ]; then 
    echo "请使用sudo运行此脚本"
    echo "sudo ./cleanup_old_orderbook_auto.sh"
    exit 1
fi

# 删除可能的旧目录
for dir in /opt/orderbook_collector /opt/btc_orderbook /opt/orderbook /opt/BTCOptionsTrading; do
    if [ -d "$dir" ]; then
        echo "删除: $dir"
        rm -rf "$dir"
        echo "✓ 已删除"
    fi
done

# 清理crontab中的旧任务
echo ""
echo "清理crontab中的旧任务..."
if crontab -l 2>/dev/null | grep -q "/opt.*orderbook"; then
    echo "发现旧的cron任务，正在清理..."
    crontab -l | grep -v "/opt.*orderbook" | crontab -
    echo "✓ 已清理"
else
    echo "未发现旧的cron任务"
fi

echo ""
echo "=== 清理完成 ==="
echo ""
echo "当前cron任务:"
crontab -l 2>/dev/null || echo "无cron任务"
