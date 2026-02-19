#!/usr/bin/env python3
"""
简单检查 .env 文件配置（不加载 settings）
"""

import os
from pathlib import Path

def check_env_file():
    """检查 .env 文件"""
    env_path = Path(__file__).parent / ".env"
    
    print("=" * 80)
    print("检查 .env 文件配置")
    print("=" * 80)
    
    if not env_path.exists():
        print("\n❌ .env 文件不存在！")
        print("\n请运行以下命令创建：")
        print("  cp .env.example .env")
        print("  nano .env")
        return
    
    print(f"\n✅ .env 文件存在: {env_path}")
    
    # 读取 .env 文件
    config = {}
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                config[key] = value.strip('"').strip("'")
    
    # 检查关键配置
    print("\n" + "=" * 80)
    print("Deribit 配置:")
    print("=" * 80)
    
    test_mode = config.get('DERIBIT_TEST_MODE', 'true').lower()
    base_url = config.get('DERIBIT_BASE_URL', '')
    ws_url = config.get('DERIBIT_WS_URL', '')
    api_key = config.get('DERIBIT_API_KEY', '')
    
    print(f"\nDERIBIT_TEST_MODE: {test_mode}")
    print(f"DERIBIT_BASE_URL: {base_url}")
    print(f"DERIBIT_WS_URL: {ws_url}")
    print(f"DERIBIT_API_KEY: {'已设置' if api_key else '未设置（公开API）'}")
    
    print("\n" + "=" * 80)
    
    if test_mode == 'false' and 'www.deribit.com' in base_url:
        print("✅ 配置正确：使用生产网")
        print("   - 将获取真实市场数据")
        print("   - 适合数据采集和生产环境")
    elif test_mode == 'true' or 'test.deribit.com' in base_url:
        print("⚠️  当前使用测试网")
        print("   - 数据是模拟的，不是真实市场数据")
        print("   - 适合开发和测试")
        print("\n如需切换到生产网，请修改 .env 文件：")
        print("   DERIBIT_TEST_MODE=false")
        print('   DERIBIT_BASE_URL="https://www.deribit.com"')
        print('   DERIBIT_WS_URL="wss://www.deribit.com/ws/api/v2"')
    else:
        print("⚠️  配置可能有误，请检查")
    
    print("=" * 80)

if __name__ == "__main__":
    check_env_file()
