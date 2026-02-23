#!/usr/bin/env python
"""
诊断 CSV 数据问题
"""

import os
import csv
from pathlib import Path

# 检查的目录列表
CSV_DATA_DIRS = [
    "./data/downloads",
    "/root/BTCTradingApp/BTCOptionsTrading/backend/data/daily_snapshots",
    "/root/BTCTradingApp/BTCOptionsTrading/backend/data/downloads",
    "data/daily_snapshots",
]

print("=" * 70)
print("CSV 数据诊断")
print("=" * 70)

# 1. 检查目录
print("\n1. 检查目录是否存在:")
for dir_path in CSV_DATA_DIRS:
    exists = os.path.exists(dir_path)
    status = "✓ 存在" if exists else "✗ 不存在"
    print(f"   {dir_path}: {status}")

# 2. 查找第一个存在的目录
print("\n2. 查找可用的数据目录:")
available_dir = None
for dir_path in CSV_DATA_DIRS:
    if os.path.exists(dir_path):
        available_dir = dir_path
        print(f"   ✓ 使用: {dir_path}")
        break

if not available_dir:
    print("   ✗ 没有找到任何数据目录!")
    print("\n建议:")
    print("   1. 创建目录: mkdir -p data/downloads")
    print("   2. 把 CSV 文件放入该目录")
    exit(1)

# 3. 列出 CSV 文件
print(f"\n3. 在 {available_dir} 中查找 CSV 文件:")
csv_files = []
try:
    for file in os.listdir(available_dir):
        if file.endswith('.csv'):
            csv_files.append(file)
            file_path = os.path.join(available_dir, file)
            file_size = os.path.getsize(file_path) / 1024  # KB
            print(f"   ✓ {file} ({file_size:.1f} KB)")
except Exception as e:
    print(f"   ✗ 错误: {e}")
    exit(1)

if not csv_files:
    print("   ✗ 没有找到 CSV 文件!")
    print("\n建议:")
    print(f"   1. 把 CSV 文件放入: {available_dir}/")
    print("   2. 确保文件名以 .csv 结尾")
    exit(1)

# 4. 检查 CSV 文件格式
print(f"\n4. 检查 CSV 文件格式 (前 3 个文件):")
for csv_file in csv_files[:3]:
    csv_path = os.path.join(available_dir, csv_file)
    print(f"\n   文件: {csv_file}")
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # 检查列名
            if reader.fieldnames:
                print(f"   列数: {len(reader.fieldnames)}")
                print(f"   列名: {', '.join(reader.fieldnames[:5])}...")
                
                # 检查数据行
                row_count = 0
                for row in reader:
                    row_count += 1
                    if row_count == 1:
                        # 显示第一行数据
                        print(f"   第一行数据:")
                        for key in list(reader.fieldnames)[:5]:
                            print(f"     - {key}: {row.get(key, 'N/A')}")
                
                print(f"   总行数: {row_count}")
                
                # 检查必要的列
                required_cols = ['instrument_name', 'timestamp']
                missing_cols = [col for col in required_cols if col not in reader.fieldnames]
                if missing_cols:
                    print(f"   ✗ 缺少必要的列: {missing_cols}")
                else:
                    print(f"   ✓ 包含所有必要的列")
            else:
                print(f"   ✗ CSV 文件为空或格式错误")
    except Exception as e:
        print(f"   ✗ 错误: {e}")

# 5. 测试 API
print(f"\n5. 测试 API 端点:")
print("   运行以下命令测试:")
print("   curl http://localhost:8000/api/csv/summary")
print("   curl http://localhost:8000/api/csv/contracts?underlying=BTC")

print("\n" + "=" * 70)
print("诊断完成")
print("=" * 70)
