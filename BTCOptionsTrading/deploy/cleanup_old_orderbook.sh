#!/bin/bash
# 清理服务器上 /opt 目录下的旧orderbook collector文件

set -e

echo "=== 清理旧的Orderbook Collector文件 ==="
echo ""

# 检查是否有sudo权限
if [ "$EUID" -ne 0 ]; then 
    echo "请使用sudo运行此脚本"
    echo "sudo ./cleanup_old_orderbook.sh"
    exit 1
fi

# 列出 /opt 下可能的旧文件
echo "检查 /opt 目录..."
if [ -d "/opt/orderbook-collector" ]; then
    echo "发现: /opt/orderbook-collector"
    ls -lh /opt/orderbook-collector
    echo ""
    read -p "确认删除 /opt/orderbook-collector? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf /opt/orderbook-collector
        echo "✓ 已删除 /opt/orderbook-collector"
    fi
fi

if [ -d "/opt/orderbook_collector" ]; then
    echo "发现: /opt/orderbook_collector"
    ls -lh /opt/orderbook_collector
    echo ""
    read -p "确认删除 /opt/orderbook_collector? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf /opt/orderbook_collector
        echo "✓ 已删除 /opt/orderbook_collector"
    fi
fi

# 检查其他可能的orderbook相关文件
for dir in /opt/btc_orderbook /opt/orderbook /opt/BTCOptionsTrading; do
    if [ -d "$dir" ]; then
        echo ""
        echo "发现: $dir"
        ls -lh "$dir" | head -10
        echo ""
        read -p "确认删除 $dir? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$dir"
            echo "✓ 已删除 $dir"
        fi
    fi
done

# 检查crontab中的旧任务
echo ""
echo "检查crontab中的旧任务..."
if crontab -l 2>/dev/null | grep -q "/opt.*orderbook"; then
    echo "发现旧的cron任务:"
    crontab -l | grep "/opt.*orderbook"
    echo ""
    read -p "是否清理这些cron任务? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        crontab -l | grep -v "/opt.*orderbook" | crontab -
        echo "✓ 已清理旧的cron任务"
    fi
fi

echo ""
echo "=== 清理完成 ==="
echo ""
echo "当前cron任务:"
crontab -l 2>/dev/null || echo "无cron任务"
