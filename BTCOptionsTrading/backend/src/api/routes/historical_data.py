"""
历史数据 API 路由
提供历史期权数据的管理和查询接口
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from src.historical.manager import HistoricalDataManager
from src.config.logging_config import get_logger

logger = get_logger(__name__)

# 创建路由器
router = APIRouter(prefix="/api/historical-data", tags=["historical-data"])

# 初始化管理器（单例）
_manager: Optional[HistoricalDataManager] = None


def get_manager() -> HistoricalDataManager:
    """获取历史数据管理器实例"""
    global _manager
    if _manager is None:
        _manager = HistoricalDataManager(
            download_dir="data/downloads",
            db_path="data/historical_options.db",
            cache_size_mb=100
        )
    return _manager


# ============================================================================
# 请求/响应模型
# ============================================================================

class ImportRequest(BaseModel):
    """导入数据请求"""
    should_validate: bool = Field(True, description="是否验证数据", alias="validate")
    generate_report: bool = Field(True, description="是否生成质量报告")


class ImportResponse(BaseModel):
    """导入数据响应"""
    success_count: int
    failure_count: int
    total_count: int
    records_imported: int
    import_duration_seconds: float
    quality_score: Optional[float] = None
    coverage_percentage: Optional[float] = None
    failed_files: List[str] = []


class InstrumentInfo(BaseModel):
    """期权合约信息"""
    instrument_name: str
    underlying_symbol: str
    strike_price: float
    expiry_date: datetime
    option_type: str


class CoverageStatsResponse(BaseModel):
    """覆盖率统计响应"""
    start_date: datetime
    end_date: datetime
    total_days: int
    days_with_data: int
    coverage_percentage: float
    missing_dates_count: int
    strikes_covered: List[float]
    expiries_covered: List[datetime]


class QualityReportResponse(BaseModel):
    """质量报告响应"""
    total_records: int
    missing_records: int
    anomaly_records: int
    coverage_percentage: float
    quality_score: float
    time_range_start: datetime
    time_range_end: datetime
    issues_count: int


class ManagerStatsResponse(BaseModel):
    """管理器统计响应"""
    download_dir: str
    csv_files: int
    database_records: int
    memory_cache_entries: int
    memory_cache_size_mb: float


class ExportRequest(BaseModel):
    """导出数据请求"""
    format: str = Field("csv", description="导出格式: csv, json")
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")
    instruments: Optional[List[str]] = Field(None, description="期权合约列表")
    compress: bool = Field(True, description="是否压缩")


class ExportResponse(BaseModel):
    """导出数据响应"""
    file_path: str
    records_exported: int
    file_size_bytes: int
    format: str


# ============================================================================
# API 端点
# ============================================================================

@router.post("/import", response_model=ImportResponse)
async def import_historical_data(request: ImportRequest):
    """
    导入历史数据
    
    从下载目录导入所有CSV文件到数据库
    """
    try:
        logger.info(f"API: Importing historical data (validate={request.should_validate})")
        
        manager = get_manager()
        result = manager.import_historical_data(
            validate=request.should_validate,
            generate_report=request.generate_report
        )
        
        response = ImportResponse(
            success_count=result.success_count,
            failure_count=result.failure_count,
            total_count=result.total_count,
            records_imported=result.records_imported,
            import_duration_seconds=result.import_duration_seconds,
            quality_score=result.quality_report.quality_score if result.quality_report else None,
            coverage_percentage=result.quality_report.coverage_percentage if result.quality_report else None,
            failed_files=result.failed_files
        )
        
        logger.info(f"API: Import complete - {result.success_count}/{result.total_count} files")
        return response
        
    except Exception as e:
        logger.error(f"API: Import failed - {str(e)}")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.get("/available/instruments", response_model=List[str])
async def get_available_instruments(
    underlying_symbol: Optional[str] = Query(None, description="标的资产符号"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期")
):
    """
    获取可用的期权合约列表
    """
    try:
        logger.info(f"API: Getting available instruments (symbol={underlying_symbol})")
        
        manager = get_manager()
        instruments = manager.get_available_instruments(
            start_date=start_date,
            end_date=end_date,
            underlying_symbol=underlying_symbol
        )
        
        logger.info(f"API: Found {len(instruments)} instruments")
        return instruments
        
    except Exception as e:
        logger.error(f"API: Failed to get instruments - {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get instruments: {str(e)}")


@router.get("/available/dates", response_model=List[datetime])
async def get_available_dates(
    instrument_name: Optional[str] = Query(None, description="期权合约名称"),
    underlying_symbol: Optional[str] = Query(None, description="标的资产符号")
):
    """
    获取可用的日期列表
    """
    try:
        logger.info(f"API: Getting available dates (instrument={instrument_name})")
        
        manager = get_manager()
        dates = manager.get_available_dates(
            instrument_name=instrument_name,
            underlying_symbol=underlying_symbol
        )
        
        logger.info(f"API: Found {len(dates)} dates")
        return dates
        
    except Exception as e:
        logger.error(f"API: Failed to get dates - {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get dates: {str(e)}")


@router.get("/coverage", response_model=CoverageStatsResponse)
async def get_coverage_stats(
    start_date: datetime = Query(..., description="开始日期"),
    end_date: datetime = Query(..., description="结束日期"),
    underlying_symbol: Optional[str] = Query(None, description="标的资产符号")
):
    """
    获取数据覆盖率统计
    """
    try:
        logger.info(f"API: Getting coverage stats ({start_date} to {end_date})")
        
        manager = get_manager()
        stats = manager.get_coverage_stats(
            start_date=start_date,
            end_date=end_date,
            underlying_symbol=underlying_symbol
        )
        
        response = CoverageStatsResponse(
            start_date=stats.start_date,
            end_date=stats.end_date,
            total_days=stats.total_days,
            days_with_data=stats.days_with_data,
            coverage_percentage=stats.coverage_percentage,
            missing_dates_count=len(stats.missing_dates),
            strikes_covered=[float(s) for s in stats.strikes_covered],
            expiries_covered=stats.expiries_covered
        )
        
        logger.info(f"API: Coverage: {stats.coverage_percentage:.1%}")
        return response
        
    except Exception as e:
        logger.error(f"API: Failed to get coverage - {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get coverage: {str(e)}")


@router.get("/quality", response_model=QualityReportResponse)
async def get_quality_report(
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    instrument_name: Optional[str] = Query(None, description="期权合约名称")
):
    """
    获取数据质量报告
    """
    try:
        logger.info(f"API: Getting quality report")
        
        manager = get_manager()
        report = manager.validate_data_quality(
            start_date=start_date,
            end_date=end_date,
            instrument_name=instrument_name
        )
        
        response = QualityReportResponse(
            total_records=report.total_records,
            missing_records=report.missing_records,
            anomaly_records=report.anomaly_records,
            coverage_percentage=report.coverage_percentage,
            quality_score=report.quality_score,
            time_range_start=report.time_range[0],
            time_range_end=report.time_range[1],
            issues_count=len(report.issues)
        )
        
        logger.info(f"API: Quality score: {report.quality_score:.1f}")
        return response
        
    except Exception as e:
        logger.error(f"API: Failed to get quality report - {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get quality report: {str(e)}")


@router.delete("/cache")
async def clear_cache(
    clear_database: bool = Query(False, description="是否同时清理数据库")
):
    """
    清理缓存
    """
    try:
        logger.info(f"API: Clearing cache (clear_database={clear_database})")
        
        manager = get_manager()
        manager.clear_cache(clear_database=clear_database)
        
        logger.info("API: Cache cleared successfully")
        return {"message": "Cache cleared successfully", "database_cleared": clear_database}
        
    except Exception as e:
        logger.error(f"API: Failed to clear cache - {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


@router.get("/stats", response_model=ManagerStatsResponse)
async def get_stats():
    """
    获取管理器统计信息
    """
    try:
        logger.info("API: Getting manager stats")
        
        manager = get_manager()
        stats = manager.get_stats()
        
        response = ManagerStatsResponse(
            download_dir=stats['download_dir'],
            csv_files=stats['csv_files'],
            database_records=stats['cache']['database']['record_count'],
            memory_cache_entries=stats['cache']['memory_cache']['entries'],
            memory_cache_size_mb=stats['cache']['memory_cache']['size_mb']
        )
        
        logger.info(f"API: Stats retrieved - {response.database_records} records")
        return response
        
    except Exception as e:
        logger.error(f"API: Failed to get stats - {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.get("/health")
async def health_check():
    """
    健康检查
    """
    try:
        manager = get_manager()
        stats = manager.get_stats()
        
        return {
            "status": "healthy",
            "database_records": stats['cache']['database']['record_count'],
            "cache_entries": stats['cache']['memory_cache']['entries']
        }
    except Exception as e:
        logger.error(f"API: Health check failed - {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.post("/export", response_model=ExportResponse)
async def export_data(request: ExportRequest):
    """
    导出历史数据
    
    支持导出为CSV或JSON格式
    """
    try:
        import json
        import csv
        from pathlib import Path
        
        logger.info(f"API: Exporting data (format={request.format})")
        
        manager = get_manager()
        
        # 查询数据
        data = manager.cache.query_option_data(
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        # 如果指定了合约，过滤数据
        if request.instruments:
            data = [d for d in data if d.instrument_name in request.instruments]
        
        if not data:
            raise HTTPException(status_code=404, detail="No data found for export")
        
        # 创建导出目录
        export_dir = Path("data/exports")
        export_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"historical_data_{timestamp}.{request.format}"
        filepath = export_dir / filename
        
        # 导出数据
        if request.format == "csv":
            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                # 写入表头
                writer.writerow([
                    'instrument_name', 'timestamp', 'open_price', 'high_price',
                    'low_price', 'close_price', 'volume', 'strike_price',
                    'expiry_date', 'option_type', 'underlying_symbol', 'data_source'
                ])
                # 写入数据
                for d in data:
                    writer.writerow([
                        d.instrument_name, d.timestamp.isoformat(), float(d.open_price),
                        float(d.high_price), float(d.low_price), float(d.close_price),
                        float(d.volume), float(d.strike_price), d.expiry_date.isoformat(),
                        d.option_type.value, d.underlying_symbol, d.data_source.value
                    ])
        
        elif request.format == "json":
            export_data = []
            for d in data:
                export_data.append({
                    'instrument_name': d.instrument_name,
                    'timestamp': d.timestamp.isoformat(),
                    'open_price': float(d.open_price),
                    'high_price': float(d.high_price),
                    'low_price': float(d.low_price),
                    'close_price': float(d.close_price),
                    'volume': float(d.volume),
                    'strike_price': float(d.strike_price),
                    'expiry_date': d.expiry_date.isoformat(),
                    'option_type': d.option_type.value,
                    'underlying_symbol': d.underlying_symbol,
                    'data_source': d.data_source.value
                })
            
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2)
        
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {request.format}")
        
        # 获取文件大小
        file_size = filepath.stat().st_size
        
        response = ExportResponse(
            file_path=str(filepath),
            records_exported=len(data),
            file_size_bytes=file_size,
            format=request.format
        )
        
        logger.info(f"API: Exported {len(data)} records to {filepath}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API: Export failed - {str(e)}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
