#!/usr/bin/env python3
"""
检查当前 Deribit 环境配置
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.config.settings import settings

def check_environment():
    """检查环境配置"""
    print("=" * 80)
    print("Deribit 环境配置检查")
    print("=" * 80)
    
    print(f"\n测试模式: {settings.deribit.test_mode}")
    print(f"Base URL: {settings.deribit.base_url}")
    print(f"WebSocket URL: {settings.deribit.websocket_url}")
    print(f"API Key: {'已设置' if settings.deribit.api_key else '未设置（使用公开API）'}")
    
    print("\n" + "=" * 80)
    if settings.deribit.test_mode:
        print("⚠️  当前使用测试网（Testnet）")
        print("   - 数据是模拟的，不是真实市场数据")
        print("   - 适合开发和测试")
        print("\n如需切换到生产网，请修改 .env 文件：")
        print("   DERIBIT_TEST_MODE=false")
        print("   DERIBIT_BASE_URL=\"https://www.deribit.com\"")
    else:
        print("✅ 当前使用生产网（Production）")
        print("   - 数据是真实市场数据")
        print("   - 适合数据采集和生产环境")
    print("=" * 80)

if __name__ == "__main__":
    check_environment()
