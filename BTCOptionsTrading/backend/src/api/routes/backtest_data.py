"""
回测数据选择器 API 接口
提供历史数据查询、数据质量统计和数据预览功能
"""

from typing import List, Optional, Dict
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, validator
from datetime import datetime, date

router = APIRouter()


# ============================================================================
# Pydantic 数据模型
# ============================================================================

class DateRange(BaseModel):
    """日期范围模型"""
    start_date: str = Field(..., description="开始日期 (ISO 8601 格式)")
    end_date: str = Field(..., description="结束日期 (ISO 8601 格式)")
    
    @validator('start_date', 'end_date')
    def validate_date_format(cls, v):
        """验证日期格式"""
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            raise ValueError(f"Invalid date format: {v}. Expected ISO 8601 format.")
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        """验证日期范围逻辑"""
        if 'start_date' in values:
            start = datetime.fromisoformat(values['start_date'].replace('Z', '+00:00'))
            end = datetime.fromisoformat(v.replace('Z', '+00:00'))
            if start > end:
                raise ValueError("start_date must be less than or equal to end_date")
        return v


class Instrument(BaseModel):
    """期权合约模型"""
    symbol: str = Field(..., description="合约名称")
    expiry_date: str = Field(..., description="到期日期")
    type: str = Field(..., description="期权类型 (call/put)")
    strike: float = Field(..., description="执行价格")
    available_date_range: DateRange = Field(..., description="数据可用日期范围")


class AvailableDatesResponse(BaseModel):
    """可用日期响应模型"""
    dates: List[str] = Field(..., description="可用日期列表 (ISO 8601 格式)")
    earliest: str = Field(..., description="最早日期")
    latest: str = Field(..., description="最晚日期")


class AvailableInstrumentsResponse(BaseModel):
    """可用合约响应模型"""
    instruments: List[Instrument] = Field(..., description="合约列表")
    total_count: int = Field(..., description="合约总数")


class CoverageStatsResponse(BaseModel):
    """数据覆盖率统计响应模型"""
    coverage_percentage: float = Field(..., description="数据覆盖率百分比")
    total_data_points: int = Field(..., description="总数据点数")
    missing_data_points: int = Field(..., description="缺失数据点数")
    date_range: DateRange = Field(..., description="查询的日期范围")
    instrument_count: int = Field(..., description="合约数量")


class PrepareDataRequest(BaseModel):
    """准备数据请求模型"""
    date_range: DateRange = Field(..., description="日期范围")
    instruments: List[str] = Field(..., min_items=1, max_items=100, description="合约列表")
    
    @validator('instruments')
    def validate_instruments(cls, v):
        """验证合约列表"""
        if not v:
            raise ValueError("instruments list cannot be empty")
        if len(v) > 100:
            raise ValueError("instruments list cannot exceed 100 items")
        return v


class PrepareDataResponse(BaseModel):
    """准备数据响应模型"""
    dataset_id: str = Field(..., description="数据集ID")
    total_records: int = Field(..., description="总记录数")
    status: str = Field(..., description="状态 (ready/processing/error)")


class DataRecord(BaseModel):
    """数据记录模型"""
    timestamp: str = Field(..., description="时间戳")
    instrument: str = Field(..., description="合约名称")
    price: float = Field(..., description="价格")
    volume: int = Field(..., description="成交量")


class PreviewDataResponse(BaseModel):
    """预览数据响应模型"""
    total_records: int = Field(..., description="总记录数")
    sample_records: List[DataRecord] = Field(..., description="样本记录")


class ErrorResponse(BaseModel):
    """错误响应模型"""
    error: str = Field(..., description="错误类型")
    message: str = Field(..., description="错误消息")
    details: Optional[Dict] = Field(None, description="错误详情")
    timestamp: str = Field(..., description="错误发生时间")


# ============================================================================
# API 端点
# ============================================================================

@router.get(
    "/available-dates",
    response_model=AvailableDatesResponse,
    summary="获取可用日期列表",
    description="返回系统中所有有历史数据的日期列表",
    responses={
        200: {"description": "成功返回可用日期列表"},
        500: {"description": "服务器内部错误", "model": ErrorResponse}
    }
)
async def get_available_dates():
    """
    获取所有可用的历史数据日期
    
    Returns:
        AvailableDatesResponse: 包含日期列表、最早和最晚日期
    """
    try:
        # TODO: 实现实际的数据查询逻辑
        # 这里需要调用 HistoricalDataManager.get_available_dates()
        
        # 临时返回示例数据
        dates = [
            "2024-01-01",
            "2024-01-02",
            "2024-01-03"
        ]
        
        return AvailableDatesResponse(
            dates=dates,
            earliest=dates[0] if dates else "",
            latest=dates[-1] if dates else ""
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="INTERNAL_SERVER_ERROR",
                message=f"Failed to fetch available dates: {str(e)}",
                timestamp=datetime.now().isoformat()
            ).dict()
        )


@router.get(
    "/available-instruments",
    response_model=AvailableInstrumentsResponse,
    summary="获取可用合约列表",
    description="返回可用的期权合约列表，可选按日期范围过滤",
    responses={
        200: {"description": "成功返回合约列表"},
        400: {"description": "请求参数错误", "model": ErrorResponse},
        500: {"description": "服务器内部错误", "model": ErrorResponse}
    }
)
async def get_available_instruments(
    start_date: Optional[str] = Query(None, description="开始日期 (ISO 8601)"),
    end_date: Optional[str] = Query(None, description="结束日期 (ISO 8601)")
):
    """
    获取可用的合约列表
    
    Args:
        start_date: 开始日期（可选）
        end_date: 结束日期（可选）
    
    Returns:
        AvailableInstrumentsResponse: 包含合约列表和总数
    """
    try:
        # 验证日期参数
        if start_date and end_date:
            try:
                date_range = DateRange(start_date=start_date, end_date=end_date)
            except ValueError as e:
                raise HTTPException(
                    status_code=400,
                    detail=ErrorResponse(
                        error="INVALID_DATE_RANGE",
                        message=str(e),
                        details={"start_date": start_date, "end_date": end_date},
                        timestamp=datetime.now().isoformat()
                    ).dict()
                )
        
        # TODO: 实现实际的数据查询逻辑
        # 这里需要调用 HistoricalDataManager.get_available_instruments()
        
        # 临时返回示例数据
        instruments = [
            Instrument(
                symbol="BTC-31MAR24-50000-C",
                expiry_date="2024-03-31",
                type="call",
                strike=50000.0,
                available_date_range=DateRange(
                    start_date="2024-01-01",
                    end_date="2024-03-31"
                )
            )
        ]
        
        return AvailableInstrumentsResponse(
            instruments=instruments,
            total_count=len(instruments)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="INTERNAL_SERVER_ERROR",
                message=f"Failed to fetch available instruments: {str(e)}",
                timestamp=datetime.now().isoformat()
            ).dict()
        )


@router.get(
    "/coverage-stats",
    response_model=CoverageStatsResponse,
    summary="获取数据覆盖率统计",
    description="返回指定日期范围和合约的数据覆盖率统计信息",
    responses={
        200: {"description": "成功返回覆盖率统计"},
        400: {"description": "请求参数错误", "model": ErrorResponse},
        404: {"description": "未找到数据", "model": ErrorResponse},
        500: {"description": "服务器内部错误", "model": ErrorResponse}
    }
)
async def get_coverage_stats(
    start_date: str = Query(..., description="开始日期 (ISO 8601)"),
    end_date: str = Query(..., description="结束日期 (ISO 8601)"),
    instruments: Optional[List[str]] = Query(None, description="合约列表（可选）")
):
    """
    获取数据覆盖率统计
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        instruments: 合约列表（可选）
    
    Returns:
        CoverageStatsResponse: 数据覆盖率统计信息
    """
    try:
        # 验证日期范围
        try:
            date_range = DateRange(start_date=start_date, end_date=end_date)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponse(
                    error="INVALID_DATE_RANGE",
                    message=str(e),
                    details={"start_date": start_date, "end_date": end_date},
                    timestamp=datetime.now().isoformat()
                ).dict()
            )
        
        # TODO: 实现实际的数据查询逻辑
        # 这里需要调用 HistoricalDataManager.get_coverage_stats()
        
        # 临时返回示例数据
        return CoverageStatsResponse(
            coverage_percentage=95.5,
            total_data_points=10000,
            missing_data_points=450,
            date_range=date_range,
            instrument_count=len(instruments) if instruments else 0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="INTERNAL_SERVER_ERROR",
                message=f"Failed to fetch coverage stats: {str(e)}",
                timestamp=datetime.now().isoformat()
            ).dict()
        )


@router.post(
    "/prepare-data",
    response_model=PrepareDataResponse,
    summary="准备回测数据集",
    description="根据指定的日期范围和合约列表准备回测数据集",
    responses={
        200: {"description": "成功准备数据集"},
        400: {"description": "请求参数错误", "model": ErrorResponse},
        404: {"description": "未找到数据", "model": ErrorResponse},
        500: {"description": "服务器内部错误", "model": ErrorResponse}
    }
)
async def prepare_backtest_data(request: PrepareDataRequest):
    """
    准备回测数据集
    
    Args:
        request: 包含日期范围和合约列表的请求
    
    Returns:
        PrepareDataResponse: 数据集ID和状态信息
    """
    try:
        # TODO: 实现实际的数据准备逻辑
        # 这里需要调用 HistoricalDataManager.get_data_for_backtest()
        
        # 临时返回示例数据
        import uuid
        dataset_id = str(uuid.uuid4())
        
        return PrepareDataResponse(
            dataset_id=dataset_id,
            total_records=10000,
            status="ready"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error="INVALID_REQUEST",
                message=str(e),
                timestamp=datetime.now().isoformat()
            ).dict()
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="INTERNAL_SERVER_ERROR",
                message=f"Failed to prepare data: {str(e)}",
                timestamp=datetime.now().isoformat()
            ).dict()
        )


@router.get(
    "/preview-data",
    response_model=PreviewDataResponse,
    summary="预览回测数据",
    description="返回指定条件的数据样本，用于预览",
    responses={
        200: {"description": "成功返回数据预览"},
        400: {"description": "请求参数错误", "model": ErrorResponse},
        404: {"description": "未找到数据", "model": ErrorResponse},
        500: {"description": "服务器内部错误", "model": ErrorResponse}
    }
)
async def preview_backtest_data(
    start_date: str = Query(..., description="开始日期 (ISO 8601)"),
    end_date: str = Query(..., description="结束日期 (ISO 8601)"),
    instruments: List[str] = Query(..., description="合约列表"),
    limit: int = Query(10, ge=1, le=100, description="返回记录数")
):
    """
    预览回测数据
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        instruments: 合约列表
        limit: 返回记录数（默认10，最多100）
    
    Returns:
        PreviewDataResponse: 数据样本和总记录数
    """
    try:
        # 验证日期范围
        try:
            date_range = DateRange(start_date=start_date, end_date=end_date)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponse(
                    error="INVALID_DATE_RANGE",
                    message=str(e),
                    details={"start_date": start_date, "end_date": end_date},
                    timestamp=datetime.now().isoformat()
                ).dict()
            )
        
        # 验证合约列表
        if not instruments:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponse(
                    error="INVALID_REQUEST",
                    message="instruments list cannot be empty",
                    timestamp=datetime.now().isoformat()
                ).dict()
            )
        
        # TODO: 实现实际的数据查询逻辑
        # 这里需要调用 HistoricalDataManager.get_data_for_backtest()
        
        # 临时返回示例数据
        sample_records = [
            DataRecord(
                timestamp="2024-01-01T00:00:00Z",
                instrument=instruments[0],
                price=2500.0,
                volume=100
            )
        ]
        
        return PreviewDataResponse(
            total_records=10000,
            sample_records=sample_records[:limit]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="INTERNAL_SERVER_ERROR",
                message=f"Failed to preview data: {str(e)}",
                timestamp=datetime.now().isoformat()
            ).dict()
        )
