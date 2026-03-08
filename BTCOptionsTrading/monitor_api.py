#!/usr/bin/env python3
"""
远程API监控脚本
用于从本地监控服务器上的情绪交易系统
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Optional

# 配置
SERVER_URL = "http://47.86.62.200:5002"
REFRESH_INTERVAL = 30  # 刷新间隔（秒）


class APIMonitor:
    """API监控器"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        
    def get_health(self) -> Optional[Dict]:
        """获取健康状态"""
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    def get_status(self) -> Optional[Dict]:
        """获取完整状态"""
        try:
            response = requests.get(f"{self.base_url}/api/status", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    def get_positions(self) -> Optional[Dict]:
        """获取持仓"""
        try:
            response = requests.get(f"{self.base_url}/api/positions", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    def get_orders(self) -> Optional[Dict]:
        """获取订单"""
        try:
            response = requests.get(f"{self.base_url}/api/orders", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    def get_history(self, limit: int = 10) -> Optional[Dict]:
        """获取交易历史"""
        try:
            response = requests.get(
                f"{self.base_url}/api/history",
                params={"limit": limit},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    def print_status(self):
        """打印状态信息"""
        print("\n" + "="*60)
        print(f"情绪交易系统监控 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        # 健康检查
        print("\n【健康状态】")
        health = self.get_health()
        if health and "error" not in health:
            status = health.get("status", "unknown")
            trader_init = health.get("trader_initialized", False)
            print(f"  状态: {status}")
            print(f"  交易器: {'已初始化' if trader_init else '未初始化'}")
        else:
            print(f"  ✗ 错误: {health.get('error', '未知错误')}")
        
        # 持仓信息
        print("\n【持仓信息】")
        positions = self.get_positions()
        if positions and "error" not in positions:
            items = positions.get("items", [])
            if items:
                for pos in items:
                    print(f"  - {pos.get('instrument_name', 'N/A')}")
                    print(f"    数量: {pos.get('size', 0)}")
                    print(f"    方向: {pos.get('direction', 'N/A')}")
                    print(f"    盈亏: {pos.get('total_profit_loss', 0):.2f} USD")
            else:
                print("  无持仓")
        else:
            print(f"  ✗ 错误: {positions.get('error', '未知错误')}")
        
        # 订单信息
        print("\n【未完成订单】")
        orders = self.get_orders()
        if orders and "error" not in orders:
            items = orders.get("items", [])
            if items:
                for order in items:
                    print(f"  - {order.get('instrument_name', 'N/A')}")
                    print(f"    类型: {order.get('order_type', 'N/A')}")
                    print(f"    数量: {order.get('amount', 0)}")
                    print(f"    价格: {order.get('price', 0)}")
            else:
                print("  无未完成订单")
        else:
            print(f"  ✗ 错误: {orders.get('error', '未知错误')}")
        
        # 最近交易
        print("\n【最近交易】")
        history = self.get_history(limit=3)
        if history and "error" not in history:
            trades = history.get("recent_trades", [])
            if trades:
                for trade in trades:
                    print(f"  - 时间: {trade.get('timestamp', 'N/A')}")
                    print(f"    策略: {trade.get('strategy_type', 'N/A')}")
                    print(f"    结果: {'成功' if trade.get('success') else '失败'}")
            else:
                print("  暂无交易记录")
        else:
            print(f"  ✗ 错误: {history.get('error', '未知错误')}")
        
        print("\n" + "="*60)
    
    def monitor_loop(self, interval: int = 30):
        """监控循环"""
        print(f"开始监控 {self.base_url}")
        print(f"刷新间隔: {interval}秒")
        print("按 Ctrl+C 停止监控")
        
        try:
            while True:
                self.print_status()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n\n监控已停止")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="监控情绪交易API")
    parser.add_argument(
        "--url",
        default=SERVER_URL,
        help=f"API服务器URL (默认: {SERVER_URL})"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=REFRESH_INTERVAL,
        help=f"刷新间隔（秒） (默认: {REFRESH_INTERVAL})"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="只检查一次，不循环"
    )
    
    args = parser.parse_args()
    
    monitor = APIMonitor(args.url)
    
    if args.once:
        monitor.print_status()
    else:
        monitor.monitor_loop(args.interval)


if __name__ == "__main__":
    main()
