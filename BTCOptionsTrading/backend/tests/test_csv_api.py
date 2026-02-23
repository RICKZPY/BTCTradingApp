#!/usr/bin/env python
"""
测试 CSV API 是否能找到文件
"""

import os
import sys
import asyncio

# 添加后端目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.api.routes.csv_data import get_csv_data_dir, load_csv_files, organize_data_by_contract, parse_csv_file

print("=" * 70)
print("CSV API 测试")
print("=" * 70)

# 1. 获取数据目录
print("\n1. 获取数据目录:")
csv_dir = get_csv_data_dir()
print(f"   使用目录: {csv_dir}")
print(f"   目录存在: {os.path.exists(csv_dir)}")

# 2. 加载 CSV 文件
print("\n2. 加载 CSV 文件:")
csv_files = load_csv_files()
print(f"   找到 {len(csv_files)} 个 CSV 文件:")
for file in csv_files[:5]:
    print(f"     - {file}")
if len(csv_files) > 5:
    print(f"     ... 还有 {len(csv_files) - 5} 个文件")

# 3. 解析数据
if csv_files:
    print("\n3. 解析 CSV 数据:")
    all_data = []
    for csv_file in csv_files:
        csv_path = os.path.join(csv_dir, csv_file)
        data = parse_csv_file(csv_path)
        all_data.extend(data)
        print(f"   {csv_file}: {len(data)} 条记录")
    
    print(f"   总计: {len(all_data)} 条记录")
    
    # 4. 按合约组织
    print("\n4. 按合约组织数据:")
    contracts = organize_data_by_contract(all_data)
    print(f"   找到 {len(contracts)} 个合约:")
    for i, (name, data) in enumerate(list(contracts.items())[:5]):
        print(f"     - {name}: {len(data)} 条记录")
    if len(contracts) > 5:
        print(f"     ... 还有 {len(contracts) - 5} 个合约")
    
    # 5. 显示第一个合约的数据
    if contracts:
        first_contract = list(contracts.items())[0]
        print(f"\n5. 第一个合约的数据样本:")
        print(f"   合约: {first_contract[0]}")
        first_row = first_contract[1][0]
        print(f"   时间戳: {first_row.get('timestamp')}")
        print(f"   标记价格: {first_row.get('mark_price')}")
        print(f"   执行价: {first_row.get('strike_price')}")
        print(f"   期权类型: {first_row.get('option_type')}")
else:
    print("\n   ✗ 没有找到 CSV 文件!")

print("\n" + "=" * 70)
print("测试完成")
print("=" * 70)
