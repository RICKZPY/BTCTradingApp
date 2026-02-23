#!/usr/bin/env python3
"""
启用生产模式脚本

此脚本会：
1. 更新.env文件，设置生产环境配置
2. 验证配置是否正确
3. 提供回滚选项
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

def backup_env_file():
    """备份当前的.env文件"""
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        backup_path = env_path.parent / f'.env.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        with open(env_path, 'r') as src:
            with open(backup_path, 'w') as dst:
                dst.write(src.read())
        print(f"✅ 已备份当前配置到: {backup_path}")
        return backup_path
    return None

def update_env_file():
    """更新.env文件为生产模式"""
    env_path = Path(__file__).parent / '.env'
    
    # 读取现有配置
    existing_config = {}
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    existing_config[key.strip()] = value.strip()
    
    # 更新生产模式配置
    production_config = {
        'ENVIRONMENT': 'production',
        'USE_MOCK_DATA': 'false',
        'STRICT_DATA_MODE': 'true',
        'API_DEBUG': 'false',
        'LOG_LEVEL': 'INFO'
    }
    
    # 合并配置
    existing_config.update(production_config)
    
    # 写入文件
    with open(env_path, 'w') as f:
        f.write("# BTC Options Trading System Configuration\n")
        f.write(f"# Updated to production mode: {datetime.now().isoformat()}\n\n")
        
        f.write("# Environment Configuration\n")
        for key in ['ENVIRONMENT', 'USE_MOCK_DATA', 'STRICT_DATA_MODE']:
            if key in existing_config:
                f.write(f"{key}={existing_config[key]}\n")
        f.write("\n")
        
        f.write("# API Configuration\n")
        for key in ['API_HOST', 'API_PORT', 'API_DEBUG']:
            if key in existing_config:
                f.write(f"{key}={existing_config[key]}\n")
        f.write("\n")
        
        f.write("# Logging Configuration\n")
        for key in ['LOG_LEVEL', 'LOG_FILE_PATH']:
            if key in existing_config:
                f.write(f"{key}={existing_config[key]}\n")
        f.write("\n")
        
        f.write("# Other Configuration\n")
        for key, value in existing_config.items():
            if key not in production_config and key not in ['API_HOST', 'API_PORT', 'LOG_FILE_PATH']:
                f.write(f"{key}={value}\n")
    
    print(f"✅ 已更新配置文件: {env_path}")

def verify_configuration():
    """验证配置是否正确"""
    try:
        from src.config.settings import Settings
        settings = Settings()
        
        print("\n📋 当前配置:")
        print(f"  环境: {settings.environment}")
        print(f"  是否生产环境: {settings.is_production}")
        print(f"  使用模拟数据: {settings.should_use_mock_data}")
        print(f"  严格模式: {settings.is_strict_mode}")
        
        # 验证生产模式配置
        if not settings.is_production:
            print("\n⚠️  警告: 环境未设置为production")
            return False
        
        if settings.should_use_mock_data:
            print("\n⚠️  警告: 仍然启用了模拟数据")
            return False
        
        if not settings.is_strict_mode:
            print("\n⚠️  警告: 严格模式未启用")
            return False
        
        print("\n✅ 配置验证通过！")
        return True
        
    except Exception as e:
        print(f"\n❌ 配置验证失败: {str(e)}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("BTC Options Trading System - 启用生产模式")
    print("=" * 60)
    print()
    
    # 确认操作
    print("⚠️  此操作将:")
    print("  1. 禁用所有模拟数据")
    print("  2. 启用严格数据模式")
    print("  3. 数据获取失败时抛出错误而不是降级")
    print()
    
    response = input("是否继续? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("操作已取消")
        return
    
    print()
    
    # 备份现有配置
    backup_path = backup_env_file()
    
    # 更新配置
    update_env_file()
    
    # 验证配置
    if verify_configuration():
        print("\n" + "=" * 60)
        print("✅ 生产模式已成功启用！")
        print("=" * 60)
        print()
        print("下一步:")
        print("  1. 重启API服务器")
        print("  2. 重启前端应用")
        print("  3. 验证系统行为")
        print()
        print("如需回滚，运行:")
        if backup_path:
            print(f"  cp {backup_path} .env")
        print()
    else:
        print("\n" + "=" * 60)
        print("❌ 配置验证失败")
        print("=" * 60)
        print()
        print("请检查配置并手动修复，或使用备份文件回滚:")
        if backup_path:
            print(f"  cp {backup_path} .env")
        print()
        sys.exit(1)

if __name__ == "__main__":
    main()
