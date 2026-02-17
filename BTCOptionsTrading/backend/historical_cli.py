#!/usr/bin/env python3
"""
Entry point for the historical data CLI tool
"""
import sys
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from src.historical.cli import historical_cli

if __name__ == '__main__':
    historical_cli()
