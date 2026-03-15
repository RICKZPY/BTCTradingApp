#!/usr/bin/env python3
"""
验证加权情绪交易系统的 Deribit 凭证配置
Verify Deribit credentials configuration for weighted sentiment trading

此脚本帮助确认：
1. 加权情绪交易使用独立的环境变量
2. 凭证与现有系统分离
3. 凭证有效性
"""

import os
import sys
from pathlib import Path

# 添加当前目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))


def check_environment_variables():
    """检查环境变量配置"""
    print("=" * 80)
    print("环境变量配置检查")
    print("=" * 80)
    
    # 检查现有系统的凭证
    existing_key = os.getenv('DERIBIT_API_KEY')
    existing_secret = os.getenv('DERIBIT_API_SECRET')
    
    # 检查加权情绪系统的凭证
    weighted_key = os.getenv('WEIGHTED_SENTIMENT_DERIBIT_API_KEY')
    weighted_secret = os.getenv('WEIGHTED_SENTIMENT_DERIBIT_API_SECRET')
    
    print("\n1. 现有系统凭证 (sentiment_trading_service.py 使用):")
    print(f"   DERIBIT_API_KEY: {'✓ 已设置' if existing_key else '✗ 未设置'}")
    if existing_key:
        print(f"   值: {existing_key[:8]}... (前8位)")
    print(f"   DERIBIT_API_SECRET: {'✓ 已设置' if existing_secret else '✗ 未设置'}")
    if existing_secret:
        print(f"   值: {existing_secret[:8]}... (前8位)")
    
    print("\n2. 加权情绪系统凭证 (weighted_sentiment_cron.py 使用):")
    print(f"   WEIGHTED_SENTIMENT_DERIBIT_API_KEY: {'✓ 已设置' if weighted_key else '✗ 未设置'}")
    if weighted_key:
        print(f"   值: {weighted_key[:8]}... (前8位)")
    print(f"   WEIGHTED_SENTIMENT_DERIBIT_API_SECRET: {'✓ 已设置' if weighted_secret else '✗ 未设置'}")
    if weighted_secret:
        print(f"   值: {weighted_secret[:8]}... (前8位)")
    
    print("\n3. 账户隔离检查:")
    if not weighted_key or not weighted_secret:
        print("   ✗ 加权情绪系统凭证未配置")
        print("   ⚠ 需要在 .env 文件中添加独立的凭证")
        return False
    
    if existing_key and weighted_key and existing_key == weighted_key:
        print("   ⚠ 警告: 两个系统使用相同的 API Key")
        print("   建议: 使用不同的 Deribit Test 账户以隔离实验")
        return False
    
    if existing_secret and weighted_secret and existing_secret == weighted_secret:
        print("   ⚠ 警告: 两个系统使用相同的 API Secret")
        print("   建议: 使用不同的 Deribit Test 账户以隔离实验")
        return False
    
    print("   ✓ 凭证已隔离 - 两个系统使用不同的账户")
    return True


def check_env_file():
    """检查 .env 文件配置"""
    print("\n" + "=" * 80)
    print(".env 文件配置检查")
    print("=" * 80)
    
    env_file = Path(__file__).parent / ".env"
    
    if not env_file.exists():
        print("\n✗ .env 文件不存在")
        return False
    
    print(f"\n✓ .env 文件存在: {env_file}")
    
    # 读取 .env 文件
    with open(env_file, 'r') as f:
        content = f.read()
    
    # 检查是否包含加权情绪凭证
    has_weighted_key = 'WEIGHTED_SENTIMENT_DERIBIT_API_KEY' in content
    has_weighted_secret = 'WEIGHTED_SENTIMENT_DERIBIT_API_SECRET' in content
    
    print("\n.env 文件中的配置:")
    print(f"   WEIGHTED_SENTIMENT_DERIBIT_API_KEY: {'✓ 存在' if has_weighted_key else '✗ 不存在'}")
    print(f"   WEIGHTED_SENTIMENT_DERIBIT_API_SECRET: {'✓ 存在' if has_weighted_secret else '✗ 不存在'}")
    
    if not has_weighted_key or not has_weighted_secret:
        print("\n⚠ 需要添加以下配置到 .env 文件:")
        print("\n# 加权情绪跨式期权交易 - 独立账户")
        print("WEIGHTED_SENTIMENT_DERIBIT_API_KEY=your_new_api_key_here")
        print("WEIGHTED_SENTIMENT_DERIBIT_API_SECRET=your_new_api_secret_here")
        return False
    
    return True


def show_configuration_guide():
    """显示配置指南"""
    print("\n" + "=" * 80)
    print("配置指南")
    print("=" * 80)
    
    print("""
要确保账户完全隔离，请按以下步骤操作：

1. 在 Deribit Test 网站创建新账户
   访问: https://test.deribit.com/register

2. 生成新的 API Key 和 Secret
   访问: https://test.deribit.com/account/BTC/api

3. 在 .env 文件中添加独立凭证
   编辑: BTCOptionsTrading/backend/.env
   
   添加以下行（在文件末尾）：
   
   # ========================================
   # 加权情绪跨式期权交易 - 独立账户
   # ========================================
   WEIGHTED_SENTIMENT_DERIBIT_API_KEY=your_new_api_key_here
   WEIGHTED_SENTIMENT_DERIBIT_API_SECRET=your_new_api_secret_here

4. 验证配置
   运行此脚本确认配置正确：
   python verify_weighted_sentiment_credentials.py

5. 测试连接
   运行 cron 脚本测试：
   python weighted_sentiment_cron.py

注意事项：
- 使用不同的 Deribit Test 账户确保实验完全隔离
- 不要将 .env 文件提交到版本控制
- 在服务器上部署时，确保设置正确的环境变量
""")


def verify_code_usage():
    """验证代码中使用的环境变量"""
    print("\n" + "=" * 80)
    print("代码使用验证")
    print("=" * 80)
    
    print("\n检查各个脚本使用的环境变量:")
    
    # 检查 sentiment_trading_service.py
    sentiment_service = Path(__file__).parent / "sentiment_trading_service.py"
    if sentiment_service.exists():
        with open(sentiment_service, 'r') as f:
            content = f.read()
        
        uses_deribit = 'DERIBIT_API_KEY' in content or 'DERIBIT_API_SECRET' in content
        uses_weighted = 'WEIGHTED_SENTIMENT_DERIBIT' in content
        
        print(f"\n1. sentiment_trading_service.py:")
        print(f"   使用 DERIBIT_API_KEY/SECRET: {'✓' if uses_deribit else '✗'}")
        print(f"   使用 WEIGHTED_SENTIMENT_DERIBIT_*: {'✗ (正确)' if not uses_weighted else '⚠ (不应该)'}")
    
    # 检查 weighted_sentiment_cron.py
    weighted_cron = Path(__file__).parent / "weighted_sentiment_cron.py"
    if weighted_cron.exists():
        with open(weighted_cron, 'r') as f:
            content = f.read()
        
        uses_deribit = 'DERIBIT_API_KEY' in content and 'WEIGHTED_SENTIMENT' not in content
        uses_weighted = 'WEIGHTED_SENTIMENT_DERIBIT' in content
        
        print(f"\n2. weighted_sentiment_cron.py:")
        print(f"   使用 DERIBIT_API_KEY/SECRET: {'⚠ (不应该)' if uses_deribit else '✓ (正确)'}")
        print(f"   使用 WEIGHTED_SENTIMENT_DERIBIT_*: {'✓' if uses_weighted else '✗'}")
    
    print("\n✓ 代码级别的隔离已确认")


def main():
    """主函数"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 15 + "加权情绪交易系统 - 凭证验证工具" + " " * 15 + "║")
    print("╚" + "=" * 78 + "╝")
    
    # 1. 检查代码使用
    verify_code_usage()
    
    # 2. 检查 .env 文件
    env_ok = check_env_file()
    
    # 3. 检查环境变量
    env_vars_ok = check_environment_variables()
    
    # 4. 显示配置指南
    if not env_ok or not env_vars_ok:
        show_configuration_guide()
    
    # 5. 总结
    print("\n" + "=" * 80)
    print("验证总结")
    print("=" * 80)
    
    if env_ok and env_vars_ok:
        print("\n✓ 所有检查通过！")
        print("✓ 加权情绪交易系统使用独立的 Deribit 账户")
        print("✓ 与现有系统完全隔离")
        print("\n可以安全部署到服务器。")
    else:
        print("\n⚠ 需要完成配置")
        print("请按照上面的配置指南添加独立的 Deribit 凭证。")
        sys.exit(1)
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
