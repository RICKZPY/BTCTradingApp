"""
交易管理 API
"""

import os
import csv
from datetime import datetime
from typing import List, Dict, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.config.logging_config import get_logger
from src.traders.scheduled_trader import ScheduledTrader
from src.scheduler.task_scheduler import get_scheduler

logger = get_logger(__name__)

router = APIRouter()

# 初始化交易执行器
scheduled_trader = ScheduledTrader()


class TradeConfig(BaseModel):
    """交易配置"""
    underlying: str = "BTC"
    option_type: str = "call"
    side: str = "buy"
    amount: float = 1.0


class ScheduleConfig(BaseModel):
    """定时交易配置"""
    underlying: str = "BTC"
    option_type: str = "call"
    side: str = "buy"
    amount: float = 1.0
    hour: int = 5
    minute: int = 0


class OrderRecord(BaseModel):
    """订单记录"""
    timestamp: str
    instrument_name: str
    side: str
    amount: float
    price: float
    order_id: str
    status: str
    filled_amount: float


@router.get("/orders")
async def get_all_orders(limit: int = Query(100, ge=1, le=1000)):
    """获取所有订单"""
    try:
        data_dir = scheduled_trader.data_dir
        
        if not os.path.exists(data_dir):
            return {
                'total_orders': 0,
                'orders': [],
                'message': 'No trade data found'
            }
        
        # 获取所有 CSV 文件
        csv_files = sorted([f for f in os.listdir(data_dir) if f.endswith('.csv')])
        
        if not csv_files:
            return {
                'total_orders': 0,
                'orders': [],
                'message': 'No CSV files found'
            }
        
        # 读取所有订单
        all_orders = []
        for csv_file in csv_files:
            filepath = os.path.join(data_dir, csv_file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        all_orders.append(row)
            except Exception as e:
                logger.warning(f"Error reading {csv_file}: {e}")
        
        # 按时间戳排序（最新的在前）
        all_orders.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # 限制返回数量
        orders = all_orders[:limit]
        
        return {
            'total_orders': len(all_orders),
            'returned': len(orders),
            'orders': orders
        }
    
    except Exception as e:
        logger.error(f"Error getting all orders: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders/{order_id}")
async def get_order_details(order_id: str):
    """获取订单详情"""
    try:
        data_dir = scheduled_trader.data_dir
        
        if not os.path.exists(data_dir):
            raise HTTPException(status_code=404, detail="No trade data found")
        
        # 搜索订单
        csv_files = sorted([f for f in os.listdir(data_dir) if f.endswith('.csv')])
        
        for csv_file in csv_files:
            filepath = os.path.join(data_dir, csv_file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row.get('order_id') == order_id:
                            return {
                                'order': row,
                                'file': csv_file
                            }
            except Exception as e:
                logger.warning(f"Error reading {csv_file}: {e}")
        
        raise HTTPException(status_code=404, detail=f"Order not found: {order_id}")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting order details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/place-order")
async def place_order(config: TradeConfig):
    """下单"""
    try:
        logger.info(f"Placing order: {config.option_type} {config.side} {config.amount}")
        
        # 执行交易
        result = scheduled_trader.execute_scheduled_trade(
            underlying=config.underlying,
            option_type=config.option_type,
            side=config.side,
            amount=config.amount
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="Failed to place order")
        
        return {
            'status': 'success',
            'message': 'Order placed successfully',
            'order': result,
            'timestamp': datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error placing order: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schedule")
async def schedule_trading(config: ScheduleConfig):
    """配置定时交易"""
    try:
        logger.info(f"Scheduling trading at {config.hour}:{config.minute:02d} Beijing time")
        
        scheduler = get_scheduler()
        job_id = scheduler.schedule_trading(
            hour=config.hour,
            minute=config.minute,
            underlying=config.underlying,
            option_type=config.option_type,
            side=config.side,
            amount=config.amount
        )
        
        if not job_id:
            raise HTTPException(status_code=500, detail="Failed to schedule trading")
        
        return {
            'status': 'success',
            'message': 'Trading scheduled',
            'job_id': job_id,
            'schedule': f"{config.hour}:{config.minute:02d} Beijing time (UTC {(config.hour - 8) % 24}:{config.minute:02d})",
            'config': {
                'underlying': config.underlying,
                'option_type': config.option_type,
                'side': config.side,
                'amount': config.amount
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scheduling trading: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schedule")
async def get_trading_schedule():
    """获取定时交易配置"""
    try:
        scheduler = get_scheduler()
        jobs = scheduler.get_jobs()
        
        trading_jobs = [j for j in jobs if 'trading' in j.id.lower()]
        
        jobs_info = []
        for job in trading_jobs:
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
        logger.error(f"Error getting trading schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_trading_summary():
    """获取交易摘要"""
    try:
        data_dir = scheduled_trader.data_dir
        
        if not os.path.exists(data_dir):
            return {
                'total_files': 0,
                'total_orders': 0,
                'data_dir': data_dir,
                'message': 'No trade data found'
            }
        
        # 获取所有 CSV 文件
        csv_files = sorted([f for f in os.listdir(data_dir) if f.endswith('.csv')])
        
        if not csv_files:
            return {
                'total_files': 0,
                'total_orders': 0,
                'data_dir': data_dir,
                'message': 'No CSV files found'
            }
        
        # 计算总订单数
        total_orders = 0
        for csv_file in csv_files:
            filepath = os.path.join(data_dir, csv_file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    total_orders += sum(1 for _ in f) - 1  # 减去表头
            except:
                pass
        
        # 获取最新文件信息
        latest_file = csv_files[-1]
        latest_path = os.path.join(data_dir, latest_file)
        latest_mtime = os.path.getmtime(latest_path)
        last_updated = datetime.fromtimestamp(latest_mtime).isoformat()
        
        return {
            'total_files': len(csv_files),
            'total_orders': total_orders,
            'latest_file': latest_file,
            'last_updated': last_updated,
            'data_dir': data_dir
        }
    
    except Exception as e:
        logger.error(f"Error getting trading summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))
