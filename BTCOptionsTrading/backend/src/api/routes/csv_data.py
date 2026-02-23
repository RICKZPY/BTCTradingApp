"""
CSV数据API - 提供从daily_snapshots下载的历史数据
"""

import os
import json
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime

from src.config.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter()

# 获取当前脚本所在目录
# csv_data.py 在 backend/src/api/routes/csv_data.py
# 所以向上走 3 级到 backend 目录
CURRENT_FILE = os.path.abspath(__file__)
ROUTES_DIR = os.path.dirname(CURRENT_FILE)  # backend/src/api/routes
API_DIR = os.path.dirname(ROUTES_DIR)  # backend/src/api
SRC_DIR = os.path.dirname(API_DIR)  # backend/src
BACKEND_DIR = os.path.dirname(SRC_DIR)  # backend

# CSV数据目录 - 支持多个位置（使用绝对路径）
CSV_DATA_DIRS = [
    os.path.join(BACKEND_DIR, "data", "downloads"),  # backend/data/downloads
    os.path.join(BACKEND_DIR, "data", "daily_snapshots"),  # backend/data/daily_snapshots
    "/root/BTCTradingApp/BTCOptionsTrading/backend/data/downloads",  # 服务器下载路径
    "/root/BTCTradingApp/BTCOptionsTrading/backend/data/daily_snapshots",  # 服务器路径
]

LOCAL_CACHE_DIR = os.path.join(BACKEND_DIR, "csv_data_cache")

# 确保缓存目录存在
Path(LOCAL_CACHE_DIR).mkdir(parents=True, exist_ok=True)

logger.info(f"CSV API initialized")
logger.info(f"Backend directory: {BACKEND_DIR}")
logger.info(f"CSV data directories: {CSV_DATA_DIRS}")


def get_csv_data_dir() -> str:
    """获取第一个存在的CSV数据目录"""
    for dir_path in CSV_DATA_DIRS:
        if os.path.exists(dir_path):
            logger.info(f"Using CSV data directory: {dir_path}")
            return dir_path
    
    # 如果都不存在，返回第一个并记录警告
    logger.warning(f"No CSV data directory found. Tried: {CSV_DATA_DIRS}")
    return CSV_DATA_DIRS[0]


class ContractDataPoint(BaseModel):
    """单个数据点"""
    timestamp: str
    mark_price: Optional[float] = None
    bid_price: Optional[float] = None
    ask_price: Optional[float] = None
    volume: Optional[float] = None
    open_interest: Optional[float] = None
    implied_volatility: Optional[float] = None


class ContractPriceData(BaseModel):
    """合约价格数据"""
    instrument_name: str
    underlying: str
    strike_price: float
    option_type: str
    expiry_date: str
    data_points: int
    price_history: List[ContractDataPoint]
    date_range: dict


class CSVDataSummary(BaseModel):
    """CSV数据摘要"""
    total_files: int
    total_records: int
    total_contracts: int
    contracts: dict
    last_updated: str


def load_csv_files():
    """从服务器加载CSV文件"""
    csv_data_dir = get_csv_data_dir()
    
    if not os.path.exists(csv_data_dir):
        logger.warning(f"CSV data directory not found: {csv_data_dir}")
        return []
    
    csv_files = []
    try:
        for file in os.listdir(csv_data_dir):
            if file.endswith('.csv'):
                csv_files.append(file)
    except Exception as e:
        logger.error(f"Error listing CSV files: {e}")
    
    return sorted(csv_files)


def parse_csv_file(csv_path: str) -> List[dict]:
    """解析CSV文件"""
    import csv
    
    data = []
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
    except Exception as e:
        logger.error(f"Error parsing CSV file {csv_path}: {e}")
    
    return data


def organize_data_by_contract(all_data: List[dict]) -> dict:
    """按合约组织数据"""
    contracts = {}
    
    for row in all_data:
        instrument_name = row.get('instrument_name', 'unknown')
        
        if instrument_name not in contracts:
            contracts[instrument_name] = []
        
        contracts[instrument_name].append(row)
    
    return contracts


@router.get("/summary")
async def get_csv_summary():
    """获取CSV数据摘要"""
    try:
        csv_data_dir = get_csv_data_dir()
        csv_files = load_csv_files()
        
        if not csv_files:
            return {
                'total_files': 0,
                'total_records': 0,
                'total_contracts': 0,
                'contracts': {},
                'last_updated': datetime.now().isoformat(),
                'message': 'No CSV files found',
                'data_dir': csv_data_dir
            }
        
        # 加载所有CSV文件
        all_data = []
        for csv_file in csv_files:
            csv_path = os.path.join(csv_data_dir, csv_file)
            data = parse_csv_file(csv_path)
            all_data.extend(data)
        
        # 按合约组织
        contracts = organize_data_by_contract(all_data)
        
        # 生成摘要
        summary = {
            'total_files': len(csv_files),
            'total_records': len(all_data),
            'total_contracts': len(contracts),
            'contracts': {
                name: {
                    'record_count': len(data),
                    'date_range': {
                        'start': min(row.get('timestamp', '') for row in data),
                        'end': max(row.get('timestamp', '') for row in data)
                    }
                }
                for name, data in contracts.items()
            },
            'last_updated': datetime.now().isoformat(),
            'data_dir': csv_data_dir
        }
        
        return summary
        
    except Exception as e:
        logger.error(f"Error getting CSV summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/contracts")
async def get_csv_contracts(underlying: str = Query("BTC", description="标的资产")):
    """获取CSV中的合约列表"""
    try:
        csv_data_dir = get_csv_data_dir()
        csv_files = load_csv_files()
        
        if not csv_files:
            return {'contracts': [], 'data_dir': csv_data_dir}
        
        # 加载所有CSV文件
        all_data = []
        for csv_file in csv_files:
            csv_path = os.path.join(csv_data_dir, csv_file)
            data = parse_csv_file(csv_path)
            all_data.extend(data)
        
        # 按合约组织
        contracts = organize_data_by_contract(all_data)
        
        # 过滤并返回
        contract_list = []
        for name, data in contracts.items():
            first_row = data[0]
            if first_row.get('underlying_symbol', 'BTC') == underlying:
                contract_list.append({
                    'instrument_name': name,
                    'record_count': len(data),
                    'strike_price': float(first_row.get('strike_price', 0)),
                    'option_type': first_row.get('option_type', ''),
                    'expiry_date': first_row.get('expiry_date', ''),
                    'date_range': {
                        'start': min(row.get('timestamp', '') for row in data),
                        'end': max(row.get('timestamp', '') for row in data)
                    }
                })
        
        return {
            'underlying': underlying,
            'contracts': sorted(contract_list, key=lambda x: x['instrument_name']),
            'data_dir': csv_data_dir
        }
        
    except Exception as e:
        logger.error(f"Error getting CSV contracts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/contract/{instrument_name}")
async def get_csv_contract_data(instrument_name: str):
    """获取特定合约的CSV数据"""
    try:
        csv_data_dir = get_csv_data_dir()
        csv_files = load_csv_files()
        
        if not csv_files:
            raise HTTPException(status_code=404, detail="No CSV files found")
        
        # 加载所有CSV文件
        all_data = []
        for csv_file in csv_files:
            csv_path = os.path.join(csv_data_dir, csv_file)
            data = parse_csv_file(csv_path)
            all_data.extend(data)
        
        # 按合约组织
        contracts = organize_data_by_contract(all_data)
        
        if instrument_name not in contracts:
            raise HTTPException(status_code=404, detail=f"Contract not found: {instrument_name}")
        
        data = contracts[instrument_name]
        first_row = data[0]
        
        # 转换数据格式
        price_history = []
        for row in data:
            try:
                price_history.append({
                    'timestamp': row.get('timestamp', ''),
                    'mark_price': float(row.get('mark_price', 0)) if row.get('mark_price') else None,
                    'bid_price': float(row.get('bid_price', 0)) if row.get('bid_price') else None,
                    'ask_price': float(row.get('ask_price', 0)) if row.get('ask_price') else None,
                    'volume': float(row.get('volume', 0)) if row.get('volume') else None,
                    'open_interest': float(row.get('open_interest', 0)) if row.get('open_interest') else None,
                    'implied_volatility': float(row.get('implied_volatility', 0)) if row.get('implied_volatility') else None
                })
            except (ValueError, TypeError):
                continue
        
        # 按时间戳排序
        price_history.sort(key=lambda x: x['timestamp'])
        
        # 计算统计信息
        prices = [p['mark_price'] for p in price_history if p['mark_price']]
        
        return {
            'instrument_name': instrument_name,
            'underlying': first_row.get('underlying_symbol', 'BTC'),
            'strike_price': float(first_row.get('strike_price', 0)),
            'option_type': first_row.get('option_type', ''),
            'expiry_date': first_row.get('expiry_date', ''),
            'data_points': len(price_history),
            'avg_price': sum(prices) / len(prices) if prices else 0,
            'price_history': price_history,
            'date_range': {
                'start': price_history[0]['timestamp'] if price_history else '',
                'end': price_history[-1]['timestamp'] if price_history else ''
            },
            'data_dir': csv_data_dir
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting CSV contract data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync")
async def sync_csv_data():
    """同步CSV数据到缓存"""
    try:
        csv_data_dir = get_csv_data_dir()
        csv_files = load_csv_files()
        
        if not csv_files:
            return {
                'status': 'no_data',
                'message': 'No CSV files found',
                'files_processed': 0,
                'data_dir': csv_data_dir
            }
        
        # 加载所有CSV文件
        all_data = []
        for csv_file in csv_files:
            csv_path = os.path.join(csv_data_dir, csv_file)
            data = parse_csv_file(csv_path)
            all_data.extend(data)
        
        # 按合约组织
        contracts = organize_data_by_contract(all_data)
        
        # 保存到缓存
        cache_file = os.path.join(LOCAL_CACHE_DIR, 'contracts_cache.json')
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump({
                'contracts': {
                    name: [
                        {
                            'timestamp': row.get('timestamp', ''),
                            'mark_price': float(row.get('mark_price', 0)) if row.get('mark_price') else None,
                            'bid_price': float(row.get('bid_price', 0)) if row.get('bid_price') else None,
                            'ask_price': float(row.get('ask_price', 0)) if row.get('ask_price') else None,
                            'volume': float(row.get('volume', 0)) if row.get('volume') else None,
                            'open_interest': float(row.get('open_interest', 0)) if row.get('open_interest') else None,
                            'implied_volatility': float(row.get('implied_volatility', 0)) if row.get('implied_volatility') else None
                        }
                        for row in data
                    ]
                    for name, data in contracts.items()
                },
                'last_synced': datetime.now().isoformat()
            }, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Synced {len(csv_files)} CSV files with {len(contracts)} contracts from {csv_data_dir}")
        
        return {
            'status': 'success',
            'files_processed': len(csv_files),
            'contracts_found': len(contracts),
            'total_records': len(all_data),
            'cache_file': cache_file,
            'data_dir': csv_data_dir
        }
        
    except Exception as e:
        logger.error(f"Error syncing CSV data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
