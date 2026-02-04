"""
API module for Bitcoin Trading System
Provides REST API endpoints for system interaction
"""

from .main import app
from .models import *
from .routes import *

__all__ = ['app']