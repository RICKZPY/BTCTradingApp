"""
Order Book 管理 API
"""

import os
from datetime import datetime
from typing import List, Dict, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.config.logging_config import get_logger
from src.collectors.orderbook_collector import OrderBookCollector
from src.scheduler.task_scheduler import get_scheduler

logger = get_logger(__name__)

router = APIRouter()

# 初始化收集器
orderbook_collector = OrderBookCollector()


class OrderBookSummary(BaseModel):
    """Order Book 摘要"""
    total_files: int
    latest_file: Optional[str]
    last_updated: Optional[str]
    total_records: int
    data_dir: str


class OrderBookRecord(BaseModel):
    """Order Book 记录"""
    timestamp: str
    instrument_name: str
    strike_price: float
    option_type: str
    expiry_date: str
    bid_price: float
    bid_size: float
    ask_price: float
    ask_size: float


class CollectionConfig(BaseModel):
    """收集配置"""
    underlying: str = "BTC"
    num_strikes: int = 4
    hour: int = 5
    minute: int = 0


@router.get("/summary")
async def get_orderbook_summary():
    """获取 Order Book 摘要"""
    try:
        data_dir = orderbook_collector.data_dir
        
        if not os.path.exists(data_dir):
            return {
                'total_files': 0,
                'latest_file': None,
                'last_updated': None,
                'total_records': 0,
                'data_dir': data_dir,
                'message': 'No orderbook data found'
            }
        
        # 获取所有 CSV 文件
        csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
        
        if not csv_files:
            return {
                'total_files': 0,
                'latest_file': None,
                'last_updated': None,
                'total_records': 0,
                'data_dir': data_dir,
                'message': 'No CSV files found'
            }
        
        # 获取最新文件
        latest_file = sorted(csv_files)[-1]
        latest_path = os.path.join(data_dir, latest_file)
        
        # 计算总记录数
        total_records = 0
        for csv_file in csv_files:
            filepath = os.path.join(data_dir, csv_file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    total_records += sum(1 for _ in f) - 1  # 减去表头
            except:
                pass
        
        # 获取最后修改时间
        latest_mtime = os.path.getmtime(latest_path)
        last_updated = datetime.fromtimestamp(latest_mtime).isoformat()
        
        return {
            'total_files': len(csv_files),
            'latest_file': latest_file,
            'last_updated': last_updated,
            'total_records': total_records,
            'data_dir': data_dir
        }
    
    except Exception as e:
        logger.error(f"Error getting orderbook summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/latest")
async def get_latest_orderbook(limit: int = Query(100, ge=1, le=1000)):
    """获取最新的 Order Book 数据"""
    try:
        data_dir = orderbook_collector.data_dir
        
        if not os.path.exists(data_dir):
            raise HTTPException(status_code=404, detail="No orderbook data found")
        
        # 获取最新文件
        csv_files = sorted([f for f in os.listdir(data_dir) if f.endswith('.csv')])
        if not csv_files:
            raise HTTPException(status_code=404, detail="No CSV files found")
        
        latest_file = csv_files[-1]
        latest_path = os.path.join(data_dir, latest_file)
        
        # 读取最新数据
        import csv
        records = []
        try:
            with open(latest_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader):
                    if i >= limit:
                        break
                    records.append(row)
        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            raise HTTPException(status_code=500, detail=f"Error reading CSV file: {e}")
        
        return {
            'file': latest_file,
            'total_records': len(records),
            'records': records
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting latest orderbook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_orderbook_history(days: int = Query(7, ge=1, le=30)):
    """获取历史 Order Book 数据"""
    try:
        data_dir = orderbook_collector.data_dir
        
        if not os.path.exists(data_dir):
            raise HTTPException(status_code=404, detail="No orderbook data found")
        
        # 获取所有 CSV 文件
        csv_files = sorted([f for f in os.listdir(data_dir) if f.endswith('.csv')])
        
        if not csv_files:
            raise HTTPException(status_code=404, detail="No CSV files found")
        
        # 返回文件列表
        files_info = []
        for csv_file in csv_files[-days:]:
            filepath = os.path.join(data_dir, csv_file)
            try:
                mtime = os.path.getmtime(filepath)
                size = os.path.getsize(filepath)
                
                # 计算记录数
                record_count = 0
                with open(filepath, 'r', encoding='utf-8') as f:
                    record_count = sum(1 for _ in f) - 1
                
                files_info.append({
                    'filename': csv_file,
                    'size': size,
                    'records': record_count,
                    'last_modified': datetime.fromtimestamp(mtime).isoformat()
                })
            except Exception as e:
                logger.warning(f"Error processing file {csv_file}: {e}")
        
        return {
            'total_files': len(files_info),
            'files': files_info
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting orderbook history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collect")
async def trigger_orderbook_collection(config: CollectionConfig = None):
    """手动触发 Order Book 收集"""
    try:
        if config is None:
            config = CollectionConfig()
        
        logger.info(f"Triggering orderbook collection: {config.underlying}, {config.num_strikes} strikes")
        
        # 执行收集
        result = orderbook_collector.collect_and_save(config.underlying, config.num_strikes)
        
        return {
            'status': 'success',
            'message': 'Orderbook collection completed',
            'file': result,
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error triggering orderbook collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schedule")
async def schedule_orderbook_collection(config: CollectionConfig):
    """配置定时 Order Book 收集"""
    try:
        logger.info(f"Scheduling orderbook collection at {config.hour}:{config.minute:02d} Beijing time")
        
        scheduler = get_scheduler()
        job_id = scheduler.schedule_orderbook_collection(
            hour=config.hour,
            minute=config.minute,
            underlying=config.underlying,
            num_strikes=config.num_strikes
        )
        
        if not job_id:
            raise HTTPException(status_code=500, detail="Failed to schedule orderbook collection")
        
        return {
            'status': 'success',
            'message': 'Orderbook collection scheduled',
            'job_id': job_id,
            'schedule': f"{config.hour}:{config.minute:02d} Beijing time (UTC {(config.hour - 8) % 24}:{config.minute:02d})"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scheduling orderbook collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schedule")
async def get_orderbook_schedule():
    """获取定时 Order Book 收集配置"""
    try:
        scheduler = get_scheduler()
        jobs = scheduler.get_jobs()
        
        orderbook_jobs = [j for j in jobs if 'orderbook' in j.id.lower()]
        
        jobs_info = []
        for job in orderbook_jobs:
            jobs_info.append({
                'id': job.id,
                'name': job.name,
                'trigger': str(job.trigger),
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None
            })
        
        return {
            'total_jobs': len(jobs_info),
            'jobs': jobs_info
        }
    
    except Exception as e:
        logger.error(f"Error getting orderbook schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))
