"""
Settings API routes for configuration management.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
import os
from pathlib import Path

from ...config.settings import settings

router = APIRouter(prefix="/api/settings", tags=["settings"])


class DeribitConfig(BaseModel):
    """Deribit API configuration"""
    api_key: str = Field(..., description="Deribit API Key")
    api_secret: str = Field(..., description="Deribit API Secret")
    test_mode: bool = Field(default=True, description="Use test environment")


class TradingConfig(BaseModel):
    """Trading parameters configuration"""
    risk_free_rate: float = Field(default=0.05, ge=0, le=1, description="Risk-free rate")
    default_initial_capital: float = Field(default=100000.0, gt=0, description="Default initial capital")
    commission_rate: float = Field(default=0.001, ge=0, le=1, description="Commission rate")


class SystemConfig(BaseModel):
    """Complete system configuration"""
    deribit: Optional[DeribitConfig] = None
    trading: Optional[TradingConfig] = None


@router.get("/deribit")
async def get_deribit_config():
    """
    Get current Deribit API configuration (without secrets).
    """
    return {
        "api_key": settings.deribit.api_key[:8] + "..." if settings.deribit.api_key else "",
        "api_secret": "***" if settings.deribit.api_secret else "",
        "test_mode": settings.deribit.test_mode,
        "has_credentials": bool(settings.deribit.api_key and settings.deribit.api_secret)
    }


@router.post("/deribit")
async def update_deribit_config(config: DeribitConfig):
    """
    Update Deribit API configuration and save to .env file.
    """
    try:
        # Update in-memory settings
        settings.deribit.api_key = config.api_key
        settings.deribit.api_secret = config.api_secret
        settings.deribit.test_mode = config.test_mode
        
        # Update base URLs based on test mode
        if config.test_mode:
            settings.deribit.base_url = "https://test.deribit.com"
            settings.deribit.websocket_url = "wss://test.deribit.com/ws/api/v2"
        else:
            settings.deribit.base_url = "https://www.deribit.com"
            settings.deribit.websocket_url = "wss://www.deribit.com/ws/api/v2"
        
        # Save to .env file
        env_path = Path(__file__).parent.parent.parent.parent / ".env"
        
        # Read existing .env or create from .env.example
        if env_path.exists():
            with open(env_path, 'r') as f:
                lines = f.readlines()
        else:
            env_example = env_path.parent / ".env.example"
            if env_example.exists():
                with open(env_example, 'r') as f:
                    lines = f.readlines()
            else:
                lines = []
        
        # Update or add Deribit settings
        updated_keys = set()
        new_lines = []
        
        for line in lines:
            if line.strip().startswith('#') or not line.strip():
                new_lines.append(line)
                continue
            
            if '=' in line:
                key = line.split('=')[0].strip()
                
                if key == 'DERIBIT_API_KEY':
                    new_lines.append(f'DERIBIT_API_KEY="{config.api_key}"\n')
                    updated_keys.add(key)
                elif key == 'DERIBIT_API_SECRET':
                    new_lines.append(f'DERIBIT_API_SECRET="{config.api_secret}"\n')
                    updated_keys.add(key)
                elif key == 'DERIBIT_TEST_MODE':
                    new_lines.append(f'DERIBIT_TEST_MODE={str(config.test_mode).lower()}\n')
                    updated_keys.add(key)
                elif key == 'DERIBIT_BASE_URL':
                    new_lines.append(f'DERIBIT_BASE_URL="{settings.deribit.base_url}"\n')
                    updated_keys.add(key)
                elif key == 'DERIBIT_WS_URL':
                    new_lines.append(f'DERIBIT_WS_URL="{settings.deribit.websocket_url}"\n')
                    updated_keys.add(key)
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
        
        # Add missing keys
        if 'DERIBIT_API_KEY' not in updated_keys:
            new_lines.append(f'DERIBIT_API_KEY="{config.api_key}"\n')
        if 'DERIBIT_API_SECRET' not in updated_keys:
            new_lines.append(f'DERIBIT_API_SECRET="{config.api_secret}"\n')
        if 'DERIBIT_TEST_MODE' not in updated_keys:
            new_lines.append(f'DERIBIT_TEST_MODE={str(config.test_mode).lower()}\n')
        if 'DERIBIT_BASE_URL' not in updated_keys:
            new_lines.append(f'DERIBIT_BASE_URL="{settings.deribit.base_url}"\n')
        if 'DERIBIT_WS_URL' not in updated_keys:
            new_lines.append(f'DERIBIT_WS_URL="{settings.deribit.websocket_url}"\n')
        
        # Write back to .env
        with open(env_path, 'w') as f:
            f.writelines(new_lines)
        
        return {
            "success": True,
            "message": "Deribit configuration saved successfully",
            "test_mode": config.test_mode
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save configuration: {str(e)}")


@router.get("/trading")
async def get_trading_config():
    """
    Get current trading parameters.
    """
    return {
        "risk_free_rate": settings.trading.risk_free_rate,
        "default_initial_capital": settings.trading.default_initial_capital,
        "commission_rate": settings.trading.commission_rate
    }


@router.post("/trading")
async def update_trading_config(config: TradingConfig):
    """
    Update trading parameters and save to .env file.
    """
    try:
        # Update in-memory settings
        settings.trading.risk_free_rate = config.risk_free_rate
        settings.trading.default_initial_capital = config.default_initial_capital
        settings.trading.commission_rate = config.commission_rate
        
        # Save to .env file
        env_path = Path(__file__).parent.parent.parent.parent / ".env"
        
        # Read existing .env
        if env_path.exists():
            with open(env_path, 'r') as f:
                lines = f.readlines()
        else:
            env_example = env_path.parent / ".env.example"
            if env_example.exists():
                with open(env_example, 'r') as f:
                    lines = f.readlines()
            else:
                lines = []
        
        # Update or add trading settings
        updated_keys = set()
        new_lines = []
        
        for line in lines:
            if line.strip().startswith('#') or not line.strip():
                new_lines.append(line)
                continue
            
            if '=' in line:
                key = line.split('=')[0].strip()
                
                if key == 'RISK_FREE_RATE':
                    new_lines.append(f'RISK_FREE_RATE={config.risk_free_rate}\n')
                    updated_keys.add(key)
                elif key == 'DEFAULT_INITIAL_CAPITAL':
                    new_lines.append(f'DEFAULT_INITIAL_CAPITAL={config.default_initial_capital}\n')
                    updated_keys.add(key)
                elif key == 'COMMISSION_RATE':
                    new_lines.append(f'COMMISSION_RATE={config.commission_rate}\n')
                    updated_keys.add(key)
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
        
        # Add missing keys
        if 'RISK_FREE_RATE' not in updated_keys:
            new_lines.append(f'RISK_FREE_RATE={config.risk_free_rate}\n')
        if 'DEFAULT_INITIAL_CAPITAL' not in updated_keys:
            new_lines.append(f'DEFAULT_INITIAL_CAPITAL={config.default_initial_capital}\n')
        if 'COMMISSION_RATE' not in updated_keys:
            new_lines.append(f'COMMISSION_RATE={config.commission_rate}\n')
        
        # Write back to .env
        with open(env_path, 'w') as f:
            f.writelines(new_lines)
        
        return {
            "success": True,
            "message": "Trading configuration saved successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save configuration: {str(e)}")


@router.get("/system-info")
async def get_system_info():
    """
    Get system information and status.
    """
    return {
        "version": settings.app_version,
        "environment": settings.environment,
        "api_status": "online",
        "database_type": settings.database.db_type,
        "database_status": "connected",
        "deribit_mode": "test" if settings.deribit.test_mode else "production",
        "deribit_status": "configured" if settings.deribit.api_key else "not_configured"
    }
