#!/usr/bin/env python
"""
直接测试 CSV API 端点
"""

import asyncio
import sys
import os

# 添加后端目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.api.routes.csv_data import (
    get_csv_summary,
    get_csv_contracts,
    get_csv_contract_data
)

async def test_api():
    print("=" * 70)
    print("CSV API 端点测试")
    print("=" * 70)
    
    # 1. 测试 get_csv_summary
    print("\n1. 测试 /api/csv/summary:")
    try:
        result = await get_csv_summary()
        print(f"   ✓ 成功")
        print(f"   - 文件数: {result.get('total_files')}")
        print(f"   - 记录数: {result.get('total_records')}")
        print(f"   - 合约数: {result.get('total_contracts')}")
        print(f"   - 数据目录: {result.get('data_dir')}")
    except Exception as e:
        print(f"   ✗ 失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 2. 测试 get_csv_contracts
    print("\n2. 测试 /api/csv/contracts?underlying=BTC:")
    try:
        result = await get_csv_contracts(underlying='BTC')
        contracts = result.get('contracts', [])
        print(f"   ✓ 成功")
        print(f"   - 合约数: {len(contracts)}")
        if contracts:
            print(f"   - 第一个合约: {contracts[0]['instrument_name']}")
            print(f"   - 执行价: {contracts[0]['strike_price']}")
            print(f"   - 期权类型: {contracts[0]['option_type']}")
    except Exception as e:
        print(f"   ✗ 失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 3. 测试 get_csv_contract_data
    print("\n3. 测试 /api/csv/contract/{instrument_name}:")
    try:
        # 先获取第一个合约名称
        result = await get_csv_contracts(underlying='BTC')
        contracts = result.get('contracts', [])
        if contracts:
            contract_name = contracts[0]['instrument_name']
            print(f"   测试合约: {contract_name}")
            
            result = await get_csv_contract_data(contract_name)
            print(f"   ✓ 成功")
            print(f"   - 数据点数: {result.get('data_points')}")
            print(f"   - 平均价格: {result.get('avg_price')}")
            print(f"   - 时间范围: {result.get('date_range')}")
        else:
            print(f"   ✗ 没有合约可测试")
    except Exception as e:
        print(f"   ✗ 失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("测试完成")
    print("=" * 70)

if __name__ == '__main__':
    asyncio.run(test_api())
