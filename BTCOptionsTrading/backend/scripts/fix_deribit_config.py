#!/usr/bin/env python3
"""
Deribit配置修复脚本

自动修复Deribit API配置问题
"""

import sys
from pathlib import Path
from datetime import datetime

def print_section(title):
    """打印分节标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def read_env_file():
    """读取.env文件"""
    env_path = Path(__file__).parent / '.env'
    config = {}
    
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip().strip('"')
    
    return config, env_path


def backup_env_file(env_path):
    """备份.env文件"""
    if env_path.exists():
        backup_path = env_path.parent / f'.env.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        with open(env_path, 'r') as src:
            with open(backup_path, 'w') as dst:
                dst.write(src.read())
        print(f"✅ 已备份配置到: {backup_path}")
        return backup_path
    return None


def detect_issues(config):
    """检测配置问题"""
    issues = []
    
    test_mode = config.get('DERIBIT_TEST_MODE', 'true').lower() == 'true'
    base_url = config.get('DERIBIT_BASE_URL', '')
    ws_url = config.get('DERIBIT_WS_URL', '')
    api_key = config.get('DERIBIT_API_KEY', '')
    api_secret = config.get('DERIBIT_API_SECRET', '')
    
    # 检查1: 测试模式与URL不匹配
    if test_mode:
        if 'test.deribit.com' not in base_url:
            issues.append({
                'type': 'url_mismatch',
                'severity': 'high',
                'message': '测试模式启用，但Base URL不是测试网地址',
                'current': base_url,
                'suggested': 'https://test.deribit.com'
            })
        if 'test.deribit.com' not in ws_url:
            issues.append({
                'type': 'ws_url_mismatch',
                'severity': 'high',
                'message': '测试模式启用，但WebSocket URL不是测试网地址',
                'current': ws_url,
                'suggested': 'wss://test.deribit.com/ws/api/v2'
            })
    else:
        if 'test.deribit.com' in base_url:
            issues.append({
                'type': 'url_mismatch',
                'severity': 'high',
                'message': '生产模式启用，但Base URL是测试网地址',
                'current': base_url,
                'suggested': 'https://www.deribit.com'
            })
        if 'test.deribit.com' in ws_url:
            issues.append({
                'type': 'ws_url_mismatch',
                'severity': 'high',
                'message': '生产模式启用，但WebSocket URL是测试网地址',
                'current': ws_url,
                'suggested': 'wss://www.deribit.com/ws/api/v2'
            })
        if not api_key or not api_secret:
            issues.append({
                'type': 'missing_credentials',
                'severity': 'high',
                'message': '生产模式需要有效的API Key和Secret',
                'current': 'API凭证缺失',
                'suggested': '请在Deribit网站生成API密钥'
            })
    
    # 检查2: API密钥格式
    if api_key and len(api_key) < 8:
        issues.append({
            'type': 'invalid_api_key',
            'severity': 'medium',
            'message': 'API Key格式可能不正确',
            'current': f'{api_key[:4]}...',
            'suggested': 'API Key通常是8个字符或更长'
        })
    
    return issues


def fix_configuration(config, issues):
    """修复配置"""
    fixed_config = config.copy()
    
    for issue in issues:
        if issue['type'] == 'url_mismatch':
            fixed_config['DERIBIT_BASE_URL'] = issue['suggested']
        elif issue['type'] == 'ws_url_mismatch':
            fixed_config['DERIBIT_WS_URL'] = issue['suggested']
    
    return fixed_config


def write_env_file(config, env_path):
    """写入.env文件"""
    with open(env_path, 'w') as f:
        f.write("# BTC Options Trading System Configuration\n")
        f.write(f"# Auto-fixed: {datetime.now().isoformat()}\n\n")
        
        # 分组写入
        groups = {
            '应用配置': ['APP_NAME', 'APP_VERSION', 'ENVIRONMENT'],
            'API服务配置': ['API_HOST', 'API_PORT', 'API_DEBUG'],
            'Deribit API配置': [
                'DERIBIT_API_KEY', 'DERIBIT_API_SECRET', 'DERIBIT_TEST_MODE',
                'DERIBIT_BASE_URL', 'DERIBIT_WS_URL', 'DERIBIT_RATE_LIMIT',
                'DERIBIT_RATE_WINDOW', 'DERIBIT_MAX_RETRIES', 'DERIBIT_RETRY_DELAY'
            ],
            '数据库配置': [
                'POSTGRES_HOST', 'POSTGRES_PORT', 'POSTGRES_DB',
                'POSTGRES_USER', 'POSTGRES_PASSWORD', 'REDIS_HOST',
                'REDIS_PORT', 'REDIS_DB', 'REDIS_PASSWORD',
                'INFLUXDB_HOST', 'INFLUXDB_PORT', 'INFLUXDB_TOKEN',
                'INFLUXDB_ORG', 'INFLUXDB_BUCKET'
            ],
            '交易配置': [
                'DEFAULT_CURRENCY', 'RISK_FREE_RATE', 'MAX_PORTFOLIO_DELTA',
                'MAX_PORTFOLIO_GAMMA', 'MAX_PORTFOLIO_VEGA', 'MAX_PORTFOLIO_VALUE',
                'MAX_SINGLE_POSITION', 'DEFAULT_INITIAL_CAPITAL', 'COMMISSION_RATE'
            ],
            'CORS配置': ['CORS_ORIGINS', 'CORS_METHODS'],
            'JWT配置': ['JWT_SECRET_KEY', 'JWT_ALGORITHM', 'JWT_EXPIRE_MINUTES'],
            '日志配置': [
                'LOG_LEVEL', 'LOG_FORMAT', 'LOG_FILE_PATH',
                'LOG_MAX_FILE_SIZE', 'LOG_BACKUP_COUNT'
            ]
        }
        
        for group_name, keys in groups.items():
            f.write(f"# {group_name}\n")
            for key in keys:
                if key in config:
                    value = config[key]
                    # 添加引号给包含特殊字符的值
                    if ' ' in value or ',' in value:
                        value = f'"{value}"'
                    f.write(f"{key}={value}\n")
            f.write("\n")


def main():
    """主函数"""
    print_section("🔧 Deribit配置修复工具")
    
    # 读取配置
    print("\n📖 读取当前配置...")
    config, env_path = read_env_file()
    
    if not config:
        print("❌ 未找到.env文件")
        print("\n💡 请先创建.env文件，可以从.env.example复制:")
        print("  cp .env.example .env")
        sys.exit(1)
    
    print(f"✅ 找到配置文件: {env_path}")
    
    # 检测问题
    print("\n🔍 检测配置问题...")
    issues = detect_issues(config)
    
    if not issues:
        print("✅ 配置正常，无需修复")
        
        # 显示当前配置
        print("\n📋 当前Deribit配置:")
        test_mode = config.get('DERIBIT_TEST_MODE', 'true').lower() == 'true'
        print(f"  测试模式: {test_mode}")
        print(f"  Base URL: {config.get('DERIBIT_BASE_URL', 'N/A')}")
        print(f"  WebSocket URL: {config.get('DERIBIT_WS_URL', 'N/A')}")
        return
    
    # 显示问题
    print(f"\n⚠️  发现 {len(issues)} 个配置问题:\n")
    for i, issue in enumerate(issues, 1):
        severity_icon = "🔴" if issue['severity'] == 'high' else "🟡"
        print(f"{severity_icon} 问题 {i}: {issue['message']}")
        print(f"   当前值: {issue['current']}")
        print(f"   建议值: {issue['suggested']}")
        print()
    
    # 询问是否修复
    response = input("是否自动修复这些问题? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("操作已取消")
        return
    
    # 备份
    print("\n💾 备份当前配置...")
    backup_path = backup_env_file(env_path)
    
    # 修复
    print("\n🔧 修复配置...")
    fixed_config = fix_configuration(config, issues)
    
    # 写入
    write_env_file(fixed_config, env_path)
    print(f"✅ 配置已更新: {env_path}")
    
    # 显示修复后的配置
    print("\n📋 修复后的Deribit配置:")
    test_mode = fixed_config.get('DERIBIT_TEST_MODE', 'true').lower() == 'true'
    print(f"  测试模式: {test_mode}")
    print(f"  Base URL: {fixed_config.get('DERIBIT_BASE_URL', 'N/A')}")
    print(f"  WebSocket URL: {fixed_config.get('DERIBIT_WS_URL', 'N/A')}")
    
    print("\n" + "=" * 70)
    print("  ✅ 配置修复完成！")
    print("=" * 70)
    
    print("\n下一步:")
    print("  1. 重启API服务器")
    print("  2. 运行诊断脚本验证: python diagnose_deribit_connection.py")
    print()
    
    if backup_path:
        print(f"如需回滚，运行:")
        print(f"  cp {backup_path} .env")
    print()


if __name__ == "__main__":
    main()
