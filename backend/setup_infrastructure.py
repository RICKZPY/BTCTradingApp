#!/usr/bin/env python3
"""
Infrastructure setup script for Bitcoin Trading System
"""
import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"Running: {description}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("✗ Python 3.7+ is required")
        return False
    
    print("✓ Python version is compatible")
    return True

def create_directories():
    """Create necessary directories"""
    directories = [
        "database",
        "tasks",
        "core",
        "api",
        "tests",
        "logs",
        "alembic/versions"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {directory}")
    
    return True

def create_init_files():
    """Create __init__.py files for Python packages"""
    packages = [
        "database",
        "tasks", 
        "core",
        "api",
        "tests"
    ]
    
    for package in packages:
        init_file = Path(package) / "__init__.py"
        if not init_file.exists():
            init_file.write_text("# Package initialization\n")
            print(f"✓ Created {init_file}")
    
    return True

def test_database_connections():
    """Test database connections with basic imports"""
    try:
        # Test basic imports
        import psycopg2
        print("✓ PostgreSQL driver (psycopg2) is available")
        
        try:
            import redis
            print("✓ Redis client is available")
        except ImportError:
            print("⚠ Redis client not available - install with: pip install redis")
        
        try:
            from influxdb_client import InfluxDBClient
            print("✓ InfluxDB client is available")
        except ImportError:
            print("⚠ InfluxDB client not available - install with: pip install influxdb-client")
            
        return True
        
    except ImportError as e:
        print(f"✗ Database driver import failed: {e}")
        return False

def create_sample_env():
    """Create a sample .env file if it doesn't exist"""
    env_file = Path(".env")
    if env_file.exists():
        print("✓ .env file already exists")
        return True
    
    sample_env = """# Bitcoin Trading System Configuration

# Application
DEBUG=true
LOG_LEVEL=INFO
SECRET_KEY=change-this-in-production

# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=bitcoin_trading
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password

# InfluxDB Configuration  
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=your-token-here
INFLUXDB_ORG=trading-org
INFLUXDB_BUCKET=market-data

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# API Keys (Replace with your actual keys)
OPENAI_API_KEY=your-openai-key-here
BINANCE_API_KEY=your-binance-key-here
BINANCE_SECRET_KEY=your-binance-secret-here
BINANCE_TESTNET=true

# Trading Configuration
MAX_POSITION_SIZE=0.1
MAX_DAILY_LOSS=0.05
STOP_LOSS_PERCENTAGE=0.02
"""
    
    env_file.write_text(sample_env)
    print("✓ Created sample .env file")
    return True

def main():
    """Main setup function"""
    print("🚀 Setting up Bitcoin Trading System Infrastructure")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create directories
    if not create_directories():
        sys.exit(1)
    
    # Create __init__.py files
    if not create_init_files():
        sys.exit(1)
    
    # Create sample .env file
    if not create_sample_env():
        sys.exit(1)
    
    # Test database connections (if packages are installed)
    test_database_connections()
    
    print("\n" + "=" * 50)
    print("✅ Infrastructure setup completed!")
    print("\nNext steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Set up databases (PostgreSQL, InfluxDB, Redis)")
    print("3. Update .env file with your API keys")
    print("4. Run database migrations: alembic upgrade head")
    print("5. Start the application: python main.py")

if __name__ == "__main__":
    main()